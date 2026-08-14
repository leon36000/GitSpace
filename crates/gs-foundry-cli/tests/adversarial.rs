use gs_canonical_json::Digest;
use gs_cas::{Cas, LocalCas};
use gs_foundry_cli::{FoundryError, NativeFoundry, NativeScenario};
use std::{fs, path::{Path, PathBuf}, sync::atomic::{AtomicU64, Ordering}};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const SOURCE_COMMIT: &str = "7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd";

struct TestDir(PathBuf);
impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!("gitspace-task9-adv-{label}-{}-{serial}", std::process::id()));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        Self(path)
    }
    fn path(&self) -> &Path { &self.0 }
}
impl Drop for TestDir { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }

#[test]
fn missing_required_cas_artifact_fails_replay_without_repair() {
    let root = TestDir::new("missing-artifact");
    let foundry = NativeFoundry::open(root.path(), SOURCE_COMMIT).unwrap();
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    let cas = LocalCas::open(foundry.cas_root()).unwrap();
    let before = count_objects(cas.root());
    let digest = digest_from_uri(&receipt.verdict_uri);
    fs::remove_file(cas.object_path(&digest)).unwrap();
    let after_delete = count_objects(cas.root());

    assert!(foundry.replay(&receipt).is_err());
    assert_eq!(count_objects(cas.root()), after_delete, "replay repaired a missing CAS object");
    assert_eq!(before, after_delete + 1);
}

#[test]
fn crossed_receipt_reference_fails_closed() {
    let root = TestDir::new("crossed-receipt");
    let foundry = NativeFoundry::open(root.path(), SOURCE_COMMIT).unwrap();
    let mut receipt = foundry.run(NativeScenario::Pass).unwrap();
    receipt.manifest_uri = receipt.verdict_uri.clone();
    assert!(foundry.replay(&receipt).is_err());
}

#[test]
fn missing_journal_blocks_replay_and_is_not_recreated() {
    let root = TestDir::new("missing-journal");
    let foundry = NativeFoundry::open(root.path(), SOURCE_COMMIT).unwrap();
    let receipt = foundry.run(NativeScenario::Policy).unwrap();
    let journal = journal_path(root.path(), &receipt.run_id);
    fs::remove_file(&journal).unwrap();

    let error = foundry.replay(&receipt).unwrap_err();
    assert!(matches!(error, FoundryError::InvalidReceipt(_)));
    assert!(!journal.exists(), "read-only replay recreated a missing journal");
}

#[test]
fn rerunning_same_deterministic_scenario_is_idempotent() {
    let root = TestDir::new("idempotent");
    let foundry = NativeFoundry::open(root.path(), SOURCE_COMMIT).unwrap();
    let first = foundry.run(NativeScenario::Pass).unwrap();
    let second = foundry.run(NativeScenario::Pass).unwrap();
    assert_eq!(first, second);
}

#[test]
fn controlled_infra_collision_is_removed_after_classification() {
    let root = TestDir::new("infra-cleanup");
    let foundry = NativeFoundry::open(root.path(), SOURCE_COMMIT).unwrap();
    let receipt = foundry.run(NativeScenario::Infra).unwrap();
    assert_eq!(receipt.classification, gs_foundry_cli::ObservedClassification::Infra);
    let runner_entries = fs::read_dir(root.path().join("runner")).unwrap().count();
    assert_eq!(runner_entries, 0, "controlled infrastructure collision survived cleanup");
}

fn digest_from_uri(uri: &str) -> Digest {
    let hex = uri.strip_prefix("cas://sha256/").unwrap();
    let mut bytes = [0_u8; 32];
    for index in 0..32 {
        bytes[index] = (hex_nibble(hex.as_bytes()[index * 2]) << 4)
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
            .map(|entries| entries.filter_map(Result::ok).map(|entry| {
                let path = entry.path();
                if path.is_dir() { walk(&path) } else { 1 }
            }).sum())
            .unwrap_or(0)
    }
    walk(&root.join("objects").join("sha256"))
}

fn journal_path(root: &Path, run_id: &str) -> PathBuf {
    let digest = gs_canonical_json::sha256_digest(run_id.as_bytes()).to_string();
    root.join("journal").join("runs").join(format!("{}.gsej", digest.strip_prefix("sha256:").unwrap()))
}
