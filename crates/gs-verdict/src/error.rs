use gs_eval_ir::ValidationReport;
use std::{error::Error, fmt};

#[derive(Debug)]
pub enum VerdictError {
    InvalidCoverage {
        field: &'static str,
        closed: u64,
        total: u64,
    },
    EmptyRiskDescription {
        index: usize,
    },
    Serialization(serde_json::Error),
    Schema(ValidationReport),
}

impl fmt::Display for VerdictError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidCoverage {
                field,
                closed,
                total,
            } => write!(
                formatter,
                "invalid {field} coverage: closed {closed} exceeds total {total}"
            ),
            Self::EmptyRiskDescription { index } => {
                write!(formatter, "residual risk at index {index} has an empty description")
            }
            Self::Serialization(source) => {
                write!(formatter, "verdict serialization failed: {source}")
            }
            Self::Schema(source) => write!(formatter, "verdict schema validation failed: {source}"),
        }
    }
}

impl Error for VerdictError {
    fn source(&self) -> Option<&(dyn Error + 'static)> {
        match self {
            Self::Serialization(source) => Some(source),
            Self::Schema(source) => Some(source),
            _ => None,
        }
    }
}

impl From<serde_json::Error> for VerdictError {
    fn from(value: serde_json::Error) -> Self {
        Self::Serialization(value)
    }
}

impl From<ValidationReport> for VerdictError {
    fn from(value: ValidationReport) -> Self {
        Self::Schema(value)
    }
}
