use gs_canonical_json::canonical_digest;
use gs_cas::{Cas, LocalCas};
use gs_eval_ir::{Extensions, RunEvent};
use gs_event_journal::{EventError, EventOffset, EventSink, EventSource, LocalEventJournal};
use serde_json::Value;
use std::{
    collections::BTreeMap,
    fs::{self, OpenOptions},
    io::{Read, Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    sync::{
        Arc, Barrier,
        atomic::{AtomicU64, Ordering},
    },
    thread,
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const RUN_1: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB1";
const RUN_2: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB2";
const RUN_3: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB3";
const RUN_4: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB4";
const RUN_5: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB5";
const RUN_6: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB6";
const RUN_7: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB7";
const RUN_8: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB8";
const RUN_WRONG: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FC0";

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task6-adversarial-{label}-{}-{serial}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TestDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn event(run_id: &str, sequence: u64, event_type: &str, message: &str) -> RunEvent {
    let mut payload = BTreeMap::new();
    payload.insert("message".to_owned(), Value::String(message.to_owned()));
    let payload_digest = canonical_digest(&serde_json::to_value(&payload).unwrap())
        .unwrap()
        .to_string();
    RunEvent {
        version: 1,
        run_id: run_id.to_owned(),
        sequence,
        event_type: event_type.to_owned(),
        occurred_at: format!("2026-08-14T01:00:{sequence:02}Z"),
        payload,
        payload_digest,
        extensions: Extensions::new(),
    }
}

fn journal(root: &TestDir, run_id: &str) -> LocalEventJournal<LocalCas> {
    LocalEventJournal::open(
        root.path().join("journal"),
        LocalCas::open(root.path().join("cas")).unwrap(),
        run_id,
    )
    .unwrap()
}

#[test]
fn truncated_header_is_rejected() {
    let root = TestDir::new("truncated-header");
    let journal = journal(&root, RUN_8);
    OpenOptions::new()
        .write(true)
        .open(journal.journal_path())
        .unwrap()
        .set_len(10)
        .unwrap();

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::InvalidHeader { .. }
    ));
}

#[test]
fn truncated_record_tail_blocks_replay_and_future_append() {
    let root = TestDir::new("truncated-tail");
    let journal = journal(&root, RUN_1);
    journal
        .append(&event(RUN_1, 0, "RUN_STARTED", "ok"))
        .unwrap();

    let mut file = OpenOptions::new()
        .append(true)
        .open(journal.journal_path())
        .unwrap();
    file.write_all(&[0xaa, 0xbb, 0xcc]).unwrap();
    file.sync_all().unwrap();
    drop(file);

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::TruncatedTail { trailing_bytes: 3 }
    ));
    assert!(matches!(
        journal
            .append(&event(RUN_1, 1, "RUN_FINISHED", "blocked"))
            .unwrap_err(),
        EventError::TruncatedTail { trailing_bytes: 3 }
    ));
}

#[test]
fn changed_chain_digest_is_detected() {
    let root = TestDir::new("chain");
    let journal = journal(&root, RUN_2);
    journal
        .append(&event(RUN_2, 0, "RUN_STARTED", "chain"))
        .unwrap();

    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .open(journal.journal_path())
        .unwrap();
    let final_byte = file.metadata().unwrap().len() - 1;
    file.seek(SeekFrom::Start(final_byte)).unwrap();
    let mut byte = [0_u8; 1];
    file.read_exact(&mut byte).unwrap();
    byte[0] ^= 0x01;
    file.seek(SeekFrom::Start(final_byte)).unwrap();
    file.write_all(&byte).unwrap();
    file.sync_all().unwrap();
    drop(file);

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::CorruptChain { offset: 0, .. }
    ));
}

#[test]
fn same_sequence_with_different_event_is_conflict() {
    let root = TestDir::new("conflict");
    let journal = journal(&root, RUN_3);
    journal
        .append(&event(RUN_3, 0, "RUN_STARTED", "first"))
        .unwrap();

    let error = journal
        .append(&event(RUN_3, 0, "RUN_STARTED", "different"))
        .unwrap_err();
    assert!(matches!(
        error,
        EventError::SequenceConflict { offset: 0, .. }
    ));
}

#[test]
fn run_id_mismatch_is_rejected() {
    let root = TestDir::new("run-id");
    let journal = journal(&root, RUN_4);

    let error = journal
        .append(&event(RUN_WRONG, 0, "RUN_STARTED", "wrong"))
        .unwrap_err();
    assert!(matches!(error, EventError::RunIdMismatch { .. }));
}

#[test]
fn concurrent_identical_writers_commit_one_record() {
    let root = TestDir::new("concurrent");
    let journal = Arc::new(journal(&root, RUN_5));
    let event = event(RUN_5, 0, "RUN_STARTED", "same");
    let barrier = Arc::new(Barrier::new(3));

    let handles = (0..2)
        .map(|_| {
            let journal = Arc::clone(&journal);
            let event = event.clone();
            let barrier = Arc::clone(&barrier);
            thread::spawn(move || {
                barrier.wait();
                journal.append(&event)
            })
        })
        .collect::<Vec<_>>();
    barrier.wait();

    for handle in handles {
        assert_eq!(handle.join().unwrap().unwrap(), EventOffset::new(0));
    }
    assert_eq!(journal.read_from(EventOffset::new(0)).unwrap().len(), 1);
}

#[test]
fn missing_cas_object_is_detected_during_replay() {
    let root = TestDir::new("missing-cas");
    let cas_root = root.path().join("cas");
    let journal = LocalEventJournal::open(
        root.path().join("journal"),
        LocalCas::open(&cas_root).unwrap(),
        RUN_6,
    )
    .unwrap();
    journal
        .append(&event(RUN_6, 0, "RUN_STARTED", "stored"))
        .unwrap();
    let digest = journal.read_from(EventOffset::new(0)).unwrap()[0].event_digest;
    let object_path = LocalCas::open(&cas_root).unwrap().object_path(&digest);
    fs::remove_file(object_path).unwrap();

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::Cas(_)
    ));
}

#[cfg(unix)]
#[test]
fn symlink_replacement_is_rejected() {
    use std::os::unix::fs::symlink;

    let root = TestDir::new("symlink");
    let journal = journal(&root, RUN_7);
    journal
        .append(&event(RUN_7, 0, "RUN_STARTED", "safe"))
        .unwrap();

    let target = root.path().join("attacker-controlled");
    fs::write(&target, b"not a journal").unwrap();
    fs::remove_file(journal.journal_path()).unwrap();
    symlink(&target, journal.journal_path()).unwrap();

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::UnsafePath { .. }
    ));
}
