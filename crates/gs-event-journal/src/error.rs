use gs_canonical_json::CanonicalJsonError;
use gs_cas::CasError;
use gs_eval_ir::ValidationReport;
use std::{error::Error, fmt, io, path::PathBuf};

#[derive(Debug)]
pub enum EventError {
    Io {
        operation: &'static str,
        path: PathBuf,
        source: io::Error,
    },
    Cas(CasError),
    Canonical(CanonicalJsonError),
    Validation(ValidationReport),
    Json(serde_json::Error),
    UnsafePath {
        path: PathBuf,
        reason: &'static str,
    },
    InvalidHeader {
        reason: String,
    },
    TruncatedTail {
        trailing_bytes: u64,
    },
    CorruptOffset {
        expected: u64,
        actual: u64,
    },
    CorruptChain {
        offset: u64,
        expected: String,
        actual: String,
    },
    PayloadDigestMismatch {
        expected: String,
        actual: String,
    },
    RunIdMismatch {
        expected: String,
        actual: String,
    },
    SequenceGap {
        expected: u64,
        actual: u64,
    },
    SequenceConflict {
        offset: u64,
        existing: String,
        attempted: String,
    },
    NonCanonicalEvent {
        offset: u64,
    },
    TypeMismatch,
}

impl EventError {
    pub(crate) fn io(operation: &'static str, path: impl Into<PathBuf>, source: io::Error) -> Self {
        Self::Io {
            operation,
            path: path.into(),
            source,
        }
    }
}

impl fmt::Display for EventError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io {
                operation,
                path,
                source,
            } => write!(
                formatter,
                "event journal I/O operation {operation} failed for {}: {source}",
                path.display()
            ),
            Self::Cas(source) => write!(formatter, "event journal CAS failure: {source}"),
            Self::Canonical(source) => {
                write!(
                    formatter,
                    "event journal canonicalization failure: {source}"
                )
            }
            Self::Validation(source) => {
                write!(
                    formatter,
                    "event journal schema validation failure: {source}"
                )
            }
            Self::Json(source) => write!(formatter, "event journal JSON failure: {source}"),
            Self::UnsafePath { path, reason } => {
                write!(
                    formatter,
                    "unsafe event journal path {}: {reason}",
                    path.display()
                )
            }
            Self::InvalidHeader { reason } => {
                write!(formatter, "invalid event journal header: {reason}")
            }
            Self::TruncatedTail { trailing_bytes } => write!(
                formatter,
                "event journal has a truncated tail of {trailing_bytes} bytes"
            ),
            Self::CorruptOffset { expected, actual } => write!(
                formatter,
                "event journal offset corruption: expected {expected}, actual {actual}"
            ),
            Self::CorruptChain {
                offset,
                expected,
                actual,
            } => write!(
                formatter,
                "event journal chain corruption at offset {offset}: expected {expected}, actual {actual}"
            ),
            Self::PayloadDigestMismatch { expected, actual } => write!(
                formatter,
                "RunEvent payload digest mismatch: expected {expected}, actual {actual}"
            ),
            Self::RunIdMismatch { expected, actual } => write!(
                formatter,
                "RunEvent run_id mismatch: expected {expected}, actual {actual}"
            ),
            Self::SequenceGap { expected, actual } => write!(
                formatter,
                "RunEvent sequence gap: expected {expected}, actual {actual}"
            ),
            Self::SequenceConflict {
                offset,
                existing,
                attempted,
            } => write!(
                formatter,
                "RunEvent sequence conflict at offset {offset}: existing {existing}, attempted {attempted}"
            ),
            Self::NonCanonicalEvent { offset } => write!(
                formatter,
                "CAS event bytes at offset {offset} are not canonical JSON"
            ),
            Self::TypeMismatch => {
                formatter.write_str("validated IR value did not decode as a RunEvent")
            }
        }
    }
}

impl Error for EventError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            Self::Cas(source) => Some(source),
            Self::Canonical(source) => Some(source),
            Self::Validation(source) => Some(source),
            Self::Json(source) => Some(source),
            _ => None,
        }
    }
}

impl From<CasError> for EventError {
    fn from(value: CasError) -> Self {
        Self::Cas(value)
    }
}

impl From<CanonicalJsonError> for EventError {
    fn from(value: CanonicalJsonError) -> Self {
        Self::Canonical(value)
    }
}

impl From<ValidationReport> for EventError {
    fn from(value: ValidationReport) -> Self {
        Self::Validation(value)
    }
}

impl From<serde_json::Error> for EventError {
    fn from(value: serde_json::Error) -> Self {
        Self::Json(value)
    }
}
