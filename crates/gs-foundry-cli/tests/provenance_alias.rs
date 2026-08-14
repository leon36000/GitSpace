mod common;

use common::source_commit;
use gs_foundry_cli::{NativeFoundry, NativeScenario};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

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
    let first_foundry = NativeFoundry::open(root.path(), source_commit()).unwrap();
    let first_receipt = first_foundry.run(NativeScenario::Pass).unwrap();

    let second_foundry = NativeFoundry::open(
        root.path(),
        "ffffffffffffffffffffffffffffffffffffffff",
    )
    .unwrap();
    assert!(
        second_foundry.run(NativeScenario::Pass).is_err(),
        "the same deterministic run ID accepted two source commits"
    );

    first_foundry.replay(&first_receipt).unwrap();
}
