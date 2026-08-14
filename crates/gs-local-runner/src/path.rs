use crate::RunnerError;
use std::{
    fs,
    path::{Component, Path, PathBuf},
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct RelativePath {
    raw: String,
    path: PathBuf,
}

impl RelativePath {
    pub(crate) fn parse(raw: &str) -> Result<Self, RunnerError> {
        if raw.is_empty() {
            return Err(RunnerError::UnsafePath {
                path: raw.to_owned(),
                reason: "path is empty",
            });
        }
        if raw.contains('\0') {
            return Err(RunnerError::UnsafePath {
                path: raw.to_owned(),
                reason: "path contains NUL",
            });
        }

        let path = Path::new(raw);
        let mut normal_components = 0_usize;
        for component in path.components() {
            match component {
                Component::Normal(_) => normal_components += 1,
                Component::Prefix(_) => {
                    return Err(RunnerError::UnsafePath {
                        path: raw.to_owned(),
                        reason: "platform path prefix is forbidden",
                    });
                }
                Component::RootDir => {
                    return Err(RunnerError::UnsafePath {
                        path: raw.to_owned(),
                        reason: "absolute paths are forbidden",
                    });
                }
                Component::CurDir => {
                    return Err(RunnerError::UnsafePath {
                        path: raw.to_owned(),
                        reason: "current-directory components are forbidden",
                    });
                }
                Component::ParentDir => {
                    return Err(RunnerError::UnsafePath {
                        path: raw.to_owned(),
                        reason: "parent-directory components are forbidden",
                    });
                }
            }
        }
        if normal_components == 0 {
            return Err(RunnerError::UnsafePath {
                path: raw.to_owned(),
                reason: "path has no normal components",
            });
        }

        Ok(Self {
            raw: raw.to_owned(),
            path: path.to_path_buf(),
        })
    }

    pub(crate) fn path(&self) -> &Path {
        &self.path
    }

    pub(crate) fn raw(&self) -> &str {
        &self.raw
    }
}

#[derive(Debug, Clone)]
pub(crate) enum Prefix {
    Root,
    Relative(PathBuf),
}

impl Prefix {
    pub(crate) fn parse(raw: &str) -> Result<Self, RunnerError> {
        if raw.is_empty() {
            return Ok(Self::Root);
        }
        RelativePath::parse(raw).map(|path| Self::Relative(path.path))
    }

    pub(crate) fn matches(&self, path: &RelativePath) -> bool {
        match self {
            Self::Root => true,
            Self::Relative(prefix) => path.path.starts_with(prefix),
        }
    }
}

pub(crate) fn validate_authority_root(path: &Path) -> Result<PathBuf, RunnerError> {
    match fs::symlink_metadata(path) {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() {
                return Err(RunnerError::UnsafePath {
                    path: path.display().to_string(),
                    reason: "authority root is a symbolic link",
                });
            }
            if !metadata.is_dir() {
                return Err(RunnerError::UnsafePath {
                    path: path.display().to_string(),
                    reason: "authority root is not a directory",
                });
            }
        }
        Err(source) if source.kind() == std::io::ErrorKind::NotFound => {
            fs::create_dir_all(path)
                .map_err(|source| RunnerError::io("create authority root", path, source))?;
            let metadata = fs::symlink_metadata(path)
                .map_err(|source| RunnerError::io("inspect authority root", path, source))?;
            if metadata.file_type().is_symlink() || !metadata.is_dir() {
                return Err(RunnerError::UnsafePath {
                    path: path.display().to_string(),
                    reason: "created authority root is not a regular directory",
                });
            }
        }
        Err(source) => return Err(RunnerError::io("inspect authority root", path, source)),
    }

    fs::canonicalize(path)
        .map_err(|source| RunnerError::io("canonicalize authority root", path, source))
}

pub(crate) fn ensure_parent_directories(
    root: &Path,
    relative: &RelativePath,
) -> Result<(), RunnerError> {
    let parent = relative.path().parent().unwrap_or_else(|| Path::new(""));
    let mut current = root.to_path_buf();
    for component in parent.components() {
        let Component::Normal(part) = component else {
            unreachable!("RelativePath was validated before parent traversal")
        };
        current.push(part);
        match fs::symlink_metadata(&current) {
            Ok(metadata) => {
                if metadata.file_type().is_symlink() {
                    return Err(RunnerError::UnsafePath {
                        path: relative.raw().to_owned(),
                        reason: "path traverses a symbolic link",
                    });
                }
                if !metadata.is_dir() {
                    return Err(RunnerError::UnsafePath {
                        path: relative.raw().to_owned(),
                        reason: "path parent is not a directory",
                    });
                }
            }
            Err(source) if source.kind() == std::io::ErrorKind::NotFound => {
                fs::create_dir(&current).map_err(|source| {
                    RunnerError::io("create workspace parent", &current, source)
                })?;
            }
            Err(source) => {
                return Err(RunnerError::io(
                    "inspect workspace parent",
                    &current,
                    source,
                ));
            }
        }
    }
    Ok(())
}

pub(crate) fn safe_file_path(
    root: &Path,
    relative: &RelativePath,
    require_existing: bool,
) -> Result<PathBuf, RunnerError> {
    let mut current = root.to_path_buf();
    let components = relative.path().components().collect::<Vec<_>>();
    for (index, component) in components.iter().enumerate() {
        let Component::Normal(part) = component else {
            unreachable!("RelativePath was validated before traversal")
        };
        current.push(part);
        let is_final = index + 1 == components.len();
        match fs::symlink_metadata(&current) {
            Ok(metadata) => {
                if metadata.file_type().is_symlink() {
                    return Err(RunnerError::UnsafePath {
                        path: relative.raw().to_owned(),
                        reason: "path resolves through a symbolic link",
                    });
                }
                if is_final {
                    if metadata.is_dir() {
                        return Err(RunnerError::UnsafePath {
                            path: relative.raw().to_owned(),
                            reason: "file path resolves to a directory",
                        });
                    }
                } else if !metadata.is_dir() {
                    return Err(RunnerError::UnsafePath {
                        path: relative.raw().to_owned(),
                        reason: "path parent is not a directory",
                    });
                }
            }
            Err(source) if source.kind() == std::io::ErrorKind::NotFound => {
                if require_existing || !is_final {
                    return Err(RunnerError::io("resolve runner path", &current, source));
                }
            }
            Err(source) => return Err(RunnerError::io("inspect runner path", &current, source)),
        }
    }
    Ok(current)
}

pub(crate) fn relative_path_string(path: &Path) -> Result<String, RunnerError> {
    let mut parts = Vec::new();
    for component in path.components() {
        let Component::Normal(part) = component else {
            return Err(RunnerError::UnsafePath {
                path: path.display().to_string(),
                reason: "snapshot path is not relative-normal",
            });
        };
        let Some(part) = part.to_str() else {
            return Err(RunnerError::UnsafePath {
                path: path.display().to_string(),
                reason: "snapshot path is not UTF-8",
            });
        };
        parts.push(part);
    }
    Ok(parts.join("/"))
}

#[cfg(all(test, unix))]
mod tests {
    use super::{RelativePath, safe_file_path};
    use crate::RunnerError;
    use std::{fs, os::unix::fs::symlink};

    #[test]
    fn existing_symlink_component_is_rejected() {
        let root = std::env::temp_dir().join(format!(
            "gitspace-task8-path-symlink-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&root);
        let workspace = root.join("workspace");
        let outside = root.join("outside");
        fs::create_dir_all(&workspace).unwrap();
        fs::create_dir_all(&outside).unwrap();
        fs::write(outside.join("secret.txt"), b"outside").unwrap();
        symlink(&outside, workspace.join("link")).unwrap();

        let relative = RelativePath::parse("link/secret.txt").unwrap();
        assert!(matches!(
            safe_file_path(&workspace, &relative, true).unwrap_err(),
            RunnerError::UnsafePath { .. }
        ));

        let _ = fs::remove_dir_all(root);
    }
}
