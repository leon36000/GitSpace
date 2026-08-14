use gs_canonical_json::{canonical_bytes, canonical_digest};
use gs_cas::{Cas, LocalCas};
use gs_eval_ir::{Extensions, RunEvent};
use gs_event_journal::{
    EventError, EventOffset, EventSink, EventSource, LocalEventJournal, projection_bytes,
    rebuild_run_projection,
};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const RUN_1: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FAV";
const RUN_2: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FAW";
const RUN_3: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FAX";
const RUN_4: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FAY";
const RUN_5: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FAZ";
const RUN_6: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB0";

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task6-{label}-{}-{serial}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).expect("create test directory");
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
    let payload_value = serde_json::to_value(&payload).expect("serialize payload");

    RunEvent {
        version: 1,
        run_id: run_id.to_owned(),
        sequence,
        event_type: event_type.to_owned(),
        occurred_at: format!("2026-08-14T00:00:{sequence:02}Z"),
        payload,
        payload_digest: canonical_digest(&payload_value)
            .expect("canonical payload")
            .to_string(),
        extensions: Extensions::new(),
    }
}

fn journal(root: &TestDir, run_id: &str) -> LocalEventJournal<LocalCas> {
    let cas = LocalCas::open(root.path().join("cas")).expect("open CAS");
    LocalEventJournal::open(root.path().join("journal"), cas, run_id).expect("open event journal")
}

#[test]
fn append_replay_and_projection_rebuild_are_deterministic() {
    let root = TestDir::new("round-trip");
    let journal = journal(&root, RUN_1);
    let started = event(RUN_1, 0, "RUN_STARTED", "start");
    let finished = event(RUN_1, 1, "RUN_FINISHED", "finish");

    assert_eq!(journal.append(&started).unwrap(), EventOffset::new(0));
    assert_eq!(journal.append(&finished).unwrap(), EventOffset::new(1));

    let records = journal.read_from(EventOffset::new(0)).unwrap();
    assert_eq!(records.len(), 2);
    assert_eq!(records[0].offset, EventOffset::new(0));
    assert_eq!(records[0].event, started);
    assert_eq!(records[1].offset, EventOffset::new(1));
    assert_eq!(records[1].event, finished);
    assert_ne!(records[0].chain_digest, records[1].chain_digest);

    let projection = rebuild_run_projection(&journal).unwrap();
    assert_eq!(projection.version, 1);
    assert_eq!(projection.run_id, RUN_1);
    assert_eq!(projection.event_count, 2);
    assert_eq!(projection.last_offset, Some(1));
    assert_eq!(projection.last_event_type.as_deref(), Some("RUN_FINISHED"));
    assert_eq!(projection.event_type_counts["RUN_STARTED"], 1);
    assert_eq!(projection.event_type_counts["RUN_FINISHED"], 1);

    let first = projection_bytes(&projection).unwrap();
    let projection_path = root.path().join("derived-projection.json");
    fs::write(&projection_path, &first).unwrap();
    fs::remove_file(&projection_path).unwrap();

    let rebuilt = rebuild_run_projection(&journal).unwrap();
    let second = projection_bytes(&rebuilt).unwrap();
    fs::write(&projection_path, &second).unwrap();
    assert_eq!(first, second);
    assert_eq!(fs::read(projection_path).unwrap(), first);
}

#[test]
fn identical_retry_is_idempotent() {
    let root = TestDir::new("idempotent");
    let journal = journal(&root, RUN_2);
    let event = event(RUN_2, 0, "RUN_STARTED", "same");

    assert_eq!(journal.append(&event).unwrap(), EventOffset::new(0));
    assert_eq!(journal.append(&event).unwrap(), EventOffset::new(0));
    assert_eq!(journal.read_from(EventOffset::new(0)).unwrap().len(), 1);
}

#[test]
fn sequence_gap_is_rejected() {
    let root = TestDir::new("gap");
    let journal = journal(&root, RUN_3);
    let event = event(RUN_3, 1, "RUN_STARTED", "gap");

    let error = journal.append(&event).unwrap_err();
    assert!(matches!(
        error,
        EventError::SequenceGap {
            expected: 0,
            actual: 1
        }
    ));
}

#[test]
fn payload_digest_mismatch_is_rejected_before_visibility() {
    let root = TestDir::new("payload-digest");
    let journal = journal(&root, RUN_4);
    let mut event = event(RUN_4, 0, "RUN_STARTED", "tampered");
    event.payload_digest = format!("sha256:{}", "0".repeat(64));

    let error = journal.append(&event).unwrap_err();
    assert!(matches!(error, EventError::PayloadDigestMismatch { .. }));
    assert!(journal.read_from(EventOffset::new(0)).unwrap().is_empty());
}

#[test]
fn orphan_cas_event_is_not_visible_until_pointer_commit() {
    let root = TestDir::new("orphan");
    let cas_root = root.path().join("cas");
    let event = event(RUN_5, 0, "RUN_STARTED", "orphan");
    let event_value = serde_json::to_value(&event).unwrap();
    let event_bytes = canonical_bytes(&event_value).unwrap();
    LocalCas::open(&cas_root)
        .unwrap()
        .put(&event_bytes)
        .unwrap();

    let journal = LocalEventJournal::open(
        root.path().join("journal"),
        LocalCas::open(&cas_root).unwrap(),
        RUN_5,
    )
    .unwrap();

    assert!(journal.read_from(EventOffset::new(0)).unwrap().is_empty());
    assert_eq!(journal.append(&event).unwrap(), EventOffset::new(0));
    assert_eq!(journal.read_from(EventOffset::new(0)).unwrap().len(), 1);
}

#[test]
fn projection_is_canonical_json() {
    let root = TestDir::new("projection-json");
    let journal = journal(&root, RUN_6);
    journal
        .append(&event(RUN_6, 0, "RUN_STARTED", "x"))
        .unwrap();

    let bytes = projection_bytes(&rebuild_run_projection(&journal).unwrap()).unwrap();
    let value: Value = serde_json::from_slice(&bytes).unwrap();
    assert_eq!(value["version"], json!(1));
    assert_eq!(bytes, canonical_bytes(&value).unwrap());
}
