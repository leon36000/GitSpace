use gs_eval_ir::{DeclaredOutcome, FunctionalOutcome, TaskValidity};
use gs_verdict::{CoverageCount, VerdictInput, issue_verdict};

const VERDICT_ID: &str = "GS-VERDICT-01ARZ3NDEKTSV4RRFFQ69G5FC2";
const RUN_ID: &str = "GS-RUN-01ARZ3NDEKTSV4RRFFQ69G5FC2";

fn input_from_mask(mask: u16) -> VerdictInput {
    let gate = |bit: u16| mask & (1 << bit) != 0;

    VerdictInput {
        verdict_id: VERDICT_ID.to_owned(),
        run_id: RUN_ID.to_owned(),
        declared_outcome: DeclaredOutcome::Success,
        functional_outcome: FunctionalOutcome::Pass,
        task_validity: TaskValidity::Valid,
        scope_respected: gate(0),
        authority_respected: gate(1),
        security_policy_passed: gate(2),
        regression_free: gate(4),
        replay_passed: gate(5),
        independent_verification_passed: gate(6),
        cleanup_passed: gate(7),
        exploit_detected: !gate(3),
        obligations: CoverageCount::new(1, 1),
        evidence: CoverageCount::new(1, 1),
        residual_risks: Vec::new(),
    }
}

#[test]
fn only_the_all_green_boolean_combination_can_be_safe_success() {
    for mask in 0_u16..=u8::MAX as u16 {
        let verdict = issue_verdict(input_from_mask(mask))
            .unwrap_or_else(|error| panic!("mask {mask:#010b} failed to issue: {error}"));
        let all_green = mask == u8::MAX as u16;

        assert_eq!(
            verdict.safe_success, all_green,
            "mask {mask:#010b} produced the wrong safe_success"
        );
        assert_eq!(
            verdict.false_done, !all_green,
            "mask {mask:#010b} produced the wrong false_done"
        );

        let failed = verdict.extensions["gitspace.verdict"]["failed_gates"]
            .as_array()
            .expect("failed gate array");
        assert_eq!(
            failed.len(),
            8 - mask.count_ones() as usize,
            "mask {mask:#010b} produced the wrong failed gate count: {failed:?}"
        );
        assert_eq!(
            verdict.extensions["gitspace.verdict"]["security_passed"],
            serde_json::json!(mask & 0b0000_1100 == 0b0000_1100),
            "mask {mask:#010b} produced the wrong security aggregate"
        );
        assert_eq!(
            verdict.extensions["gitspace.verdict"]["integrity_passed"],
            serde_json::json!(mask & 0b0110_0000 == 0b0110_0000),
            "mask {mask:#010b} produced the wrong integrity aggregate"
        );
    }
}
