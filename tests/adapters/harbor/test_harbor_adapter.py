from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from gs_eval_adapters import AdapterRequest, AdapterStatus, execute_adapter
from gs_eval_adapters.errors import AdapterContractError
from gs_eval_adapters.harbor_adapter import (
    HarborAdapter,
    HarborExecutionCapture,
    HarborExecutionRequest,
    HarborProcessResult,
    HarborSdkExecutor,
)
from gs_eval_adapters.harbor_replay import (
    HARBOR_ENVIRONMENT_IMPORT_PATH,
    TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
    TERMINAL_BENCH_SOURCE_TASK_SHA256,
)

SOURCE_MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "terminal-bench-2.1-regex-log"
    / "source-manifest.json"
)
FIXTURE_ROOT = SOURCE_MANIFEST_PATH.parent


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _fixture_inventory_bytes(task_path: str = "/fixture") -> bytes:
    relative_paths = (
        "source-manifest.json",
        "task.toml",
        "instruction.md",
        "solution/solve.sh",
        "tests/test_outputs.py",
        "tests/run_test.py",
        "tests/test.sh",
        "environment/Dockerfile",
    )
    files = {}
    for relative in relative_paths:
        content = (FIXTURE_ROOT / relative).read_bytes()
        files[relative] = {
            "sha256": _digest(content),
            "bytes": len(content),
            "mode": "0644",
        }
    return _json_bytes(
        {
            "schema": "gitspace.harbor.fixture-inventory.v1",
            "task_path": task_path,
            "files": files,
        }
    )


def task12_request() -> AdapterRequest:
    task = {
        "id": "GS-TASK-000012",
        "version": 1,
        "lane": "L01",
        "origin": {
            "kind": "imported",
            "source": "terminal-bench-2.1@7131e437",
            "license": "UNKNOWN",
            "contamination_risk": "low",
        },
        "intent": {
            "owner_outcome": "Create the regex-log solution file.",
            "explicit_requirements": ["use the normalized regex-log fixture"],
            "latent_requirements": [],
            "non_goals": ["network access", "external model"],
            "allowed_ambiguities": [],
        },
        "world_fixture": {
            "version": 1,
            "base_artifact_digest": "sha256:" + "a" * 64,
            "environment_digest": "sha256:" + "b" * 64,
            "services": [],
            "initial_state_digest": "sha256:" + "a" * 64,
            "extensions": {},
        },
        "authority": {
            "allowed_actions": ["adapter.invoke", "artifact.publish"],
            "forbidden_actions": ["network.use", "external_model.invoke"],
            "scope_boundaries": ["adapter://harbor/controlled"],
            "required_approvals": [],
        },
        "obligations": {
            "visible": ["oracle reward is one"],
            "protected": ["replay agrees"],
            "runtime": ["no network", "cleanup"],
        },
        "budgets": {
            "wall_time_seconds": 60,
            "token_limit": 0,
            "cost_limit_usd": 0.0,
            "tool_calls": 4,
        },
        "evaluation": {
            "version": 1,
            "public_checks": ["check://harbor/regex-log"],
            "hidden_oracles": ["oracle://harbor/replay"],
            "mutation_set": ["mutation://harbor/reward"],
            "adversarial_variants": ["variant://harbor/no-network"],
            "cleanup_oracle": "oracle://harbor/cleanup",
            "replay_oracle": "oracle://harbor/replay",
            "extensions": {},
        },
        "qa": {
            "author_id": "reviewer://task12/author",
            "independent_reviewer_id": "reviewer://task12/verifier",
            "human_solution_digest": "sha256:" + "a" * 64,
            "known_exploits": [],
        },
        "extensions": {},
    }
    agent = {
        "version": 1,
        "harness": "harbor",
        "harness_version": "0.21.0",
        "model": "none",
        "model_version": "none",
        "provider": "none",
        "model_parameters": {},
        "system_instructions_digest": "sha256:" + "a" * 64,
        "tools_digest": "sha256:" + "b" * 64,
        "context_digest": "sha256:" + "a" * 64,
        "memory_digest": "sha256:" + "b" * 64,
        "extensions": {},
    }
    profile = {
        "run_purpose": "qualification_oracle",
        "source_task_sha256": TERMINAL_BENCH_SOURCE_TASK_SHA256,
        "normalized_task_sha256": TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
        "environment_image_ref": "registry.invalid/gitspace/regex-log@sha256:"
        + "e" * 64,
        "environment_image_id": "sha256:" + "e" * 64,
        "egress_sidecar_image_ref": "registry.invalid/gitspace/harbor-egress@sha256:"
        + "f" * 64,
        "egress_sidecar_image_id": "sha256:" + "f" * 64,
    }
    return AdapterRequest(
        task=task,
        agent=agent,
        seed=12,
        extensions={"gitspace.harbor": profile},
    )


def _capture(
    *,
    process_return_code: int = 0,
    reward_json: bytes | None = b'{"reward":1}',
    oracle_exit: bytes | None = None,
    exception_info: dict[str, object] | None = None,
    exception_discriminant: str | None = None,
    stage_obligations: dict[str, bool] | None = None,
) -> HarborExecutionCapture:
    environment_image_ref = "registry.invalid/gitspace/regex-log@sha256:" + "e" * 64
    environment_image_id = "sha256:" + "e" * 64
    sidecar_image_ref = "registry.invalid/gitspace/harbor-egress@sha256:" + "f" * 64
    sidecar_image_id = "sha256:" + "f" * 64
    effective_stage = stage_obligations or {
        "environment_started": True,
        "agent_setup_completed": True,
        "agent_execution_started": True,
        "agent_execution_completed": True,
        "verifier_started": True,
        "verifier_completed": True,
    }
    job_result = {
        "id": "job-1",
        "n_total_trials": 1,
        "trial_results": [{"id": "trial-1"}],
    }
    trial_result = {
        "id": "trial-1",
        "task_name": "terminal-bench/regex-log",
        "trial_name": "regex-log__trial-1",
        "exception_info": exception_info,
        "exception_stage": "agent_execution" if exception_info else None,
        "environment_setup": {
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:00Z",
        }
        if effective_stage["environment_started"]
        else None,
        "agent_setup": {
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:00Z",
        }
        if effective_stage["agent_setup_completed"]
        else None,
        "agent_execution": {
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:01Z"
            if effective_stage["agent_execution_completed"]
            else None,
        }
        if effective_stage["agent_execution_started"]
        else None,
        "verifier": {
            "started_at": "2026-08-20T00:00:01Z",
            "finished_at": "2026-08-20T00:00:02Z"
            if effective_stage["verifier_completed"]
            else None,
        }
        if effective_stage["verifier_started"]
        else None,
    }
    cleanup = {
        "process_group_absent": True,
        "temp_root_absent": True,
        "containers_absent": True,
        "networks_absent": True,
        "derived_images_absent": True,
        "foreign_resources_untouched": True,
    }
    job_config = {
        "job_name": "gitspace-p00-task-012-oracle",
        "n_attempts": 1,
        "n_concurrent_trials": 1,
        "retry": {"max_retries": 0},
        "environment": {
            "import_path": HARBOR_ENVIRONMENT_IMPORT_PATH,
            "kwargs": {
                "gitspace_environment_image_ref": environment_image_ref,
                "gitspace_environment_image_id": environment_image_id,
                "gitspace_egress_sidecar_image_ref": sidecar_image_ref,
                "gitspace_egress_sidecar_image_id": sidecar_image_id,
            },
        },
        "agents": [{"name": "oracle", "n_concurrent": 1}],
        "datasets": [],
        "tasks": [{"path": "/fixture"}],
    }
    result_kind = (
        "harness_infra"
        if reward_json is None
        else (
            "functional_assertion"
            if reward_json == b'{"reward":0}'
            else "functional_pass"
        )
    )
    result_value = {
        "exception_message_or_null": str(
            exception_info.get("exception_message", "harness")
        )
        if exception_info or reward_json is None
        else None,
        "exception_type_or_null": str(
            exception_info.get("exception_type", "VerifierFailure")
        )
        if exception_info or reward_json is None
        else None,
        "kind": result_kind,
        "schema": "gitspace.verifier.v1",
        "test_source_sha256": TERMINAL_BENCH_SOURCE_TASK_SHA256,
    }
    runtime_identity = {
        "environment_image_ref": environment_image_ref,
        "environment_image_id": environment_image_id,
        "egress_sidecar_image_ref": sidecar_image_ref,
        "egress_sidecar_image_id": sidecar_image_id,
        "environment_platform": "linux/amd64",
        "runtime_network_mode": "no-network",
    }
    before_resources = [
        {
            "kind": "process_group",
            "id": "gitspace-harbor-runner",
            "owner": "gitspace",
            "state_digest": "sha256:" + "1" * 64,
        },
        {
            "kind": "temp_root",
            "id": "gitspace-harbor-run",
            "owner": "gitspace",
            "state_digest": "sha256:" + "2" * 64,
        },
    ]
    after_resources: list[dict[str, str]] = []
    inventory_scope = [
        "process_group",
        "temp_root",
        "container",
        "network",
        "derived_image",
    ]

    def inventory_digest(resources: object) -> str:
        return _digest(_json_bytes(resources))

    before_manifest = {
        "schema": "gitspace.harbor.resource-manifest.v1",
        "phase": "before",
        "identity": None,
        "resources": before_resources,
        "inventory_complete": True,
        "inventory_scope": inventory_scope,
        "collector": "gitspace.harbor.resource-observer.v1",
        "inventory_digest": inventory_digest(before_resources),
    }
    after_manifest = {
        "schema": "gitspace.harbor.resource-manifest.v1",
        "phase": "after",
        "identity": runtime_identity,
        "resources": after_resources,
        "inventory_complete": True,
        "inventory_scope": inventory_scope,
        "collector": "gitspace.harbor.resource-observer.v1",
        "inventory_digest": inventory_digest(after_resources),
    }
    return HarborExecutionCapture(
        process_return_code=process_return_code,
        harbor_stdout=b"harbor stdout\n",
        harbor_stderr=b"",
        job_config_bytes=_json_bytes(job_config),
        job_result_bytes=_json_bytes(job_result),
        trial_config_bytes=_json_bytes(
            {
                "task": {"path": "/fixture"},
                "trial_name": "regex-log__trial-1",
                "trials_dir": "/fixture/jobs",
                "agent": {"name": "oracle", "n_concurrent": 1},
                "environment": {
                    "import_path": HARBOR_ENVIRONMENT_IMPORT_PATH,
                    "kwargs": {
                        "gitspace_environment_image_ref": environment_image_ref,
                        "gitspace_environment_image_id": environment_image_id,
                        "gitspace_egress_sidecar_image_ref": sidecar_image_ref,
                        "gitspace_egress_sidecar_image_id": sidecar_image_id,
                    },
                },
                "job_id": "job-1",
            }
        ),
        trial_result_bytes=_json_bytes(trial_result),
        agent_stdout=b"oracle stdout\n",
        agent_stderr=b"",
        oracle_exit_code_bytes=oracle_exit,
        verifier_stdout=b"verifier stdout\n",
        verifier_stderr=b"",
        verifier_reward_json_bytes=reward_json,
        verifier_result_json_bytes=_json_bytes(result_value),
        source_manifest_bytes=(FIXTURE_ROOT / "source-manifest.json").read_bytes(),
        task_toml_bytes=(FIXTURE_ROOT / "task.toml").read_bytes(),
        instruction_md_bytes=(FIXTURE_ROOT / "instruction.md").read_bytes(),
        solution_solve_sh_bytes=(FIXTURE_ROOT / "solution" / "solve.sh").read_bytes(),
        test_source_bytes=(FIXTURE_ROOT / "tests" / "test_outputs.py").read_bytes(),
        verifier_script_bytes=(FIXTURE_ROOT / "tests" / "run_test.py").read_bytes(),
        verifier_test_script_bytes=(FIXTURE_ROOT / "tests" / "test.sh").read_bytes(),
        environment_dockerfile_bytes=(
            FIXTURE_ROOT / "environment" / "Dockerfile"
        ).read_bytes(),
        fixture_inventory_bytes=_fixture_inventory_bytes(),
        resource_manifest_before_bytes=_json_bytes(before_manifest),
        resource_manifest_after_bytes=_json_bytes(after_manifest),
        cleanup_report_bytes=_json_bytes(cleanup),
        exception_boundary_bytes=_json_bytes(
            {
                "discriminant": exception_discriminant,
                "stage": "agent_execution" if exception_discriminant else None,
            }
        ),
        exception_discriminant=exception_discriminant,
        stage_obligations=stage_obligations
        or {
            "environment_started": True,
            "agent_setup_completed": True,
            "agent_execution_started": True,
            "agent_execution_completed": True,
            "verifier_started": True,
            "verifier_completed": True,
        },
    )


class FakeHarborExecutor:
    def __init__(self, capture: HarborExecutionCapture | None = None) -> None:
        self.capture = capture or _capture()
        self.requests: list[HarborExecutionRequest] = []

    def run_oracle(self, request: HarborExecutionRequest) -> HarborExecutionCapture:
        self.requests.append(request)
        return self.capture


class FakeResourceObserver:
    def capture_before(self, _request: HarborExecutionRequest) -> dict[str, object]:
        return json.loads(_capture().resource_manifest_before_bytes)

    def capture_after(
        self,
        _request: HarborExecutionRequest,
        _process_result: HarborProcessResult,
    ) -> dict[str, object]:
        return json.loads(_capture().resource_manifest_after_bytes)


class MemoryCas:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def publish(self, content: bytes) -> str:
        uri = "cas://sha256/" + _digest(content).removeprefix("sha256:")
        self.objects[uri] = content
        return uri

    def read(self, uri: str) -> bytes:
        return self.objects[uri]


class HarborAdapterTests(unittest.TestCase):
    def test_fake_oracle_passes_through_sdk_and_publishes_cas_evidence(self) -> None:
        cas = MemoryCas()
        executor = FakeHarborExecutor()
        result = execute_adapter(
            HarborAdapter(cas.publish, executor=executor, read_artifact=cas.read),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.PASS)
        self.assertEqual(len(executor.requests), 1)
        self.assertEqual(executor.requests[0].job_config["n_attempts"], 1)
        self.assertEqual(executor.requests[0].job_config["n_concurrent_trials"], 1)
        self.assertEqual(
            executor.requests[0].job_config["environment"]["import_path"],
            HARBOR_ENVIRONMENT_IMPORT_PATH,
        )
        self.assertEqual(
            executor.requests[0].job_config["environment"]["kwargs"][
                "gitspace_environment_image_ref"
            ],
            task12_request().extensions["gitspace.harbor"]["environment_image_ref"],
        )
        from harbor.models.job.config import JobConfig

        effective = JobConfig.model_validate(
            executor.requests[0].job_config
        ).model_dump(exclude_defaults=True)
        self.assertEqual(
            effective["environment"],
            executor.requests[0].job_config["environment"],
        )
        self.assertIn("harbor_record", result.artifacts)
        self.assertIn("oracle_exit_status", result.artifacts)
        self.assertIn("verifier_result_json", result.artifacts)

    def test_harbor_process_failure_is_infra_before_reward(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(_capture(process_return_code=17)),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_malformed_reward_is_infra(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(_capture(reward_json=b'{"reward":1.0}')),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_exact_agent_timeout_boundary_is_timeout(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(
                    _capture(
                        reward_json=None,
                        exception_info={"exception_type": "AgentTimeoutError"},
                        exception_discriminant="agent_timeout_exact",
                        stage_obligations={
                            "environment_started": True,
                            "agent_setup_completed": True,
                            "agent_execution_started": True,
                            "agent_execution_completed": False,
                            "verifier_started": False,
                            "verifier_completed": False,
                        },
                    )
                ),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.TIMEOUT)

    def test_diagnostic_agent_timeout_without_boundary_is_infra(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(
                    _capture(
                        reward_json=None,
                        exception_info={"exception_type": "AgentTimeoutError"},
                        stage_obligations={
                            "environment_started": True,
                            "agent_setup_completed": True,
                            "agent_execution_started": True,
                            "agent_execution_completed": False,
                            "verifier_started": False,
                            "verifier_completed": False,
                        },
                    )
                ),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_oracle_nonzero_is_infra_and_candidate_invalid(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(_capture(oracle_exit=b"7\n")),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertEqual(
            result.extensions["gitspace.harbor"]["task_invalid_candidate"], True
        )

    def test_missing_cas_reader_is_infra_not_pass(self) -> None:
        result = execute_adapter(
            HarborAdapter(MemoryCas().publish, executor=FakeHarborExecutor()),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_prepared_request_is_not_authorized_to_change_profile(self) -> None:
        adapter = HarborAdapter(MemoryCas().publish, executor=FakeHarborExecutor())
        prepared = adapter.prepare(
            {
                "version": 1,
                "task": deepcopy(task12_request().task),
                "agent": deepcopy(task12_request().agent),
                "seed": 12,
                "extensions": deepcopy(task12_request().extensions),
            }
        )
        prepared["framework_request"]["environment_platform"] = "windows"

        with self.assertRaises(AdapterContractError):
            adapter.invoke(prepared)

    def test_profile_requires_digest_bound_image_references(self) -> None:
        adapter = HarborAdapter(MemoryCas().publish, executor=FakeHarborExecutor())

        for reference in (
            "registry.invalid/gitspace/regex-log:latest",
            "registry.invalid/gitspace/regex-log@sha256:" + "0" * 64,
        ):
            with self.subTest(reference=reference):
                request = task12_request()
                request.extensions["gitspace.harbor"]["environment_image_ref"] = (
                    reference
                )
                with self.assertRaises(AdapterContractError):
                    adapter.prepare(
                        {
                            "version": 1,
                            "task": deepcopy(request.task),
                            "agent": deepcopy(request.agent),
                            "seed": request.seed,
                            "extensions": deepcopy(request.extensions),
                        }
                    )

    def test_prepared_job_config_cannot_expand_attempts_or_retries(self) -> None:
        adapter = HarborAdapter(MemoryCas().publish, executor=FakeHarborExecutor())
        request = task12_request()
        prepared = adapter.prepare(
            {
                "version": 1,
                "task": deepcopy(request.task),
                "agent": deepcopy(request.agent),
                "seed": request.seed,
                "extensions": deepcopy(request.extensions),
            }
        )
        job_config = prepared["framework_request"]["job_config"]
        job_config["n_attempts"] = 2

        with self.assertRaises(AdapterContractError):
            adapter.invoke(prepared)

    def test_prepared_job_config_rejects_boolean_cardinality(self) -> None:
        adapter = HarborAdapter(MemoryCas().publish, executor=FakeHarborExecutor())
        request = task12_request()
        prepared = adapter.prepare(
            {
                "version": 1,
                "task": deepcopy(request.task),
                "agent": deepcopy(request.agent),
                "seed": request.seed,
                "extensions": deepcopy(request.extensions),
            }
        )
        prepared["framework_request"]["job_config"]["agents"][0]["n_concurrent"] = True

        with self.assertRaises(AdapterContractError):
            adapter.invoke(prepared)

    def test_harbor_job_result_must_report_one_total_trial(self) -> None:
        capture = _capture()
        job_result = json.loads(capture.job_result_bytes)
        job_result["n_total_trials"] = 2
        capture = replace(capture, job_result_bytes=_json_bytes(job_result))
        cas = MemoryCas()

        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(capture),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_sdk_trial_config_without_a_top_level_id_is_still_bound_to_result(
        self,
    ) -> None:
        capture = _capture()
        trial_config = json.loads(capture.trial_config_bytes)
        self.assertNotIn("id", trial_config)
        trial_config["trial_name"] = "regex-log__trial-1"
        capture = replace(capture, trial_config_bytes=_json_bytes(trial_config))
        cas = MemoryCas()

        result = execute_adapter(
            HarborAdapter(
                cas.publish,
                executor=FakeHarborExecutor(capture),
                read_artifact=cas.read,
            ),
            task12_request(),
        )

        self.assertIs(result.status, AdapterStatus.PASS)


class HarborSdkExecutorTests(unittest.TestCase):
    @staticmethod
    def _job_config() -> dict[str, object]:
        return {
            "job_name": "gitspace-p00-task-012-oracle",
            "n_attempts": 1,
            "n_concurrent_trials": 1,
            "retry": {"max_retries": 0},
            "environment": {
                "import_path": HARBOR_ENVIRONMENT_IMPORT_PATH,
                "kwargs": {
                    "gitspace_environment_image_ref": (
                        "registry.invalid/gitspace/regex-log@sha256:" + "e" * 64
                    ),
                    "gitspace_environment_image_id": "sha256:" + "e" * 64,
                    "gitspace_egress_sidecar_image_ref": (
                        "registry.invalid/gitspace/harbor-egress@sha256:" + "f" * 64
                    ),
                    "gitspace_egress_sidecar_image_id": "sha256:" + "f" * 64,
                },
            },
            "agents": [{"name": "oracle", "n_concurrent": 1}],
            "datasets": [],
            "tasks": [{"path": "/fixture"}],
        }

    def test_pinned_harbor_trial_config_serialization_is_the_closed_effective_shape(
        self,
    ) -> None:
        from harbor.models.job.config import JobConfig
        from harbor.models.trial.config import TrialConfig

        job = JobConfig.model_validate(self._job_config())
        trial = TrialConfig(
            task=job.tasks[0],
            trials_dir=Path("/qualified-worker/jobs"),
            agent=job.agents[0],
            environment=job.environment,
            verifier=job.verifier,
            artifacts=job.artifacts,
            extra_instruction_paths=job.extra_instruction_paths,
            job_id=uuid4(),
        )

        effective = trial.model_dump(mode="json", exclude_defaults=True)

        self.assertEqual(
            set(effective),
            {"task", "trial_name", "trials_dir", "agent", "environment", "job_id"},
        )
        self.assertEqual(set(effective["task"]), {"path"})
        self.assertEqual(set(effective["agent"]), {"name", "n_concurrent"})
        self.assertEqual(
            set(effective["environment"]),
            {"import_path", "kwargs"},
        )
        self.assertIsInstance(effective["job_id"], str)
        self.assertTrue(effective["trial_name"])

    def test_sdk_executor_projects_one_trial_from_harbor_job_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = FIXTURE_ROOT

            def runner(config: dict[str, object]) -> None:
                job_dir = Path(str(config["jobs_dir"])) / str(config["job_name"])
                trial_dir = job_dir / "trial-1"
                (trial_dir / "agent").mkdir(parents=True)
                (trial_dir / "verifier").mkdir(parents=True)
                trial_uri = trial_dir.resolve().as_uri()
                job_result = {
                    "id": "job-1",
                    "n_total_trials": 1,
                    "trial_results": [{"id": "trial-1", "trial_uri": trial_uri}],
                }
                trial_result = {
                    "id": "trial-1",
                    "task_name": "terminal-bench/regex-log",
                    "exception_info": None,
                    "agent_execution": {"started_at": "a", "finished_at": "b"},
                    "verifier": {"started_at": "b", "finished_at": "c"},
                }
                trial_config = {
                    "id": "trial-1",
                    "task_name": "terminal-bench/regex-log",
                }
                job_dir.mkdir(parents=True, exist_ok=True)
                (job_dir / "config.json").write_bytes(_json_bytes(config))
                (job_dir / "result.json").write_bytes(_json_bytes(job_result))
                (trial_dir / "config.json").write_bytes(_json_bytes(trial_config))
                (trial_dir / "result.json").write_bytes(_json_bytes(trial_result))
                (trial_dir / "agent" / "oracle.txt").write_bytes(b"oracle\n")
                (trial_dir / "verifier" / "test-stdout.txt").write_bytes(b"ok\n")
                (trial_dir / "verifier" / "test-stderr.txt").write_bytes(b"")
                (trial_dir / "verifier" / "reward.json").write_bytes(b'{"reward":1}')
                (job_dir / "job.log").write_bytes(b"harbor\n")

            request = HarborExecutionRequest(
                run_root=str(root / "run"),
                fixture_root=str(fixture),
                job_config=self._job_config(),
                environment_image_ref="registry.invalid/gitspace/regex-log@sha256:"
                + "e" * 64,
                environment_image_id="sha256:" + "e" * 64,
                egress_sidecar_image_ref="registry.invalid/gitspace/harbor-egress@sha256:"
                + "f" * 64,
                egress_sidecar_image_id="sha256:" + "f" * 64,
            )
            capture = HarborSdkExecutor(
                job_runner=runner,
                resource_observer=FakeResourceObserver(),
            ).run_oracle(request)

            self.assertEqual(capture.process_return_code, 0)
            self.assertEqual(capture.oracle_exit_code_bytes, None)
            self.assertEqual(capture.verifier_reward_json_bytes, b'{"reward":1}')
            self.assertIn(b"terminal-bench/regex-log", capture.trial_result_bytes)

    def test_default_executor_uses_exact_cli_and_minimal_worker_environment(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = FIXTURE_ROOT
            qualified_venv = root / "qualified-venv"
            seen: dict[str, object] = {}

            def runner(
                argv: tuple[str, ...], cwd: str, environment: dict[str, str]
            ) -> HarborProcessResult:
                seen["argv"] = argv
                seen["cwd"] = cwd
                seen["environment"] = environment
                config_path = Path(argv[-1])
                config = json.loads(config_path.read_bytes())
                job_dir = Path(str(config["jobs_dir"])) / str(config["job_name"])
                trial_dir = job_dir / "trial-1"
                (trial_dir / "agent").mkdir(parents=True)
                (trial_dir / "verifier").mkdir(parents=True)
                job_dir.mkdir(parents=True, exist_ok=True)
                (job_dir / "result.json").write_bytes(
                    _json_bytes(
                        {
                            "id": "job-1",
                            "n_total_trials": 1,
                            "trial_results": [
                                {
                                    "id": "trial-1",
                                    "trial_uri": trial_dir.resolve().as_uri(),
                                }
                            ],
                        }
                    )
                )
                (trial_dir / "config.json").write_bytes(_json_bytes({"id": "trial-1"}))
                (trial_dir / "result.json").write_bytes(
                    _json_bytes(
                        {
                            "id": "trial-1",
                            "task_name": "terminal-bench/regex-log",
                            "exception_info": None,
                        }
                    )
                )
                return HarborProcessResult(0, b"harbor stdout", b"")

            request = HarborExecutionRequest(
                run_root=str(root / "run"),
                fixture_root=str(fixture),
                job_config=self._job_config(),
                environment_image_ref="registry.invalid/gitspace/regex-log@sha256:"
                + "e" * 64,
                environment_image_id="sha256:" + "e" * 64,
                egress_sidecar_image_ref="registry.invalid/gitspace/harbor-egress@sha256:"
                + "f" * 64,
                egress_sidecar_image_id="sha256:" + "f" * 64,
            )
            capture = HarborSdkExecutor(
                qualified_venv=str(qualified_venv),
                worker_environment={
                    "DOCKER_HOST": "unix:///run/gitspace-docker.sock",
                    "XDG_RUNTIME_DIR": str(root / "runtime"),
                },
                process_runner=runner,
                resource_observer=FakeResourceObserver(),
            ).run_oracle(request)

            self.assertEqual(capture.process_return_code, 0)
            self.assertEqual(capture.harbor_stdout, b"harbor stdout")
            self.assertEqual(
                seen["argv"],
                (
                    str(qualified_venv / "bin" / "harbor"),
                    "run",
                    "--config",
                    str(root / "run" / "job-config.json"),
                ),
            )
            self.assertEqual(seen["cwd"], str(root / "run"))
            self.assertEqual(
                set(seen["environment"]),
                {
                    "PATH",
                    "PYTHONPATH",
                    "HOME",
                    "TMPDIR",
                    "XDG_CONFIG_HOME",
                    "XDG_CACHE_HOME",
                    "HARBOR_TELEMETRY",
                    "DOCKER_HOST",
                    "XDG_RUNTIME_DIR",
                },
            )
            self.assertEqual(seen["environment"]["HARBOR_TELEMETRY"], "0")
            self.assertEqual(
                seen["environment"]["PYTHONPATH"],
                str(Path(__file__).resolve().parents[3] / "python"),
            )
            self.assertNotIn("SECRET_TOKEN", seen["environment"])

    def test_executor_requires_an_independent_resource_observer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def runner(
                _argv: tuple[str, ...], _cwd: str, _environment: dict[str, str]
            ) -> HarborProcessResult:
                return HarborProcessResult(0, b"", b"")

            with self.assertRaisesRegex(
                AdapterContractError, "resource_observer is required"
            ):
                HarborSdkExecutor(
                    qualified_venv=str(root / "qualified-venv"),
                    process_runner=runner,
                )

    def test_executor_rejects_worker_environment_outside_qualification_allowlist(
        self,
    ) -> None:
        with self.assertRaises(AdapterContractError):
            HarborSdkExecutor(
                qualified_venv="/qualified/venv",
                worker_environment={"SECRET_TOKEN": "must-not-cross"},
                resource_observer=FakeResourceObserver(),
            )

    def test_sdk_executor_turns_worker_exception_into_infra_capture(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture"
            fixture.mkdir()

            def runner(_config: dict[str, object]) -> None:
                raise RuntimeError("qualified worker unavailable")

            request = HarborExecutionRequest(
                run_root=str(root / "run"),
                fixture_root=str(fixture),
                job_config=self._job_config(),
                environment_image_ref="registry.invalid/gitspace/regex-log@sha256:"
                + "e" * 64,
                environment_image_id="sha256:" + "e" * 64,
                egress_sidecar_image_ref="registry.invalid/gitspace/harbor-egress@sha256:"
                + "f" * 64,
                egress_sidecar_image_id="sha256:" + "f" * 64,
            )
            capture = HarborSdkExecutor(
                job_runner=runner,
                resource_observer=FakeResourceObserver(),
            ).run_oracle(request)

            self.assertEqual(capture.process_return_code, 1)
            self.assertIn(b"RuntimeError", capture.harbor_stderr)
            self.assertIn(b"qualified worker unavailable", capture.trial_result_bytes)
            self.assertEqual(capture.resource_manifest_before_bytes, b"")
            self.assertEqual(capture.resource_manifest_after_bytes, b"")


if __name__ == "__main__":
    unittest.main()
