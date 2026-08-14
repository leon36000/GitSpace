#![forbid(unsafe_code)]

mod artifacts;
mod error;
mod model;
mod native;
mod replay;

pub use error::FoundryError;
pub use model::{NativeScenario, ObservedClassification, ReplayReport, RunReceipt};
pub use native::NativeFoundry;

pub fn receipt_bytes(receipt: &RunReceipt) -> Result<Vec<u8>, FoundryError> {
    let value = serde_json::to_value(receipt)?;
    Ok(gs_canonical_json::canonical_bytes(&value)?)
}

pub fn replay_bytes(report: &ReplayReport) -> Result<Vec<u8>, FoundryError> {
    let value = serde_json::to_value(report)?;
    Ok(gs_canonical_json::canonical_bytes(&value)?)
}
