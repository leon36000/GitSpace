use gs_cas::LocalCas;
use gs_local_runner::{
    AgentOperation, Capability, FixtureFile, LocalRunner, OracleCheck, OracleFile, RunPlan,
    RunStatus, RunnerError,
};
use std::{
    fs,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
    time::Duration,
};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TestDir(PathBuf);

impl TestDir {
    fn new(label: &str) -> Self {
        let serial = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "gitspace-task8-adv-{label}-{}-{serial}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&path);
        fs::create_dir_all(&path).unwrap();
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TestDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn runner(root: &TestDir) -> LocalRunner<LocalCas> {
    LocalRunner::open(
        root.path().join("runs"),
        LocalCas::open(root.path().join("cas")).unwrap(),
    )
    .unwrap()
}

fn plan(run_id: &str) -> RunPlan {
    RunPlan {
        run_id: run_id.to_owned(),
        fixture: vec![FixtureFile {
            path: "fixture/a.txt".to_owned(),
            bytes: b"a".to_vec(),
        }],
        oracle: vec![OracleFile {
            path: "truth/hidden.txt".to_owned(),
            bytes: b"hidden".to_vec(),
        }],
        capability: Capability {
            readable_prefixes: vec![String::new()],
            writable_prefixes: vec![String::new()],
        },
        operations: Vec::new(),
        oracle_checks: vec![OracleCheck::OracleFileEquals {
            path: "truth/hidden.txt".to_owned(),
            expected: b"hidden".to_vec(),
        }],
        timeout: Duration::from_secs(1),
    }
}

#[test]
fn unsafe_operation_paths_are_policy_blocked_without_effects() {
    let unsafe_paths = ["", ".", "../escape", "/absolute", "safe/../escape", "nul\0byte"];

    for (index, path) in unsafe_paths.into_iter().enumerate() {
        let root = TestDir::new(&format!("unsafe-{index}"));
        let runner = runner(&root);
        let mut plan = plan(&format!("GS-RUN-TASK8-UNSAFE-{index}"));
        plan.operations = vec![AgentOperation::Write {
            path: path.to_owned(),
            bytes: b"x".to_vec(),
        }];
        let result = runner.execute(&plan).unwrap();
        assert_eq!(result.status, RunStatus::PolicyBlocked, "path={path:?}");
        assert!(result.effects.is_empty(), "path={path:?}");
        assert!(result.cleaned_up);
    }
}

#[test]
fn duplicate_fixture_and_oracle_paths_fail_before_effects() {
    let root = TestDir::new("duplicates");
    let runner = runner(&root);

    let mut fixture_dup = plan("GS-RUN-TASK8-DUP-FIXTURE");
    fixture_dup.fixture.push(FixtureFile {
        path: "fixture/a.txt".to_owned(),
        bytes: b"duplicate".to_vec(),
    });
    assert!(matches!(
        runner.execute(&fixture_dup).unwrap_err(),
        RunnerError::DuplicatePath { .. }
    ));

    let mut oracle_dup = plan("GS-RUN-TASK8-DUP-ORACLE");
    oracle_dup.oracle.push(OracleFile {
        path: "truth/hidden.txt".to_owned(),
        bytes: b"duplicate".to_vec(),
    });
    assert!(matches!(
        runner.execute(&oracle_dup).unwrap_err(),
        RunnerError::DuplicatePath { .. }
    ));
}

#[test]
fn empty_or_nul_run_id_fails_before_directory_creation() {
    for run_id in ["", "GS-RUN\0BAD"] {
        let root = TestDir::new("run-id");
        let runner = runner(&root);
        let plan = plan(run_id);
        assert!(matches!(
            runner.execute(&plan).unwrap_err(),
            RunnerError::UnsafeRunId
        ));
    }
}

#[cfg(unix)]
#[test]
fn symlink_authority_root_is_rejected() {
    use std::os::unix::fs::symlink;

    let root = TestDir::new("root-symlink");
    let real = root.path().join("real");
    fs::create_dir_all(&real).unwrap();
    let link = root.path().join("link");
    symlink(&real, &link).unwrap();

    let error = LocalRunner::open(link, LocalCas::open(root.path().join("cas")).unwrap())
        .unwrap_err();
    assert!(matches!(error, RunnerError::UnsafePath { .. }));
}

#[test]
fn effect_indices_are_contiguous_and_follow_operation_order() {
    let root = TestDir::new("effects");
    let runner = runner(&root);
    let mut plan = plan("GS-RUN-TASK8-EFFECTS");
    plan.operations = vec![
        AgentOperation::Read {
            path: "fixture/a.txt".to_owned(),
        },
        AgentOperation::Write {
            path: "out/one.txt".to_owned(),
            bytes: b"1".to_vec(),
        },
        AgentOperation::Write {
            path: "out/two.txt".to_owned(),
            bytes: b"2".to_vec(),
        },
    ];
    let result = runner.execute(&plan).unwrap();
    assert_eq!(
        result.effects.iter().map(|effect| effect.index).collect::<Vec<_>>(),
        vec![0, 1, 2]
    );
}

#[test]
fn snapshot_never_contains_oracle_paths() {
    let root = TestDir::new("snapshot-no-oracle");
    let cas = LocalCas::open(root.path().join("cas")).unwrap();
    let runner = LocalRunner::open(
        root.path().join("runs"),
        LocalCas::open(root.path().join("cas")).unwrap(),
    )
    .unwrap();
    let result = runner.execute(&plan("GS-RUN-TASK8-SNAPSHOT")).unwrap();
    let snapshot = gs_cas::Cas::get(&cas, &result.workspace_snapshot).unwrap();
    let text = String::from_utf8(snapshot).unwrap();
    assert!(!text.contains("truth/hidden.txt"));
    assert!(!text.contains("oracle"));
}
