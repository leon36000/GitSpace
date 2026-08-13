use crate::{
    AgentConfiguration, EvalRunManifest, EvalTaskSpec, EvalVerdict, EvidenceBundle, OracleBundle,
    RunEvent, SchemaName, ValidationIssue, ValidationReport, WorldFixture,
};
use jsonschema::{Draft, Registry, Validator};
use serde_json::Value;

#[derive(Debug, Clone, PartialEq)]
pub enum EvaluationIr {
    EvalTaskSpec(EvalTaskSpec),
    WorldFixture(WorldFixture),
    OracleBundle(OracleBundle),
    AgentConfiguration(AgentConfiguration),
    EvalRunManifest(EvalRunManifest),
    RunEvent(RunEvent),
    EvidenceBundle(EvidenceBundle),
    EvalVerdict(EvalVerdict),
}

fn schema_value(name: SchemaName) -> Result<Value, ValidationReport> {
    serde_json::from_str(name.schema_text()).map_err(|error| {
        ValidationReport::single(
            "/",
            "internal.schema_json",
            format!("embedded {} schema is not JSON: {error}", name.as_str()),
        )
    })
}

fn registry() -> Result<Registry<'static>, ValidationReport> {
    let mut builder = Registry::new();
    for name in SchemaName::ALL {
        builder = builder
            .add(name.schema_id(), schema_value(name)?)
            .map_err(|error| {
                ValidationReport::single(
                    "/",
                    "internal.registry",
                    format!("failed to register {}: {error}", name.as_str()),
                )
            })?;
    }
    builder.prepare().map_err(|error| {
        ValidationReport::single(
            "/",
            "internal.registry",
            format!("failed to prepare offline schema registry: {error}"),
        )
    })
}

fn validator(name: SchemaName) -> Result<Validator, ValidationReport> {
    let schema = schema_value(name)?;
    let registry = registry()?;
    jsonschema::options()
        .with_draft(Draft::Draft202012)
        .with_registry(&registry)
        .build(&schema)
        .map_err(|error| {
            ValidationReport::single(
                "/",
                "internal.schema_compile",
                format!("failed to compile {}: {error}", name.as_str()),
            )
        })
}

fn normalized_path(path: String) -> String {
    if path.is_empty() { "/".to_owned() } else { path }
}

fn schema_code(schema_path: String) -> String {
    let keyword = schema_path.rsplit('/').next().filter(|part| !part.is_empty());
    format!("schema.{}", keyword.unwrap_or("validation"))
}

pub fn validate_named_json(name: SchemaName, value: &Value) -> Result<(), ValidationReport> {
    let validator = validator(name)?;
    let mut issues = validator
        .iter_errors(value)
        .map(|error| ValidationIssue {
            path: normalized_path(error.instance_path().to_string()),
            code: schema_code(error.schema_path().to_string()),
            message: error.to_string(),
        })
        .collect::<Vec<_>>();

    if issues.is_empty() {
        return Ok(());
    }

    issues.sort_by(|left, right| {
        (&left.path, &left.code, &left.message).cmp(&(
            &right.path,
            &right.code,
            &right.message,
        ))
    });
    Err(ValidationReport { issues })
}

pub fn parse_named_json(name: SchemaName, value: &Value) -> Result<EvaluationIr, ValidationReport> {
    validate_named_json(name, value)?;
    let decode = |error: serde_json::Error| {
        ValidationReport::single("/", "typed.decode", error.to_string())
    };

    match name {
        SchemaName::EvalTaskSpec => serde_json::from_value(value.clone())
            .map(EvaluationIr::EvalTaskSpec)
            .map_err(decode),
        SchemaName::WorldFixture => serde_json::from_value(value.clone())
            .map(EvaluationIr::WorldFixture)
            .map_err(decode),
        SchemaName::OracleBundle => serde_json::from_value(value.clone())
            .map(EvaluationIr::OracleBundle)
            .map_err(decode),
        SchemaName::AgentConfiguration => serde_json::from_value(value.clone())
            .map(EvaluationIr::AgentConfiguration)
            .map_err(decode),
        SchemaName::EvalRunManifest => serde_json::from_value(value.clone())
            .map(EvaluationIr::EvalRunManifest)
            .map_err(decode),
        SchemaName::RunEvent => serde_json::from_value(value.clone())
            .map(EvaluationIr::RunEvent)
            .map_err(decode),
        SchemaName::EvidenceBundle => serde_json::from_value(value.clone())
            .map(EvaluationIr::EvidenceBundle)
            .map_err(decode),
        SchemaName::EvalVerdict => serde_json::from_value(value.clone())
            .map(EvaluationIr::EvalVerdict)
            .map_err(decode),
    }
}
