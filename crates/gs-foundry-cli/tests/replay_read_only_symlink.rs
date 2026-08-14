#![cfg(unix)]

mod common;

use common::source_commit;
use gs_foundry_cli::NativeFoundry;
use std::{
    fs,
    os::unix::fs::symlink,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task9-replay-read-only-symlink-{label}-{}-{serial}",
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
fn read_only_open_rejects_a_symlinked_foundry_root() {
    let root = TestDir::new("root");
    let store = root.path().join("store");
    NativeFoundry::open(&store, source_commit()).unwrap();

    let alias = root.path().join("store-alias");
    symlink(&store, &alias).unwrap();

    assert!(
        NativeFoundry::open_read_only(&alias, source_commit()).is_err(),
        "read-only open followed a symlinked Foundry root"
    );
}

#[test]
fn read_only_open_rejects_a_symlinked_cas_layout_component() {
    let root = TestDir::new("cas-tmp");
    let store = root.path().join("store");
    NativeFoundry::open(&store, source_commit()).unwrap();

    let temporary_root = store.join("cas").join("tmp");
    fs::remove_dir_all(&temporary_root).unwrap();
    let external = root.path().join("external-tmp");
    fs::create_dir_all(&external).unwrap();
    symlink(&external, &temporary_root).unwrap();

    assert!(
        NativeFoundry::open_read_only(&store, source_commit()).is_err(),
        "read-only open followed a symlinked CAS layout component"
    );
    assert_eq!(
        fs::read_dir(&external).unwrap().count(),
        0,
        "read-only validation wrote through the CAS symlink"
    );
}

#[test]
fn read_only_open_rejects_a_symlinked_journal_layout_component() {
    let root = TestDir::new("journal-runs");
    let store = root.path().join("store");
    NativeFoundry::open(&store, source_commit()).unwrap();

    let runs_root = store.join("journal").join("runs");
    fs::remove_dir_all(&runs_root).unwrap();
    let external = root.path().join("external-runs");
    fs::create_dir_all(&external).unwrap();
    symlink(&external, &runs_root).unwrap();

    assert!(
        NativeFoundry::open_read_only(&store, source_commit()).is_err(),
        "read-only open followed a symlinked journal layout component"
    );
    assert_eq!(
        fs::read_dir(&external).unwrap().count(),
        0,
        "read-only validation wrote through the journal symlink"
    );
}
