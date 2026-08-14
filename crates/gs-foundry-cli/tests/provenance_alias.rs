mod common;

use common::source_commit;
use gs_foundry_cli::{NativeFoundry, NativeScenario};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const SECOND_SOURCE_COMMIT: &str = "ffffffffffffffffffffffffffffffffffffffff";

struct TestDir(PathBuf);

impl TestDir {
    fn new() -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task9-provenance-alias-{}-{serial}",
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
fn one_deterministic_run_id_cannot_alias_two_source_commits() {
    let root = TestDir::new();
    let first_source_commit = source_commit();
    let first_foundry = NativeFoundry::open(root.path(), &first_source_commit).unwrap();
    let first_receipt = first_foundry.run(NativeScenario::Pass).unwrap();

    let second_foundry = NativeFoundry::open(root.path(), SECOND_SOURCE_COMMIT).unwrap();
    let second_receipt = second_foundry.run(NativeScenario::Pass).unwrap();

    assert_ne!(
        first_receipt.run_id, second_receipt.run_id,
        "two source commits aliased one deterministic run ID"
    );
    assert_eq!(first_receipt.source_commit, first_source_commit);
    assert_eq!(second_receipt.source_commit, SECOND_SOURCE_COMMIT);

    first_foundry.replay(&first_receipt).unwrap();
    second_foundry.replay(&second_receipt).unwrap();
    assert!(first_foundry.replay(&second_receipt).is_err());
    assert!(second_foundry.replay(&first_receipt).is_err());
}
