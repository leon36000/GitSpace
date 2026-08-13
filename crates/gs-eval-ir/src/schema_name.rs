use std::{error::Error, fmt};

const EVAL_TASK_SPEC: &str = include_str!("../../../schemas/v1/eval-task-spec.schema.json");
const WORLD_FIXTURE: &str = include_str!("../../../schemas/v1/world-fixture.schema.json");
const ORACLE_BUNDLE: &str = include_str!("../../../schemas/v1/oracle-bundle.schema.json");
const AGENT_CONFIGURATION: &str = include_str!("../../../schemas/v1/agent-configuration.schema.json");
const EVAL_RUN_MANIFEST: &str = include_str!("../../../schemas/v1/eval-run-manifest.schema.json");
const RUN_EVENT: &str = include_str!("../../../schemas/v1/run-event.schema.json");
const EVIDENCE_BUNDLE: &str = include_str!("../../../schemas/v1/evidence-bundle.schema.json");
const EVAL_VERDICT: &str = include_str!("../../../schemas/v1/eval-verdict.schema.json");

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum SchemaName {
    EvalTaskSpec,
    WorldFixture,
    OracleBundle,
    AgentConfiguration,
    EvalRunManifest,
    RunEvent,
    EvidenceBundle,
    EvalVerdict,
}

impl SchemaName {
    pub const ALL: [Self; 8] = [
        Self::EvalTaskSpec,
        Self::WorldFixture,
        Self::OracleBundle,
        Self::AgentConfiguration,
        Self::EvalRunManifest,
        Self::RunEvent,
        Self::EvidenceBundle,
        Self::EvalVerdict,
    ];

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::EvalTaskSpec => "EvalTaskSpec",
            Self::WorldFixture => "WorldFixture",
            Self::OracleBundle => "OracleBundle",
            Self::AgentConfiguration => "AgentConfiguration",
            Self::EvalRunManifest => "EvalRunManifest",
            Self::RunEvent => "RunEvent",
            Self::EvidenceBundle => "EvidenceBundle",
            Self::EvalVerdict => "EvalVerdict",
        }
    }

    pub(crate) const fn schema_id(self) -> &'static str {
        match self {
            Self::EvalTaskSpec => "urn:gitspace:schema:v1:eval-task-spec",
            Self::WorldFixture => "urn:gitspace:schema:v1:world-fixture",
            Self::OracleBundle => "urn:gitspace:schema:v1:oracle-bundle",
            Self::AgentConfiguration => "urn:gitspace:schema:v1:agent-configuration",
            Self::EvalRunManifest => "urn:gitspace:schema:v1:eval-run-manifest",
            Self::RunEvent => "urn:gitspace:schema:v1:run-event",
            Self::EvidenceBundle => "urn:gitspace:schema:v1:evidence-bundle",
            Self::EvalVerdict => "urn:gitspace:schema:v1:eval-verdict",
        }
    }

    pub(crate) const fn schema_text(self) -> &'static str {
        match self {
            Self::EvalTaskSpec => EVAL_TASK_SPEC,
            Self::WorldFixture => WORLD_FIXTURE,
            Self::OracleBundle => ORACLE_BUNDLE,
            Self::AgentConfiguration => AGENT_CONFIGURATION,
            Self::EvalRunManifest => EVAL_RUN_MANIFEST,
            Self::RunEvent => RUN_EVENT,
            Self::EvidenceBundle => EVIDENCE_BUNDLE,
            Self::EvalVerdict => EVAL_VERDICT,
        }
    }
}

impl TryFrom<&str> for SchemaName {
    type Error = UnknownSchemaName;

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value {
            "EvalTaskSpec" => Ok(Self::EvalTaskSpec),
            "WorldFixture" => Ok(Self::WorldFixture),
            "OracleBundle" => Ok(Self::OracleBundle),
            "AgentConfiguration" => Ok(Self::AgentConfiguration),
            "EvalRunManifest" => Ok(Self::EvalRunManifest),
            "RunEvent" => Ok(Self::RunEvent),
            "EvidenceBundle" => Ok(Self::EvidenceBundle),
            "EvalVerdict" => Ok(Self::EvalVerdict),
            other => Err(UnknownSchemaName(other.to_owned())),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct UnknownSchemaName(String);

impl fmt::Display for UnknownSchemaName {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "unknown Evaluation IR schema: {}", self.0)
    }
}

impl Error for UnknownSchemaName {}
