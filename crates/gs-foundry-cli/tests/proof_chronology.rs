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
            "gitspace-task9-proof-chronology-{}-{serial}",
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
fn historical_verdict_does_not_self_award_regression_proof() {
    let root = TestDir::new();
    let foundry = NativeFoundry::open(root.path(), source_commit()).unwrap();
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    let replay = foundry.replay(&receipt).unwrap();

    assert!(
        !replay.verdict.regression_free,
        "historical verdict self-awarded regression_free without a persisted regression proof"
    );

    let failed_gates = replay.verdict.extensions["gitspace.verdict"]["failed_gates"]
        .as_array()
        .expect("deterministic failed gate array");
    assert!(
        failed_gates.iter().any(|gate| gate == "regression"),
        "historical verdict did not expose the open regression gate"
    );
}
