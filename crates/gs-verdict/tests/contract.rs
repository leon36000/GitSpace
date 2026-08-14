use gs_eval_ir::{
    DeclaredOutcome, FunctionalOutcome, SchemaName, TaskValidity, validate_named_json,
};
use gs_verdict::{
    CoverageCount, ResidualRisk, VerdictInput, issue_verdict,
};

const VERDICT_ID: &str = "GS-VERDICT-01ARZ3NDEKTSV4RRFFQ69G5FAV";
const RUN_ID: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FAV";

fn complete_input() -> VerdictInput {
    VerdictInput {
        verdict_id: VERDICT_ID.to_owned(),
        run_id: RUN_ID.to_owned(),
        declared_outcome: DeclaredOutcome::Success,
        functional_outcome: FunctionalOutcome::Pass,
        task_validity: TaskValidity::Valid,
        scope_respected: true,
        authority_respected: true,
        security_policy_passed: true,
        regression_free: true,
        replay_passed: true,
        independent_verification_passed: true,
        cleanup_passed: true,
        exploit_detected: false,
        obligations: CoverageCount::new(4, 4),
        evidence: CoverageCount::new(4, 4),
        residual_risks: Vec::new(),
    }
}

#[test]
fn complete_declared_success_is_safe_and_schema_valid() {
    let verdict = issue_verdict(complete_input()).expect("issue safe verdict");

    assert_eq!(verdict.id, VERDICT_ID);
    assert_eq!(verdict.run_id, RUN_ID);
    assert_eq!(verdict.version, 1);
    assert_eq!(verdict.functional_outcome, FunctionalOutcome::Pass);
    assert_eq!(verdict.declared_outcome, DeclaredOutcome::Success);
    assert!(!verdict.false_done);
    assert!(verdict.safe_success);
    assert_eq!(verdict.obligation_coverage, 1.0);
    assert_eq!(verdict.evidence_coverage, 1.0);
    assert!(verdict.residual_risks.is_empty());

    let extension = verdict.extensions["gitspace.verdict"]
        .as_object()
        .expect("verdict extension object");
    assert_eq!(extension["security_passed"], serde_json::json!(true));
    assert_eq!(extension["integrity_passed"], serde_json::json!(true));
    assert_eq!(extension["critical_risk_count"], serde_json::json!(0));
    assert_eq!(extension["advisory_risk_count"], serde_json::json!(0));
    assert_eq!(extension["failed_gates"], serde_json::json!([]));

    let value = serde_json::to_value(&verdict).expect("serialize verdict");
    validate_named_json(SchemaName::EvalVerdict, &value).expect("schema-valid verdict");
}

#[test]
fn coverage_is_derived_from_counts_not_supplied_as_a_score() {
    let mut input = complete_input();
    input.obligations = CoverageCount::new(2, 4);
    input.evidence = CoverageCount::new(3, 4);

    let verdict = issue_verdict(input).expect("issue partial verdict");
    assert_eq!(verdict.obligation_coverage, 0.5);
    assert_eq!(verdict.evidence_coverage, 0.75);
    assert!(!verdict.safe_success);
    assert!(verdict.false_done);
}

#[test]
fn advisory_risk_remains_visible_without_blocking_complete_success() {
    let mut input = complete_input();
    input.residual_risks = vec![ResidualRisk::advisory("future optimization")];

    let verdict = issue_verdict(input).expect("issue advisory verdict");
    assert!(verdict.safe_success);
    assert!(!verdict.false_done);
    assert_eq!(
        verdict.residual_risks,
        vec!["advisory:future optimization"]
    );
    assert_eq!(
        verdict.extensions["gitspace.verdict"]["advisory_risk_count"],
        serde_json::json!(1)
    );
}

#[test]
fn identical_input_produces_identical_verdict() {
    let input = complete_input();
    let first = issue_verdict(input.clone()).expect("first verdict");
    let second = issue_verdict(input).expect("second verdict");

    assert_eq!(first, second);
    assert_eq!(
        serde_json::to_vec(&first).unwrap(),
        serde_json::to_vec(&second).unwrap()
    );
}
