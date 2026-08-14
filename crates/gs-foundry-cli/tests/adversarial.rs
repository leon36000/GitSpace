mod common;

use common::source_commit;
use gs_canonical_json::{Digest, sha256_digest};
use gs_cas::LocalCas;
use gs_foundry_cli::{FoundryError, NativeFoundry, NativeScenario, RunReceipt};
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
            "gitspace-task9-adv-{label}-{}-{serial}",
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
    NativeFoundry::open(root.path(), source_commit()).expect("open native Foundry")
}

#[derive(Clone, Copy)]
enum RequiredObject {
    Task,
    Plan,
    Scoring,
    Verdict,
    Evidence,
    Manifest,
    Trace,
    StateBefore,
    StateAfter,
    Patch,
    FixtureInput,
    WorkspaceOutput,
}

impl RequiredObject {
    const ALL: [Self; 12] = [
        Self::Task,
        Self::Plan,
        Self::Scoring,
        Self::Verdict,
        Self::Evidence,
        Self::Manifest,
        Self::Trace,
        Self::StateBefore,
        Self::StateAfter,
        Self::Patch,
        Self::FixtureInput,
        Self::WorkspaceOutput,
    ];

    fn label(self) -> &'static str {
        match self {
            Self::Task => "task",
            Self::Plan => "plan",
            Self::Scoring => "scoring",
            Self::Verdict => "verdict",
            Self::Evidence => "evidence",
            Self::Manifest => "manifest",
            Self::Trace => "trace",
            Self::StateBefore => "state-before",
            Self::StateAfter => "state-after",
            Self::Patch => "patch",
            Self::FixtureInput => "fixture-input",
            Self::WorkspaceOutput => "workspace-output",
        }
    }

    fn digest(self, receipt: &RunReceipt) -> Digest {
        match self {
            Self::Task => digest_from_uri(&receipt.task_uri),
            Self::Plan => digest_from_uri(&receipt.plan_uri),
            Self::Scoring => digest_from_uri(&receipt.scoring_uri),
            Self::Verdict => digest_from_uri(&receipt.verdict_uri),
            Self::Evidence => digest_from_uri(&receipt.evidence_uri),
            Self::Manifest => digest_from_uri(&receipt.manifest_uri),
            Self::Trace => digest_from_uri(&receipt.trace_uri),
            Self::StateBefore => digest_from_uri(&receipt.state_before_uri),
            Self::StateAfter => digest_from_uri(&receipt.state_after_uri),
            Self::Patch => digest_from_uri(&receipt.patch_uri),
            Self::FixtureInput => sha256_digest(b"hello"),
            Self::WorkspaceOutput => sha256_digest(b"done"),
        }
    }
}

#[test]
fn every_required_cas_object_fails_replay_without_repair_when_missing() {
    for object in RequiredObject::ALL {
        let root = TestDir::new(object.label());
        let foundry = open_foundry(&root);
        let receipt = foundry.run(NativeScenario::Pass).unwrap();
        let cas = LocalCas::open(foundry.cas_root()).unwrap();
        let before = count_objects(cas.root());
        fs::remove_file(cas.object_path(&object.digest(&receipt))).unwrap();
        let after_delete = count_objects(cas.root());

        assert!(
            foundry.replay(&receipt).is_err(),
            "replay accepted missing {} object",
            object.label()
        );
        assert_eq!(
            count_objects(cas.root()),
            after_delete,
            "replay repaired missing {} object",
            object.label()
        );
        assert_eq!(
            before,
            after_delete + 1,
            "test did not remove exactly one {} object",
            object.label()
        );
    }
}

#[test]
fn crossed_receipt_reference_fails_closed() {
    let root = TestDir::new("crossed-receipt");
    let foundry = open_foundry(&root);
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    receipt.manifest_uri = receipt.verdict_uri.clone();
    assert!(foundry.replay(&receipt).is_err());
}

#[test]
fn source_commit_mismatch_fails_closed_before_replay() {
    let root = TestDir::new("source-commit-mismatch");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    let mismatched =
        NativeFoundry::open(root.path(), "ffffffffffffffffffffffffffffffffffffffff").unwrap();

    let error = mismatched.replay(&receipt).unwrap_err();
    assert!(matches!(error, FoundryError::InvalidReceipt(_)));
}

#[test]
fn missing_journal_blocks_replay_and_is_not_recreated() {
    let root = TestDir::new("missing-journal");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Policy).unwrap();
    let journal = journal_path(root.path(), &receipt.run_id);
    fs::remove_file(&journal).unwrap();

    let error = foundry.replay(&receipt).unwrap_err();
    assert!(matches!(error, FoundryError::InvalidReceipt(_)));
    assert!(
        !journal.exists(),
        "read-only replay recreated a missing journal"
    );
}

#[test]
fn corrupt_journal_blocks_replay_without_repair() {
    let root = TestDir::new("corrupt-journal");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    let journal = journal_path(root.path(), &receipt.run_id);
    let mut corrupted = fs::read(&journal).unwrap();
    corrupted[0] ^= 0xff;
    fs::write(&journal, &corrupted).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let before_count = count_objects(cas.root());

    assert!(foundry.replay(&receipt).is_err());
    assert_eq!(fs::read(&journal).unwrap(), corrupted);
    assert_eq!(count_objects(cas.root()), before_count);
}

#[test]
fn rerunning_same_deterministic_scenario_is_idempotent() {
    let root = TestDir::new("idempotent");
    let foundry = open_foundry(&root);
    let first = foundry.run(NativeScenario::Pass).unwrap();
    let second = foundry.run(NativeScenario::Pass).unwrap();
    assert_eq!(first, second);
}

#[test]
fn controlled_infra_collision_is_removed_after_classification() {
    let root = TestDir::new("infra-cleanup");
    let foundry = open_foundry(&root);
    let receipt = foundry.run(NativeScenario::Infra).unwrap();
    assert_eq!(
        receipt.classification,
        gs_foundry_cli::ObservedClassification::Infra
    );
    let runner_entries = fs::read_dir(root.path().join("runner")).unwrap().count();
    assert_eq!(
        runner_entries, 0,
        "controlled infrastructure collision survived cleanup"
    );
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

fn count_objects(root: &Path) -> usize {
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
    walk(&root.join("objects").join("sha256"))
}

fn journal_path(root: &Path, run_id: &str) -> PathBuf {
    let digest = sha256_digest(run_id.as_bytes()).to_string();
    root.join("journal")
        .join("runs")
        .join(format!("{}.gsej", digest.strip_prefix("sha256:").unwrap()))
}
