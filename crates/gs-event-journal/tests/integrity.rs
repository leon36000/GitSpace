use gs_canonical_json::canonical_digest;
use gs_cas::LocalCas;
use gs_eval_ir::{Extensions, RunEvent};
use gs_event_journal::{EventError, EventOffset, EventSink, EventSource, LocalEventJournal};
use serde_json::Value;
use std::{
    collections::BTreeMap,
    fs::{self, OpenOptions},
    io::{Seek, SeekFrom, Write},
    path::{Path, PathBuf},
    sync::{
        Arc, Barrier,
        atomic::{AtomicU64, Ordering},
    },
    thread,
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const RUN_1: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FD1";
const RUN_2: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FD2";
const RUN_3: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FD3";
const RUN_4: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FD4";
const RUN_5: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FD5";

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task6-integrity-{label}-{}-{serial}",
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

fn event(run_id: &str, sequence: u64, event_type: &str) -> RunEvent {
    let mut payload = BTreeMap::new();
    payload.insert(
        "sequence".to_owned(),
        Value::Number(serde_json::Number::from(sequence)),
    );
    let payload_digest = canonical_digest(&serde_json::to_value(&payload).unwrap())
        .unwrap()
        .to_string();
    RunEvent {
        version: 1,
        run_id: run_id.to_owned(),
        sequence,
        event_type: event_type.to_owned(),
        occurred_at: format!("2026-08-14T03:00:{sequence:02}Z"),
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
fn corrupt_header_magic_is_rejected() {
    let root = TestDir::new("magic");
    let journal = journal(&root, RUN_1);
    let mut file = OpenOptions::new()
        .write(true)
        .open(journal.journal_path())
        .unwrap();
    file.write_all(b"X").unwrap();
    file.sync_all().unwrap();

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::InvalidHeader { .. }
    ));
}

#[test]
fn changed_record_offset_is_rejected() {
    let root = TestDir::new("offset");
    let journal = journal(&root, RUN_2);
    journal.append(&event(RUN_2, 0, "RUN_STARTED")).unwrap();

    let mut file = OpenOptions::new()
        .read(true)
        .write(true)
        .open(journal.journal_path())
        .unwrap();
    file.seek(SeekFrom::Start(40)).unwrap();
    file.write_all(&1_u64.to_be_bytes()).unwrap();
    file.sync_all().unwrap();

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::CorruptOffset {
            expected: 0,
            actual: 1
        }
    ));
}

#[test]
fn corrupted_cas_event_is_rejected_during_replay() {
    let root = TestDir::new("cas-corrupt");
    let cas_root = root.path().join("cas");
    let journal = LocalEventJournal::open(
        root.path().join("journal"),
        LocalCas::open(&cas_root).unwrap(),
        RUN_3,
    )
    .unwrap();
    journal.append(&event(RUN_3, 0, "RUN_STARTED")).unwrap();
    let digest = journal.read_from(EventOffset::new(0)).unwrap()[0].event_digest;
    let object_path = LocalCas::open(&cas_root).unwrap().object_path(&digest);
    fs::write(object_path, b"corrupted event bytes").unwrap();

    assert!(matches!(
        journal.read_from(EventOffset::new(0)).unwrap_err(),
        EventError::Cas(_)
    ));
}

#[test]
fn read_from_returns_the_requested_verified_suffix() {
    let root = TestDir::new("suffix");
    let journal = journal(&root, RUN_4);
    journal.append(&event(RUN_4, 0, "RUN_STARTED")).unwrap();
    journal.append(&event(RUN_4, 1, "RUN_FINISHED")).unwrap();

    let suffix = journal.read_from(EventOffset::new(1)).unwrap();
    assert_eq!(suffix.len(), 1);
    assert_eq!(suffix[0].offset, EventOffset::new(1));
    assert_eq!(suffix[0].event.event_type, "RUN_FINISHED");
    assert!(journal.read_from(EventOffset::new(2)).unwrap().is_empty());
    assert!(
        journal
            .read_from(EventOffset::new(u64::MAX))
            .unwrap()
            .is_empty()
    );
}

#[test]
fn independent_handles_serialize_an_identical_retry() {
    let root = TestDir::new("independent-handles");
    let journal_root = root.path().join("journal");
    let cas_root = root.path().join("cas");
    let first = Arc::new(
        LocalEventJournal::open(&journal_root, LocalCas::open(&cas_root).unwrap(), RUN_5).unwrap(),
    );
    let second = Arc::new(
        LocalEventJournal::open(&journal_root, LocalCas::open(&cas_root).unwrap(), RUN_5).unwrap(),
    );
    let event = event(RUN_5, 0, "RUN_STARTED");
    let barrier = Arc::new(Barrier::new(3));

    let handles = [first.clone(), second]
        .into_iter()
        .map(|journal| {
            let event = event.clone();
            let barrier = barrier.clone();
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
    assert_eq!(first.read_from(EventOffset::new(0)).unwrap().len(), 1);
}
