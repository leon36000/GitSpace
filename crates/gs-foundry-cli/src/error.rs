use gs_canonical_json::CanonicalJsonError;
use gs_cas::CasError;
use gs_event_journal::EventError;
use gs_eval_ir::ValidationReport;
use gs_local_runner::RunnerError;
use gs_verdict::VerdictError;
use std::{error::Error, fmt, io, path::PathBuf};

#[derive(Debug)]
pub enum FoundryError {
    Io { operation: &'static str, path: PathBuf, source: io::Error },
    Cas(CasError),
    Event(EventError),
    Runner(RunnerError),
    Verdict(VerdictError),
    Validation(ValidationReport),
    Canonical(CanonicalJsonError),
    Json(serde_json::Error),
    InvalidSourceCommit,
    InvalidReceipt(String),
    Inconsistency(String),
}

impl FoundryError {
    pub(crate) fn io(operation: &'static str, path: impl Into<PathBuf>, source: io::Error) -> Self {
        Self::Io { operation, path: path.into(), source }
    }
}

impl fmt::Display for FoundryError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io { operation, path, source } => write!(formatter, "Foundry I/O operation {operation} failed for {}: {source}", path.display()),
            Self::Cas(source) => write!(formatter, "Foundry CAS failure: {source}"),
            Self::Event(source) => write!(formatter, "Foundry journal failure: {source}"),
            Self::Runner(source) => write!(formatter, "Foundry runner failure: {source}"),
            Self::Verdict(source) => write!(formatter, "Foundry verdict failure: {source}"),
            Self::Validation(source) => write!(formatter, "Foundry Evaluation IR validation failure: {source}"),
            Self::Canonical(source) => write!(formatter, "Foundry canonical JSON failure: {source}"),
            Self::Json(source) => write!(formatter, "Foundry JSON failure: {source}"),
            Self::InvalidSourceCommit => formatter.write_str("source commit must be lowercase 40- or 64-character hex"),
            Self::InvalidReceipt(message) => write!(formatter, "invalid run receipt: {message}"),
            Self::Inconsistency(message) => write!(formatter, "Foundry consistency failure: {message}"),
        }
    }
}

impl Error for FoundryError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            Self::Cas(source) => Some(source),
            Self::Event(source) => Some(source),
            Self::Runner(source) => Some(source),
            Self::Verdict(source) => Some(source),
            Self::Validation(source) => Some(source),
            Self::Canonical(source) => Some(source),
            Self::Json(source) => Some(source),
            _ => None,
        }
    }
}

impl From<CasError> for FoundryError { fn from(value: CasError) -> Self { Self::Cas(value) } }
impl From<EventError> for FoundryError { fn from(value: EventError) -> Self { Self::Event(value) } }
impl From<RunnerError> for FoundryError { fn from(value: RunnerError) -> Self { Self::Runner(value) } }
impl From<VerdictError> for FoundryError { fn from(value: VerdictError) -> Self { Self::Verdict(value) } }
impl From<ValidationReport> for FoundryError { fn from(value: ValidationReport) -> Self { Self::Validation(value) } }
impl From<CanonicalJsonError> for FoundryError { fn from(value: CanonicalJsonError) -> Self { Self::Canonical(value) } }
impl From<serde_json::Error> for FoundryError { fn from(value: serde_json::Error) -> Self { Self::Json(value) } }
