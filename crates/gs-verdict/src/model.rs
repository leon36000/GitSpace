use gs_eval_ir::{DeclaredOutcome, FunctionalOutcome, TaskValidity};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CoverageCount {
    pub closed: u64,
    pub total: u64,
}

impl CoverageCount {
    pub const fn new(closed: u64, total: u64) -> Self {
        Self { closed, total }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum RiskSeverity {
    Advisory,
    Critical,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ResidualRisk {
    pub severity: RiskSeverity,
    pub description: String,
}

impl ResidualRisk {
    pub fn advisory(description: impl Into<String>) -> Self {
        Self {
            severity: RiskSeverity::Advisory,
            description: description.into(),
        }
    }

    pub fn critical(description: impl Into<String>) -> Self {
        Self {
            severity: RiskSeverity::Critical,
            description: description.into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct VerdictInput {
    pub verdict_id: String,
    pub run_id: String,
    pub declared_outcome: DeclaredOutcome,
    pub functional_outcome: FunctionalOutcome,
    pub task_validity: TaskValidity,
    pub scope_respected: bool,
    pub authority_respected: bool,
    pub security_policy_passed: bool,
    pub regression_free: bool,
    pub replay_passed: bool,
    pub independent_verification_passed: bool,
    pub cleanup_passed: bool,
    pub exploit_detected: bool,
    pub obligations: CoverageCount,
    pub evidence: CoverageCount,
    pub residual_risks: Vec<ResidualRisk>,
}
