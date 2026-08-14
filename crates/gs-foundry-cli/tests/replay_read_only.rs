mod common;

use common::source_commit;
use gs_foundry_cli::{NativeFoundry, NativeScenario, receipt_bytes};
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task9-replay-read-only-{label}-{}-{serial}",
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
fn replay_does_not_initialize_an_absent_store() {
    let root = TestDir::new("absent-store");
    let source_root = root.path().join("source");
    let receipt_path = root.path().join("receipt.json");
    write_pass_receipt(&source_root, &receipt_path);

    let absent_root = root.path().join("absent");
    assert!(!absent_root.exists());

    let output = replay_command(&absent_root, &receipt_path);
    assert!(!output.status.success(), "replay unexpectedly succeeded");
    assert!(
        !absent_root.exists(),
        "read-only replay initialized an absent Foundry store"
    );
}

#[test]
fn replay_does_not_recreate_the_runner_root() {
    let root = TestDir::new("runner-root");
    let store = root.path().join("store");
    let receipt_path = root.path().join("receipt.json");
    write_pass_receipt(&store, &receipt_path);

    let runner_root = store.join("runner");
    fs::remove_dir_all(&runner_root).unwrap();
    assert!(!runner_root.exists());

    let output = replay_command(&store, &receipt_path);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(
        !runner_root.exists(),
        "read-only replay recreated the runner root"
    );
}

#[test]
fn replay_does_not_repair_a_missing_cas_layout_directory() {
    let root = TestDir::new("cas-layout");
    let store = root.path().join("store");
    let receipt_path = root.path().join("receipt.json");
    write_pass_receipt(&store, &receipt_path);

    let temporary_root = store.join("cas").join("tmp");
    fs::remove_dir_all(&temporary_root).unwrap();
    assert!(!temporary_root.exists());

    let output = replay_command(&store, &receipt_path);
    assert!(
        !output.status.success(),
        "replay silently repaired a missing CAS layout directory"
    );
    assert!(
        !temporary_root.exists(),
        "read-only replay recreated a missing CAS layout directory"
    );
}

#[test]
fn library_replay_does_not_repair_a_missing_cas_layout_directory() {
    let root = TestDir::new("library-cas-layout");
    let store = root.path().join("store");
    let foundry = NativeFoundry::open(&store, source_commit()).unwrap();
    let receipt = foundry.run(NativeScenario::Pass).unwrap();

    let temporary_root = store.join("cas").join("tmp");
    fs::remove_dir_all(&temporary_root).unwrap();
    assert!(!temporary_root.exists());

    assert!(
        foundry.replay(&receipt).is_err(),
        "library replay silently repaired a missing CAS layout directory"
    );
    assert!(
        !temporary_root.exists(),
        "library replay recreated a missing CAS layout directory"
    );
}

#[test]
fn read_only_handle_cannot_execute_or_recreate_the_runner_root() {
    let root = TestDir::new("read-only-handle");
    let store = root.path().join("store");
    let receipt_path = root.path().join("receipt.json");
    write_pass_receipt(&store, &receipt_path);

    let runner_root = store.join("runner");
    fs::remove_dir_all(&runner_root).unwrap();
    let read_only = NativeFoundry::open_read_only(&store, source_commit()).unwrap();

    assert!(
        read_only.run(NativeScenario::Pass).is_err(),
        "read-only Foundry handle executed a scenario"
    );
    assert!(
        !runner_root.exists(),
        "read-only Foundry handle recreated the runner root"
    );
}

fn write_pass_receipt(store: &Path, receipt_path: &Path) {
    let foundry = NativeFoundry::open(store, source_commit()).unwrap();
    let receipt = foundry.run(NativeScenario::Pass).unwrap();
    fs::write(receipt_path, receipt_bytes(&receipt).unwrap()).unwrap();
}

fn replay_command(store: &Path, receipt_path: &Path) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_gs-foundry-cli"))
        .args([
            "replay",
            "--root",
            store.to_str().unwrap(),
            "--receipt",
            receipt_path.to_str().unwrap(),
        ])
        .output()
        .unwrap()
}
