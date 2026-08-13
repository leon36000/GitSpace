use gs_canonical_json::sha256_digest;
use gs_cas::{Cas, CasError, LocalCas};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Barrier,
    },
    thread,
};

static NEXT_ROOT: AtomicU64 = AtomicU64::new(10_000);

struct TestRoot(PathBuf);

impl TestRoot {
    fn new(label: &str) -> Self {
        let serial = NEXT_ROOT.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-gs-cas-{label}-{}-{serial}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).expect("create isolated CAS test root");
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TestRoot {
    fn drop(&mut self) {
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let tmp = self.0.join("tmp");
            if let Ok(metadata) = fs::metadata(&tmp) {
                let mut permissions = metadata.permissions();
                permissions.set_mode(0o700);
                let _ = fs::set_permissions(tmp, permissions);
            }
        }
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn make_writable(path: &Path) {
    let mut permissions = fs::metadata(path).expect("object metadata").permissions();
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        permissions.set_mode(0o600);
    }
    #[cfg(not(unix))]
    permissions.set_readonly(false);
    fs::set_permissions(path, permissions).expect("make object writable for corruption injection");
}

fn file_count(path: &Path) -> usize {
    if !path.exists() {
        return 0;
    }
    fs::read_dir(path)
        .expect("read directory")
        .map(|entry| entry.expect("directory entry").path())
        .map(|path| {
            let metadata = fs::symlink_metadata(&path).expect("entry metadata");
            if metadata.is_dir() {
                file_count(&path)
            } else if metadata.is_file() {
                1
            } else {
                0
            }
        })
        .sum()
}

#[test]
fn corrupted_object_is_rejected_and_never_silently_overwritten() {
    let root = TestRoot::new("corrupt");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let original = b"authoritative bytes";
    let tampered = b"tampered bytes";
    let digest = cas.put(original).expect("put original");
    let path = cas.object_path(&digest);

    make_writable(&path);
    fs::write(&path, tampered).expect("inject corruption");

    match cas.get(&digest).expect_err("corruption must fail read") {
        CasError::CorruptObject { expected, actual } => {
            assert_eq!(expected, digest);
            assert_eq!(actual, sha256_digest(tampered));
        }
        other => panic!("unexpected read error: {other:?}"),
    }

    match cas.put(original).expect_err("put must not heal or overwrite corruption") {
        CasError::CorruptObject { expected, actual } => {
            assert_eq!(expected, digest);
            assert_eq!(actual, sha256_digest(tampered));
        }
        other => panic!("unexpected put error: {other:?}"),
    }

    assert_eq!(fs::read(path).expect("read preserved negative evidence"), tampered);
    assert_eq!(file_count(&root.path().join("tmp")), 0);
}

#[test]
fn concurrent_identical_writers_commit_one_complete_object() {
    let root = TestRoot::new("concurrent");
    let cas = Arc::new(LocalCas::open(root.path()).expect("open local CAS"));
    let bytes = Arc::new(vec![0x5a; 256 * 1024]);
    let expected = sha256_digest(bytes.as_slice());
    let workers = 24;
    let barrier = Arc::new(Barrier::new(workers));

    let handles = (0..workers)
        .map(|_| {
            let cas = Arc::clone(&cas);
            let bytes = Arc::clone(&bytes);
            let barrier = Arc::clone(&barrier);
            thread::spawn(move || {
                barrier.wait();
                cas.put(bytes.as_slice())
            })
        })
        .collect::<Vec<_>>();

    for handle in handles {
        assert_eq!(handle.join().expect("writer thread").expect("concurrent put"), expected);
    }

    assert_eq!(cas.get(&expected).expect("read concurrent winner"), bytes.as_slice());
    assert_eq!(file_count(&root.path().join("objects")), 1);
    assert_eq!(file_count(&root.path().join("tmp")), 0);
}

#[test]
fn interrupted_partial_temporary_file_is_not_addressable_or_blocking() {
    let root = TestRoot::new("interrupted");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let partial = b"partial uncommitted bytes";
    let stale = root.path().join("tmp").join("abandoned-writer.partial");
    fs::write(&stale, partial).expect("inject stale temporary file");

    let partial_digest = sha256_digest(partial);
    assert!(matches!(
        cas.get(&partial_digest),
        Err(CasError::NotFound { digest }) if digest == partial_digest
    ));

    let committed = b"later complete bytes";
    let digest = cas.put(committed).expect("put after interrupted writer");
    assert_eq!(cas.get(&digest).expect("get committed bytes"), committed);
    assert!(stale.exists(), "foreign stale temp remains non-addressable evidence");
}

#[cfg(unix)]
#[test]
fn write_permission_failure_is_reported_without_partial_object() {
    use std::os::unix::fs::PermissionsExt;

    let root = TestRoot::new("permission");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let tmp = root.path().join("tmp");
    let mut permissions = fs::metadata(&tmp).expect("tmp metadata").permissions();
    permissions.set_mode(0o500);
    fs::set_permissions(&tmp, permissions).expect("remove tmp write permission");

    let result = cas.put(b"cannot create temp");

    let mut restore = fs::metadata(&tmp).expect("tmp metadata after failure").permissions();
    restore.set_mode(0o700);
    fs::set_permissions(&tmp, restore).expect("restore tmp permissions");

    match result.expect_err("permission failure must be visible") {
        CasError::Io { source, .. } => {
            assert_eq!(source.kind(), std::io::ErrorKind::PermissionDenied)
        }
        other => panic!("unexpected permission error: {other:?}"),
    }
    assert_eq!(file_count(&root.path().join("objects")), 0);
}

#[cfg(unix)]
#[test]
fn symlink_object_is_rejected_even_when_target_bytes_match() {
    use std::os::unix::fs::symlink;

    let root = TestRoot::new("symlink");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let bytes = b"outside but matching";
    let digest = sha256_digest(bytes);
    let object = cas.object_path(&digest);
    fs::create_dir_all(object.parent().expect("object parent")).expect("create shard");
    let outside = root.path().join("outside");
    fs::write(&outside, bytes).expect("write outside file");
    symlink(&outside, &object).expect("inject symlink object");

    assert!(matches!(
        cas.get(&digest),
        Err(CasError::UnsafePath { path, .. }) if path == object
    ));
}

#[test]
fn non_regular_object_path_is_rejected() {
    let root = TestRoot::new("non-regular");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let digest = sha256_digest(b"directory masquerading as object");
    let object = cas.object_path(&digest);
    fs::create_dir_all(&object).expect("inject directory object");

    assert!(matches!(
        cas.get(&digest),
        Err(CasError::UnsafePath { path, .. }) if path == object
    ));
}
