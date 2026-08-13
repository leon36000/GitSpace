use crate::{layout::digest_hex, CasError, Digest};
use std::{
    fs::{self, File, OpenOptions},
    io,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT_TEMPORARY: AtomicU64 = AtomicU64::new(0);
const TEMPORARY_ATTEMPTS: usize = 4_096;

pub(crate) fn create_temporary(
    directory: &Path,
    digest: &Digest,
) -> Result<(File, TemporaryGuard), CasError> {
    let hex = digest_hex(digest);
    for _ in 0..TEMPORARY_ATTEMPTS {
        let serial = NEXT_TEMPORARY.fetch_add(1, Ordering::Relaxed);
        let path = directory.join(format!(
            ".put-{}-{serial}-{hex}",
            std::process::id()
        ));
        match OpenOptions::new().write(true).create_new(true).open(&path) {
            Ok(file) => return Ok((file, TemporaryGuard::new(path))),
            Err(source) if source.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(source) => return Err(CasError::io("create temporary object", path, source)),
        }
    }

    Err(CasError::io(
        "allocate unique temporary object",
        directory,
        io::Error::new(
            io::ErrorKind::AlreadyExists,
            "temporary filename retry budget exhausted",
        ),
    ))
}

pub(crate) struct TemporaryGuard {
    path: PathBuf,
    armed: bool,
}

impl TemporaryGuard {
    fn new(path: PathBuf) -> Self {
        Self { path, armed: true }
    }

    pub(crate) fn path(&self) -> &Path {
        &self.path
    }

    pub(crate) fn cleanup(&mut self) -> io::Result<()> {
        if !self.armed {
            return Ok(());
        }
        match fs::remove_file(&self.path) {
            Ok(()) => {
                self.armed = false;
                Ok(())
            }
            Err(source) if source.kind() == io::ErrorKind::NotFound => {
                self.armed = false;
                Ok(())
            }
            Err(source) => Err(source),
        }
    }
}

impl Drop for TemporaryGuard {
    fn drop(&mut self) {
        let _ = self.cleanup();
    }
}
