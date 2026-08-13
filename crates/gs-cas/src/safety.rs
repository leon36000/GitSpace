use crate::{CasError, Digest};
use std::{fs, fs::File, path::Path};

pub(crate) fn validate_directory(path: &Path) -> Result<(), CasError> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|source| CasError::io("inspect directory", path, source))?;
    if metadata.file_type().is_symlink() {
        return Err(CasError::UnsafePath {
            path: path.to_owned(),
            reason: "directory component is a symbolic link",
        });
    }
    if !metadata.is_dir() {
        return Err(CasError::UnsafePath {
            path: path.to_owned(),
            reason: "directory component is not a directory",
        });
    }
    Ok(())
}

pub(crate) fn object_metadata(path: &Path, digest: &Digest) -> Result<fs::Metadata, CasError> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.file_type().is_symlink() => Err(CasError::UnsafePath {
            path: path.to_owned(),
            reason: "object is a symbolic link",
        }),
        Ok(metadata) if !metadata.is_file() => Err(CasError::UnsafePath {
            path: path.to_owned(),
            reason: "object is not a regular file",
        }),
        Ok(metadata) => Ok(metadata),
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => {
            Err(CasError::NotFound { digest: *digest })
        }
        Err(source) => Err(CasError::io("inspect object", path, source)),
    }
}

#[cfg(unix)]
pub(crate) fn same_file_identity(left: &fs::Metadata, right: &fs::Metadata) -> bool {
    use std::os::unix::fs::MetadataExt;
    left.dev() == right.dev() && left.ino() == right.ino()
}

#[cfg(not(unix))]
pub(crate) fn same_file_identity(_left: &fs::Metadata, right: &fs::Metadata) -> bool {
    right.is_file()
}

#[cfg(unix)]
pub(crate) fn prepare_read_only(file: &File, path: &Path) -> Result<(), CasError> {
    use std::os::unix::fs::PermissionsExt;
    let mut permissions = file
        .metadata()
        .map_err(|source| CasError::io("inspect temporary permissions", path, source))?
        .permissions();
    permissions.set_mode(0o444);
    file.set_permissions(permissions)
        .map_err(|source| CasError::io("set temporary read-only", path, source))
}

#[cfg(not(unix))]
pub(crate) fn prepare_read_only(_file: &File, _path: &Path) -> Result<(), CasError> {
    Ok(())
}

#[cfg(unix)]
pub(crate) fn finalize_read_only(_path: &Path) -> Result<(), CasError> {
    Ok(())
}

#[cfg(not(unix))]
pub(crate) fn finalize_read_only(path: &Path) -> Result<(), CasError> {
    let mut permissions = fs::metadata(path)
        .map_err(|source| CasError::io("inspect committed permissions", path, source))?
        .permissions();
    permissions.set_readonly(true);
    fs::set_permissions(path, permissions)
        .map_err(|source| CasError::io("set committed read-only", path, source))
}

#[cfg(unix)]
pub(crate) fn sync_directory(path: &Path) -> Result<(), CasError> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|source| CasError::io("sync directory", path, source))
}

#[cfg(not(unix))]
pub(crate) fn sync_directory(_path: &Path) -> Result<(), CasError> {
    Ok(())
}
