use crate::task::Extensions;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AgentConfiguration {
    pub version: u64,
    pub harness: String,
    pub harness_version: String,
    pub model: String,
    pub model_version: String,
    pub provider: String,
    pub model_parameters: BTreeMap<String, Value>,
    pub system_instructions_digest: String,
    pub tools_digest: String,
    pub context_digest: String,
    pub memory_digest: String,
    #[serde(default)]
    pub extensions: Extensions,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EvalRunManifest {
    pub id: String,
    pub version: u64,
    pub task_id: String,
    pub task_version: u64,
    pub agent: AgentConfiguration,
    pub environment: RunEnvironment,
    pub execution: ExecutionWindow,
    pub artifacts: RunArtifacts,
    #[serde(default)]
    pub extensions: Extensions,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RunEnvironment {
    pub image_digest: String,
    pub architecture: String,
    pub dependency_lock_digest: String,
    pub network_policy_digest: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ExecutionWindow {
    pub seed: i64,
    pub started_at: String,
    pub ended_at: String,
    pub interruption_schedule: Vec<Value>,
    pub retries: u64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RunArtifacts {
    pub trace: String,
    pub state_before: String,
    pub state_after: String,
    pub patch: String,
    pub evidence_bundle: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct RunEvent {
    pub version: u64,
    pub run_id: String,
    pub sequence: u64,
    pub event_type: String,
    pub occurred_at: String,
    pub payload: BTreeMap<String, Value>,
    pub payload_digest: String,
    #[serde(default)]
    pub extensions: Extensions,
}
