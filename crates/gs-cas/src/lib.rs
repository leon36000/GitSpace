#![forbid(unsafe_code)]

mod error;
mod layout;
mod read;
mod safety;
mod temporary;
mod write;

pub use error::CasError;
pub use gs_canonical_json::Digest;
pub use layout::LocalCas;

pub trait Cas {
    fn put(&self, bytes: &[u8]) -> Result<Digest, CasError>;
    fn get(&self, digest: &Digest) -> Result<Vec<u8>, CasError>;
}

impl Cas for LocalCas {
    fn put(&self, bytes: &[u8]) -> Result<Digest, CasError> {
        write::put(self, bytes)
    }

    fn get(&self, digest: &Digest) -> Result<Vec<u8>, CasError> {
        read::read_verified(self, digest)
    }
}
