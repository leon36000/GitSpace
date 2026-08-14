use crate::{RunnerError, WorkspaceArtifact, path::relative_path_string};
use gs_canonical_json::canonical_bytes;
use gs_cas::{Cas, Digest};
use serde::Serialize;
use std::{fs, path::Path};

#[derive(Serialize)]
struct SnapshotEntry<'a> {
    path: &'a str,
    digest: String,
}

pub(crate) fn snapshot_workspace<C: Cas>(
    workspace: &Path,
    cas: &C,
) -> Result<(Vec<WorkspaceArtifact>, Digest), RunnerError> {
    let mut artifacts = Vec::new();
    collect_files(workspace, workspace, cas, &mut artifacts)?;
    artifacts.sort_by(|left, right| left.path.cmp(&right.path));

    let entries = artifacts
        .iter()
        .map(|artifact| SnapshotEntry {
            path: &artifact.path,
            digest: artifact.digest.to_string(),
        })
        .collect::<Vec<_>>();
    let value = serde_json::to_value(entries)?;
    let bytes = canonical_bytes(&value)?;
    let digest = cas.put(&bytes)?;
    Ok((artifacts, digest))
}

fn collect_files<C: Cas>(
    workspace: &Path,
    directory: &Path,
    cas: &C,
    artifacts: &mut Vec<WorkspaceArtifact>,
) -> Result<(), RunnerError> {
    let mut entries = fs::read_dir(directory)
        .map_err(|source| RunnerError::io("read workspace directory", directory, source))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|source| RunnerError::io("enumerate workspace directory", directory, source))?;
    entries.sort_by_key(|entry| entry.file_name());

    for entry in entries {
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|source| RunnerError::io("inspect workspace snapshot path", &path, source))?;
        if metadata.file_type().is_symlink() {
            return Err(RunnerError::UnsafePath {
                path: path.display().to_string(),
                reason: "workspace snapshot contains a symbolic link",
            });
        }
        if metadata.is_dir() {
            collect_files(workspace, &path, cas, artifacts)?;
            continue;
        }
        if !metadata.is_file() {
            return Err(RunnerError::UnsafePath {
                path: path.display().to_string(),
                reason: "workspace snapshot contains a non-regular file",
            });
        }

        let bytes = fs::read(&path)
            .map_err(|source| RunnerError::io("read workspace snapshot file", &path, source))?;
        let digest = cas.put(&bytes)?;
        let relative = path
            .strip_prefix(workspace)
            .map_err(|_| RunnerError::UnsafePath {
                path: path.display().to_string(),
                reason: "workspace snapshot path escaped its root",
            })?;
        artifacts.push(WorkspaceArtifact {
            path: relative_path_string(relative)?,
            digest,
        });
    }
    Ok(())
}
