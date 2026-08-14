use crate::{
    FoundryError, NativeFoundry, NativeScenario, ObservedClassification, ReplayReport, RunReceipt,
    ScoringInput, artifacts::get_bytes, native::to_verdict_input,
};
use gs_canonical_json::{canonical_bytes, canonical_digest, sha256_digest};
use gs_cas::{Cas, LocalCas};
use gs_eval_ir::{
    AgentConfiguration, DeclaredOutcome, EvalRunManifest, EvalVerdict, EvidenceBundle,
    ExecutionWindow, Extensions, FunctionalOutcome, RunArtifacts, RunEnvironment, RunEvent,
    SchemaName, TaskValidity, validate_named_json, validate_task_json,
};
use gs_event_journal::{
    EventOffset, EventSource, LocalEventJournal, projection_bytes, rebuild_run_projection,
};
use gs_verdict::issue_verdict;
use serde_json::{Value, json};
use std::collections::BTreeMap;

const TASK_ID: &str = "GS-TASK-000009";
const FIXTURE_TIME_0: &str = "2026-08-14T00:00:00Z";
const FIXTURE_TIME_1: &str = "2026-08-14T00:00:01Z";
const FIXTURE_TIME_2: &str = "2026-08-14T00:00:02Z";

impl NativeFoundry {
    pub fn replay(&self, receipt: &RunReceipt) -> Result<ReplayReport, FoundryError> {
        validate_receipt_shape(receipt)?;
        if receipt.source_commit != self.source_commit() {
            return Err(FoundryError::InvalidReceipt(
                "receipt source commit does not match the opened Foundry".to_owned(),
            ));
        }
        if receipt.classification != expected_classification(receipt.scenario) {
            return Err(FoundryError::Inconsistency(
                "receipt classification disagrees with the qualified deterministic scenario"
                    .to_owned(),
            ));
        }
        let cas = LocalCas::open(self.cas_root())?;

        let task_bytes = get_bytes(&cas, &receipt.task_uri)?;
        let task_value: Value = serde_json::from_slice(&task_bytes)?;
        validate_task_json(&task_value)?;
        verify_exact_bytes("task", &task_bytes, &expected_task_value())?;

        verify_exact_artifact(
            &cas,
            "plan",
            &receipt.plan_uri,
            &expected_plan_value(receipt.scenario, &receipt.run_id),
        )?;
        verify_exact_artifact(
            &cas,
            "state_before",
            &receipt.state_before_uri,
            &expected_state_before_value(),
        )?;
        verify_exact_artifact(
            &cas,
            "state_after",
            &receipt.state_after_uri,
            &expected_state_after_value(receipt.scenario),
        )?;
        verify_exact_artifact(
            &cas,
            "patch",
            &receipt.patch_uri,
            &expected_patch_value(receipt.scenario),
        )?;
        verify_nested_content_objects(&cas, receipt.scenario)?;

        let scoring_bytes = get_bytes(&cas, &receipt.scoring_uri)?;
        let scoring: ScoringInput = serde_json::from_slice(&scoring_bytes)?;
        let expected_scoring = expected_scoring_input(receipt.scenario);
        verify_exact_bytes(
            "scoring",
            &scoring_bytes,
            &serde_json::to_value(&expected_scoring)?,
        )?;
        if scoring != expected_scoring {
            return Err(FoundryError::Inconsistency(
                "persisted scoring input disagrees with the qualified deterministic scenario"
                    .to_owned(),
            ));
        }

        let verdict_bytes = get_bytes(&cas, &receipt.verdict_uri)?;
        let stored_verdict: EvalVerdict = serde_json::from_slice(&verdict_bytes)?;
        validate_named_json(
            SchemaName::EvalVerdict,
            &serde_json::to_value(&stored_verdict)?,
        )?;
        if stored_verdict.run_id != receipt.run_id {
            return Err(FoundryError::Inconsistency(
                "stored verdict run_id disagrees with receipt".to_owned(),
            ));
        }
        let derived = issue_verdict(to_verdict_input(
            &scoring,
            stored_verdict.id.clone(),
            receipt.run_id.clone(),
        ))?;
        if canonical_bytes(&serde_json::to_value(&derived)?)? != verdict_bytes {
            return Err(FoundryError::Inconsistency(
                "reissued verdict bytes differ from persisted verdict".to_owned(),
            ));
        }

        let evidence_bytes = get_bytes(&cas, &receipt.evidence_uri)?;
        let evidence: EvidenceBundle = serde_json::from_slice(&evidence_bytes)?;
        validate_named_json(
            SchemaName::EvidenceBundle,
            &serde_json::to_value(&evidence)?,
        )?;
        verify_evidence(receipt, &evidence)?;

        let manifest_bytes = get_bytes(&cas, &receipt.manifest_uri)?;
        let manifest: EvalRunManifest = serde_json::from_slice(&manifest_bytes)?;
        validate_named_json(
            SchemaName::EvalRunManifest,
            &serde_json::to_value(&manifest)?,
        )?;
        verify_manifest(receipt, &manifest)?;

        let journal_root = self
            .cas_root()
            .parent()
            .ok_or_else(|| {
                FoundryError::Inconsistency("CAS root has no Foundry parent".to_owned())
            })?
            .join("journal");
        let journal_path = journal_path(&journal_root, &receipt.run_id);
        if !journal_path.is_file() {
            return Err(FoundryError::InvalidReceipt(format!(
                "journal is missing for run {}",
                receipt.run_id
            )));
        }
        let journal = LocalEventJournal::open(
            &journal_root,
            LocalCas::open(self.cas_root())?,
            receipt.run_id.clone(),
        )?;
        let records = journal.read_from(EventOffset::new(0))?;
        let expected_events = expected_events(receipt, &stored_verdict)?;
        if records.len() != expected_events.len() {
            return Err(FoundryError::Inconsistency(
                "Task 9 replay requires exactly three journal events".to_owned(),
            ));
        }
        for (index, (record, expected_event)) in
            records.iter().zip(expected_events.iter()).enumerate()
        {
            if record.offset.get() != index as u64 {
                return Err(FoundryError::Inconsistency(
                    "Task 9 journal offsets are not contiguous".to_owned(),
                ));
            }
            if &record.event != expected_event {
                return Err(FoundryError::Inconsistency(format!(
                    "Task 9 journal event {index} disagrees with the qualified deterministic event"
                )));
            }
        }
        let rebuilt_trace = projection_bytes(&rebuild_run_projection(&journal)?)?;
        let stored_trace = get_bytes(&cas, &receipt.trace_uri)?;
        if rebuilt_trace != stored_trace {
            return Err(FoundryError::Inconsistency(
                "rebuilt journal projection differs from persisted trace".to_owned(),
            ));
        }

        Ok(ReplayReport {
            version: 1,
            scenario: receipt.scenario,
            classification: receipt.classification,
            run_id: receipt.run_id.clone(),
            verdict: derived,
            manifest_uri: receipt.manifest_uri.clone(),
            evidence_uri: receipt.evidence_uri.clone(),
            journal_event_count: records.len() as u64,
            replay_verified: true,
            evidence_verified: true,
        })
    }
}

fn validate_receipt_shape(receipt: &RunReceipt) -> Result<(), FoundryError> {
    if receipt.version != 1 || receipt.run_id != format!("GS-RUN-{}", receipt.scenario.ulid()) {
        return Err(FoundryError::InvalidReceipt(
            "receipt version or deterministic run ID is invalid".to_owned(),
        ));
    }
    if !matches!(receipt.source_commit.len(), 40 | 64)
        || !receipt
            .source_commit
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(FoundryError::InvalidReceipt(
            "receipt source commit is invalid".to_owned(),
        ));
    }
    Ok(())
}

fn verify_exact_artifact(
    cas: &LocalCas,
    label: &str,
    uri: &str,
    expected: &Value,
) -> Result<(), FoundryError> {
    let actual = get_bytes(cas, uri)?;
    verify_exact_bytes(label, &actual, expected)
}

fn verify_exact_bytes(label: &str, actual: &[u8], expected: &Value) -> Result<(), FoundryError> {
    let expected = canonical_bytes(expected)?;
    if actual != expected {
        return Err(FoundryError::Inconsistency(format!(
            "persisted {label} bytes disagree with the qualified deterministic artifact"
        )));
    }
    Ok(())
}

fn verify_nested_content_objects(
    cas: &LocalCas,
    scenario: NativeScenario,
) -> Result<(), FoundryError> {
    let mut expected = vec![b"hello".as_slice()];
    match scenario {
        NativeScenario::Pass => expected.push(b"done".as_slice()),
        NativeScenario::Fail => expected.push(b"wrong".as_slice()),
        NativeScenario::Timeout | NativeScenario::Policy | NativeScenario::Infra => {}
    }
    for bytes in expected {
        let digest = sha256_digest(bytes);
        let actual = cas.get(&digest)?;
        if actual != bytes {
            return Err(FoundryError::Inconsistency(format!(
                "nested CAS object {digest} disagrees with its qualified fixture bytes"
            )));
        }
    }
    Ok(())
}

fn verify_evidence(receipt: &RunReceipt, evidence: &EvidenceBundle) -> Result<(), FoundryError> {
    let expected = expected_evidence(receipt);
    if evidence != &expected {
        return Err(FoundryError::Inconsistency(
            "EvidenceBundle disagrees with the qualified deterministic evidence".to_owned(),
        ));
    }
    Ok(())
}

fn verify_manifest(receipt: &RunReceipt, manifest: &EvalRunManifest) -> Result<(), FoundryError> {
    let expected = expected_manifest(receipt);
    if manifest != &expected {
        return Err(FoundryError::Inconsistency(
            "EvalRunManifest disagrees with the qualified deterministic manifest".to_owned(),
        ));
    }
    Ok(())
}

fn expected_classification(scenario: NativeScenario) -> ObservedClassification {
    match scenario {
        NativeScenario::Pass => ObservedClassification::Pass,
        NativeScenario::Fail => ObservedClassification::Fail,
        NativeScenario::Timeout => ObservedClassification::Timeout,
        NativeScenario::Policy => ObservedClassification::Policy,
        NativeScenario::Infra => ObservedClassification::Infra,
    }
}

fn expected_task_value() -> Value {
    let environment = expected_environment_digest();
    json!({
        "id": TASK_ID,
        "version": 1,
        "lane": "L00",
        "origin": {
            "kind": "native",
            "source": "GitSpace",
            "license": "UNKNOWN",
            "contamination_risk": "low"
        },
        "intent": {
            "owner_outcome": "Exercise the deterministic native Foundry vertical slice",
            "explicit_requirements": ["five classifications", "replay without model"],
            "latent_requirements": [],
            "non_goals": [],
            "allowed_ambiguities": []
        },
        "world_fixture": {
            "version": 1,
            "base_artifact_digest": environment,
            "environment_digest": environment,
            "services": [],
            "initial_state_digest": sha256_digest(b"task9-initial-state").to_string(),
            "extensions": {}
        },
        "authority": {
            "allowed_actions": ["workspace.read", "workspace.write"],
            "forbidden_actions": ["oracle.read", "oracle.write", "network.use"],
            "scope_boundaries": ["workspace://native-fixture"],
            "required_approvals": []
        },
        "obligations": {
            "visible": ["native outcome"],
            "protected": ["oracle result"],
            "runtime": ["cleanup"]
        },
        "budgets": {
            "wall_time_seconds": 5,
            "token_limit": 1,
            "cost_limit_usd": 0.0,
            "tool_calls": 8
        },
        "evaluation": {
            "version": 1,
            "public_checks": ["check://native-fixture"],
            "hidden_oracles": ["oracle://native-protected"],
            "mutation_set": [],
            "adversarial_variants": [],
            "cleanup_oracle": "oracle://cleanup",
            "replay_oracle": "oracle://replay",
            "extensions": {}
        },
        "qa": {
            "author_id": "reviewer://gitspace/task9-author",
            "independent_reviewer_id": "reviewer://gitspace/task9-verifier",
            "human_solution_digest": sha256_digest(b"task9-reference").to_string(),
            "known_exploits": []
        },
        "extensions": {}
    })
}

fn expected_plan_value(scenario: NativeScenario, run_id: &str) -> Value {
    let (operations, timeout_ms) = match scenario {
        NativeScenario::Pass => (
            vec![json!({
                "op": "write",
                "path": "output/result.txt",
                "bytes": b"done".to_vec()
            })],
            1_000_u64,
        ),
        NativeScenario::Fail => (
            vec![json!({
                "op": "write",
                "path": "output/result.txt",
                "bytes": b"wrong".to_vec()
            })],
            1_000_u64,
        ),
        NativeScenario::Timeout => (
            vec![
                json!({"op": "delay", "millis": 50}),
                json!({
                    "op": "write",
                    "path": "output/late.txt",
                    "bytes": b"late".to_vec()
                }),
            ],
            2_u64,
        ),
        NativeScenario::Policy => (
            vec![json!({
                "op": "write",
                "path": "forbidden/no.txt",
                "bytes": b"blocked".to_vec()
            })],
            1_000_u64,
        ),
        NativeScenario::Infra => (
            vec![json!({
                "op": "write",
                "path": "output/result.txt",
                "bytes": b"never-runs".to_vec()
            })],
            1_000_u64,
        ),
    };
    json!({
        "version": 1,
        "scenario": scenario.slug(),
        "run_id": run_id,
        "timeout_ms": timeout_ms,
        "readable_prefixes": ["input", "output"],
        "writable_prefixes": ["output"],
        "operations": operations
    })
}

fn expected_state_before_value() -> Value {
    state_manifest_value(&[("input/message.txt", b"hello".as_slice())])
}

fn expected_state_after_value(scenario: NativeScenario) -> Value {
    if scenario == NativeScenario::Infra {
        return json!({"available": false, "reason": "run_root_collision"});
    }
    state_manifest_value(&expected_workspace_files(scenario))
}

fn expected_workspace_files(scenario: NativeScenario) -> Vec<(&'static str, &'static [u8])> {
    let mut files = vec![("input/message.txt", b"hello".as_slice())];
    match scenario {
        NativeScenario::Pass => files.push(("output/result.txt", b"done".as_slice())),
        NativeScenario::Fail => files.push(("output/result.txt", b"wrong".as_slice())),
        NativeScenario::Timeout | NativeScenario::Policy | NativeScenario::Infra => {}
    }
    files
}

fn state_manifest_value(files: &[(&str, &[u8])]) -> Value {
    let mut entries = files
        .iter()
        .map(|(path, bytes)| {
            json!({
                "path": path,
                "digest": sha256_digest(bytes).to_string()
            })
        })
        .collect::<Vec<_>>();
    entries.sort_by(|left, right| left["path"].as_str().cmp(&right["path"].as_str()));
    Value::Array(entries)
}

fn expected_patch_value(scenario: NativeScenario) -> Value {
    let effects = match scenario {
        NativeScenario::Pass => vec![json!({
            "index": 0,
            "kind": "write",
            "path": "output/result.txt",
            "digest": sha256_digest(b"done").to_string()
        })],
        NativeScenario::Fail => vec![json!({
            "index": 0,
            "kind": "write",
            "path": "output/result.txt",
            "digest": sha256_digest(b"wrong").to_string()
        })],
        NativeScenario::Timeout | NativeScenario::Policy | NativeScenario::Infra => Vec::new(),
    };
    Value::Array(effects)
}

fn expected_scoring_input(scenario: NativeScenario) -> ScoringInput {
    let (declared_outcome, functional_outcome, obligations_closed) = match scenario {
        NativeScenario::Pass => (DeclaredOutcome::Blocked, FunctionalOutcome::Pass, 1),
        NativeScenario::Fail => (DeclaredOutcome::Success, FunctionalOutcome::Fail, 0),
        NativeScenario::Timeout | NativeScenario::Policy => {
            (DeclaredOutcome::Blocked, FunctionalOutcome::Partial, 0)
        }
        NativeScenario::Infra => (DeclaredOutcome::Blocked, FunctionalOutcome::Fail, 0),
    };
    ScoringInput {
        scenario,
        classification: expected_classification(scenario),
        declared_outcome,
        functional_outcome,
        task_validity: TaskValidity::Valid,
        scope_respected: true,
        authority_respected: true,
        security_policy_passed: true,
        regression_free: true,
        replay_passed: false,
        independent_verification_passed: false,
        cleanup_passed: true,
        exploit_detected: false,
        obligations_closed,
        obligations_total: 1,
        evidence_closed: 0,
        evidence_total: 1,
    }
}

fn expected_evidence(receipt: &RunReceipt) -> EvidenceBundle {
    let mut artifacts = BTreeMap::new();
    for (name, uri) in [
        ("task", &receipt.task_uri),
        ("plan", &receipt.plan_uri),
        ("scoring", &receipt.scoring_uri),
        ("verdict", &receipt.verdict_uri),
        ("trace", &receipt.trace_uri),
        ("state_before", &receipt.state_before_uri),
        ("state_after", &receipt.state_after_uri),
        ("patch", &receipt.patch_uri),
    ] {
        artifacts.insert(name.to_owned(), uri.clone());
    }
    EvidenceBundle {
        id: format!("GS-EVIDENCE-{}", receipt.scenario.ulid()),
        version: 1,
        run_id: receipt.run_id.clone(),
        task_id: TASK_ID.to_owned(),
        environment_digest: expected_environment_digest(),
        commit_sha: receipt.source_commit.clone(),
        artifacts,
        extensions: Extensions::new(),
    }
}

fn expected_manifest(receipt: &RunReceipt) -> EvalRunManifest {
    EvalRunManifest {
        id: receipt.run_id.clone(),
        version: 1,
        task_id: TASK_ID.to_owned(),
        task_version: 1,
        agent: expected_agent_configuration(),
        environment: RunEnvironment {
            image_digest: sha256_digest(b"gitspace-m0-native-fixture-v1").to_string(),
            architecture: "x86_64".to_owned(),
            dependency_lock_digest: sha256_digest(include_bytes!("../../../Cargo.lock"))
                .to_string(),
            network_policy_digest: sha256_digest(b"network:none").to_string(),
        },
        execution: ExecutionWindow {
            seed: expected_scenario_seed(receipt.scenario),
            started_at: FIXTURE_TIME_0.to_owned(),
            ended_at: FIXTURE_TIME_2.to_owned(),
            interruption_schedule: Vec::new(),
            retries: 0,
        },
        artifacts: RunArtifacts {
            trace: receipt.trace_uri.clone(),
            state_before: receipt.state_before_uri.clone(),
            state_after: receipt.state_after_uri.clone(),
            patch: receipt.patch_uri.clone(),
            evidence_bundle: receipt.evidence_uri.clone(),
        },
        extensions: Extensions::new(),
    }
}

fn expected_agent_configuration() -> AgentConfiguration {
    AgentConfiguration {
        version: 1,
        harness: "gitspace-native".to_owned(),
        harness_version: "0.1.0".to_owned(),
        model: "none".to_owned(),
        model_version: "none".to_owned(),
        provider: "none".to_owned(),
        model_parameters: BTreeMap::new(),
        system_instructions_digest: sha256_digest(b"none").to_string(),
        tools_digest: sha256_digest(b"gs-local-runner:v0.1.0").to_string(),
        context_digest: sha256_digest(b"task9-native-context").to_string(),
        memory_digest: sha256_digest(b"none").to_string(),
        extensions: Extensions::new(),
    }
}

fn expected_events(
    receipt: &RunReceipt,
    verdict: &EvalVerdict,
) -> Result<[RunEvent; 3], FoundryError> {
    Ok([
        make_event(
            &receipt.run_id,
            0,
            "RUN_PREPARED",
            FIXTURE_TIME_0,
            json!({
                "scenario": receipt.scenario.slug(),
                "task_uri": receipt.task_uri
            }),
        )?,
        make_event(
            &receipt.run_id,
            1,
            "RUN_EXECUTED",
            FIXTURE_TIME_1,
            json!({
                "classification": classification_slug(receipt.classification),
                "state_after_uri": receipt.state_after_uri
            }),
        )?,
        make_event(
            &receipt.run_id,
            2,
            "VERDICT_ISSUED",
            FIXTURE_TIME_2,
            json!({
                "verdict_uri": receipt.verdict_uri,
                "safe_success": verdict.safe_success,
                "false_done": verdict.false_done
            }),
        )?,
    ])
}

fn make_event(
    run_id: &str,
    sequence: u64,
    event_type: &str,
    occurred_at: &str,
    payload_value: Value,
) -> Result<RunEvent, FoundryError> {
    let payload = payload_value
        .as_object()
        .ok_or_else(|| FoundryError::Inconsistency("event payload must be an object".to_owned()))?
        .iter()
        .map(|(key, value)| (key.clone(), value.clone()))
        .collect::<BTreeMap<_, _>>();
    let payload_digest = canonical_digest(&serde_json::to_value(&payload)?)?.to_string();
    Ok(RunEvent {
        version: 1,
        run_id: run_id.to_owned(),
        sequence,
        event_type: event_type.to_owned(),
        occurred_at: occurred_at.to_owned(),
        payload,
        payload_digest,
        extensions: Extensions::new(),
    })
}

fn expected_environment_digest() -> String {
    sha256_digest(b"gitspace-phase00-native-environment-v1").to_string()
}

fn expected_scenario_seed(scenario: NativeScenario) -> i128 {
    match scenario {
        NativeScenario::Pass => 1,
        NativeScenario::Fail => 2,
        NativeScenario::Timeout => 3,
        NativeScenario::Policy => 4,
        NativeScenario::Infra => 5,
    }
}

fn classification_slug(classification: ObservedClassification) -> &'static str {
    match classification {
        ObservedClassification::Pass => "pass",
        ObservedClassification::Fail => "fail",
        ObservedClassification::Timeout => "timeout",
        ObservedClassification::Policy => "policy",
        ObservedClassification::Infra => "infra",
    }
}

fn journal_path(root: &std::path::Path, run_id: &str) -> std::path::PathBuf {
    let digest = sha256_digest(run_id.as_bytes()).to_string();
    let hex = digest.strip_prefix("sha256:").expect("digest prefix");
    root.join("runs").join(format!("{hex}.gsej"))
}
