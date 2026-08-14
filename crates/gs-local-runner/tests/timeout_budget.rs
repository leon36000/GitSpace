use gs_cas::LocalCas;
use gs_local_runner::{AgentOperation, Capability, LocalRunner, RunPlan, RunStatus};
use std::{
    fs,
    time::{Duration, Instant},
};

#[test]
fn delay_is_bounded_by_the_remaining_timeout_budget() {
    let root = std::env::temp_dir().join(format!(
        "gitspace-task8-delay-budget-{}",
        std::process::id()
    ));
    let _ = fs::remove_dir_all(&root);
    fs::create_dir_all(&root).unwrap();

    let runner =
        LocalRunner::open(root.join("runs"), LocalCas::open(root.join("cas")).unwrap()).unwrap();
    let plan = RunPlan {
        run_id: "GS-RUN-TASK8-DELAY-BUDGET".to_owned(),
        fixture: Vec::new(),
        oracle: Vec::new(),
        capability: Capability {
            readable_prefixes: Vec::new(),
            writable_prefixes: Vec::new(),
        },
        operations: vec![AgentOperation::Delay { millis: 500 }],
        oracle_checks: Vec::new(),
        timeout: Duration::from_millis(10),
    };

    let started = Instant::now();
    let result = runner.execute(&plan).unwrap();
    let elapsed = started.elapsed();

    assert_eq!(result.status, RunStatus::TimedOut);
    assert!(result.effects.is_empty());
    assert!(result.cleaned_up);
    assert!(
        elapsed < Duration::from_millis(250),
        "runner slept for the requested delay instead of the timeout budget: {elapsed:?}"
    );

    let _ = fs::remove_dir_all(root);
}
