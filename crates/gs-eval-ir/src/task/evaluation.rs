use super::Extensions;
use serde::{Deserialize, Serialize};

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
    pub extensions: Extensions,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct QualityAssurance {
    pub author_id: String,
    pub independent_reviewer_id: String,
    pub human_solution_digest: String,
    pub known_exploits: Vec<String>,
}
