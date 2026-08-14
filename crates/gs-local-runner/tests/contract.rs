use gs_cas::{Cas, LocalCas};
use gs_local_runner::{
    AgentOperation, Capability, EffectKind, FixtureFile, LocalRunner, OracleCheck, OracleFile,
    RunPlan, RunStatus,
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
            "gitspace-task8-{label}-{}-{serial}",
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

fn runner(root: &TestDir) -> (LocalRunner<LocalCas>, LocalCas) {
    let cas = LocalCas::open(root.path().join("cas")).unwrap();
    let runner = LocalRunner::open(root.path().join("runs"), LocalCas::open(root.path().join("cas")).unwrap()).unwrap();
    (runner, cas)
}

fn base_plan(run_id: &str) -> RunPlan {
    RunPlan {
        run_id: run_id.to_owned(),
        fixture: vec![FixtureFile {
            path: "input/message.txt".to_owned(),
            bytes: b"hello".to_vec(),
        }],
        oracle: vec![OracleFile {
            path: "secret/expected.txt".to_owned(),
            bytes: b"protected".to_vec(),
        }],
        capability: Capability {
            readable_prefixes: vec!["input".to_owned(), "output".to_owned()],
            writable_prefixes: vec!["output".to_owned()],
        },
        operations: Vec::new(),
        oracle_checks: Vec::new(),
        timeout: Duration::from_secs(1),
    }
}

#[test]
fn allowed_read_and_write_are_attributed_and_snapshot_backed_by_cas() {
    let root = TestDir::new("allowed");
    let (runner, cas) = runner(&root);
    let mut plan = base_plan("GS-RUN-TASK8-ALLOWED");
    plan.operations = vec![
        AgentOperation::Read {
            path: "input/message.txt".to_owned(),
        },
        AgentOperation::Write {
            path: "output/result.txt".to_owned(),
            bytes: b"done".to_vec(),
        },
    ];
    plan.oracle_checks = vec![OracleCheck::WorkspaceFileEquals {
        path: "output/result.txt".to_owned(),
        expected: b"done".to_vec(),
    }];

    let result = runner.execute(&plan).unwrap();
    assert_eq!(result.status, RunStatus::Completed);
    assert!(result.oracle_passed);
    assert!(result.cleaned_up);
    assert_eq!(result.effects.len(), 2);
    assert_eq!(result.effects[0].index, 0);
    assert_eq!(result.effects[0].kind, EffectKind::Read);
    assert_eq!(result.effects[1].index, 1);
    assert_eq!(result.effects[1].kind, EffectKind::Write);
    assert_eq!(cas.get(&result.effects[0].digest).unwrap(), b"hello");
    assert_eq!(cas.get(&result.effects[1].digest).unwrap(), b"done");

    let snapshot = cas.get(&result.workspace_snapshot).unwrap();
    let value: serde_json::Value = serde_json::from_slice(&snapshot).unwrap();
    let paths = value
        .as_array()
        .unwrap()
        .iter()
        .map(|entry| entry["path"].as_str().unwrap())
        .collect::<Vec<_>>();
    assert_eq!(paths, vec!["input/message.txt", "output/result.txt"]);
    assert!(
        result
            .workspace_artifacts
            .iter()
            .any(|artifact| artifact.path == "output/result.txt")
    );
}

#[test]
fn component_prefix_does_not_authorize_a_sibling() {
    let root = TestDir::new("prefix");
    let (runner, _) = runner(&root);
    let mut plan = base_plan("GS-RUN-TASK8-PREFIX");
    plan.capability.writable_prefixes = vec!["src".to_owned()];
    plan.operations = vec![AgentOperation::Write {
        path: "src2/escape.txt".to_owned(),
        bytes: b"no".to_vec(),
    }];

    let result = runner.execute(&plan).unwrap();
    assert_eq!(result.status, RunStatus::PolicyBlocked);
    assert!(result.effects.is_empty());
    assert!(result.cleaned_up);
}

#[test]
fn explicit_empty_prefix_authorizes_the_whole_workspace() {
    let root = TestDir::new("root-prefix");
    let (runner, _) = runner(&root);
    let mut plan = base_plan("GS-RUN-TASK8-ROOT");
    plan.capability.writable_prefixes = vec![String::new()];
    plan.operations = vec![AgentOperation::Write {
        path: "anywhere/file.txt".to_owned(),
        bytes: b"ok".to_vec(),
    }];

    let result = runner.execute(&plan).unwrap();
    assert_eq!(result.status, RunStatus::Completed);
    assert_eq!(result.effects.len(), 1);
}

#[test]
fn oracle_read_and_write_traversal_are_policy_blocked_before_effects() {
    for operation in [
        AgentOperation::Read {
            path: "../oracle/secret/expected.txt".to_owned(),
        },
        AgentOperation::Write {
            path: "../oracle/secret/expected.txt".to_owned(),
            bytes: b"tamper".to_vec(),
        },
    ] {
        let root = TestDir::new("oracle-deny");
        let (runner, _) = runner(&root);
        let mut plan = base_plan("GS-RUN-TASK8-ORACLE-DENY");
        plan.capability.readable_prefixes = vec![String::new()];
        plan.capability.writable_prefixes = vec![String::new()];
        plan.operations = vec![operation, AgentOperation::Write {
            path: "output/after.txt".to_owned(),
            bytes: b"must-not-run".to_vec(),
        }];

        let result = runner.execute(&plan).unwrap();
        assert_eq!(result.status, RunStatus::PolicyBlocked);
        assert!(result.effects.is_empty());
        assert!(result.cleaned_up);
    }
}

#[test]
fn timeout_stops_all_later_effects() {
    let root = TestDir::new("timeout");
    let (runner, _) = runner(&root);
    let mut plan = base_plan("GS-RUN-TASK8-TIMEOUT");
    plan.timeout = Duration::from_millis(5);
    plan.operations = vec![
        AgentOperation::Delay { millis: 25 },
        AgentOperation::Write {
            path: "output/late.txt".to_owned(),
            bytes: b"late".to_vec(),
        },
    ];

    let result = runner.execute(&plan).unwrap();
    assert_eq!(result.status, RunStatus::TimedOut);
    assert!(result.effects.is_empty());
    assert!(result.cleaned_up);
    assert!(
        result
            .workspace_artifacts
            .iter()
            .all(|artifact| artifact.path != "output/late.txt")
    );
}

#[test]
fn oracle_failure_is_observed_after_operations_and_cleanup_still_occurs() {
    let root = TestDir::new("oracle-fail");
    let (runner, _) = runner(&root);
    let mut plan = base_plan("GS-RUN-TASK8-ORACLE-FAIL");
    plan.operations = vec![AgentOperation::Write {
        path: "output/result.txt".to_owned(),
        bytes: b"wrong".to_vec(),
    }];
    plan.oracle_checks = vec![
        OracleCheck::WorkspaceFileEquals {
            path: "output/result.txt".to_owned(),
            expected: b"right".to_vec(),
        },
        OracleCheck::OracleFileEquals {
            path: "secret/expected.txt".to_owned(),
            expected: b"protected".to_vec(),
        },
    ];

    let result = runner.execute(&plan).unwrap();
    assert_eq!(result.status, RunStatus::OracleFailed);
    assert!(!result.oracle_passed);
    assert!(result.cleaned_up);
}
