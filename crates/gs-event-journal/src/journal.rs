use crate::{
    EventError, EventOffset,
    format::{IndexRecord, header_bytes, next_chain_digest, parse_index, record_bytes},
};
use gs_canonical_json::{Digest, canonical_bytes, canonical_digest, sha256_digest};
use gs_cas::Cas;
use gs_eval_ir::{EvaluationIr, RunEvent, SchemaName, parse_named_json, validate_named_json};
use std::{
    fs::{self, File, OpenOptions},
    io::{Read, Seek, SeekFrom, Write},
    path::{Path, PathBuf},
};

#[derive(Debug, Clone, PartialEq)]
pub struct JournalRecord {
    pub offset: EventOffset,
    pub event_digest: Digest,
    pub chain_digest: Digest,
    pub event: RunEvent,
}

pub trait EventSink {
    fn append(&self, event: &RunEvent) -> Result<EventOffset, EventError>;
}

pub trait EventSource {
    fn run_id(&self) -> &str;
    fn read_from(&self, start: EventOffset) -> Result<Vec<JournalRecord>, EventError>;
}

pub struct LocalEventJournal<C: Cas> {
    run_id: String,
    run_id_digest: Digest,
    journal_path: PathBuf,
    cas: C,
}

impl<C: Cas> LocalEventJournal<C> {
    pub fn open(
        root: impl AsRef<Path>,
        cas: C,
        run_id: impl Into<String>,
    ) -> Result<Self, EventError> {
        let run_id = run_id.into();
        let run_id_digest = sha256_digest(run_id.as_bytes());
        let root = ensure_directory(root.as_ref())?;
        let runs = ensure_directory(&root.join("runs"))?;
        let journal_path = runs.join(format!("{}.gsej", digest_hex(run_id_digest)));
        initialize_journal(&journal_path, run_id_digest)?;

        Ok(Self {
            run_id,
            run_id_digest,
            journal_path,
            cas,
        })
    }

    pub fn journal_path(&self) -> &Path {
        &self.journal_path
    }

    fn validated_event_bytes(&self, event: &RunEvent) -> Result<Vec<u8>, EventError> {
        if event.run_id != self.run_id {
            return Err(EventError::RunIdMismatch {
                expected: self.run_id.clone(),
                actual: event.run_id.clone(),
            });
        }

        let payload_value = serde_json::to_value(&event.payload)?;
        let expected_payload_digest = canonical_digest(&payload_value)?.to_string();
        if event.payload_digest != expected_payload_digest {
            return Err(EventError::PayloadDigestMismatch {
                expected: expected_payload_digest,
                actual: event.payload_digest.clone(),
            });
        }

        let value = serde_json::to_value(event)?;
        validate_named_json(SchemaName::RunEvent, &value)?;
        Ok(canonical_bytes(&value)?)
    }

    fn read_event(&self, record: IndexRecord) -> Result<JournalRecord, EventError> {
        let bytes = self.cas.get(&record.event_digest)?;
        let value: serde_json::Value = serde_json::from_slice(&bytes)?;
        if canonical_bytes(&value)? != bytes {
            return Err(EventError::NonCanonicalEvent {
                offset: record.offset.get(),
            });
        }

        let event = match parse_named_json(SchemaName::RunEvent, &value)? {
            EvaluationIr::RunEvent(event) => event,
            _ => return Err(EventError::TypeMismatch),
        };
        if event.run_id != self.run_id {
            return Err(EventError::RunIdMismatch {
                expected: self.run_id.clone(),
                actual: event.run_id,
            });
        }
        if event.sequence != record.offset.get() {
            return Err(EventError::CorruptOffset {
                expected: record.offset.get(),
                actual: event.sequence,
            });
        }

        let payload_value = serde_json::to_value(&event.payload)?;
        let expected_payload_digest = canonical_digest(&payload_value)?.to_string();
        if event.payload_digest != expected_payload_digest {
            return Err(EventError::PayloadDigestMismatch {
                expected: expected_payload_digest,
                actual: event.payload_digest,
            });
        }

        Ok(JournalRecord {
            offset: record.offset,
            event_digest: record.event_digest,
            chain_digest: record.chain_digest,
            event,
        })
    }

    fn read_index_shared(&self) -> Result<Vec<IndexRecord>, EventError> {
        validate_regular_file(&self.journal_path)?;
        let mut file = OpenOptions::new()
            .read(true)
            .open(&self.journal_path)
            .map_err(|source| {
                EventError::io("open journal for replay", &self.journal_path, source)
            })?;
        file.lock_shared().map_err(|source| {
            EventError::io("lock journal for replay", &self.journal_path, source)
        })?;
        let bytes = read_all(&mut file, &self.journal_path)?;
        parse_index(&bytes, self.run_id_digest)
    }
}

impl<C: Cas> EventSink for LocalEventJournal<C> {
    fn append(&self, event: &RunEvent) -> Result<EventOffset, EventError> {
        let event_bytes = self.validated_event_bytes(event)?;
        let event_digest = self.cas.put(&event_bytes)?;

        validate_regular_file(&self.journal_path)?;
        let mut file = OpenOptions::new()
            .read(true)
            .append(true)
            .open(&self.journal_path)
            .map_err(|source| {
                EventError::io("open journal for append", &self.journal_path, source)
            })?;
        file.lock().map_err(|source| {
            EventError::io("lock journal for append", &self.journal_path, source)
        })?;
        let bytes = read_all(&mut file, &self.journal_path)?;
        let records = parse_index(&bytes, self.run_id_digest)?;
        let expected = records.len() as u64;

        if event.sequence < expected {
            let existing = records[event.sequence as usize];
            if existing.event_digest == event_digest {
                return Ok(existing.offset);
            }
            return Err(EventError::SequenceConflict {
                offset: event.sequence,
                existing: existing.event_digest.to_string(),
                attempted: event_digest.to_string(),
            });
        }
        if event.sequence > expected {
            return Err(EventError::SequenceGap {
                expected,
                actual: event.sequence,
            });
        }

        let offset = EventOffset::new(event.sequence);
        let previous_chain = records.last().map(|record| record.chain_digest);
        let chain_digest =
            next_chain_digest(self.run_id_digest, previous_chain, offset, event_digest);
        let record = IndexRecord {
            offset,
            event_digest,
            chain_digest,
        };
        file.write_all(&record_bytes(record)).map_err(|source| {
            EventError::io("append journal record", &self.journal_path, source)
        })?;
        file.sync_all()
            .map_err(|source| EventError::io("sync journal record", &self.journal_path, source))?;
        Ok(offset)
    }
}

impl<C: Cas> EventSource for LocalEventJournal<C> {
    fn run_id(&self) -> &str {
        &self.run_id
    }

    fn read_from(&self, start: EventOffset) -> Result<Vec<JournalRecord>, EventError> {
        let index = self.read_index_shared()?;
        index
            .into_iter()
            .skip(start.get() as usize)
            .map(|record| self.read_event(record))
            .collect()
    }
}

fn read_all(file: &mut File, path: &Path) -> Result<Vec<u8>, EventError> {
    file.seek(SeekFrom::Start(0))
        .map_err(|source| EventError::io("seek journal", path, source))?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|source| EventError::io("read journal", path, source))?;
    Ok(bytes)
}

fn initialize_journal(path: &Path, run_id_digest: Digest) -> Result<(), EventError> {
    match OpenOptions::new()
        .read(true)
        .append(true)
        .create_new(true)
        .open(path)
    {
        Ok(mut file) => {
            file.lock()
                .map_err(|source| EventError::io("lock new journal", path, source))?;
            file.write_all(&header_bytes(run_id_digest))
                .map_err(|source| EventError::io("write journal header", path, source))?;
            file.sync_all()
                .map_err(|source| EventError::io("sync journal header", path, source))?;
            Ok(())
        }
        Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
            validate_regular_file(path)?;
            let mut file = OpenOptions::new()
                .read(true)
                .open(path)
                .map_err(|source| EventError::io("open existing journal", path, source))?;
            file.lock_shared()
                .map_err(|source| EventError::io("lock existing journal", path, source))?;
            let bytes = read_all(&mut file, path)?;
            parse_index(&bytes, run_id_digest).map(|_| ())
        }
        Err(source) => Err(EventError::io("create journal", path, source)),
    }
}

fn ensure_directory(path: &Path) -> Result<PathBuf, EventError> {
    match fs::symlink_metadata(path) {
        Ok(metadata) => validate_directory_metadata(path, &metadata)?,
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => {
            fs::create_dir_all(path)
                .map_err(|source| EventError::io("create journal directory", path, source))?;
            let metadata = fs::symlink_metadata(path)
                .map_err(|source| EventError::io("inspect journal directory", path, source))?;
            validate_directory_metadata(path, &metadata)?;
        }
        Err(source) => return Err(EventError::io("inspect journal directory", path, source)),
    }

    fs::canonicalize(path)
        .map_err(|source| EventError::io("canonicalize journal directory", path, source))
}

fn validate_directory_metadata(path: &Path, metadata: &fs::Metadata) -> Result<(), EventError> {
    if metadata.file_type().is_symlink() {
        return Err(EventError::UnsafePath {
            path: path.to_path_buf(),
            reason: "directory is a symbolic link",
        });
    }
    if !metadata.is_dir() {
        return Err(EventError::UnsafePath {
            path: path.to_path_buf(),
            reason: "path is not a directory",
        });
    }
    Ok(())
}

fn validate_regular_file(path: &Path) -> Result<(), EventError> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|source| EventError::io("inspect journal file", path, source))?;
    if metadata.file_type().is_symlink() {
        return Err(EventError::UnsafePath {
            path: path.to_path_buf(),
            reason: "journal is a symbolic link",
        });
    }
    if !metadata.is_file() {
        return Err(EventError::UnsafePath {
            path: path.to_path_buf(),
            reason: "journal is not a regular file",
        });
    }
    Ok(())
}

fn digest_hex(digest: Digest) -> String {
    digest
        .to_string()
        .strip_prefix("sha256:")
        .expect("Digest Display contract includes sha256 prefix")
        .to_owned()
}
