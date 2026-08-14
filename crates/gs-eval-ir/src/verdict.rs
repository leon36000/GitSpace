use crate::task::Extensions;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvidenceBundle {
    pub id: String,
    pub version: u64,
    pub run_id: String,
    pub task_id: String,
    pub environment_digest: String,
    pub commit_sha: String,
    pub artifacts: BTreeMap<String, String>,
    #[serde(default)]
    pub extensions: Extensions,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvalVerdict {
    pub id: String,
    pub version: u64,
    pub run_id: String,
    pub functional_outcome: FunctionalOutcome,
    pub declared_outcome: DeclaredOutcome,
    pub false_done: bool,
    pub safe_success: bool,
    pub scope_respected: bool,
    pub authority_respected: bool,
    pub regression_free: bool,
    pub replay_passed: bool,
    pub independent_verification_passed: bool,
    pub obligation_coverage: f64,
    pub evidence_coverage: f64,
    pub exploit_detected: bool,
    pub cleanup_passed: bool,
    pub task_validity: TaskValidity,
    pub residual_risks: Vec<String>,
    #[serde(default)]
    pub extensions: Extensions,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum FunctionalOutcome {
    Pass,
    Partial,
    Fail,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum DeclaredOutcome {
    Success,
    Blocked,
    Abstained,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum TaskValidity {
    Valid,
    Invalid,
    Inconclusive,
}
