mod report;
mod run;
mod schema_name;
mod task;
mod validation;
mod verdict;

pub use report::*;
pub use run::*;
pub use schema_name::*;
pub use task::*;
pub use validation::*;
pub use verdict::*;

use serde_json::Value;

pub fn validate_task_json(value: &Value) -> Result<(), ValidationReport> {
    validate_named_json(SchemaName::EvalTaskSpec, value)
}

pub fn parse_task_json(value: &Value) -> Result<EvalTaskSpec, ValidationReport> {
    match parse_named_json(SchemaName::EvalTaskSpec, value)? {
        EvaluationIr::EvalTaskSpec(task) => Ok(task),
        _ => Err(ValidationReport::type_mismatch()),
    }
}
