mod common;

use common::source_commit;
use gs_canonical_json::Digest;
use gs_cas::{Cas, LocalCas};
use gs_foundry_cli::{
    NativeFoundry, NativeScenario, ObservedClassification, ReplayReport, RunReceipt, receipt_bytes,
    replay_bytes,
};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task9-{label}-{}-{serial}",
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

fn open_foundry(root: &TestDir) -> NativeFoundry {
    NativeFoundry::open(root.path(), source_commit()).expect("open native foundry")
}

fn assert_cas_uri(value: &str) {
    assert!(value.starts_with("cas://sha256/"), "not a CAS URI: {value}");
    assert_eq!(value.len(), "cas://sha256/".len() + 64);
}

#[test]
fn five_native_scenarios_have_expected_classifications_and_verdicts() {
    let root = TestDir::new("five-scenarios");
    let foundry = open_foundry(&root);
    let cases = [
        (NativeScenario::Pass, ObservedClassification::Pass),
        (NativeScenario::Fail, ObservedClassification::Fail),
        (NativeScenario::Timeout, ObservedClassification::Timeout),
        (NativeScenario::Policy, ObservedClassification::Policy),
        (NativeScenario::Infra, ObservedClassification::Infra),
    ];

    for (scenario, expected) in cases {
        let receipt = foundry.run(scenario).expect("run deterministic scenario");
        assert_eq!(receipt.scenario, scenario);
        assert_eq!(receipt.classification, expected);
        assert_eq!(receipt.source_commit, source_commit());
        for uri in [
            &receipt.task_uri,
            &receipt.plan_uri,
            &receipt.scoring_uri,
            &receipt.verdict_uri,
            &receipt.evidence_uri,
            &receipt.manifest_uri,
            &receipt.trace_uri,
            &receipt.state_before_uri,
            &receipt.state_after_uri,
            &receipt.patch_uri,
        ] {
            assert_cas_uri(uri);
        }

        let replay = foundry
            .replay(&receipt)
            .expect("replay deterministic scenario");
        assert_eq!(replay.scenario, scenario);
        assert_eq!(replay.classification, expected);
        assert_eq!(replay.run_id, receipt.run_id);
        assert_eq!(replay.journal_event_count, 3);
        assert!(replay.replay_verified);
        assert!(replay.evidence_verified);
        match scenario {
            NativeScenario::Pass => {
                assert!(!replay.verdict.safe_success);
                assert!(!replay.verdict.false_done);
            }
            NativeScenario::Fail => {
                assert!(!replay.verdict.safe_success);
                assert!(replay.verdict.false_done);
            }
            NativeScenario::Timeout | NativeScenario::Policy | NativeScenario::Infra => {
                assert!(!replay.verdict.safe_success);
                assert!(!replay.verdict.false_done);
            }
        }
    }
}

#[test]
fn replay_is_read_only_and_byte_stable() {
    let root = TestDir::new("replay-stable");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let before_count = object_count(cas.root());
    let journal_before = journal_bytes(root.path(), &receipt.run_id);

    let first = foundry.replay(&receipt).unwrap();
    let second = foundry.replay(&receipt).unwrap();

    assert_eq!(
        replay_bytes(&first).unwrap(),
        replay_bytes(&second).unwrap()
    );
    assert_eq!(
        object_count(cas.root()),
        before_count,
        "replay wrote CAS objects"
    );
    assert_eq!(
        journal_bytes(root.path(), &receipt.run_id),
        journal_before,
        "replay wrote journal bytes"
    );
}

#[test]
fn world_fixture_digests_bind_the_actual_state_before() {
    let root = TestDir::new("world-fixture-binding");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let task_bytes = cas.get(&digest_from_uri(&receipt.task_uri)).unwrap();
    let task: serde_json::Value = serde_json::from_slice(&task_bytes).unwrap();
    let state_digest = receipt
        .state_before_uri
        .strip_prefix("cas://sha256/")
        .map(|hex| format!("sha256:{hex}"))
        .unwrap();

    assert_eq!(task["world_fixture"]["base_artifact_digest"], state_digest);
    assert_eq!(task["world_fixture"]["initial_state_digest"], state_digest);
}

#[test]
fn receipt_json_is_deterministic_and_round_trips() {
    let root = TestDir::new("receipt");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Policy).unwrap();
    let first = receipt_bytes(&receipt).unwrap();
    let decoded: RunReceipt = serde_json::from_slice(&first).unwrap();
    let second = receipt_bytes(&decoded).unwrap();
    assert_eq!(first, second);
    assert_eq!(decoded, receipt);
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

fn object_count(cas_root: &Path) -> usize {
    fn walk(path: &Path) -> usize {
        fs::read_dir(path)
            .map(|entries| {
                entries
                    .filter_map(Result::ok)
                    .map(|entry| {
                        let path = entry.path();
                        if path.is_dir() { walk(&path) } else { 1 }
                    })
                    .sum()
            })
            .unwrap_or(0)
    }
    walk(&cas_root.join("objects").join("sha256"))
}

fn journal_bytes(root: &Path, run_id: &str) -> Vec<u8> {
    let journal_root = root.join("journal");
    let digest = gs_canonical_json::sha256_digest(run_id.as_bytes()).to_string();
    let hex = digest.strip_prefix("sha256:").unwrap();
    let path = journal_root.join("runs").join(format!("{hex}.gsej"));
    fs::read(path).unwrap()
}

fn _assert_report_type(_: ReplayReport) {}
