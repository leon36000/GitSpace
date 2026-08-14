use serde_json::Value;
use sha2::{Digest as ShaDigestTrait, Sha256};
use std::{error::Error, fmt};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CanonicalJsonError {
    NegativeZero,
    Canonicalization(String),
}

impl fmt::Display for CanonicalJsonError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NegativeZero => {
                f.write_str("negative zero is not accepted at the GitSpace canonical JSON boundary")
            }
            Self::Canonicalization(message) => {
                write!(f, "canonical JSON serialization failed: {message}")
            }
        }
    }
}

impl Error for CanonicalJsonError {}

#[derive(Clone, Copy, PartialEq, Eq, Hash)]
pub struct Digest([u8; 32]);

impl Digest {
    pub const fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }
}

impl fmt::Debug for Digest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        fmt::Display::fmt(self, f)
    }
}

impl fmt::Display for Digest {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str("sha256:")?;
        for byte in self.0 {
            write!(f, "{byte:02x}")?;
        }
        Ok(())
    }
}

fn reject_negative_zero(value: &Value) -> Result<(), CanonicalJsonError> {
    match value {
        Value::Number(number) => {
            if let Some(float) = number.as_f64()
                && float == 0.0
                && float.is_sign_negative()
            {
                return Err(CanonicalJsonError::NegativeZero);
            }
        }
        Value::Array(values) => {
            for value in values {
                reject_negative_zero(value)?;
            }
        }
        Value::Object(values) => {
            for value in values.values() {
                reject_negative_zero(value)?;
            }
        }
        Value::Null | Value::Bool(_) | Value::String(_) => {}
    }
    Ok(())
}

pub fn canonical_bytes(value: &Value) -> Result<Vec<u8>, CanonicalJsonError> {
    reject_negative_zero(value)?;
    serde_json_canonicalizer::to_vec(value)
        .map_err(|error| CanonicalJsonError::Canonicalization(error.to_string()))
}

pub fn sha256_digest(bytes: &[u8]) -> Digest {
    let output = Sha256::digest(bytes);
    let mut digest = [0_u8; 32];
    digest.copy_from_slice(&output);
    Digest(digest)
}

pub fn canonical_digest(value: &Value) -> Result<Digest, CanonicalJsonError> {
    canonical_bytes(value).map(|bytes| sha256_digest(&bytes))
}
