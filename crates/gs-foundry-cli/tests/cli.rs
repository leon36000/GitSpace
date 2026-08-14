use gs_foundry_cli::{ObservedClassification, ReplayReport, RunReceipt};
use std::{
    fs,
    path::PathBuf,
    process::Command,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);
const SOURCE_COMMIT: &str = "7cc65f670dfd7a682c77d3cc8cda656fe9c30ccd";

#[test]
fn cli_run_and_replay_emit_json_that_matches_the_library_contract() {
    let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
    let root = std::env::temp_dir().join(format!(
        "gitspace-task9-cli-{}-{serial}",
        std::process::id()
    ));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(&root).unwrap();

    let run = Command::new(env!("CARGO_BIN_EXE_gs-foundry-cli"))
        .args([
            "run",
            "--root",
            root.to_str().unwrap(),
            "--scenario",
            "pass",
            "--source-commit",
            SOURCE_COMMIT,
        ])
        .output()
        .unwrap();
    assert!(
        run.status.success(),
        "{}",
        String::from_utf8_lossy(&run.stderr)
    );
    let receipt: RunReceipt = serde_json::from_slice(&run.stdout).unwrap();
    assert_eq!(receipt.classification, ObservedClassification::Pass);

    let receipt_path: PathBuf = root.join("receipt.json");
    fs::write(&receipt_path, &run.stdout).unwrap();
    let replay = Command::new(env!("CARGO_BIN_EXE_gs-foundry-cli"))
        .args([
            "replay",
            "--root",
            root.to_str().unwrap(),
            "--receipt",
            receipt_path.to_str().unwrap(),
        ])
        .output()
        .unwrap();
    assert!(
        replay.status.success(),
        "{}",
        String::from_utf8_lossy(&replay.stderr)
    );
    let report: ReplayReport = serde_json::from_slice(&replay.stdout).unwrap();
    assert_eq!(report.run_id, receipt.run_id);
    assert_eq!(report.classification, ObservedClassification::Pass);
    assert!(report.verdict.safe_success);

    let _ = fs::remove_dir_all(root);
}
