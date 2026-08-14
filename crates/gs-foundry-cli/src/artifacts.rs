use crate::FoundryError;
use gs_canonical_json::{Digest, canonical_bytes};
use gs_cas::{Cas, LocalCas};
use serde::{Serialize, de::DeserializeOwned};

pub(crate) fn put_json<T: Serialize>(cas: &LocalCas, value: &T) -> Result<String, FoundryError> {
    let json = serde_json::to_value(value)?;
    let bytes = canonical_bytes(&json)?;
    Ok(cas_uri(cas.put(&bytes)?))
}

pub(crate) fn put_value(cas: &LocalCas, value: &serde_json::Value) -> Result<String, FoundryError> {
    let bytes = canonical_bytes(value)?;
    Ok(cas_uri(cas.put(&bytes)?))
}

pub(crate) fn get_bytes(cas: &LocalCas, uri: &str) -> Result<Vec<u8>, FoundryError> {
    let digest = parse_cas_uri(uri)?;
    Ok(cas.get(&digest)?)
}

pub(crate) fn get_json<T: DeserializeOwned>(cas: &LocalCas, uri: &str) -> Result<T, FoundryError> {
    let bytes = get_bytes(cas, uri)?;
    Ok(serde_json::from_slice(&bytes)?)
}

pub(crate) fn cas_uri(digest: Digest) -> String {
    format!("cas://sha256/{}", &digest.to_string()["sha256:".len()..])
}

pub(crate) fn parse_cas_uri(uri: &str) -> Result<Digest, FoundryError> {
    let hex = uri
        .strip_prefix("cas://sha256/")
        .ok_or_else(|| FoundryError::InvalidReceipt(format!("not a CAS URI: {uri}")))?;
    if hex.len() != 64 || !hex.bytes().all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)) {
        return Err(FoundryError::InvalidReceipt(format!("malformed CAS digest: {uri}")));
    }
    let mut bytes = [0_u8; 32];
    for (index, slot) in bytes.iter_mut().enumerate() {
        let high = hex_value(hex.as_bytes()[index * 2]);
        let low = hex_value(hex.as_bytes()[index * 2 + 1]);
        *slot = (high << 4) | low;
    }
    Ok(Digest::from_bytes(bytes))
}

fn hex_value(byte: u8) -> u8 {
    match byte {
        b'0'..=b'9' => byte - b'0',
        b'a'..=b'f' => byte - b'a' + 10,
        _ => unreachable!("parse_cas_uri checked lowercase hex"),
    }
}
