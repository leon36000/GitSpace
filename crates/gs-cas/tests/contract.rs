use gs_canonical_json::sha256_digest;
use gs_cas::{Cas, CasError, Digest, LocalCas};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_ROOT: AtomicU64 = AtomicU64::new(0);

struct TestRoot {
    path: PathBuf,
}

impl TestRoot {
    fn new(label: &str) -> Self {
        let serial = NEXT_ROOT.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-gs-cas-{label}-{}-{serial}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).expect("create isolated CAS test root");
        Self { path }
    }

    fn path(&self) -> &Path {
        &self.path
    }
}

impl Drop for TestRoot {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn digest_hex(digest: &Digest) -> String {
    digest
        .to_string()
        .strip_prefix("sha256:")
        .expect("GitSpace digest prefix")
        .to_owned()
}

fn count_regular_files(path: &Path) -> usize {
    if !path.exists() {
        return 0;
    }
    fs::read_dir(path)
        .expect("read directory")
        .map(|entry| entry.expect("directory entry").path())
        .map(|path| {
            let metadata = fs::symlink_metadata(&path).expect("entry metadata");
            if metadata.is_dir() {
                count_regular_files(&path)
            } else if metadata.is_file() {
                1
            } else {
                0
            }
        })
        .sum()
}

#[test]
fn put_get_round_trip_uses_documented_layout() {
    let root = TestRoot::new("round-trip");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let bytes = b"GitSpace CAS v1";

    let digest = cas.put(bytes).expect("put bytes");
    assert_eq!(digest, sha256_digest(bytes));
    assert_eq!(cas.get(&digest).expect("get bytes"), bytes);

    let hex = digest_hex(&digest);
    let expected_path = root
        .path()
        .join("objects")
        .join("sha256")
        .join(&hex[..2])
        .join(&hex[2..]);
    assert_eq!(cas.object_path(&digest), expected_path);

    let metadata = fs::metadata(expected_path).expect("committed object metadata");
    assert!(metadata.is_file());
    assert!(metadata.permissions().readonly());
    assert_eq!(count_regular_files(&root.path().join("tmp")), 0);
}

#[test]
fn empty_object_uses_the_standard_sha256_identity() {
    let root = TestRoot::new("empty");
    let cas = LocalCas::open(root.path()).expect("open local CAS");

    let digest = cas.put(&[]).expect("put empty bytes");

    assert_eq!(
        digest.to_string(),
        "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    );
    assert_eq!(cas.get(&digest).expect("get empty bytes"), Vec::<u8>::new());
}

#[test]
fn duplicate_put_is_idempotent_and_does_not_replace_the_object() {
    let root = TestRoot::new("dedup");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let bytes = b"same bytes";

    let first = cas.put(bytes).expect("first put");
    let path = cas.object_path(&first);

    #[cfg(unix)]
    let first_inode = {
        use std::os::unix::fs::MetadataExt;
        fs::metadata(&path).expect("first metadata").ino()
    };

    let second = cas.put(bytes).expect("second put");
    assert_eq!(first, second);
    assert_eq!(cas.get(&second).expect("deduplicated get"), bytes);
    assert_eq!(count_regular_files(&root.path().join("objects")), 1);

    #[cfg(unix)]
    {
        use std::os::unix::fs::MetadataExt;
        assert_eq!(
            first_inode,
            fs::metadata(path).expect("second metadata").ino(),
            "idempotent put must not replace the committed inode"
        );
    }
}

#[test]
fn missing_object_is_reported_by_digest() {
    let root = TestRoot::new("missing");
    let cas = LocalCas::open(root.path()).expect("open local CAS");
    let missing = sha256_digest(b"not stored");

    match cas.get(&missing).expect_err("missing object must fail") {
        CasError::NotFound { digest } => assert_eq!(digest, missing),
        other => panic!("unexpected error: {other:?}"),
    }
}
