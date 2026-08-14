use crate::{
    FoundryError, NativeScenario, ObservedClassification, RunReceipt, ScoringInput,
    artifacts::{cas_uri, put_json, put_value},
};
use gs_canonical_json::{canonical_digest, sha256_digest};
use gs_cas::{Cas, LocalCas};
use gs_eval_ir::{
    AgentConfiguration, DeclaredOutcome, EvalRunManifest, EvidenceBundle, ExecutionWindow,
    Extensions, FunctionalOutcome, RunArtifacts, RunEnvironment, RunEvent, SchemaName,
    TaskValidity, validate_named_json, validate_task_json,
};
use gs_event_journal::{EventSink, LocalEventJournal, projection_bytes, rebuild_run_projection};
use gs_local_runner::{
    AgentOperation, Capability, Effect, EffectKind, FixtureFile, LocalRunner, OracleCheck,
    OracleFile, RunPlan, RunResult, RunStatus, RunnerError,
};
use gs_verdict::{CoverageCount, VerdictInput, issue_verdict};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    time::Duration,
};

const TASK_ID: &str = "GS-TASK-000009";
const FIXTURE_TIME_0: &str = "2026-08-14T00:00:00Z";
const FIXTURE_TIME_1: &str = "2026-08-14T00:00:01Z";
const FIXTURE_TIME_2: &str = "2026-08-14T00:00:02Z";

pub struct NativeFoundry {
    cas_root: PathBuf,
    journal_root: PathBuf,
    runner_root: PathBuf,
    source_commit: String,
}

struct Observation {
    classification: ObservedClassification,
    effects: Vec<Effect>,
    state_after_uri: String,
    cleanup_passed: bool,
}

struct EventContext<'a> {
    scenario: NativeScenario,
    run_id: &'a str,
    task_uri: &'a str,
    classification: ObservedClassification,
    state_after_uri: &'a str,
    verdict_uri: &'a str,
    safe_success: bool,
    false_done: bool,
}

impl NativeFoundry {
    pub fn open(
        root: impl AsRef<Path>,
        source_commit: impl Into<String>,
    ) -> Result<Self, FoundryError> {
        let source_commit = source_commit.into();
        if !valid_source_commit(&source_commit) {
            return Err(FoundryError::InvalidSourceCommit);
        }
        let requested = root.as_ref();
        fs::create_dir_all(requested)
            .map_err(|source| FoundryError::io("create Foundry root", requested, source))?;
        let metadata = fs::symlink_metadata(requested)
            .map_err(|source| FoundryError::io("inspect Foundry root", requested, source))?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(FoundryError::Inconsistency(
                "Foundry root must be a real directory, not a symlink".to_owned(),
            ));
        }
        let root = fs::canonicalize(requested)
            .map_err(|source| FoundryError::io("canonicalize Foundry root", requested, source))?;
        let cas_root = root.join("cas");
        let journal_root = root.join("journal");
        let runner_root = root.join("runner");
        LocalCas::open(&cas_root)?;
        fs::create_dir_all(&journal_root)
            .map_err(|source| FoundryError::io("create journal root", &journal_root, source))?;
        LocalRunner::open(&runner_root, LocalCas::open(&cas_root)?)?;
        Ok(Self {
            cas_root,
            journal_root,
            runner_root,
            source_commit,
        })
    }

    pub fn cas_root(&self) -> &Path {
        &self.cas_root
    }

    pub(crate) fn source_commit(&self) -> &str {
        &self.source_commit
    }

    pub fn run(&self, scenario: NativeScenario) -> Result<RunReceipt, FoundryError> {
        let cas = LocalCas::open(&self.cas_root)?;
        let identity = scenario.identity_suffix(&self.source_commit);
        let run_id = format!("GS-RUN-{identity}");
        let plan = runner_plan(scenario, &run_id);
        let state_before = state_before_value(&plan.fixture);
        let state_before_digest = canonical_digest(&state_before)?.to_string();

        let task = task_value(&state_before_digest);
        validate_task_json(&task)?;
        let task_uri = put_value(&cas, &task)?;

        let plan_uri = put_value(&cas, &plan_value(scenario, &plan))?;
        let state_before_uri = store_state_before(&cas, &plan.fixture, &state_before)?;

        let observation = self.execute_scenario(scenario, &run_id, &plan, &cas)?;
        let patch_uri = put_value(&cas, &effects_value(&observation.effects))?;
        let scoring = scoring_input(scenario, &observation);
        let scoring_uri = put_json(&cas, &scoring)?;

        // This verdict is intentionally issued before the EvidenceBundle and
        // before replay/independent verification exist. It must therefore not
        // self-award those gates. The later ReplayReport records the replay
        // verification separately while preserving byte-identical rescoring.
        let verdict_id = format!("GS-VERDICT-{identity}");
        let verdict = issue_verdict(to_verdict_input(&scoring, verdict_id, run_id.clone()))?;
        let verdict_value = serde_json::to_value(&verdict)?;
        validate_named_json(SchemaName::EvalVerdict, &verdict_value)?;
        let verdict_uri = put_json(&cas, &verdict)?;

        let journal = LocalEventJournal::open(
            &self.journal_root,
            LocalCas::open(&self.cas_root)?,
            run_id.clone(),
        )?;
        let events = run_events(EventContext {
            scenario,
            run_id: &run_id,
            task_uri: &task_uri,
            classification: observation.classification,
            state_after_uri: &observation.state_after_uri,
            verdict_uri: &verdict_uri,
            safe_success: verdict.safe_success,
            false_done: verdict.false_done,
        })?;
        for event in &events {
            journal.append(event)?;
        }
        let trace = projection_bytes(&rebuild_run_projection(&journal)?)?;
        let trace_uri = cas_uri(cas.put(&trace)?);

        let mut evidence_artifacts = BTreeMap::new();
        for (name, uri) in [
            ("task", &task_uri),
            ("plan", &plan_uri),
            ("scoring", &scoring_uri),
            ("verdict", &verdict_uri),
            ("trace", &trace_uri),
            ("state_before", &state_before_uri),
            ("state_after", &observation.state_after_uri),
            ("patch", &patch_uri),
        ] {
            evidence_artifacts.insert(name.to_owned(), uri.clone());
        }
        let environment_digest = environment_digest();
        let evidence = EvidenceBundle {
            id: format!("GS-EVIDENCE-{identity}"),
            version: 1,
            run_id: run_id.clone(),
            task_id: TASK_ID.to_owned(),
            environment_digest: environment_digest.clone(),
            commit_sha: self.source_commit.clone(),
            artifacts: evidence_artifacts,
            extensions: Extensions::new(),
        };
        let evidence_value = serde_json::to_value(&evidence)?;
        validate_named_json(SchemaName::EvidenceBundle, &evidence_value)?;
        let evidence_uri = put_json(&cas, &evidence)?;

        let manifest = EvalRunManifest {
            id: run_id.clone(),
            version: 1,
            task_id: TASK_ID.to_owned(),
            task_version: 1,
            agent: agent_configuration(),
            environment: RunEnvironment {
                image_digest: sha256_digest(b"gitspace-m0-native-fixture-v1").to_string(),
                architecture: "x86_64".to_owned(),
                dependency_lock_digest: sha256_digest(include_bytes!("../../../Cargo.lock"))
                    .to_string(),
                network_policy_digest: sha256_digest(b"network:none").to_string(),
            },
            execution: ExecutionWindow {
                seed: scenario_seed(scenario),
                started_at: FIXTURE_TIME_0.to_owned(),
                ended_at: FIXTURE_TIME_2.to_owned(),
                interruption_schedule: Vec::new(),
                retries: 0,
            },
            artifacts: RunArtifacts {
                trace: trace_uri.clone(),
                state_before: state_before_uri.clone(),
                state_after: observation.state_after_uri.clone(),
                patch: patch_uri.clone(),
                evidence_bundle: evidence_uri.clone(),
            },
            extensions: Extensions::new(),
        };
        let manifest_value = serde_json::to_value(&manifest)?;
        validate_named_json(SchemaName::EvalRunManifest, &manifest_value)?;
        let manifest_uri = put_json(&cas, &manifest)?;

        Ok(RunReceipt {
            version: 1,
            scenario,
            classification: observation.classification,
            run_id,
            source_commit: self.source_commit.clone(),
            task_uri,
            plan_uri,
            scoring_uri,
            verdict_uri,
            evidence_uri,
            manifest_uri,
            trace_uri,
            state_before_uri,
            state_after_uri: observation.state_after_uri,
            patch_uri,
        })
    }

    fn execute_scenario(
        &self,
        scenario: NativeScenario,
        run_id: &str,
        plan: &RunPlan,
        cas: &LocalCas,
    ) -> Result<Observation, FoundryError> {
        let runner = LocalRunner::open(&self.runner_root, LocalCas::open(&self.cas_root)?)?;
        if scenario == NativeScenario::Infra {
            let digest = sha256_digest(run_id.as_bytes()).to_string();
            let collision = self
                .runner_root
                .join(digest.strip_prefix("sha256:").expect("digest prefix"));
            match fs::create_dir(&collision) {
                Ok(()) => {}
                Err(source) if source.kind() == std::io::ErrorKind::AlreadyExists => {
                    return Err(FoundryError::Inconsistency(
                        "controlled INFRA collision already existed before scenario".to_owned(),
                    ));
                }
                Err(source) => {
                    return Err(FoundryError::io(
                        "create controlled INFRA collision",
                        &collision,
                        source,
                    ));
                }
            }
            let result = runner.execute(plan);
            fs::remove_dir_all(&collision).map_err(|source| {
                FoundryError::io("clean controlled INFRA collision", &collision, source)
            })?;
            match result {
                Err(RunnerError::RunAlreadyExists { .. }) => {
                    let marker = json!({"available": false, "reason": "run_root_collision"});
                    return Ok(Observation {
                        classification: ObservedClassification::Infra,
                        effects: Vec::new(),
                        state_after_uri: put_value(cas, &marker)?,
                        cleanup_passed: true,
                    });
                }
                Err(error) => return Err(error.into()),
                Ok(_) => {
                    return Err(FoundryError::Inconsistency(
                        "INFRA scenario unexpectedly executed successfully".to_owned(),
                    ));
                }
            }
        }

        let result = runner.execute(plan)?;
        if !result.cleaned_up {
            return Err(FoundryError::Inconsistency(
                "runner returned before cleanup was proven".to_owned(),
            ));
        }
        let classification = classify_runner(scenario, &result)?;
        Ok(Observation {
            classification,
            effects: result.effects,
            state_after_uri: cas_uri(result.workspace_snapshot),
            cleanup_passed: result.cleaned_up,
        })
    }
}

fn runner_plan(scenario: NativeScenario, run_id: &str) -> RunPlan {
    let fixture = vec![FixtureFile {
        path: "input/message.txt".to_owned(),
        bytes: b"hello".to_vec(),
    }];
    let oracle = vec![OracleFile {
        path: "truth/expected.txt".to_owned(),
        bytes: b"protected".to_vec(),
    }];
    let capability = Capability {
        readable_prefixes: vec!["input".to_owned(), "output".to_owned()],
        writable_prefixes: vec!["output".to_owned()],
    };
    let (operations, oracle_checks, timeout) = match scenario {
        NativeScenario::Pass => (
            vec![AgentOperation::Write {
                path: "output/result.txt".to_owned(),
                bytes: b"done".to_vec(),
            }],
            vec![
                OracleCheck::WorkspaceFileEquals {
                    path: "output/result.txt".to_owned(),
                    expected: b"done".to_vec(),
                },
                OracleCheck::OracleFileEquals {
                    path: "truth/expected.txt".to_owned(),
                    expected: b"protected".to_vec(),
                },
            ],
            Duration::from_secs(1),
        ),
        NativeScenario::Fail => (
            vec![AgentOperation::Write {
                path: "output/result.txt".to_owned(),
                bytes: b"wrong".to_vec(),
            }],
            vec![OracleCheck::WorkspaceFileEquals {
                path: "output/result.txt".to_owned(),
                expected: b"done".to_vec(),
            }],
            Duration::from_secs(1),
        ),
        NativeScenario::Timeout => (
            vec![
                AgentOperation::Delay { millis: 50 },
                AgentOperation::Write {
                    path: "output/late.txt".to_owned(),
                    bytes: b"late".to_vec(),
                },
            ],
            Vec::new(),
            Duration::from_millis(2),
        ),
        NativeScenario::Policy => (
            vec![AgentOperation::Write {
                path: "forbidden/no.txt".to_owned(),
                bytes: b"blocked".to_vec(),
            }],
            Vec::new(),
            Duration::from_secs(1),
        ),
        NativeScenario::Infra => (
            vec![AgentOperation::Write {
                path: "output/result.txt".to_owned(),
                bytes: b"never-runs".to_vec(),
            }],
            Vec::new(),
            Duration::from_secs(1),
        ),
    };
    RunPlan {
        run_id: run_id.to_owned(),
        fixture,
        oracle,
        capability,
        operations,
        oracle_checks,
        timeout,
    }
}

fn classify_runner(
    scenario: NativeScenario,
    result: &RunResult,
) -> Result<ObservedClassification, FoundryError> {
    let expected = match scenario {
        NativeScenario::Pass => (RunStatus::Completed, true, ObservedClassification::Pass),
        NativeScenario::Fail => (RunStatus::OracleFailed, false, ObservedClassification::Fail),
        NativeScenario::Timeout => (RunStatus::TimedOut, false, ObservedClassification::Timeout),
        NativeScenario::Policy => (
            RunStatus::PolicyBlocked,
            false,
            ObservedClassification::Policy,
        ),
        NativeScenario::Infra => unreachable!("INFRA is handled before runner classification"),
    };
    if result.status != expected.0 || result.oracle_passed != expected.1 {
        return Err(FoundryError::Inconsistency(format!(
            "scenario {} observed runner status {:?}, oracle_passed={} instead of {:?}, {}",
            scenario.slug(),
            result.status,
            result.oracle_passed,
            expected.0,
            expected.1
        )));
    }
    Ok(expected.2)
}

fn scoring_input(scenario: NativeScenario, observation: &Observation) -> ScoringInput {
    let (declared_outcome, functional_outcome, obligations_closed) = match scenario {
        // A functionally correct run is still blocked at verdict-issuance time
        // because the EvidenceBundle, replay and independent verification have
        // not yet been closed. This is the expected false-DONE discipline.
        NativeScenario::Pass => (DeclaredOutcome::Blocked, FunctionalOutcome::Pass, 1),
        NativeScenario::Fail => (DeclaredOutcome::Success, FunctionalOutcome::Fail, 0),
        NativeScenario::Timeout | NativeScenario::Policy => {
            (DeclaredOutcome::Blocked, FunctionalOutcome::Partial, 0)
        }
        NativeScenario::Infra => (DeclaredOutcome::Blocked, FunctionalOutcome::Fail, 0),
    };
    ScoringInput {
        scenario,
        classification: observation.classification,
        declared_outcome,
        functional_outcome,
        task_validity: TaskValidity::Valid,
        scope_respected: true,
        authority_respected: scenario != NativeScenario::Policy,
        security_policy_passed: true,
        regression_free: true,
        replay_passed: false,
        independent_verification_passed: false,
        cleanup_passed: observation.cleanup_passed,
        exploit_detected: false,
        obligations_closed,
        obligations_total: 1,
        evidence_closed: 0,
        evidence_total: 1,
    }
}

pub(crate) fn to_verdict_input(
    scoring: &ScoringInput,
    verdict_id: String,
    run_id: String,
) -> VerdictInput {
    VerdictInput {
        verdict_id,
        run_id,
        declared_outcome: scoring.declared_outcome,
        functional_outcome: scoring.functional_outcome,
        task_validity: scoring.task_validity,
        scope_respected: scoring.scope_respected,
        authority_respected: scoring.authority_respected,
        security_policy_passed: scoring.security_policy_passed,
        regression_free: scoring.regression_free,
        replay_passed: scoring.replay_passed,
        independent_verification_passed: scoring.independent_verification_passed,
        cleanup_passed: scoring.cleanup_passed,
        exploit_detected: scoring.exploit_detected,
        obligations: CoverageCount::new(scoring.obligations_closed, scoring.obligations_total),
        evidence: CoverageCount::new(scoring.evidence_closed, scoring.evidence_total),
        residual_risks: Vec::new(),
    }
}

fn task_value(initial_state_digest: &str) -> Value {
    let environment = environment_digest();
    json!({
        "id": TASK_ID,
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
            "base_artifact_digest":initial_state_digest,
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
    })
}

fn state_before_value(fixture: &[FixtureFile]) -> Value {
    let mut entries = fixture
        .iter()
        .map(|file| {
            json!({
                "path": file.path,
                "digest": sha256_digest(&file.bytes).to_string()
            })
        })
        .collect::<Vec<_>>();
    entries.sort_by(|left, right| left["path"].as_str().cmp(&right["path"].as_str()));
    Value::Array(entries)
}

fn store_state_before(
    cas: &LocalCas,
    fixture: &[FixtureFile],
    state_before: &Value,
) -> Result<String, FoundryError> {
    for file in fixture {
        let digest = cas.put(&file.bytes)?;
        if digest != sha256_digest(&file.bytes) {
            return Err(FoundryError::Inconsistency(
                "CAS returned an unexpected fixture digest".to_owned(),
            ));
        }
    }
    put_value(cas, state_before)
}

fn effects_value(effects: &[Effect]) -> Value {
    Value::Array(
        effects
            .iter()
            .map(|effect| {
                json!({
                    "index": effect.index,
                    "kind": match effect.kind { EffectKind::Read => "read", EffectKind::Write => "write" },
                    "path": effect.path,
                    "digest": effect.digest.to_string()
                })
            })
            .collect(),
    )
}

fn plan_value(scenario: NativeScenario, plan: &RunPlan) -> Value {
    let operations = plan
        .operations
        .iter()
        .map(|operation| match operation {
            AgentOperation::Read { path } => json!({"op":"read","path":path}),
            AgentOperation::Write { path, bytes } => {
                json!({"op":"write","path":path,"bytes":bytes})
            }
            AgentOperation::Delay { millis } => json!({"op":"delay","millis":millis}),
        })
        .collect::<Vec<_>>();
    json!({
        "version":1,
        "scenario":scenario.slug(),
        "run_id":plan.run_id,
        "timeout_ms":plan.timeout.as_millis() as u64,
        "readable_prefixes":plan.capability.readable_prefixes,
        "writable_prefixes":plan.capability.writable_prefixes,
        "operations":operations
    })
}

fn run_events(context: EventContext<'_>) -> Result<[RunEvent; 3], FoundryError> {
    Ok([
        make_event(
            context.run_id,
            0,
            "RUN_PREPARED",
            FIXTURE_TIME_0,
            json!({"scenario":context.scenario.slug(),"task_uri":context.task_uri}),
        )?,
        make_event(
            context.run_id,
            1,
            "RUN_EXECUTED",
            FIXTURE_TIME_1,
            json!({"classification":classification_slug(context.classification),"state_after_uri":context.state_after_uri}),
        )?,
        make_event(
            context.run_id,
            2,
            "VERDICT_ISSUED",
            FIXTURE_TIME_2,
            json!({"verdict_uri":context.verdict_uri,"safe_success":context.safe_success,"false_done":context.false_done}),
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

fn agent_configuration() -> AgentConfiguration {
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

fn environment_digest() -> String {
    sha256_digest(b"gitspace-phase00-native-environment-v1").to_string()
}

fn scenario_seed(scenario: NativeScenario) -> i128 {
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

fn valid_source_commit(value: &str) -> bool {
    matches!(value.len(), 40 | 64)
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}
