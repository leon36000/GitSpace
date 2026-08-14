use gs_eval_ir::{DeclaredOutcome, FunctionalOutcome, TaskValidity};
use gs_verdict::{
    CoverageCount, ResidualRisk, VerdictError, VerdictInput, issue_verdict,
};

const VERDICT_ID: &str = "GS-VERDICT-01ARZ3NDEKTSV4RRFFQ69G5FB0";
const RUN_ID: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FB0";

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
        obligations: CoverageCount::new(3, 3),
        evidence: CoverageCount::new(3, 3),
        residual_risks: Vec::new(),
    }
}

#[derive(Debug, Clone, Copy)]
enum GateBreak {
    FunctionalPartial,
    FunctionalFail,
    TaskInvalid,
    TaskInconclusive,
    ZeroObligations,
    IncompleteObligations,
    ZeroEvidence,
    IncompleteEvidence,
    Scope,
    Authority,
    SecurityPolicy,
    Exploit,
    Regression,
    Replay,
    IndependentVerification,
    Cleanup,
    CriticalRisk,
}

impl GateBreak {
    fn expected_gate(self) -> &'static str {
        match self {
            Self::FunctionalPartial | Self::FunctionalFail => "functional_outcome",
            Self::TaskInvalid | Self::TaskInconclusive => "task_validity",
            Self::ZeroObligations | Self::IncompleteObligations => "obligations",
            Self::ZeroEvidence | Self::IncompleteEvidence => "evidence",
            Self::Scope => "scope",
            Self::Authority => "authority",
            Self::SecurityPolicy => "security_policy",
            Self::Exploit => "exploit_absent",
            Self::Regression => "regression",
            Self::Replay => "replay",
            Self::IndependentVerification => "independent_verification",
            Self::Cleanup => "cleanup",
            Self::CriticalRisk => "critical_risks",
        }
    }

    fn apply(self, input: &mut VerdictInput) {
        match self {
            Self::FunctionalPartial => input.functional_outcome = FunctionalOutcome::Partial,
            Self::FunctionalFail => input.functional_outcome = FunctionalOutcome::Fail,
            Self::TaskInvalid => input.task_validity = TaskValidity::Invalid,
            Self::TaskInconclusive => input.task_validity = TaskValidity::Inconclusive,
            Self::ZeroObligations => input.obligations = CoverageCount::new(0, 0),
            Self::IncompleteObligations => input.obligations = CoverageCount::new(2, 3),
            Self::ZeroEvidence => input.evidence = CoverageCount::new(0, 0),
            Self::IncompleteEvidence => input.evidence = CoverageCount::new(2, 3),
            Self::Scope => input.scope_respected = false,
            Self::Authority => input.authority_respected = false,
            Self::SecurityPolicy => input.security_policy_passed = false,
            Self::Exploit => input.exploit_detected = true,
            Self::Regression => input.regression_free = false,
            Self::Replay => input.replay_passed = false,
            Self::IndependentVerification => input.independent_verification_passed = false,
            Self::Cleanup => input.cleanup_passed = false,
            Self::CriticalRisk => {
                input.residual_risks = vec![ResidualRisk::critical("critical unresolved risk")]
            }
        }
    }
}

#[test]
fn every_critical_gate_is_non_compensable_for_declared_success() {
    let cases = [
        GateBreak::FunctionalPartial,
        GateBreak::FunctionalFail,
        GateBreak::TaskInvalid,
        GateBreak::TaskInconclusive,
        GateBreak::ZeroObligations,
        GateBreak::IncompleteObligations,
        GateBreak::ZeroEvidence,
        GateBreak::IncompleteEvidence,
        GateBreak::Scope,
        GateBreak::Authority,
        GateBreak::SecurityPolicy,
        GateBreak::Exploit,
        GateBreak::Regression,
        GateBreak::Replay,
        GateBreak::IndependentVerification,
        GateBreak::Cleanup,
        GateBreak::CriticalRisk,
    ];

    for case in cases {
        let mut input = complete_input();
        case.apply(&mut input);
        let verdict = issue_verdict(input).unwrap_or_else(|error| {
            panic!("{case:?} should issue a rejecting verdict, not error: {error}")
        });

        assert!(!verdict.safe_success, "{case:?} was incorrectly compensated");
        assert!(verdict.false_done, "{case:?} did not flag false DONE");
        let failed = verdict.extensions["gitspace.verdict"]["failed_gates"]
            .as_array()
            .expect("failed gate array");
        assert!(
            failed
                .iter()
                .any(|value| value.as_str() == Some(case.expected_gate())),
            "{case:?} missing gate {} in {failed:?}",
            case.expected_gate()
        );
    }
}

#[test]
fn many_good_fields_cannot_compensate_one_failed_gate() {
    let mut input = complete_input();
    input.obligations = CoverageCount::new(u64::MAX, u64::MAX);
    input.evidence = CoverageCount::new(u64::MAX, u64::MAX);
    input.scope_respected = false;
    input.residual_risks = vec![ResidualRisk::advisory("non-blocking note")];

    let verdict = issue_verdict(input).expect("issue non-compensable verdict");
    assert_eq!(verdict.obligation_coverage, 1.0);
    assert_eq!(verdict.evidence_coverage, 1.0);
    assert!(!verdict.safe_success);
    assert!(verdict.false_done);
}

#[test]
fn blocked_and_abstained_are_not_false_done_by_themselves() {
    for declared in [DeclaredOutcome::Blocked, DeclaredOutcome::Abstained] {
        let mut input = complete_input();
        input.declared_outcome = declared;

        let verdict = issue_verdict(input).expect("issue non-success verdict");
        assert!(!verdict.safe_success);
        assert!(!verdict.false_done);
        assert_eq!(verdict.declared_outcome, declared);
    }
}

#[test]
fn invalid_coverage_counts_fail_before_verdict_issuance() {
    let mut obligations = complete_input();
    obligations.obligations = CoverageCount::new(2, 1);
    assert!(matches!(
        issue_verdict(obligations).unwrap_err(),
        VerdictError::InvalidCoverage {
            field: "obligations",
            closed: 2,
            total: 1
        }
    ));

    let mut evidence = complete_input();
    evidence.evidence = CoverageCount::new(4, 3);
    assert!(matches!(
        issue_verdict(evidence).unwrap_err(),
        VerdictError::InvalidCoverage {
            field: "evidence",
            closed: 4,
            total: 3
        }
    ));
}

#[test]
fn blank_risk_description_is_rejected() {
    let mut input = complete_input();
    input.residual_risks = vec![ResidualRisk::critical("   ")];

    assert!(matches!(
        issue_verdict(input).unwrap_err(),
        VerdictError::EmptyRiskDescription { index: 0 }
    ));
}

#[test]
fn risks_are_deduplicated_and_sorted_deterministically() {
    let mut input = complete_input();
    input.declared_outcome = DeclaredOutcome::Blocked;
    input.residual_risks = vec![
        ResidualRisk::critical("zeta"),
        ResidualRisk::advisory("beta"),
        ResidualRisk::critical("alpha"),
        ResidualRisk::advisory("beta"),
    ];

    let verdict = issue_verdict(input).expect("issue risk verdict");
    assert_eq!(
        verdict.residual_risks,
        vec!["advisory:beta", "critical:alpha", "critical:zeta"]
    );
    assert_eq!(
        verdict.extensions["gitspace.verdict"]["critical_risk_count"],
        serde_json::json!(2)
    );
    assert_eq!(
        verdict.extensions["gitspace.verdict"]["advisory_risk_count"],
        serde_json::json!(1)
    );
}

#[test]
fn failed_gate_order_is_fixed_and_integrity_is_explained() {
    let mut input = complete_input();
    input.functional_outcome = FunctionalOutcome::Fail;
    input.evidence = CoverageCount::new(0, 2);
    input.scope_respected = false;
    input.security_policy_passed = false;
    input.replay_passed = false;
    input.independent_verification_passed = false;
    input.cleanup_passed = false;

    let verdict = issue_verdict(input).expect("issue multi-failure verdict");
    assert_eq!(
        verdict.extensions["gitspace.verdict"]["failed_gates"],
        serde_json::json!([
            "functional_outcome",
            "evidence",
            "scope",
            "security_policy",
            "replay",
            "independent_verification",
            "cleanup"
        ])
    );
    assert_eq!(
        verdict.extensions["gitspace.verdict"]["integrity_passed"],
        serde_json::json!(false)
    );
}

#[test]
fn schema_invalid_identifiers_are_rejected() {
    let mut bad_verdict = complete_input();
    bad_verdict.verdict_id = "not-a-verdict-id".to_owned();
    assert!(matches!(
        issue_verdict(bad_verdict).unwrap_err(),
        VerdictError::Schema(_)
    ));

    let mut bad_run = complete_input();
    bad_run.run_id = "not-a-run-id".to_owned();
    assert!(matches!(
        issue_verdict(bad_run).unwrap_err(),
        VerdictError::Schema(_)
    ));
}
