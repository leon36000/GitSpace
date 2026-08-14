use crate::{
    AgentOperation, Capability, Effect, EffectKind, OracleCheck, RunPlan, RunResult, RunStatus,
    RunnerError,
    path::{
        Prefix, RelativePath, ensure_parent_directories, relative_path_string, safe_file_path,
        validate_authority_root,
    },
    snapshot::snapshot_workspace,
};
use gs_canonical_json::sha256_digest;
use gs_cas::Cas;
use std::{
    collections::BTreeSet,
    fs,
    path::{Path, PathBuf},
    thread,
    time::{Duration, Instant},
};

#[derive(Debug)]
pub struct LocalRunner<C: Cas> {
    root: PathBuf,
    cas: C,
}

#[derive(Debug)]
struct ValidatedCapability {
    readable: Vec<Prefix>,
    writable: Vec<Prefix>,
}

impl ValidatedCapability {
    fn from_public(capability: &Capability) -> Result<Self, RunnerError> {
        let readable = capability
            .readable_prefixes
            .iter()
            .map(|prefix| Prefix::parse(prefix))
            .collect::<Result<Vec<_>, _>>()?;
        let writable = capability
            .writable_prefixes
            .iter()
            .map(|prefix| Prefix::parse(prefix))
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Self { readable, writable })
    }

    fn can_read(&self, path: &RelativePath) -> bool {
        self.readable.iter().any(|prefix| prefix.matches(path))
    }

    fn can_write(&self, path: &RelativePath) -> bool {
        self.writable.iter().any(|prefix| prefix.matches(path))
    }
}

impl<C: Cas> LocalRunner<C> {
    pub fn open(root: impl AsRef<Path>, cas: C) -> Result<Self, RunnerError> {
        Ok(Self {
            root: validate_authority_root(root.as_ref())?,
            cas,
        })
    }

    pub fn execute(&self, plan: &RunPlan) -> Result<RunResult, RunnerError> {
        let capability = validate_plan(plan)?;
        let run_dir = self.create_run_directory(&plan.run_id)?;
        let execution = self.execute_in(&run_dir, plan, &capability);
        let cleanup = fs::remove_dir_all(&run_dir);

        match execution {
            Ok(mut result) => {
                cleanup.map_err(|source| RunnerError::Cleanup {
                    path: run_dir,
                    source,
                })?;
                result.cleaned_up = true;
                Ok(result)
            }
            Err(error) => {
                if let Err(source) = cleanup {
                    return Err(RunnerError::Cleanup {
                        path: run_dir,
                        source,
                    });
                }
                Err(error)
            }
        }
    }

    fn create_run_directory(&self, run_id: &str) -> Result<PathBuf, RunnerError> {
        let digest = sha256_digest(run_id.as_bytes()).to_string();
        let hex = digest
            .strip_prefix("sha256:")
            .expect("Digest display is prefixed with sha256:");
        let path = self.root.join(hex);
        match fs::create_dir(&path) {
            Ok(()) => Ok(path),
            Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
                Err(RunnerError::RunAlreadyExists { path })
            }
            Err(source) => Err(RunnerError::io("create run directory", &path, source)),
        }
    }

    fn execute_in(
        &self,
        run_dir: &Path,
        plan: &RunPlan,
        capability: &ValidatedCapability,
    ) -> Result<RunResult, RunnerError> {
        let workspace = run_dir.join("workspace");
        let oracle = run_dir.join("oracle");
        fs::create_dir(&workspace)
            .map_err(|source| RunnerError::io("create workspace", &workspace, source))?;
        fs::create_dir(&oracle)
            .map_err(|source| RunnerError::io("create oracle", &oracle, source))?;

        materialize_files(
            &workspace,
            plan.fixture.iter().map(|file| (&file.path, &file.bytes)),
        )?;
        materialize_files(
            &oracle,
            plan.oracle.iter().map(|file| (&file.path, &file.bytes)),
        )?;

        let started = Instant::now();
        let mut status = RunStatus::Completed;
        let mut effects = Vec::new();

        for operation in &plan.operations {
            if deadline_reached(started, plan.timeout) {
                status = RunStatus::TimedOut;
                break;
            }

            match operation {
                AgentOperation::Delay { millis } => {
                    let elapsed = started.elapsed();
                    let Some(remaining) = plan.timeout.checked_sub(elapsed) else {
                        status = RunStatus::TimedOut;
                        break;
                    };
                    let requested = Duration::from_millis(*millis);
                    thread::sleep(requested.min(remaining));
                    if deadline_reached(started, plan.timeout) {
                        status = RunStatus::TimedOut;
                        break;
                    }
                }
                AgentOperation::Read { path } => {
                    let Some(relative) = parse_agent_path(path) else {
                        status = RunStatus::PolicyBlocked;
                        break;
                    };
                    if !capability.can_read(&relative) {
                        status = RunStatus::PolicyBlocked;
                        break;
                    }
                    let resolved = match safe_file_path(&workspace, &relative, true) {
                        Ok(path) => path,
                        Err(RunnerError::UnsafePath { .. }) => {
                            status = RunStatus::PolicyBlocked;
                            break;
                        }
                        Err(error) => return Err(error),
                    };
                    let bytes = fs::read(&resolved).map_err(|source| {
                        RunnerError::io("read workspace file", &resolved, source)
                    })?;
                    let digest = self.cas.put(&bytes)?;
                    effects.push(Effect {
                        index: effects.len() as u64,
                        kind: EffectKind::Read,
                        path: relative.raw().to_owned(),
                        digest,
                    });
                }
                AgentOperation::Write { path, bytes } => {
                    let Some(relative) = parse_agent_path(path) else {
                        status = RunStatus::PolicyBlocked;
                        break;
                    };
                    if !capability.can_write(&relative) {
                        status = RunStatus::PolicyBlocked;
                        break;
                    }
                    if let Err(error) = ensure_parent_directories(&workspace, &relative) {
                        match error {
                            RunnerError::UnsafePath { .. } => {
                                status = RunStatus::PolicyBlocked;
                                break;
                            }
                            other => return Err(other),
                        }
                    }
                    let resolved = match safe_file_path(&workspace, &relative, false) {
                        Ok(path) => path,
                        Err(RunnerError::UnsafePath { .. }) => {
                            status = RunStatus::PolicyBlocked;
                            break;
                        }
                        Err(error) => return Err(error),
                    };
                    fs::write(&resolved, bytes).map_err(|source| {
                        RunnerError::io("write workspace file", &resolved, source)
                    })?;
                    let digest = self.cas.put(bytes)?;
                    effects.push(Effect {
                        index: effects.len() as u64,
                        kind: EffectKind::Write,
                        path: relative.raw().to_owned(),
                        digest,
                    });
                }
            }
        }

        let oracle_passed = if status == RunStatus::Completed {
            evaluate_oracle_checks(&workspace, &oracle, &plan.oracle_checks)?
        } else {
            false
        };
        if status == RunStatus::Completed && !oracle_passed {
            status = RunStatus::OracleFailed;
        }

        let (workspace_artifacts, workspace_snapshot) = snapshot_workspace(&workspace, &self.cas)?;
        Ok(RunResult {
            status,
            effects,
            workspace_artifacts,
            workspace_snapshot,
            oracle_passed,
            cleaned_up: false,
        })
    }
}

fn validate_plan(plan: &RunPlan) -> Result<ValidatedCapability, RunnerError> {
    if plan.run_id.is_empty() || plan.run_id.contains('\0') {
        return Err(RunnerError::UnsafeRunId);
    }

    validate_unique_paths(
        "fixture",
        plan.fixture.iter().map(|file| file.path.as_str()),
    )?;
    validate_unique_paths("oracle", plan.oracle.iter().map(|file| file.path.as_str()))?;
    for check in &plan.oracle_checks {
        match check {
            OracleCheck::WorkspaceFileEquals { path, .. }
            | OracleCheck::WorkspaceFileAbsent { path }
            | OracleCheck::OracleFileEquals { path, .. } => {
                RelativePath::parse(path)?;
            }
        }
    }
    ValidatedCapability::from_public(&plan.capability)
}

fn validate_unique_paths<'a>(
    kind: &'static str,
    paths: impl IntoIterator<Item = &'a str>,
) -> Result<(), RunnerError> {
    let mut seen = BTreeSet::new();
    for raw in paths {
        let path = RelativePath::parse(raw)?;
        let normalized = relative_path_string(path.path())?;
        if !seen.insert(normalized.clone()) {
            return Err(RunnerError::DuplicatePath {
                kind,
                path: normalized,
            });
        }
    }
    Ok(())
}

fn materialize_files<'a>(
    root: &Path,
    files: impl IntoIterator<Item = (&'a String, &'a Vec<u8>)>,
) -> Result<(), RunnerError> {
    for (raw, bytes) in files {
        let relative = RelativePath::parse(raw)?;
        ensure_parent_directories(root, &relative)?;
        let path = safe_file_path(root, &relative, false)?;
        fs::write(&path, bytes)
            .map_err(|source| RunnerError::io("materialize runner file", &path, source))?;
    }
    Ok(())
}

fn parse_agent_path(raw: &str) -> Option<RelativePath> {
    RelativePath::parse(raw).ok()
}

fn deadline_reached(started: Instant, timeout: Duration) -> bool {
    started.elapsed() >= timeout
}

fn evaluate_oracle_checks(
    workspace: &Path,
    oracle: &Path,
    checks: &[OracleCheck],
) -> Result<bool, RunnerError> {
    for check in checks {
        let passed = match check {
            OracleCheck::WorkspaceFileEquals { path, expected } => {
                optional_read(workspace, &RelativePath::parse(path)?)?
                    .is_some_and(|bytes| bytes.as_slice() == expected.as_slice())
            }
            OracleCheck::WorkspaceFileAbsent { path } => {
                optional_read(workspace, &RelativePath::parse(path)?)?.is_none()
            }
            OracleCheck::OracleFileEquals { path, expected } => {
                optional_read(oracle, &RelativePath::parse(path)?)?
                    .is_some_and(|bytes| bytes.as_slice() == expected.as_slice())
            }
        };
        if !passed {
            return Ok(false);
        }
    }
    Ok(true)
}

fn optional_read(root: &Path, relative: &RelativePath) -> Result<Option<Vec<u8>>, RunnerError> {
    let path = match safe_file_path(root, relative, true) {
        Ok(path) => path,
        Err(RunnerError::Io { source, .. }) if source.kind() == std::io::ErrorKind::NotFound => {
            return Ok(None);
        }
        Err(error) => return Err(error),
    };
    fs::read(&path)
        .map(Some)
        .map_err(|source| RunnerError::io("read oracle-check file", &path, source))
}
