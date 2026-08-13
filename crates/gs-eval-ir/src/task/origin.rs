use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Origin {
    pub kind: OriginKind,
    pub source: String,
    pub license: String,
    pub contamination_risk: ContaminationRisk,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum OriginKind {
    Native,
    Imported,
    Transformed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
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
