use gs_canonical_json::{canonical_digest, sha256_digest};
use gs_eval_ir::validate_task_json;
use serde_json::json;

#[test]
fn native_task_template_is_valid_in_the_rust_schema_boundary() {
    let environment = sha256_digest(b"gitspace-phase00-native-environment-v1").to_string();
    let state_before = json!([{
        "path": "input/message.txt",
        "digest": sha256_digest(b"hello").to_string()
    }]);
    let initial_state_digest = canonical_digest(&state_before).unwrap().to_string();
    let task = json!({
        "id": "GS-TASK-000009",
        "version": 1,
        "lane": "L00",
        "origin": {"kind":"native","source":"GitSpace","license":"UNKNOWN","contamination_risk":"low"},
        "intent": {
            "owner_outcome":"Exercise the deterministic native Foundry vertical slice",
            "explicit_requirements":["five classifications","replay without model"],
            "latent_requirements":[],"non_goals":[],"allowed_ambiguities":[]
        },
        "world_fixture": {
            "version":1,
            "base_artifact_digest":initial_state_digest.clone(),
            "environment_digest":environment,
            "services":[],
            "initial_state_digest":initial_state_digest,
            "extensions":{}
        },
        "authority": {
            "allowed_actions":["workspace.read","workspace.write"],
            "forbidden_actions":["oracle.read","oracle.write","network.use"],
            "scope_boundaries":["workspace://native-fixture"],"required_approvals":[]
        },
        "obligations": {"visible":["native outcome"],"protected":["oracle result"],"runtime":["cleanup"]},
        "budgets": {"wall_time_seconds":5,"token_limit":1,"cost_limit_usd":0.0,"tool_calls":8},
        "evaluation": {
            "version":1,"public_checks":["check://native-fixture"],"hidden_oracles":["oracle://native-protected"],
            "mutation_set":[],"adversarial_variants":[],"cleanup_oracle":"oracle://cleanup","replay_oracle":"oracle://replay","extensions":{}
        },
        "qa": {
            "author_id":"reviewer://gitspace/task9-author","independent_reviewer_id":"reviewer://gitspace/task9-verifier",
            "human_solution_digest":sha256_digest(b"task9-reference").to_string(),"known_exploits":[]
        },
        "extensions": {}
    });

    if let Err(report) = validate_task_json(&task) {
        panic!(
            "Task 9 native task failed Rust schema validation: {:#?}",
            report.issues()
        );
    }
}
