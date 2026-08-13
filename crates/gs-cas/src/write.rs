use crate::{
    read::verify_for_put,
    safety::{finalize_read_only, prepare_read_only, sync_directory, validate_directory},
    temporary::create_temporary,
    CasError, Digest, LocalCas,
};
use gs_canonical_json::sha256_digest;
use std::{fs, io::{self, Write}};

pub(crate) fn put(cas: &LocalCas, bytes: &[u8]) -> Result<Digest, CasError> {
    let digest = sha256_digest(bytes);
    let target = cas.object_path(&digest);

    match fs::symlink_metadata(&target) {
        Ok(_) => return verify_for_put(cas, &digest, bytes),
        Err(source) if source.kind() == io::ErrorKind::NotFound => {}
        Err(source) => return Err(CasError::io("inspect object", &target, source)),
    }

    let shard = target.parent().expect("CAS object path always has a shard");
    match fs::create_dir(shard) {
        Ok(()) => {}
        Err(source) if source.kind() == io::ErrorKind::AlreadyExists => {}
        Err(source) => return Err(CasError::io("create object shard", shard, source)),
    }
    validate_directory(shard)?;

    let (mut file, mut temporary) = create_temporary(&cas.temporary, &digest)?;
    file.write_all(bytes)
        .map_err(|source| CasError::io("write temporary object", temporary.path(), source))?;
    file.flush()
        .map_err(|source| CasError::io("flush temporary object", temporary.path(), source))?;
    file.sync_all()
        .map_err(|source| CasError::io("sync temporary object", temporary.path(), source))?;
    prepare_read_only(&file, temporary.path())?;
    drop(file);

    match fs::hard_link(temporary.path(), &target) {
        Ok(()) => {
            finalize_read_only(&target)?;
            temporary.cleanup().map_err(|source| {
                CasError::io("remove committed temporary object", temporary.path(), source)
            })?;
            sync_directory(shard)?;
            sync_directory(&cas.temporary)?;
            verify_for_put(cas, &digest, bytes)
        }
        Err(source) if source.kind() == io::ErrorKind::AlreadyExists => {
            temporary.cleanup().map_err(|cleanup| {
                CasError::io("remove losing temporary object", temporary.path(), cleanup)
            })?;
            verify_for_put(cas, &digest, bytes)
        }
        Err(source) => Err(CasError::AtomicCommit {
            path: target,
            source,
        }),
    }
}
