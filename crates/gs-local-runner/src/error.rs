use gs_canonical_json::CanonicalJsonError;
use gs_cas::CasError;
use std::{error::Error, fmt, io, path::PathBuf};

#[derive(Debug)]
pub enum RunnerError {
    Io {
        operation: &'static str,
        path: PathBuf,
        source: io::Error,
    },
    Cas(CasError),
    Canonical(CanonicalJsonError),
    Json(serde_json::Error),
    UnsafePath {
        path: String,
        reason: &'static str,
    },
    DuplicatePath {
        kind: &'static str,
        path: String,
    },
    UnsafeRunId,
    RunAlreadyExists {
        path: PathBuf,
    },
    Cleanup {
        path: PathBuf,
        source: io::Error,
    },
}

impl RunnerError {
    pub(crate) fn io(operation: &'static str, path: impl Into<PathBuf>, source: io::Error) -> Self {
        Self::Io {
            operation,
            path: path.into(),
            source,
        }
    }
}

impl fmt::Display for RunnerError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io {
                operation,
                path,
                source,
            } => write!(
                formatter,
                "local runner I/O operation {operation} failed for {}: {source}",
                path.display()
            ),
            Self::Cas(source) => write!(formatter, "local runner CAS failure: {source}"),
            Self::Canonical(source) => {
                write!(formatter, "local runner canonical JSON failure: {source}")
            }
            Self::Json(source) => write!(formatter, "local runner JSON failure: {source}"),
            Self::UnsafePath { path, reason } => {
                write!(formatter, "unsafe local runner path {path:?}: {reason}")
            }
            Self::DuplicatePath { kind, path } => {
                write!(formatter, "duplicate {kind} path {path:?}")
            }
            Self::UnsafeRunId => formatter.write_str("unsafe or empty local runner run_id"),
            Self::RunAlreadyExists { path } => {
                write!(
                    formatter,
                    "run directory already exists: {}",
                    path.display()
                )
            }
            Self::Cleanup { path, source } => {
                write!(
                    formatter,
                    "run cleanup failed for {}: {source}",
                    path.display()
                )
            }
        }
    }
}

impl Error for RunnerError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            Self::Cas(source) => Some(source),
            Self::Canonical(source) => Some(source),
            Self::Json(source) => Some(source),
            Self::Cleanup { source, .. } => Some(source),
            _ => None,
        }
    }
}

impl From<CasError> for RunnerError {
    fn from(value: CasError) -> Self {
        Self::Cas(value)
    }
}

impl From<CanonicalJsonError> for RunnerError {
    fn from(value: CanonicalJsonError) -> Self {
        Self::Canonical(value)
    }
}

impl From<serde_json::Error> for RunnerError {
    fn from(value: serde_json::Error) -> Self {
        Self::Json(value)
    }
}
