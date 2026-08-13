use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

pub type Extensions = BTreeMap<String, Value>;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvalTaskSpec {
    pub id: String,
    pub version: u64,
    pub lane: String,
    pub origin: Origin,
    pub intent: Intent,
    pub world_fixture: WorldFixture,
    pub authority: Authority,
    pub obligations: Obligations,
    pub budgets: Budgets,
    pub evaluation: OracleBundle,
    pub qa: QualityAssurance,
    #[serde(default)]
    pub extensions: Extensions,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Origin {
    pub kind: OriginKind,
    pub source: String,
    pub license: String,
    pub contamination_risk: ContaminationRisk,
}

[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum OriginKind {
    Native,
    Imported,
    Transformed,
}

[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ContaminationRisk {
    Low,
    Medium,
    High,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Intent {
    pub owner_outcome: String,
    pub explicit_requirements: Vec<String>,
    pub latent_requirements: Vec<String>,
    pub non_goals: Vec<String>,
    pub allowed_ambiguities: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct WorldFixture {
    pub version: u64,
    pub base_artifact_digest: String,
    pub environment_digest: String,
    pub services: Vec<ServiceFixture>,
    pub initial_state_digest: String,
    #[serde(default)]
    pub extensions: Extensions,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ServiceFixture {
    pub name: String,
    pub kind: String,
    pub endpoint: Option<String>,
    pub artifact_digest: Option<String>,
    #[serde(default)]
    pub extensions: Extensions,}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Authority {
    pub allowed_actions: Vec<String>,
    pub forbidden_actions: Vec<String>,
    pub scope_boundaries: Vec<String>,
    pub required_approvals: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Obligations {
    pub visible: Vec<String>,
    pub protected: Vec<String>,
    pub runtime: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Budgets {
    pub wall_time_seconds: u64,
    pub token_limit: u64,
    pub cost_limit_usd: f64,
    pub tool_calls: u64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OracleBundle {
    pub version: u64,
    pub public_checks: Vec<String>,
    pub hidden_oracles: Vec<String>,
    pub mutation_set: Vec<String>,
    pub adversarial_variants: Vec<String>,
    pub cleanup_oracle: String,
    pub replay_oracle: String,
    #[serde(default)]
    pub extensions: Extensions,}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QualityAssurance {
    pub author_id: String,
    pub independent_reviewer_id: String,
    pub human_solution_digest: String,
    pub known_exploits: Vec<String>,
}
