from __future__ import annotations

import hashlib
import json
import unittest

from gs_eval_adapters.harbor_replay import (
    HarborReplayRecord,
    build_replay_record,
    canonical_record_bytes,
    classify_harbor_record,
    HarborReplayResult,
    project_harbor_capture,
)
from gs_eval_adapters.errors import AdapterContractError
from gs_eval_adapters.model import AdapterStatus


CAS_DIGEST = "a" * 64


def valid_record_json() -> dict[str, object]:
    return {
        "version": 1,
        "run_purpose": "qualification_oracle",
        "framework": "harbor",
        "framework_version": "0.21.0",
        "framework_commit": "64afbbcb62165950301e1a6407c729aa26d844ff",
        "framework_wheel_sha256": "c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21",
        "dataset_repository": "harbor-framework/terminal-bench-2-1",
        "dataset_commit": "7131e4375048a0e408a8fb404b5f499d726b695b",
        "task_name": "terminal-bench/regex-log",
        "source_task_sha256": f"sha256:{'b' * 64}",
        "normalized_task_sha256": f"sha256:{'c' * 64}",
        "environment_image_ref": "local://gitspace/regex-log@sha256:" + "d" * 64,
        "environment_image_id": "sha256:" + "d" * 64,
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
        "exception_type": None,
        "exception_stage": None,
        "stage_timings": {"agent_execution": 1.0},
        "artifacts": {"oracle_exit_status": f"cas://sha256/{CAS_DIGEST}"},
        "artifact_sha256": {"oracle_exit_status": f"sha256:{CAS_DIGEST}"},
        "cleanup_obligations": {
            "run_root_clean": True,
            "agent_processes_clean": True,
            "containers_clean": True,
            "foreign_resources_unchanged": True,
            "workspace_removed": True,
        },
    }


def record_with_content(
    *, run_purpose: str = "status_control", reward: int | None = 1
) -> tuple[HarborReplayRecord, dict[str, bytes]]:
    content = b'{"present":false,"value":null}\n'
    digest = hashlib.sha256(content).hexdigest()
    value = valid_record_json()
    value["run_purpose"] = run_purpose
    value["agent"] = "fake" if run_purpose == "status_control" else "oracle"
    value["observed_reward"] = reward
    artifact_bytes = {"oracle_exit_status": content}
    artifacts = {"oracle_exit_status": f"cas://sha256/{digest}"}
    artifact_sha256 = {"oracle_exit_status": f"sha256:{digest}"}
    if reward is not None:
        reward_content = json.dumps(
            {"reward": reward}, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        reward_digest = hashlib.sha256(reward_content).hexdigest()
        artifact_bytes["verifier_reward_json"] = reward_content
        artifacts["verifier_reward_json"] = f"cas://sha256/{reward_digest}"
        artifact_sha256["verifier_reward_json"] = f"sha256:{reward_digest}"
    value["artifacts"] = artifacts
    value["artifact_sha256"] = artifact_sha256
    record = build_replay_record(
        value,
        artifact_bytes=artifact_bytes,
        artifact_uris=artifacts,
    )
    return record, {uri: artifact_bytes[name] for name, uri in artifacts.items()}


class HarborReplayRedTests(unittest.TestCase):
    def test_harbor_replay_record_module_is_available(self) -> None:
        self.assertIsNotNone(HarborReplayRecord)

    def test_valid_record_round_trips_as_json_builtins(self) -> None:
        record = HarborReplayRecord.from_json(valid_record_json())

        self.assertEqual(record.to_json(), valid_record_json())

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
        record, store = record_with_content(reward=None)
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_type": "AgentTimeoutError",
                "exception_stage": "agent_execution",
            }
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.TIMEOUT)

    def test_timeout_in_verifier_is_infra(self) -> None:
        record, store = record_with_content(reward=None)
        value = record.to_json()
        value.update(
            {
                "harbor_status": "exception",
                "observed_reward": None,
                "exception_type": "AgentTimeoutError",
                "exception_stage": "verifier",
            }
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertFalse(result.obligations["timeout_attribution_valid"])

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
                "exception_type": "SomeHarborError",
                "exception_stage": "agent_execution",
            }
        )
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
                for name in {
                    "qualification_pinned",
                    "run_purpose_valid",
                    "process_exit_zero",
                    "network_closed",
                    "job_cardinality_one",
                    "trial_cardinality_one",
                    "reward_well_typed",
                    "oracle_exit_consistent",
                    "artifact_integrity",
                    "cleanup_complete",
                    "policy_clear",
                    "infra_clear",
                    "timeout_attribution_valid",
                }
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
                "exception_type": "GitSpacePolicyViolation",
                "exception_stage": "agent_execution",
            }
        )
        record = HarborReplayRecord.from_json(value)

        result = classify_harbor_record(record, read_artifact=store.__getitem__)

        self.assertIs(result.status, AdapterStatus.INFRA)
        self.assertTrue(result.obligations["policy_clear"])


if __name__ == "__main__":
    unittest.main()
