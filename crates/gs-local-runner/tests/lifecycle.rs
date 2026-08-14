use gs_cas::LocalCas;
use gs_local_runner::{
    AgentOperation, Capability, FixtureFile, LocalRunner, OracleCheck, RunPlan, RunStatus,
};
use std::{fs, path::Path, time::Duration};

fn runner(root: &Path) -> LocalRunner<LocalCas> {
    LocalRunner::open(root.join("runs"), LocalCas::open(root.join("cas")).unwrap()).unwrap()
}

fn plan(run_id: &str) -> RunPlan {
    RunPlan {
        run_id: run_id.to_owned(),
        fixture: vec![FixtureFile {
            path: "input/a.txt".to_owned(),
            bytes: b"a".to_vec(),
        }],
        oracle: Vec::new(),
        capability: Capability {
            readable_prefixes: vec!["input".to_owned()],
            writable_prefixes: vec!["output".to_owned()],
        },
        operations: Vec::new(),
        oracle_checks: vec![OracleCheck::WorkspaceFileAbsent {
            path: "output/must-not-exist.txt".to_owned(),
        }],
        timeout: Duration::from_secs(1),
    }
}

fn assert_run_root_empty(root: &Path) {
    let entries = fs::read_dir(root.join("runs")).unwrap().count();
    assert_eq!(entries, 0, "mutable run directory survived cleanup");
}

#[test]
fn policy_block_preserves_prior_effect_but_stops_all_later_operations() {
    let root = std::env::temp_dir().join(format!(
        "gitspace-task8-lifecycle-policy-{}",
        std::process::id()
    ));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(&root).unwrap();
    let runner = runner(&root);
    let mut plan = plan("GS-RUN-TASK8-LIFECYCLE-POLICY");
    plan.operations = vec![
        AgentOperation::Read {
            path: "input/a.txt".to_owned(),
        },
        AgentOperation::Write {
            path: "forbidden/no.txt".to_owned(),
            bytes: b"blocked".to_vec(),
        },
        AgentOperation::Write {
            path: "output/must-not-exist.txt".to_owned(),
            bytes: b"late".to_vec(),
        },
    ];

    let result = runner.execute(&plan).unwrap();
    assert_eq!(result.status, RunStatus::PolicyBlocked);
    assert_eq!(result.effects.len(), 1);
    assert_eq!(result.effects[0].path, "input/a.txt");
    assert!(
        result
            .workspace_artifacts
            .iter()
            .all(|artifact| artifact.path != "output/must-not-exist.txt")
    );
    assert!(result.cleaned_up);
    assert_run_root_empty(&root);
    let _ = fs::remove_dir_all(root);
}

#[test]
fn mutable_run_directory_is_removed_for_every_returned_status() {
    let scenarios = [
        (
            "completed",
            RunStatus::Completed,
            Vec::new(),
            vec![OracleCheck::WorkspaceFileAbsent {
                path: "output/x.txt".to_owned(),
            }],
        ),
        (
            "timeout",
            RunStatus::TimedOut,
            vec![AgentOperation::Delay { millis: 20 }],
            Vec::new(),
        ),
        (
            "oracle",
            RunStatus::OracleFailed,
            Vec::new(),
            vec![OracleCheck::WorkspaceFileEquals {
                path: "input/a.txt".to_owned(),
                expected: b"wrong".to_vec(),
            }],
        ),
    ];

    for (label, expected_status, operations, checks) in scenarios {
        let root = std::env::temp_dir().join(format!(
            "gitspace-task8-lifecycle-{label}-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir_all(&root).unwrap();
        let runner = runner(&root);
        let mut plan = plan(&format!("GS-RUN-TASK8-LIFECYCLE-{label}"));
        plan.operations = operations;
        plan.oracle_checks = checks;
        if expected_status == RunStatus::TimedOut {
            plan.timeout = Duration::from_millis(2);
        }

        let result = runner.execute(&plan).unwrap();
        assert_eq!(result.status, expected_status, "scenario={label}");
        assert!(result.cleaned_up, "scenario={label}");
        assert_run_root_empty(&root);
        let _ = fs::remove_dir_all(root);
    }
}
