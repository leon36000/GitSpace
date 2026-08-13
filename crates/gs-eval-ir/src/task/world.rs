use super::Extensions;
use serde::{Deserialize, Serialize};

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
    pub extensions: Extensions,
}

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
