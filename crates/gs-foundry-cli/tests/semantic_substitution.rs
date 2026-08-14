use gs_canonical_json::{Digest, canonical_bytes, canonical_digest, sha256_digest};
use gs_cas::{Cas, LocalCas};
use gs_eval_ir::{EvalRunManifest, EvidenceBundle};
use gs_event_journal::{
    EventOffset, EventSink, EventSource, LocalEventJournal, projection_bytes,
    rebuild_run_projection,
};
use gs_foundry_cli::{NativeFoundry, NativeScenario, RunReceipt};
use serde::{Serialize, de::DeserializeOwned};
use serde_json::{Value, json};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const SOURCE_COMMIT: &str = "7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd";

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task9-semantic-{label}-{}-{serial}",
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

#[test]
fn schema_valid_task_substitution_fails_closed() {
    let root = TestDir::new("task");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut task: Value = get_json(&cas, &receipt.task_uri);
    task["intent"]["owner_outcome"] = json!("tampered but schema-valid outcome");
    let uri = put_json(&cas, &task);
    replace_artifact(&cas, &mut receipt, "task", uri);

    assert_replay_rejects(&foundry, &receipt, "schema-valid task substitution");
}

#[test]
fn deterministic_plan_substitution_fails_closed() {
    let root = TestDir::new("plan");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut plan: Value = get_json(&cas, &receipt.plan_uri);
    plan["operations"] = json!([]);
    let uri = put_json(&cas, &plan);
    replace_artifact(&cas, &mut receipt, "plan", uri);

    assert_replay_rejects(&foundry, &receipt, "deterministic plan substitution");
}

#[test]
fn state_before_substitution_fails_closed() {
    let root = TestDir::new("state-before");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut state: Value = get_json(&cas, &receipt.state_before_uri);
    state[0]["digest"] = json!(sha256_digest(b"wrong fixture bytes").to_string());
    let uri = put_json(&cas, &state);
    replace_artifact(&cas, &mut receipt, "state_before", uri);

    assert_replay_rejects(&foundry, &receipt, "state-before substitution");
}

#[test]
fn state_after_substitution_fails_closed() {
    let root = TestDir::new("state-after");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut state: Value = get_json(&cas, &receipt.state_after_uri);
    state
        .as_array_mut()
        .unwrap()
        .retain(|entry| entry.get("path").and_then(Value::as_str) != Some("output/result.txt"));
    let uri = put_json(&cas, &state);
    replace_artifact(&cas, &mut receipt, "state_after", uri);

    assert_replay_rejects(&foundry, &receipt, "state-after substitution");
}

#[test]
fn patch_substitution_fails_closed() {
    let root = TestDir::new("patch");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut patch: Value = get_json(&cas, &receipt.patch_uri);
    patch.as_array_mut().unwrap().clear();
    let uri = put_json(&cas, &patch);
    replace_artifact(&cas, &mut receipt, "patch", uri);

    assert_replay_rejects(&foundry, &receipt, "patch substitution");
}

#[test]
fn scoring_artifact_with_unknown_field_fails_closed() {
    let root = TestDir::new("scoring");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut scoring: Value = get_json(&cas, &receipt.scoring_uri);
    let _ = scoring
        .as_object_mut()
        .unwrap()
        .insert("gitspace.tampered".to_owned(), Value::Bool(true));
    let uri = put_json(&cas, &scoring);
    replace_artifact(&cas, &mut receipt, "scoring", uri);

    assert_replay_rejects(&foundry, &receipt, "non-canonical scoring substitution");
}

#[test]
fn evidence_environment_substitution_fails_closed() {
    let root = TestDir::new("evidence-environment");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut evidence: EvidenceBundle = get_json(&cas, &receipt.evidence_uri);
    evidence.environment_digest = sha256_digest(b"wrong environment").to_string();
    replace_evidence(&cas, &mut receipt, evidence);

    assert_replay_rejects(
        &foundry,
        &receipt,
        "EvidenceBundle environment substitution",
    );
}

#[test]
fn manifest_environment_substitution_fails_closed() {
    let root = TestDir::new("manifest-environment");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let mut manifest: EvalRunManifest = get_json(&cas, &receipt.manifest_uri);
    manifest.environment.architecture = "aarch64".to_owned();
    receipt.manifest_uri = put_json(&cas, &manifest);

    assert_replay_rejects(&foundry, &receipt, "RunManifest environment substitution");
}

#[test]
fn journal_payload_substitution_with_matching_trace_fails_closed() {
    let root = TestDir::new("journal");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let journal_root = root.path().join("journal");

    let mut events = {
        let journal = LocalEventJournal::open(
            &journal_root,
            LocalCas::open(foundry.cas_root()).unwrap(),
            receipt.run_id.clone(),
        )
        .unwrap();
        journal
            .read_from(EventOffset::new(0))
            .unwrap()
            .into_iter()
            .map(|record| record.event)
            .collect::<Vec<_>>()
    };
    let _ = events[0]
        .payload
        .insert("scenario".to_owned(), json!("fail"));
    events[0].payload_digest = canonical_digest(&serde_json::to_value(&events[0].payload).unwrap())
        .unwrap()
        .to_string();

    fs::remove_file(journal_path(root.path(), &receipt.run_id)).unwrap();
    let rewritten = LocalEventJournal::open(
        &journal_root,
        LocalCas::open(foundry.cas_root()).unwrap(),
        receipt.run_id.clone(),
    )
    .unwrap();
    for event in &events {
        rewritten.append(event).unwrap();
    }
    let trace = projection_bytes(&rebuild_run_projection(&rewritten).unwrap()).unwrap();
    drop(rewritten);
    let trace_uri = cas_uri(cas.put(&trace).unwrap());
    replace_artifact(&cas, &mut receipt, "trace", trace_uri);

    assert_replay_rejects(&foundry, &receipt, "journal payload substitution");
}

fn open_foundry(root: &TestDir) -> NativeFoundry {
    NativeFoundry::open(root.path(), SOURCE_COMMIT).expect("open native Foundry")
}

fn assert_replay_rejects(foundry: &NativeFoundry, receipt: &RunReceipt, label: &str) {
    assert!(foundry.replay(receipt).is_err(), "replay accepted {label}");
}

fn replace_artifact(cas: &LocalCas, receipt: &mut RunReceipt, name: &str, uri: String) {
    match name {
        "task" => receipt.task_uri = uri.clone(),
        "plan" => receipt.plan_uri = uri.clone(),
        "scoring" => receipt.scoring_uri = uri.clone(),
        "verdict" => receipt.verdict_uri = uri.clone(),
        "trace" => receipt.trace_uri = uri.clone(),
        "state_before" => receipt.state_before_uri = uri.clone(),
        "state_after" => receipt.state_after_uri = uri.clone(),
        "patch" => receipt.patch_uri = uri.clone(),
        _ => panic!("unsupported receipt artifact {name}"),
    }

    let mut evidence: EvidenceBundle = get_json(cas, &receipt.evidence_uri);
    let _ = evidence.artifacts.insert(name.to_owned(), uri.clone());
    let evidence_uri = put_json(cas, &evidence);
    receipt.evidence_uri = evidence_uri.clone();

    let mut manifest: EvalRunManifest = get_json(cas, &receipt.manifest_uri);
    match name {
        "trace" => manifest.artifacts.trace = uri,
        "state_before" => manifest.artifacts.state_before = uri,
        "state_after" => manifest.artifacts.state_after = uri,
        "patch" => manifest.artifacts.patch = uri,
        _ => {}
    }
    manifest.artifacts.evidence_bundle = evidence_uri;
    receipt.manifest_uri = put_json(cas, &manifest);
}

fn replace_evidence(cas: &LocalCas, receipt: &mut RunReceipt, evidence: EvidenceBundle) {
    let evidence_uri = put_json(cas, &evidence);
    receipt.evidence_uri = evidence_uri.clone();
    let mut manifest: EvalRunManifest = get_json(cas, &receipt.manifest_uri);
    manifest.artifacts.evidence_bundle = evidence_uri;
    receipt.manifest_uri = put_json(cas, &manifest);
}

fn get_json<T: DeserializeOwned>(cas: &LocalCas, uri: &str) -> T {
    let bytes = cas.get(&digest_from_uri(uri)).unwrap();
    serde_json::from_slice(&bytes).unwrap()
}

fn put_json<T: Serialize>(cas: &LocalCas, value: &T) -> String {
    let value = serde_json::to_value(value).unwrap();
    let bytes = canonical_bytes(&value).unwrap();
    cas_uri(cas.put(&bytes).unwrap())
}

fn cas_uri(digest: Digest) -> String {
    let text = digest.to_string();
    format!(
        "cas://sha256/{}",
        text.strip_prefix("sha256:").expect("digest prefix")
    )
}

fn digest_from_uri(uri: &str) -> Digest {
    let hex = uri.strip_prefix("cas://sha256/").unwrap();
    let mut bytes = [0_u8; 32];
    for (index, byte) in bytes.iter_mut().enumerate() {
        *byte = (hex_nibble(hex.as_bytes()[index * 2]) << 4)
            | hex_nibble(hex.as_bytes()[index * 2 + 1]);
    }
    Digest::from_bytes(bytes)
}

fn hex_nibble(byte: u8) -> u8 {
    match byte {
        b'0'..=b'9' => byte - b'0',
        b'a'..=b'f' => byte - b'a' + 10,
        _ => panic!("invalid hex"),
    }
}

fn journal_path(root: &Path, run_id: &str) -> PathBuf {
    let digest = sha256_digest(run_id.as_bytes()).to_string();
    let hex = digest.strip_prefix("sha256:").expect("digest prefix");
    root.join("journal")
        .join("runs")
        .join(format!("{hex}.gsej"))
}
