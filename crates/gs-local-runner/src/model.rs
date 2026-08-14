use gs_cas::Digest;
use serde::Serialize;
use std::time::Duration;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Capability {
    pub readable_prefixes: Vec<String>,
    pub writable_prefixes: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FixtureFile {
    pub path: String,
    pub bytes: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OracleFile {
    pub path: String,
    pub bytes: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum AgentOperation {
    Read { path: String },
    Write { path: String, bytes: Vec<u8> },
    Delay { millis: u64 },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum OracleCheck {
    WorkspaceFileEquals { path: String, expected: Vec<u8> },
    WorkspaceFileAbsent { path: String },
    OracleFileEquals { path: String, expected: Vec<u8> },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunPlan {
    pub run_id: String,
    pub fixture: Vec<FixtureFile>,
    pub oracle: Vec<OracleFile>,
    pub capability: Capability,
    pub operations: Vec<AgentOperation>,
    pub oracle_checks: Vec<OracleCheck>,
    pub timeout: Duration,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RunStatus {
    Completed,
    PolicyBlocked,
    TimedOut,
    OracleFailed,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EffectKind {
    Read,
    Write,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Effect {
    pub index: u64,
    pub kind: EffectKind,
    pub path: String,
    pub digest: Digest,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WorkspaceArtifact {
    pub path: String,
    pub digest: Digest,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RunResult {
    pub status: RunStatus,
    pub effects: Vec<Effect>,
    pub workspace_artifacts: Vec<WorkspaceArtifact>,
    pub workspace_snapshot: Digest,
    pub oracle_passed: bool,
    pub cleaned_up: bool,
}
