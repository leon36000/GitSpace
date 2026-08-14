use crate::{EventError, EventOffset, EventSource};
use gs_canonical_json::canonical_bytes;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RunProjection {
    pub version: u64,
    pub run_id: String,
    pub event_count: u64,
    pub last_offset: Option<u64>,
    pub last_event_type: Option<String>,
    pub last_occurred_at: Option<String>,
    pub event_type_counts: BTreeMap<String, u64>,
    pub chain_head: Option<String>,
}

pub fn rebuild_run_projection(source: &impl EventSource) -> Result<RunProjection, EventError> {
    let records = source.read_from(EventOffset::new(0))?;
    let mut event_type_counts = BTreeMap::new();
    for record in &records {
        *event_type_counts
            .entry(record.event.event_type.clone())
            .or_insert(0) += 1;
    }

    let last = records.last();
    Ok(RunProjection {
        version: 1,
        run_id: source.run_id().to_owned(),
        event_count: records.len() as u64,
        last_offset: last.map(|record| record.offset.get()),
        last_event_type: last.map(|record| record.event.event_type.clone()),
        last_occurred_at: last.map(|record| record.event.occurred_at.clone()),
        event_type_counts,
        chain_head: last.map(|record| record.chain_digest.to_string()),
    })
}

pub fn projection_bytes(projection: &RunProjection) -> Result<Vec<u8>, EventError> {
    let value = serde_json::to_value(projection)?;
    Ok(canonical_bytes(&value)?)
}
