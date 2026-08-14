#![forbid(unsafe_code)]

mod error;
mod format;
mod journal;
mod projection;

pub use error::EventError;
pub use format::EventOffset;
pub use journal::{EventSink, EventSource, JournalRecord, LocalEventJournal};
pub use projection::{RunProjection, projection_bytes, rebuild_run_projection};
