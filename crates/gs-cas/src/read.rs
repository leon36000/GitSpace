use crate::{safety, CasError, Digest, LocalCas};
use gs_canonical_json::sha256_digest;
use std::{fs::File, io::Read};

pub(crate) fn read_verified(cas: &LocalCas, digest: &Digest) -> Result<Vec<u8>, CasError> {
    let path = cas.object_path(digest);
    let path_metadata = safety::object_metadata(&path, digest)?;
    let mut file = File::open(&path)
        .map_err(|source| CasError::io("open object", &path, source))?;
    let opened_metadata = file
        .metadata()
        .map_err(|source| CasError::io("inspect opened object", &path, source))?;
    if !opened_metadata.is_file() || !safety::same_file_identity(&path_metadata, &opened_metadata) {
        return Err(CasError::UnsafePath {
            path,
            reason: "object path changed while it was being opened",
        });
    }
    let capacity = usize::try_from(opened_metadata.len()).unwrap_or(0);
    let mut bytes = Vec::with_capacity(capacity);
    file.read_to_end(&mut bytes)
        .map_err(|source| CasError::io("read object", &path, source))?;
    let actual = sha256_digest(&bytes);
    if actual != *digest {
        return Err(CasError::CorruptObject { expected: *digest, actual });
    }
    Ok(bytes)
}

pub(crate) fn verify_for_put(cas: &LocalCas, digest: &Digest, bytes: &[u8]) -> Result<Digest, CasError> {
    let existing = read_verified(cas, digest)?;
    if existing == bytes {
        Ok(*digest)
    } else {
        Err(CasError::DigestCollision { digest: *digest })
    }
}
