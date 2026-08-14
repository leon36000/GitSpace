use gs_eval_ir::{DeclaredOutcome, EvalVerdict, FunctionalOutcome, TaskValidity};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum NativeScenario {
    Pass,
    Fail,
    Timeout,
    Policy,
    Infra,
}

impl NativeScenario {
    pub(crate) const fn slug(self) -> &'static str {
        match self {
            Self::Pass => "pass",
            Self::Fail => "fail",
            Self::Timeout => "timeout",
            Self::Policy => "policy",
            Self::Infra => "infra",
        }
    }

    pub(crate) const fn ulid(self) -> &'static str {
        match self {
            Self::Pass => "01ARZ3NDEKTSV4RRFFQ69G5FAV",
            Self::Fail => "01ARZ3NDEKTSV4RRFFQ69G5FAW",
            Self::Timeout => "01ARZ3NDEKTSV4RRFFQ69G5FAX",
            Self::Policy => "01ARZ3NDEKTSV4RRFFQ69G5FAY",
            Self::Infra => "01ARZ3NDEKTSV4RRFFQ69G5FAZ",
        }
    }

    pub fn parse(value: &str) -> Option<Self> {
        match value {
            "pass" => Some(Self::Pass),
            "fail" => Some(Self::Fail),
            "timeout" => Some(Self::Timeout),
            "policy" => Some(Self::Policy),
            "infra" => Some(Self::Infra),
            _ => None,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ObservedClassification {
    Pass,
    Fail,
    Timeout,
    Policy,
    Infra,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RunReceipt {
    pub version: u64,
    pub scenario: NativeScenario,
    pub classification: ObservedClassification,
    pub run_id: String,
    pub source_commit: String,
    pub task_uri: String,
    pub plan_uri: String,
    pub scoring_uri: String,
    pub verdict_uri: String,
    pub evidence_uri: String,
    pub manifest_uri: String,
    pub trace_uri: String,
    pub state_before_uri: String,
    pub state_after_uri: String,
    pub patch_uri: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReplayReport {
    pub version: u64,
    pub scenario: NativeScenario,
    pub classification: ObservedClassification,
    pub run_id: String,
    pub verdict: EvalVerdict,
    pub manifest_uri: String,
    pub evidence_uri: String,
    pub journal_event_count: u64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub(crate) struct ScoringInput {
    pub scenario: NativeScenario,
    pub classification: ObservedClassification,
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
    pub obligations_closed: u64,
    pub obligations_total: u64,
    pub evidence_closed: u64,
    pub evidence_total: u64,
}
