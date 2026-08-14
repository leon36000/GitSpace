use crate::EventError;
use gs_canonical_json::{Digest, sha256_digest};

pub(crate) const HEADER_LEN: usize = 40;
pub(crate) const RECORD_LEN: usize = 72;
const MAGIC: &[u8; 8] = b"GSEJ0001";
const CHAIN_DOMAIN: &[u8] = b"GSEJ-CHAIN-V1";

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct EventOffset(u64);

impl EventOffset {
    pub const fn new(value: u64) -> Self {
        Self(value)
    }

    pub const fn get(self) -> u64 {
        self.0
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct IndexRecord {
    pub offset: EventOffset,
    pub event_digest: Digest,
    pub chain_digest: Digest,
}

pub(crate) fn header_bytes(run_id_digest: Digest) -> [u8; HEADER_LEN] {
    let mut output = [0_u8; HEADER_LEN];
    output[..MAGIC.len()].copy_from_slice(MAGIC);
    output[MAGIC.len()..].copy_from_slice(run_id_digest.as_bytes());
    output
}

pub(crate) fn record_bytes(record: IndexRecord) -> [u8; RECORD_LEN] {
    let mut output = [0_u8; RECORD_LEN];
    output[..8].copy_from_slice(&record.offset.get().to_be_bytes());
    output[8..40].copy_from_slice(record.event_digest.as_bytes());
    output[40..72].copy_from_slice(record.chain_digest.as_bytes());
    output
}

pub(crate) fn next_chain_digest(
    run_id_digest: Digest,
    previous_chain: Option<Digest>,
    offset: EventOffset,
    event_digest: Digest,
) -> Digest {
    let predecessor = previous_chain.unwrap_or(run_id_digest);
    let mut input = Vec::with_capacity(CHAIN_DOMAIN.len() + 32 + 8 + 32);
    input.extend_from_slice(CHAIN_DOMAIN);
    input.extend_from_slice(predecessor.as_bytes());
    input.extend_from_slice(&offset.get().to_be_bytes());
    input.extend_from_slice(event_digest.as_bytes());
    sha256_digest(&input)
}

pub(crate) fn parse_index(
    bytes: &[u8],
    expected_run_id_digest: Digest,
) -> Result<Vec<IndexRecord>, EventError> {
    if bytes.len() < HEADER_LEN {
        return Err(EventError::InvalidHeader {
            reason: format!(
                "expected {HEADER_LEN} bytes, found {}",
                bytes.len()
            ),
        });
    }
    if &bytes[..MAGIC.len()] != MAGIC {
        return Err(EventError::InvalidHeader {
            reason: "magic does not match GSEJ0001".to_owned(),
        });
    }

    let mut run_digest_bytes = [0_u8; 32];
    run_digest_bytes.copy_from_slice(&bytes[MAGIC.len()..HEADER_LEN]);
    let actual_run_id_digest = Digest::from_bytes(run_digest_bytes);
    if actual_run_id_digest != expected_run_id_digest {
        return Err(EventError::InvalidHeader {
            reason: format!(
                "run identifier digest mismatch: expected {expected_run_id_digest}, actual {actual_run_id_digest}"
            ),
        });
    }

    let body = &bytes[HEADER_LEN..];
    let trailing = body.len() % RECORD_LEN;
    if trailing != 0 {
        return Err(EventError::TruncatedTail {
            trailing_bytes: trailing as u64,
        });
    }

    let mut records = Vec::with_capacity(body.len() / RECORD_LEN);
    let mut previous_chain = None;
    for (index, record_bytes) in body.chunks_exact(RECORD_LEN).enumerate() {
        let mut offset_bytes = [0_u8; 8];
        offset_bytes.copy_from_slice(&record_bytes[..8]);
        let actual_offset = u64::from_be_bytes(offset_bytes);
        let expected_offset = index as u64;
        if actual_offset != expected_offset {
            return Err(EventError::CorruptOffset {
                expected: expected_offset,
                actual: actual_offset,
            });
        }

        let mut event_digest_bytes = [0_u8; 32];
        event_digest_bytes.copy_from_slice(&record_bytes[8..40]);
        let event_digest = Digest::from_bytes(event_digest_bytes);

        let mut chain_digest_bytes = [0_u8; 32];
        chain_digest_bytes.copy_from_slice(&record_bytes[40..72]);
        let actual_chain = Digest::from_bytes(chain_digest_bytes);
        let offset = EventOffset::new(actual_offset);
        let expected_chain = next_chain_digest(
            expected_run_id_digest,
            previous_chain,
            offset,
            event_digest,
        );
        if actual_chain != expected_chain {
            return Err(EventError::CorruptChain {
                offset: actual_offset,
                expected: expected_chain.to_string(),
                actual: actual_chain.to_string(),
            });
        }

        records.push(IndexRecord {
            offset,
            event_digest,
            chain_digest: actual_chain,
        });
        previous_chain = Some(actual_chain);
    }
    Ok(records)
}
