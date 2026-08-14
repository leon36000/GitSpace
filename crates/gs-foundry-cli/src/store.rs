use crate::FoundryError;
use std::{
    fs,
    io,
    path::{Path, PathBuf},
};

pub(crate) fn canonical_existing_directory(
    path: &Path,
    label: &str,
) -> Result<PathBuf, FoundryError> {
    require_existing_directory(path, label)?;
    fs::canonicalize(path)
        .map_err(|source| FoundryError::io("canonicalize existing replay directory", path, source))
}

pub(crate) fn validate_replay_layout(
    cas_root: &Path,
    journal_root: &Path,
) -> Result<(), FoundryError> {
    for (path, label) in [
        (cas_root.to_path_buf(), "CAS root"),
        (cas_root.join("objects"), "CAS objects root"),
        (
            cas_root.join("objects").join("sha256"),
            "CAS SHA-256 namespace",
        ),
        (cas_root.join("tmp"), "CAS temporary root"),
        (journal_root.to_path_buf(), "journal root"),
        (journal_root.join("runs"), "journal runs root"),
    ] {
        require_existing_directory(&path, label)?;
    }
    Ok(())
}

fn require_existing_directory(path: &Path, label: &str) -> Result<(), FoundryError> {
    let metadata = match fs::symlink_metadata(path) {
        Ok(metadata) => metadata,
        Err(source) if source.kind() == io::ErrorKind::NotFound => {
            return Err(FoundryError::InvalidReceipt(format!(
                "{label} is missing at {}",
                path.display()
            )));
        }
        Err(source) => {
            return Err(FoundryError::io(
                "inspect existing replay directory",
                path,
                source,
            ));
        }
    };

    if metadata.file_type().is_symlink() {
        return Err(FoundryError::InvalidReceipt(format!(
            "{label} is a symbolic link at {}",
            path.display()
        )));
    }
    if !metadata.is_dir() {
        return Err(FoundryError::InvalidReceipt(format!(
            "{label} is not a directory at {}",
            path.display()
        )));
    }
    Ok(())
}
