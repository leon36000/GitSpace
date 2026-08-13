mod evaluation;
mod origin;
mod world;

pub use evaluation::*;
pub use origin::*;
pub use world::*;

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
