use crate::Digest;
use std::{error::Error, fmt, io, path::PathBuf};

#[derive(Debug)]
pub enum CasError {
    Io {
        operation: &'static str,
        path: PathBuf,
        source: io::Error,
    },
    NotFound { digest: Digest },
    CorruptObject { expected: Digest, actual: Digest },
    DigestCollision { digest: Digest },
    UnsafePath { path: PathBuf, reason: &'static str },
    AtomicCommit { path: PathBuf, source: io::Error },
}

impl CasError {
    pub(crate) fn io(operation: &'static str, path: impl Into<PathBuf>, source: io::Error) -> Self {
        Self::Io { operation, path: path.into(), source }
    }
}

impl fmt::Display for CasError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io { operation, path, source } => write!(formatter, "CAS I/O operation {operation} failed for {}: {source}", path.display()),
            Self::NotFound { digest } => write!(formatter, "CAS object not found: {digest}"),
            Self::CorruptObject { expected, actual } => write!(formatter, "CAS object corruption: expected {expected}, actual {actual}"),
            Self::DigestCollision { digest } => write!(formatter, "CAS digest collision: distinct bytes resolve to {digest}"),
            Self::UnsafePath { path, reason } => write!(formatter, "unsafe CAS path {}: {reason}", path.display()),
            Self::AtomicCommit { path, source } => write!(formatter, "atomic no-replace CAS commit failed for {}: {source}", path.display()),
        }
    }
}

impl Error for CasError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } | Self::AtomicCommit { source, .. } => Some(source),
            _ => None,
        }
    }
}
