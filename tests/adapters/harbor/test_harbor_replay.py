from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from gs_eval_adapters.errors import AdapterContractError
from gs_eval_adapters.harbor_replay import (
    HARBOR_ENVIRONMENT_IMPORT_PATH,
    TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
    TERMINAL_BENCH_SOURCE_TASK_SHA256,
    HarborReplayRecord,
    HarborReplayResult,
    build_replay_record,
    canonical_record_bytes,
    classify_harbor_record,
    project_harbor_capture,
)
from gs_eval_adapters.model import AdapterStatus

CAS_DIGEST = "a" * 64
SOURCE_MANIFEST_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "terminal-bench-2.1-regex-log"
    / "source-manifest.json"
)
FIXTURE_ROOT = SOURCE_MANIFEST_PATH.parent


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
            "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
            "mode": "0644",
        }
    return json.dumps(
        {
            "schema": "gitspace.harbor.fixture-inventory.v1",
            "task_path": task_path,
            "files": files,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


def valid_record_json() -> dict[str, object]:
    return {
        "version": 2,
        "run_purpose": "qualification_oracle",
        "framework": "harbor",
        "framework_version": "0.21.0",
        "framework_commit": "64afbbcb62165950301e1a6407c729aa26d844ff",
        "framework_wheel_sha256": "c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21",
        "dataset_repository": "harbor-framework/terminal-bench-2-1",
        "dataset_commit": "7131e4375048a0e408a8fb404b5f499d726b695b",
        "task_name": "terminal-bench/regex-log",
        "source_task_sha256": TERMINAL_BENCH_SOURCE_TASK_SHA256,
        "normalized_task_sha256": TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
        "environment_image_ref": "registry.invalid/gitspace/regex-log@sha256:"
        + "d" * 64,
        "environment_image_id": "sha256:" + "d" * 64,
        "egress_sidecar_image_ref": "registry.invalid/gitspace/harbor-egress@sha256:"
        + "e" * 64,
        "egress_sidecar_image_id": "sha256:" + "e" * 64,
        "environment_platform": "linux/amd64",
        "runtime_network_mode": "no-network",
        "verifier_environment_mode": "shared",
        "verifier_python": "3.13.15",
        "agent": "oracle",
        "oracle_exit_code": None,
        "job_id": "job-1",
        "trial_id": "trial-1",
        "harbor_process_return_code": 0,
        "harbor_status": "completed",
        "observed_reward": 1,
        "exception_discriminant": None,
        "exception_type_diagnostic": None,
        "exception_stage": None,
        "stage_timings": {"agent_execution": 1.0},
        "stage_obligations": {
            "environment_started": True,
            "agent_setup_completed": True,
            "agent_execution_started": True,
            "agent_execution_completed": True,
            "verifier_started": True,
            "verifier_completed": True,
        },
        "artifacts": {"oracle_exit_status": f"cas://sha256/{CAS_DIGEST}"},
        "artifact_sha256": {"oracle_exit_status": f"sha256:{CAS_DIGEST}"},
        "cleanup_obligations": {
            "process_group_absent": True,
            "temp_root_absent": True,
            "containers_absent": True,
            "networks_absent": True,
            "derived_images_absent": True,
            "foreign_resources_untouched": True,
        },
    }


def record_with_content(
    *,
    run_purpose: str = "status_control",
    reward: int | None = 1,
    stage_obligations: dict[str, bool] | None = None,
) -> tuple[HarborReplayRecord, dict[str, bytes]]:
    content = b'{"present":false,"value":null}\n'
    boundary_content = b'{"discriminant":null,"stage":null}'
    value = valid_record_json()
    value["run_purpose"] = run_purpose
    value["agent"] = "fake" if run_purpose == "status_control" else "oracle"
    value["observed_reward"] = reward
    stage_values = stage_obligations or {
        "environment_started": True,
        "agent_setup_completed": True,
        "agent_execution_started": True,
        "agent_execution_completed": True,
        "verifier_started": True,
        "verifier_completed": True,
    }
    stage_timings: dict[str, object] = {}
    if stage_values["environment_started"]:
        stage_timings["environment_setup"] = {
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:00Z",
        }
    if stage_values["agent_setup_completed"]:
        stage_timings["agent_setup"] = {
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:00Z",
        }
    if stage_values["agent_execution_started"]:
        stage_timings["agent_execution"] = {
            "started_at": "2026-08-20T00:00:00Z",
            "finished_at": "2026-08-20T00:00:01Z"
            if stage_values["agent_execution_completed"]
            else None,
        }
    if stage_values["verifier_started"]:
        stage_timings["verifier"] = {
            "started_at": "2026-08-20T00:00:01Z",
            "finished_at": "2026-08-20T00:00:02Z"
            if stage_values["verifier_completed"]
            else None,
        }
    value["stage_obligations"] = stage_values
    value["stage_timings"] = stage_timings

    job_config = {
        "job_name": "gitspace-p00-task-012-oracle",
        "n_attempts": 1,
        "n_concurrent_trials": 1,
        "retry": {"max_retries": 0},
        "environment": {
            "import_path": HARBOR_ENVIRONMENT_IMPORT_PATH,
            "kwargs": {
                "gitspace_environment_image_ref": value["environment_image_ref"],
                "gitspace_environment_image_id": value["environment_image_id"],
                "gitspace_egress_sidecar_image_ref": value["egress_sidecar_image_ref"],
                "gitspace_egress_sidecar_image_id": value["egress_sidecar_image_id"],
            },
        },
        "agents": [{"name": "oracle", "n_concurrent": 1}],
        "datasets": [],
        "tasks": [{"path": "/fixture"}],
    }
    job_result = {
        "id": value["job_id"],
        "n_total_trials": 1,
        "trial_results": [{"id": value["trial_id"]}],
    }
    trial_config = {
        "task": {"path": "/fixture"},
        "trial_name": "regex-log__trial-1",
        "trials_dir": "/fixture/jobs",
        "agent": {"name": "oracle", "n_concurrent": 1},
        "environment": {
            "import_path": HARBOR_ENVIRONMENT_IMPORT_PATH,
            "kwargs": {
                "gitspace_environment_image_ref": value["environment_image_ref"],
                "gitspace_environment_image_id": value["environment_image_id"],
                "gitspace_egress_sidecar_image_ref": value["egress_sidecar_image_ref"],
                "gitspace_egress_sidecar_image_id": value["egress_sidecar_image_id"],
            },
        },
        "job_id": value["job_id"],
    }
    trial_result = {
        "id": value["trial_id"],
        "task_name": value["task_name"],
        "trial_name": "regex-log__trial-1",
        "exception_info": None,
        **stage_timings,
    }
    identity = {
        "environment_image_ref": value["environment_image_ref"],
        "environment_image_id": value["environment_image_id"],
        "egress_sidecar_image_ref": value["egress_sidecar_image_ref"],
        "egress_sidecar_image_id": value["egress_sidecar_image_id"],
        "environment_platform": value["environment_platform"],
        "runtime_network_mode": value["runtime_network_mode"],
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
        encoded = json.dumps(resources, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    manifest_before = {
        "schema": "gitspace.harbor.resource-manifest.v1",
        "phase": "before",
        "identity": None,
        "resources": before_resources,
        "inventory_complete": True,
        "inventory_scope": inventory_scope,
        "collector": "gitspace.harbor.resource-observer.v1",
        "inventory_digest": inventory_digest(before_resources),
    }
    manifest_after = {
        "schema": "gitspace.harbor.resource-manifest.v1",
        "phase": "after",
        "identity": identity,
        "resources": after_resources,
        "inventory_complete": True,
        "inventory_scope": inventory_scope,
        "collector": "gitspace.harbor.resource-observer.v1",
        "inventory_digest": inventory_digest(after_resources),
    }
    cleanup = {
        "process_group_absent": True,
        "temp_root_absent": True,
        "containers_absent": True,
        "networks_absent": True,
        "derived_images_absent": True,
        "foreign_resources_untouched": True,
    }
    if reward is None:
        result_value = {
            "exception_message_or_null": "harness timeout",
            "exception_type_or_null": "AgentTimeoutError",
            "kind": "harness_infra",
            "schema": "gitspace.verifier.v1",
            "test_source_sha256": value["source_task_sha256"],
        }
    else:
        result_value = {
            "exception_message_or_null": "wrong" if reward == 0 else None,
            "exception_type_or_null": "AssertionError" if reward == 0 else None,
            "kind": "functional_pass" if reward == 1 else "functional_assertion",
            "schema": "gitspace.verifier.v1",
            "test_source_sha256": value["source_task_sha256"],
        }
    result_content = (
        json.dumps(result_value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    )
    artifact_bytes: dict[str, bytes] = {
        "job_config": json.dumps(
            job_config, sort_keys=True, separators=(",", ":")
        ).encode(),
        "job_result": json.dumps(
            job_result, sort_keys=True, separators=(",", ":")
        ).encode(),
        "trial_config": json.dumps(
            trial_config, sort_keys=True, separators=(",", ":")
        ).encode(),
        "trial_result": json.dumps(
            trial_result, sort_keys=True, separators=(",", ":")
        ).encode(),
        "oracle_exit_status": content,
        "verifier_reward_json": (
            json.dumps({"reward": reward}, separators=(",", ":")).encode()
            if reward is not None
            else b""
        ),
        "verifier_result_json": result_content,
        "source_manifest": SOURCE_MANIFEST_PATH.read_bytes(),
        "task_toml": (FIXTURE_ROOT / "task.toml").read_bytes(),
        "instruction_md": (FIXTURE_ROOT / "instruction.md").read_bytes(),
        "solution_solve_sh": (FIXTURE_ROOT / "solution" / "solve.sh").read_bytes(),
        "test_source": (FIXTURE_ROOT / "tests" / "test_outputs.py").read_bytes(),
        "verifier_script": (FIXTURE_ROOT / "tests" / "run_test.py").read_bytes(),
        "verifier_test_script": (FIXTURE_ROOT / "tests" / "test.sh").read_bytes(),
        "environment_dockerfile": (
            FIXTURE_ROOT / "environment" / "Dockerfile"
        ).read_bytes(),
        "fixture_inventory": _fixture_inventory_bytes(),
        "exception_boundary": boundary_content,
        "resource_manifest_before": json.dumps(
            manifest_before, sort_keys=True, separators=(",", ":")
        ).encode(),
        "resource_manifest_after": json.dumps(
            manifest_after, sort_keys=True, separators=(",", ":")
        ).encode(),
        "cleanup_report": json.dumps(
            cleanup, sort_keys=True, separators=(",", ":")
        ).encode(),
    }
    artifacts = {
        name: f"cas://sha256/{hashlib.sha256(item).hexdigest()}"
        for name, item in artifact_bytes.items()
    }
    artifact_sha256 = {
        name: f"sha256:{hashlib.sha256(item).hexdigest()}"
        for name, item in artifact_bytes.items()
    }
    value["artifacts"] = artifacts
    value["artifact_sha256"] = artifact_sha256
    record = build_replay_record(
        value,
        artifact_bytes=artifact_bytes,
        artifact_uris=artifacts,
    )
    return record, {uri: artifact_bytes[name] for name, uri in artifacts.items()}


def replace_boundary(
    value: dict[str, object], store: dict[str, bytes], discriminant: str, stage: str
) -> None:
    content = json.dumps(
        {"discriminant": discriminant, "stage": stage},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(content).hexdigest()
    artifacts = value["artifacts"]
    artifact_sha256 = value["artifact_sha256"]
    assert isinstance(artifacts, dict)
    assert isinstance(artifact_sha256, dict)
    old_uri = artifacts["exception_boundary"]
    assert isinstance(old_uri, str)
    store.pop(old_uri, None)
    new_uri = f"cas://sha256/{digest}"
    artifacts["exception_boundary"] = new_uri
    artifact_sha256["exception_boundary"] = f"sha256:{digest}"
    store[new_uri] = content


def replace_artifact(
    value: dict[str, object],
    store: dict[str, bytes],
    name: str,
    content: bytes,
) -> None:
    artifacts = value["artifacts"]
    artifact_sha256 = value["artifact_sha256"]
    assert isinstance(artifacts, dict)
    assert isinstance(artifact_sha256, dict)
    old_uri = artifacts[name]
    assert isinstance(old_uri, str)
    store.pop(old_uri, None)
    digest = hashlib.sha256(content).hexdigest()
    new_uri = f"cas://sha256/{digest}"
    artifacts[name] = new_uri
    artifact_sha256[name] = f"sha256:{digest}"
    store[new_uri] = content


def replace_json_artifact(
    value: dict[str, object],
    store: dict[str, bytes],
    name: str,
    update: dict[str, object],
) -> None:
    artifacts = value["artifacts"]
    assert isinstance(artifacts, dict)
    uri = artifacts[name]
    assert isinstance(uri, str)
    current = json.loads(store[uri])
    assert isinstance(current, dict)
    current.update(update)
    replace_artifact(
        value,
        store,
        name,
        json.dumps(current, sort_keys=True, separators=(",", ":")).encode(),
    )


class HarborReplayRedTests(unittest.TestCase):
    def test_harbor_replay_record_module_is_available(self) -> None:
        self.assertIsNotNone(HarborReplayRecord)

    def test_valid_record_round_trips_as_json_builtins(self) -> None:
        record = HarborReplayRecord.from_json(valid_record_json())

        self.assertEqual(record.to_json(), valid_record_json())

    def test_replay_record_rejects_image_reference_digest_mismatch(self) -> None:
        value = valid_record_json()
        value["environment_image_ref"] = (
            "registry.invalid/gitspace/regex-log@sha256:" + "0" * 64
        )

        with self.assertRaisesRegex(AdapterContractError, "digest"):
            HarborReplayRecord.from_json(value)

    def test_replay_record_rejects_mutable_sidecar_reference(self) -> None:
        value = valid_record_json()
        value["egress_sidecar_image_ref"] = (
            "registry.invalid/gitspace/harbor-egress:latest"
        )

        with self.assertRaisesRegex(AdapterContractError, "digest"):
            HarborReplayRecord.from_json(value)

    def test_record_rejects_boolean_version(self) -> None:
        value = valid_record_json()
        value["version"] = True

        with self.assertRaises(AdapterContractError):
            HarborReplayRecord.from_json(value)

    def test_canonical_record_bytes_are_sorted_compact_json(self) -> None:
        record = HarborReplayRecord.from_json(valid_record_json())

        expected = json.dumps(
            valid_record_json(),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        self.assertEqual(canonical_record_bytes(record), expected)

    def test_build_record_rehashes_and_binds_artifacts(self) -> None:
        content = b'{"present":false,"value":null}\n'
        digest = hashlib.sha256(content).hexdigest()
        value = valid_record_json()
        value["artifacts"] = {"oracle_exit_status": f"cas://sha256/{digest}"}
        value["artifact_sha256"] = {"oracle_exit_status": f"sha256:{digest}"}

        record = build_replay_record(
            value,
            artifact_bytes={"oracle_exit_status": content},
            artifact_uris={"oracle_exit_status": f"cas://sha256/{digest}"},
        )

        self.assertEqual(
            record.artifacts["oracle_exit_status"], f"cas://sha256/{digest}"
        )

    def test_build_record_rejects_digest_mismatch(self) -> None:
        value = valid_record_json()
        content = b"wrong"

        with self.assertRaises(AdapterContractError):
            build_replay_record(
                value,
                artifact_bytes={"oracle_exit_status": content},
                artifact_uris=value["artifacts"],  # type: ignore[arg-type]
            )

    def test_missing_loader_is_infra(self) -> None:
        record, _ = record_with_content()

        result = classify_harbor_record(record, read_artifact=None)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["artifact_integrity"])

    def test_replay_missing_runtime_evidence_is_infra(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        artifacts = value["artifacts"]
        artifact_sha256 = value["artifact_sha256"]
        assert isinstance(artifacts, dict)
        assert isinstance(artifact_sha256, dict)
        for name in (
            "job_config",
            "job_result",
            "trial_config",
            "trial_result",
            "verifier_result_json",
            "resource_manifest_before",
            "resource_manifest_after",
            "cleanup_report",
        ):
            uri = artifacts.pop(name)
            artifact_sha256.pop(name)
            assert isinstance(uri, str)
            store.pop(uri, None)
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["job_cardinality_one"])
        self.assertFalse(result.obligations["network_closed"])
        self.assertFalse(result.obligations["cleanup_complete"])

    def test_structured_verifier_result_must_agree_with_reward(self) -> None:
        record, store = record_with_content(run_purpose="qualification_oracle")
        value = record.to_json()
        result_content = (
            json.dumps(
                {
                    "exception_message_or_null": "wrong",
                    "exception_type_or_null": "AssertionError",
                    "kind": "functional_assertion",
                    "schema": "gitspace.verifier.v1",
                    "test_source_sha256": value["source_task_sha256"],
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            + b"\n"
        )
        replace_artifact(value, store, "verifier_result_json", result_content)
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["reward_well_typed"])

    def test_verifier_source_digest_must_be_locked_not_profile_selected(self) -> None:
        record, store = record_with_content(run_purpose="qualification_oracle")
        value = record.to_json()
        selected_digest = "sha256:" + "a" * 64
        value["source_task_sha256"] = selected_digest
        replace_json_artifact(
            value,
            store,
            "verifier_result_json",
            {"test_source_sha256": selected_digest},
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["qualification_pinned"])

    def test_normalized_task_digest_must_be_locked(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        value["normalized_task_sha256"] = "sha256:" + "a" * 64
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["qualification_pinned"])

    def test_exception_boundary_divergence_is_infra(self) -> None:
        record, store = record_with_content(run_purpose="qualification_oracle")
        value = record.to_json()
        replace_boundary(value, store, "other_exception", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["exception_boundary_consistent"])

    def test_runtime_identity_must_match_observed_manifest(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        after_uri = value["artifacts"]["resource_manifest_after"]
        assert isinstance(after_uri, str)
        after = json.loads(store[after_uri])
        after["identity"]["environment_image_id"] = "sha256:" + "0" * 64
        replace_artifact(
            value,
            store,
            "resource_manifest_after",
            json.dumps(after, sort_keys=True, separators=(",", ":")).encode(),
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["qualification_pinned"])

    def test_cleanup_rejects_a_leftover_owned_resource(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        after_uri = value["artifacts"]["resource_manifest_after"]
        assert isinstance(after_uri, str)
        after = json.loads(store[after_uri])
        assert isinstance(after, dict)
        after["resources"] = [
            {
                "kind": "container",
                "id": "still-running",
                "owner": "gitspace",
                "state_digest": "sha256:" + "a" * 64,
            }
        ]
        replace_artifact(
            value,
            store,
            "resource_manifest_after",
            json.dumps(after, sort_keys=True, separators=(",", ":")).encode(),
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["cleanup_complete"])

    def test_cleanup_rejects_an_empty_incomplete_observer_inventory(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        before_uri = value["artifacts"]["resource_manifest_before"]
        assert isinstance(before_uri, str)
        before = json.loads(store[before_uri])
        before["resources"] = []
        before["inventory_digest"] = "sha256:" + hashlib.sha256(b"[]").hexdigest()
        replace_artifact(
            value,
            store,
            "resource_manifest_before",
            json.dumps(before, sort_keys=True, separators=(",", ":")).encode(),
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["cleanup_complete"])

    def test_sidecar_identity_must_be_present_in_effective_job_config(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        job_uri = value["artifacts"]["job_config"]
        assert isinstance(job_uri, str)
        job = json.loads(store[job_uri])
        job["environment"]["kwargs"]["gitspace_egress_sidecar_image_ref"] = (
            "registry.invalid/wrong@sha256:" + "0" * 64
        )
        job["environment"]["kwargs"]["gitspace_egress_sidecar_image_id"] = (
            "sha256:" + "0" * 64
        )
        replace_json_artifact(
            value,
            store,
            "job_config",
            job,
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["network_closed"])

    def test_effective_job_config_accepts_harbor_excluded_default_fields(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        job_uri = value["artifacts"]["job_config"]
        assert isinstance(job_uri, str)
        job = json.loads(store[job_uri])
        job.pop("n_attempts")
        job.pop("retry")
        job.pop("datasets")
        job["jobs_dir"] = "/qualified-worker/jobs"
        replace_artifact(
            value,
            store,
            "job_config",
            json.dumps(job, sort_keys=True, separators=(",", ":")).encode(),
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.PASS)
        self.assertTrue(result.obligations["job_cardinality_one"])
        self.assertTrue(result.obligations["network_closed"])

    def test_effective_job_config_rejects_runtime_modifiers_and_task_drift(
        self,
    ) -> None:
        mutations = (
            {"install_only": True},
            {"verifier": {"disable": True}},
            {"source_jobs": "regrade"},
            {"extra_instruction_paths": ["/untrusted/instructions"]},
            {"tasks": [{"path": "/fixture", "git_url": "https://invalid"}]},
            {"tasks": [{"path": "/different-task"}]},
            {"environment": {}},
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                record, store = record_with_content()
                value = record.to_json()
                replace_json_artifact(value, store, "job_config", mutation)
                record = HarborReplayRecord.from_json(value)

                result = classify_harbor_record(record, read_artifact=store.__getitem__)

                self.assertIs(result.status, AdapterStatus.INFRA)
                self.assertFalse(
                    result.obligations["job_cardinality_one"]
                    and result.obligations["network_closed"]
                    and result.obligations["qualification_pinned"]
                )

    def test_trial_config_binds_generated_trial_name_and_environment_extension(
        self,
    ) -> None:
        record, store = record_with_content()
        value = record.to_json()
        replace_json_artifact(
            value,
            store,
            "trial_config",
            {
                "trial_name": "trial-1",
                "environment": {},
            },
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["trial_cardinality_one"])

    def test_fixture_inventory_rejects_an_unexpected_runtime_file(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        inventory_uri = value["artifacts"]["fixture_inventory"]
        assert isinstance(inventory_uri, str)
        inventory = json.loads(store[inventory_uri])
        inventory["files"]["environment/docker-compose.yaml"] = {
            "sha256": "sha256:" + "0" * 64,
            "bytes": 1,
            "mode": "0644",
        }
        replace_artifact(
            value,
            store,
            "fixture_inventory",
            json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode(),
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["qualification_pinned"])

    def test_fixture_inventory_task_path_must_match_effective_job(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        replace_json_artifact(
            value,
            store,
            "job_config",
            {"tasks": [{"path": "/different-task"}]},
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["qualification_pinned"])

    def test_exact_policy_boundary_precedes_infra(self) -> None:
        record, store = record_with_content(
            reward=None,
            stage_obligations={
                name: False
                for name in (
                    "environment_started",
                    "agent_setup_completed",
                    "agent_execution_started",
                    "agent_execution_completed",
                    "verifier_started",
                    "verifier_completed",
                )
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "exception_discriminant": "policy_violation_exact",
                "exception_type_diagnostic": "AdapterPolicyViolation",
                "exception_stage": "unknown",
            }
        )
        replace_json_artifact(
            value,
            store,
            "trial_result",
            {
                "exception_info": {
                    "exception_type": "AdapterPolicyViolation",
                    "exception_message": "network is not authorized",
                },
                "exception_stage": "unknown",
            },
        )
        replace_boundary(value, store, "policy_violation_exact", "unknown")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.POLICY)
        self.assertFalse(result.obligations["policy_clear"])

    def test_status_control_reward_one_is_pass(self) -> None:
        record, store = record_with_content(run_purpose="qualification_oracle")

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.PASS)
        self.assertFalse(result.task_invalid_candidate)

    def test_status_control_reward_zero_is_fail(self) -> None:
        record, store = record_with_content(reward=0)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.FAIL)

    def test_qualification_oracle_reward_zero_is_infra_and_task_invalid(self) -> None:
        record, store = record_with_content(
            run_purpose="qualification_oracle", reward=0
        )

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertTrue(result.task_invalid_candidate)

    def test_nonzero_harbor_process_is_infra_before_reward(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        value["harbor_process_return_code"] = 17
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["process_exit_zero"])

    def test_timeout_requires_agent_execution_and_no_reward(self) -> None:
        record, store = record_with_content(
            reward=None,
            stage_obligations={
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": False,
                "verifier_started": False,
                "verifier_completed": False,
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "agent_execution",
                "stage_obligations": {
                    "environment_started": True,
                    "agent_setup_completed": True,
                    "agent_execution_started": True,
                    "agent_execution_completed": False,
                    "verifier_started": False,
                    "verifier_completed": False,
                },
            }
        )
        replace_json_artifact(
            value,
            store,
            "trial_result",
            {
                "exception_info": {
                    "exception_type": "AgentTimeoutError",
                    "exception_message": "harness timeout",
                },
                "exception_stage": "agent_execution",
            },
        )
        replace_boundary(value, store, "agent_timeout_exact", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.TIMEOUT)

    def test_exact_agent_timeout_allows_absent_verifier_outputs(self) -> None:
        record, store = record_with_content(
            reward=None,
            stage_obligations={
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": False,
                "verifier_started": False,
                "verifier_completed": False,
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "agent_execution",
                "stage_obligations": {
                    "environment_started": True,
                    "agent_setup_completed": True,
                    "agent_execution_started": True,
                    "agent_execution_completed": False,
                    "verifier_started": False,
                    "verifier_completed": False,
                },
            }
        )
        replace_json_artifact(
            value,
            store,
            "trial_result",
            {
                "exception_info": {
                    "exception_type": "AgentTimeoutError",
                    "exception_message": "harness timeout",
                },
                "exception_stage": "agent_execution",
            },
        )
        replace_boundary(value, store, "agent_timeout_exact", "agent_execution")
        replace_artifact(value, store, "verifier_reward_json", b"")
        replace_artifact(value, store, "verifier_result_json", b"")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.TIMEOUT)
        self.assertTrue(result.obligations["reward_well_typed"])

    def test_stage_timings_must_match_the_trial_result(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        value["stage_timings"] = {
            "environment_setup": {
                "started_at": "2026-08-20T00:00:00Z",
                "finished_at": "2026-08-20T00:00:00Z",
            },
            "agent_setup": {
                "started_at": "2026-08-20T00:00:00Z",
                "finished_at": "2026-08-20T00:00:00Z",
            },
            "agent_execution": {
                "started_at": "2026-08-20T00:00:00Z",
                "finished_at": "2026-08-20T00:00:09Z",
            },
            "verifier": {
                "started_at": "2026-08-20T00:00:01Z",
                "finished_at": "2026-08-20T00:00:02Z",
            },
        }
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["stage_obligations_consistent"])

    def test_timeout_requires_the_observed_trial_exception(self) -> None:
        record, store = record_with_content(
            reward=None,
            stage_obligations={
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": False,
                "verifier_started": False,
                "verifier_completed": False,
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "agent_execution",
            }
        )
        replace_boundary(value, store, "agent_timeout_exact", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["trial_exception_consistent"])

    def test_invalid_phase_timestamp_is_infra(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        replace_json_artifact(
            value,
            store,
            "trial_result",
            {
                "environment_setup": {"started_at": False, "finished_at": 0},
                "agent_setup": {"started_at": False, "finished_at": 0},
                "agent_execution": {"started_at": False, "finished_at": 0},
                "verifier": {"started_at": False, "finished_at": 0},
            },
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["stage_obligations_consistent"])

    def test_timeout_with_a_reward_is_infra(self) -> None:
        record, store = record_with_content(
            run_purpose="qualification_oracle",
            stage_obligations={
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": False,
                "verifier_started": False,
                "verifier_completed": False,
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "agent_execution",
            }
        )
        replace_boundary(value, store, "agent_timeout_exact", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["timeout_attribution_valid"])

    def test_timeout_rejects_a_later_phase_after_an_incomplete_phase(self) -> None:
        record, store = record_with_content(
            reward=None,
            stage_obligations={
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": False,
                "verifier_started": False,
                "verifier_completed": False,
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "agent_execution",
            }
        )
        trial_uri = value["artifacts"]["trial_result"]
        assert isinstance(trial_uri, str)
        trial_result = json.loads(store[trial_uri])
        trial_result["verifier"] = {
            "started_at": "2026-08-20T00:00:01Z",
            "finished_at": "2026-08-20T00:00:02Z",
        }
        replace_artifact(
            value,
            store,
            "trial_result",
            json.dumps(trial_result, sort_keys=True, separators=(",", ":")).encode(),
        )
        replace_boundary(value, store, "agent_timeout_exact", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["stage_obligations_consistent"])

    def test_timeout_in_verifier_is_infra(self) -> None:
        record, store = record_with_content(reward=None)
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "verifier_timeout_exact",
                "exception_type_diagnostic": "VerifierTimeoutError",
                "exception_stage": "verifier",
            }
        )
        replace_boundary(value, store, "verifier_timeout_exact", "verifier")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["timeout_attribution_valid"])

    def test_agent_timeout_at_wrong_stage_is_infra_after_observed_exception(
        self,
    ) -> None:
        record, store = record_with_content(
            reward=None,
            stage_obligations={
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": True,
                "verifier_started": True,
                "verifier_completed": False,
            },
        )
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "verifier",
            }
        )
        replace_json_artifact(
            value,
            store,
            "trial_result",
            {
                "exception_info": {
                    "exception_type": "AgentTimeoutError",
                    "exception_message": "verifier timeout",
                },
                "exception_stage": "verifier",
            },
        )
        replace_boundary(value, store, "agent_timeout_exact", "verifier")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertTrue(result.obligations["trial_exception_consistent"])
        self.assertFalse(result.obligations["timeout_attribution_valid"])

    def test_timeout_diagnostic_name_without_exact_discriminant_is_infra(self) -> None:
        record, store = record_with_content(reward=None)
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": None,
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "agent_execution",
                "stage_obligations": {
                    "environment_started": True,
                    "agent_setup_completed": True,
                    "agent_execution_started": True,
                    "agent_execution_completed": False,
                    "verifier_started": False,
                    "verifier_completed": False,
                },
            }
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_agent_setup_timeout_discriminant_is_infra(self) -> None:
        record, store = record_with_content(reward=None)
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "agent_setup_timeout_exact",
                "exception_type_diagnostic": "AgentSetupTimeoutError",
                "exception_stage": "agent_setup",
            }
        )
        replace_boundary(value, store, "agent_setup_timeout_exact", "agent_setup")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_agent_timeout_discriminant_at_verifier_is_infra(self) -> None:
        record, store = record_with_content(reward=None)
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "agent_timeout_exact",
                "exception_type_diagnostic": "AgentTimeoutError",
                "exception_stage": "verifier",
            }
        )
        replace_boundary(value, store, "agent_timeout_exact", "verifier")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["timeout_attribution_valid"])

    def test_completed_record_requires_all_stage_obligations(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        stage_obligations = dict(value["stage_obligations"])
        stage_obligations["verifier_completed"] = False
        value["stage_obligations"] = stage_obligations
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["stage_obligations_consistent"])

    def test_stage_obligations_require_exact_boolean_closed_map(self) -> None:
        value = valid_record_json()
        stage_obligations = dict(value["stage_obligations"])
        stage_obligations["verifier_completed"] = 1
        value["stage_obligations"] = stage_obligations

        with self.assertRaises(AdapterContractError):
            HarborReplayRecord.from_json(value)

    def test_oracle_exit_artifact_must_match_record_presence_and_value(self) -> None:
        record, store = record_with_content(run_purpose="qualification_oracle")
        value = record.to_json()
        value["oracle_exit_code"] = 0
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["oracle_exit_consistent"])
        self.assertTrue(result.task_invalid_candidate)

    def test_malformed_oracle_exit_artifact_is_infra(self) -> None:
        content = b"not-json"
        digest = hashlib.sha256(content).hexdigest()
        value = valid_record_json()
        value["artifacts"] = {"oracle_exit_status": f"cas://sha256/{digest}"}
        value["artifact_sha256"] = {"oracle_exit_status": f"sha256:{digest}"}
        record = build_replay_record(
            value,
            artifact_bytes={"oracle_exit_status": content},
            artifact_uris={"oracle_exit_status": f"cas://sha256/{digest}"},
        )

        result = classify_harbor_record(
            record,
            read_artifact={record.artifacts["oracle_exit_status"]: content}.__getitem__,
        )

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["oracle_exit_consistent"])

    def test_observed_reward_requires_a_nonempty_typed_reward_artifact(self) -> None:
        oracle_content = b'{"present":false,"value":null}\n'
        oracle_digest = hashlib.sha256(oracle_content).hexdigest()
        reward_content = b""
        reward_digest = hashlib.sha256(reward_content).hexdigest()
        value = valid_record_json()
        value["artifacts"] = {
            "oracle_exit_status": f"cas://sha256/{oracle_digest}",
            "verifier_reward_json": f"cas://sha256/{reward_digest}",
        }
        value["artifact_sha256"] = {
            "oracle_exit_status": f"sha256:{oracle_digest}",
            "verifier_reward_json": f"sha256:{reward_digest}",
        }
        record = build_replay_record(
            value,
            artifact_bytes={
                "oracle_exit_status": oracle_content,
                "verifier_reward_json": reward_content,
            },
            artifact_uris=value["artifacts"],  # type: ignore[arg-type]
        )
        store = {
            record.artifacts["oracle_exit_status"]: oracle_content,
            record.artifacts["verifier_reward_json"]: reward_content,
        }

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["reward_well_typed"])

    def test_completed_status_with_structured_exception_is_infra(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        value.update(
            {
                "exception_discriminant": "other_exception",
                "exception_type_diagnostic": "SomeHarborError",
                "exception_stage": "agent_execution",
            }
        )
        replace_boundary(value, store, "other_exception", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)

    def test_projection_derives_status_from_structured_exception_presence(self) -> None:
        capture = valid_record_json()
        capture.pop("harbor_status")
        capture["trial_exception_present"] = False

        projection = project_harbor_capture(capture)

        self.assertEqual(projection["harbor_status"], "completed")

        capture["trial_exception_present"] = True
        projection = project_harbor_capture(capture)
        self.assertEqual(projection["harbor_status"], "exception")

    def test_replay_result_revalidates_mutated_obligations(self) -> None:
        result = HarborReplayResult(
            status=AdapterStatus.PASS,
            obligations={
                name: True
                for name in (
                    "qualification_pinned",
                    "run_purpose_valid",
                    "process_exit_zero",
                    "network_closed",
                    "job_cardinality_one",
                    "trial_cardinality_one",
                    "trial_exception_consistent",
                    "reward_well_typed",
                    "oracle_exit_consistent",
                    "exception_boundary_consistent",
                    "artifact_integrity",
                    "cleanup_complete",
                    "stage_obligations_consistent",
                    "policy_clear",
                    "infra_clear",
                    "timeout_attribution_valid",
                )
            },
            record_sha256="sha256:" + "e" * 64,
            task_invalid_candidate=False,
        )
        result.obligations["cleanup_complete"] = "yes"  # type: ignore[assignment]

        with self.assertRaises(AdapterContractError):
            result.to_json()

    def test_external_policy_exception_name_is_not_policy(self) -> None:
        record, store = record_with_content()
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_discriminant": "other_exception",
                "exception_type_diagnostic": "GitSpacePolicyViolation",
                "exception_stage": "agent_execution",
            }
        )
        replace_boundary(value, store, "other_exception", "agent_execution")
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertTrue(result.obligations["policy_clear"])


if __name__ == "__main__":
    unittest.main()
