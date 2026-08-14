#![forbid(unsafe_code)]

mod engine;
mod error;
mod model;

pub use engine::issue_verdict;
pub use error::VerdictError;
pub use model::{CoverageCount, ResidualRisk, RiskSeverity, VerdictInput};
