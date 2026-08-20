from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Callable

from .errors import AdapterContractError
from .json_boundary import JsonObject, JsonValue, clone_object, validate_cas_uri
from .model import AdapterStatus

HARBOR_VERSION = "0.21.0"
HARBOR_COMMIT = "64afbbcb62165950301e1a6407c729aa26d844ff"
HARBOR_WHEEL_SHA256 = "c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21"
TERMINAL_BENCH_COMMIT = "7131e4375048a0e408a8fb404b5f499d726b695b"
TERMINAL_BENCH_REPOSITORY = "harbor-framework/terminal-bench-2-1"
TERMINAL_BENCH_TASK = "terminal-bench/regex-log"

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_CAS_URI_PREFIX = "cas://sha256/"
_RUN_PURPOSES = {"qualification_oracle", "status_control"}
_HARBOR_STATUSES = {"completed", "exception"}
_EXCEPTION_STAGES = {
    "environment_setup",
    "agent_setup",
    "agent_execution",
    "verifier",
    "unknown",
}
_CLEANUP_FIELDS = {
    "run_root_clean",
    "agent_processes_clean",
    "containers_clean",
    "foreign_resources_unchanged",
    "workspace_removed",
}
_RECORD_FIELDS = {
    "version",
    "run_purpose",
    "framework",
    "framework_version",
    "framework_commit",
    "framework_wheel_sha256",
    "dataset_repository",
    "dataset_commit",
    "task_name",
    "source_task_sha256",
    "normalized_task_sha256",
    "environment_image_ref",
    "environment_image_id",
    "environment_platform",
    "runtime_network_mode",
    "verifier_environment_mode",
    "verifier_python",
    "agent",
    "oracle_exit_code",
    "job_id",
    "trial_id",
    "harbor_process_return_code",
    "harbor_status",
    "observed_reward",
    "exception_type",
    "exception_stage",
    "stage_timings",
    "artifacts",
    "artifact_sha256",
    "cleanup_obligations",
}
_RESULT_FIELDS = {"status", "obligations", "record_sha256", "task_invalid_candidate"}
_CAPTURE_FIELDS = (_RECORD_FIELDS - {"harbor_status"}) | {"trial_exception_present"}


@dataclass(frozen=True, slots=True)
class HarborReplayRecord:
    version: int
    run_purpose: str
    framework: str
    framework_version: str
    framework_commit: str
    framework_wheel_sha256: str
    dataset_repository: str
    dataset_commit: str
    task_name: str
    source_task_sha256: str
    normalized_task_sha256: str
    environment_image_ref: str
    environment_image_id: str
    environment_platform: str
    runtime_network_mode: str
    verifier_environment_mode: str
    verifier_python: str
    agent: str
    oracle_exit_code: int | None
    job_id: str
    trial_id: str
    harbor_process_return_code: int
    harbor_status: str
    observed_reward: int | None
    exception_type: str | None
    exception_stage: str | None
    stage_timings: dict[str, JsonValue]
    artifacts: dict[str, str]
    artifact_sha256: dict[str, str]
    cleanup_obligations: dict[str, bool]

    def __post_init__(self) -> None:
        _validate_record(self)
        object.__setattr__(self, "stage_timings", dict(self.stage_timings))
        object.__setattr__(self, "artifacts", dict(self.artifacts))
        object.__setattr__(self, "artifact_sha256", dict(self.artifact_sha256))
        object.__setattr__(self, "cleanup_obligations", dict(self.cleanup_obligations))

    @classmethod
    def from_json(cls, value: object) -> "HarborReplayRecord":
        data = _exact_object(value, "record")
        _require_exact_fields(data, _RECORD_FIELDS, "record")
        record = cls(
            version=_exact_int(data["version"], "version"),
            run_purpose=_bounded_string(data["run_purpose"], "run_purpose"),
            framework=_bounded_string(data["framework"], "framework"),
            framework_version=_bounded_string(
                data["framework_version"], "framework_version"
            ),
            framework_commit=_bounded_string(
                data["framework_commit"], "framework_commit"
            ),
            framework_wheel_sha256=_bounded_string(
                data["framework_wheel_sha256"], "framework_wheel_sha256"
            ),
            dataset_repository=_bounded_string(
                data["dataset_repository"], "dataset_repository"
            ),
            dataset_commit=_bounded_string(data["dataset_commit"], "dataset_commit"),
            task_name=_bounded_string(data["task_name"], "task_name"),
            source_task_sha256=_bounded_string(
                data["source_task_sha256"], "source_task_sha256"
            ),
            normalized_task_sha256=_bounded_string(
                data["normalized_task_sha256"], "normalized_task_sha256"
            ),
            environment_image_ref=_bounded_string(
                data["environment_image_ref"], "environment_image_ref"
            ),
            environment_image_id=_bounded_string(
                data["environment_image_id"], "environment_image_id"
            ),
            environment_platform=_bounded_string(
                data["environment_platform"], "environment_platform"
            ),
            runtime_network_mode=_bounded_string(
                data["runtime_network_mode"], "runtime_network_mode"
            ),
            verifier_environment_mode=_bounded_string(
                data["verifier_environment_mode"], "verifier_environment_mode"
            ),
            verifier_python=_bounded_string(data["verifier_python"], "verifier_python"),
            agent=_bounded_string(data["agent"], "agent"),
            oracle_exit_code=_optional_int(
                data["oracle_exit_code"], "oracle_exit_code"
            ),
            job_id=_bounded_string(data["job_id"], "job_id"),
            trial_id=_bounded_string(data["trial_id"], "trial_id"),
            harbor_process_return_code=_exact_int(
                data["harbor_process_return_code"], "harbor_process_return_code"
            ),
            harbor_status=_bounded_string(data["harbor_status"], "harbor_status"),
            observed_reward=_optional_reward(data["observed_reward"]),
            exception_type=_optional_string(data["exception_type"], "exception_type"),
            exception_stage=_optional_string(
                data["exception_stage"], "exception_stage"
            ),
            stage_timings=_json_object(data["stage_timings"], "stage_timings"),
            artifacts=_string_map(data["artifacts"], "artifacts"),
            artifact_sha256=_string_map(data["artifact_sha256"], "artifact_sha256"),
            cleanup_obligations=_bool_map(
                data["cleanup_obligations"], "cleanup_obligations"
            ),
        )
        _validate_record(record)
        return record

    def to_json(self) -> JsonObject:
        _validate_record(self)
        return clone_object(
            {
                "version": self.version,
                "run_purpose": self.run_purpose,
                "framework": self.framework,
                "framework_version": self.framework_version,
                "framework_commit": self.framework_commit,
                "framework_wheel_sha256": self.framework_wheel_sha256,
                "dataset_repository": self.dataset_repository,
                "dataset_commit": self.dataset_commit,
                "task_name": self.task_name,
                "source_task_sha256": self.source_task_sha256,
                "normalized_task_sha256": self.normalized_task_sha256,
                "environment_image_ref": self.environment_image_ref,
                "environment_image_id": self.environment_image_id,
                "environment_platform": self.environment_platform,
                "runtime_network_mode": self.runtime_network_mode,
                "verifier_environment_mode": self.verifier_environment_mode,
                "verifier_python": self.verifier_python,
                "agent": self.agent,
                "oracle_exit_code": self.oracle_exit_code,
                "job_id": self.job_id,
                "trial_id": self.trial_id,
                "harbor_process_return_code": self.harbor_process_return_code,
                "harbor_status": self.harbor_status,
                "observed_reward": self.observed_reward,
                "exception_type": self.exception_type,
                "exception_stage": self.exception_stage,
                "stage_timings": self.stage_timings,
                "artifacts": self.artifacts,
                "artifact_sha256": self.artifact_sha256,
                "cleanup_obligations": self.cleanup_obligations,
            },
            path="$/harbor_replay_record",
        )


@dataclass(frozen=True, slots=True)
class HarborReplayResult:
    status: AdapterStatus
    obligations: dict[str, bool]
    record_sha256: str
    task_invalid_candidate: bool

    def __post_init__(self) -> None:
        _validate_result(self)
        object.__setattr__(self, "obligations", dict(self.obligations))

    def to_json(self) -> JsonObject:
        _validate_result(self)
        return {
            "status": self.status.value,
            "obligations": dict(self.obligations),
            "record_sha256": self.record_sha256,
            "task_invalid_candidate": self.task_invalid_candidate,
        }


def canonical_record_bytes(record: HarborReplayRecord) -> bytes:
    if type(record) is not HarborReplayRecord:
        raise AdapterContractError("record must be an exact HarborReplayRecord")
    value = record.to_json()
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AdapterContractError("record is not canonical JSON") from error


def build_replay_record(
    projection: object,
    *,
    artifact_bytes: dict[str, bytes],
    artifact_uris: dict[str, str],
) -> HarborReplayRecord:
    record = HarborReplayRecord.from_json(projection)
    if type(artifact_bytes) is not dict or type(artifact_uris) is not dict:
        raise AdapterContractError("artifact inputs must be exact dicts")
    expected_keys = set(record.artifacts)
    if set(artifact_bytes) != expected_keys or set(artifact_uris) != expected_keys:
        raise AdapterContractError("artifact input keys differ from the record")
    for name in expected_keys:
        content = artifact_bytes[name]
        if type(content) is not bytes:
            raise AdapterContractError(f"artifact bytes must be exact bytes for {name}")
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        if digest != record.artifact_sha256[name]:
            raise AdapterContractError(f"artifact bytes digest differs for {name}")
        uri = artifact_uris[name]
        if type(uri) is not str or uri != record.artifacts[name]:
            raise AdapterContractError(f"artifact URI differs for {name}")
    return record


def project_harbor_capture(capture: object) -> JsonObject:
    data = _exact_object(capture, "harbor_capture")
    _require_exact_fields(data, _CAPTURE_FIELDS, "harbor_capture")
    exception_present = data.pop("trial_exception_present")
    if type(exception_present) is not bool:
        raise AdapterContractError("trial_exception_present must be an exact boolean")
    data["harbor_status"] = "exception" if exception_present else "completed"
    return HarborReplayRecord.from_json(data).to_json()


def classify_harbor_record(
    record: HarborReplayRecord | object,
    *,
    read_artifact: Callable[[str], bytes] | None,
) -> HarborReplayResult:
    if type(record) is not HarborReplayRecord:
        raise AdapterContractError("record must be an exact HarborReplayRecord")
    _validate_record(record)
    record_digest = (
        "sha256:" + hashlib.sha256(canonical_record_bytes(record)).hexdigest()
    )
    obligations = {name: True for name in _OBLIGATION_FIELDS}
    obligations["process_exit_zero"] = record.harbor_process_return_code == 0
    obligations["oracle_exit_consistent"] = record.oracle_exit_code in {None, 0}
    obligations["cleanup_complete"] = all(record.cleanup_obligations.values())
    artifact_contents: dict[str, bytes] = {}

    if read_artifact is None:
        obligations["artifact_integrity"] = False
    else:
        for name, uri in record.artifacts.items():
            try:
                content = read_artifact(uri)
            except Exception:
                obligations["artifact_integrity"] = False
                break
            if type(content) is not bytes:
                obligations["artifact_integrity"] = False
                break
            artifact_contents[name] = content
            expected_digest = record.artifact_sha256[name].removeprefix("sha256:")
            if hashlib.sha256(content).hexdigest() != expected_digest:
                obligations["artifact_integrity"] = False
                break
        if obligations["artifact_integrity"]:
            _validate_observed_artifacts(record, artifact_contents, obligations)

    task_invalid_candidate = False
    status = AdapterStatus.INFRA
    if not obligations["artifact_integrity"]:
        status = AdapterStatus.INFRA
    elif not obligations["process_exit_zero"]:
        status = AdapterStatus.INFRA
    elif not obligations["oracle_exit_consistent"]:
        task_invalid_candidate = record.run_purpose == "qualification_oracle"
        status = AdapterStatus.INFRA
    elif not obligations["reward_well_typed"]:
        status = AdapterStatus.INFRA
    elif not obligations["cleanup_complete"]:
        status = AdapterStatus.INFRA
    elif record.exception_type == "AgentTimeoutError":
        if (
            record.harbor_status == "exception"
            and record.exception_stage == "agent_execution"
            and record.observed_reward is None
        ):
            status = AdapterStatus.TIMEOUT
        else:
            obligations["timeout_attribution_valid"] = False
            status = AdapterStatus.INFRA
    elif record.exception_type is not None:
        status = AdapterStatus.INFRA
    elif record.harbor_status == "exception":
        status = AdapterStatus.INFRA
    elif record.observed_reward is None:
        status = AdapterStatus.INFRA
    elif record.run_purpose == "qualification_oracle" and record.observed_reward == 0:
        task_invalid_candidate = True
        status = AdapterStatus.INFRA
    elif record.observed_reward == 1:
        status = AdapterStatus.PASS
    elif record.run_purpose == "status_control" and record.observed_reward == 0:
        status = AdapterStatus.FAIL

    obligations["infra_clear"] = status not in {
        AdapterStatus.INFRA,
        AdapterStatus.POLICY,
    }
    return HarborReplayResult(
        status=status,
        obligations=obligations,
        record_sha256=record_digest,
        task_invalid_candidate=task_invalid_candidate,
    )


def _validate_observed_artifacts(
    record: HarborReplayRecord,
    contents: dict[str, bytes],
    obligations: dict[str, bool],
) -> None:
    oracle_content = contents.get("oracle_exit_status")
    if oracle_content is None:
        obligations["oracle_exit_consistent"] = False
    else:
        try:
            value = json.loads(oracle_content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            obligations["oracle_exit_consistent"] = False
        else:
            if type(value) is not dict or set(value) != {"present", "value"}:
                obligations["oracle_exit_consistent"] = False
            else:
                present = value["present"]
                exit_value = value["value"]
                if type(present) is not bool:
                    obligations["oracle_exit_consistent"] = False
                elif not present:
                    if exit_value is not None or record.oracle_exit_code is not None:
                        obligations["oracle_exit_consistent"] = False
                elif (
                    type(exit_value) is not int or record.oracle_exit_code != exit_value
                ):
                    obligations["oracle_exit_consistent"] = False

    reward_content = contents.get("verifier_reward_json")
    if reward_content is None or reward_content == b"":
        if record.observed_reward is not None:
            obligations["reward_well_typed"] = False
    else:
        try:
            value = json.loads(reward_content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            obligations["reward_well_typed"] = False
        else:
            if (
                type(value) is not dict
                or set(value) != {"reward"}
                or type(value["reward"]) is not int
                or value["reward"] not in {0, 1}
                or value["reward"] != record.observed_reward
            ):
                obligations["reward_well_typed"] = False


def _validate_record(record: HarborReplayRecord) -> None:
    if type(record.stage_timings) is not dict:
        raise AdapterContractError("stage_timings must be an exact dict")
    if type(record.artifacts) is not dict or type(record.artifact_sha256) is not dict:
        raise AdapterContractError("artifacts must be exact dicts")
    if type(record.cleanup_obligations) is not dict:
        raise AdapterContractError("cleanup_obligations must be an exact dict")
    if record.version != 1:
        raise AdapterContractError("version must be exactly 1")
    if record.run_purpose not in _RUN_PURPOSES:
        raise AdapterContractError("run_purpose is invalid")
    if record.framework != "harbor" or record.framework_version != HARBOR_VERSION:
        raise AdapterContractError("Harbor version is not pinned")
    if record.framework_commit != HARBOR_COMMIT:
        raise AdapterContractError("Harbor commit is not pinned")
    if record.framework_wheel_sha256 != HARBOR_WHEEL_SHA256:
        raise AdapterContractError("Harbor wheel digest is not pinned")
    if record.dataset_repository != TERMINAL_BENCH_REPOSITORY:
        raise AdapterContractError("dataset repository is not pinned")
    if record.dataset_commit != TERMINAL_BENCH_COMMIT:
        raise AdapterContractError("dataset commit is not pinned")
    if record.task_name != TERMINAL_BENCH_TASK:
        raise AdapterContractError("task name is not pinned")
    for name in (
        "source_task_sha256",
        "normalized_task_sha256",
        "environment_image_id",
    ):
        if not _DIGEST.fullmatch(getattr(record, name)):
            raise AdapterContractError(f"{name} must be a sha256 digest")
    if record.environment_platform != "linux/amd64":
        raise AdapterContractError("environment platform must be linux/amd64")
    if record.runtime_network_mode != "no-network":
        raise AdapterContractError("runtime network mode must be no-network")
    if record.verifier_environment_mode != "shared":
        raise AdapterContractError("verifier environment mode must be shared")
    if record.verifier_python != "3.13.15":
        raise AdapterContractError("verifier Python must be 3.13.15")
    if record.run_purpose == "qualification_oracle" and record.agent != "oracle":
        raise AdapterContractError("qualification_oracle must use the oracle agent")
    if record.harbor_status not in _HARBOR_STATUSES:
        raise AdapterContractError("Harbor status is invalid")
    if (
        record.exception_stage is not None
        and record.exception_stage not in _EXCEPTION_STAGES
    ):
        raise AdapterContractError("exception stage is invalid")
    if record.exception_type is None and record.exception_stage is not None:
        raise AdapterContractError("exception stage requires exception type")
    if set(record.artifacts) != set(record.artifact_sha256):
        raise AdapterContractError("artifact and digest keys differ")
    for name, uri in record.artifacts.items():
        try:
            validate_cas_uri(uri, path=f"$/artifacts/{name}")
        except Exception as error:
            raise AdapterContractError(f"artifact URI is invalid for {name}") from error
        digest = record.artifact_sha256[name]
        if not _DIGEST.fullmatch(digest):
            raise AdapterContractError(f"artifact digest is invalid for {name}")
        if uri != _CAS_URI_PREFIX + digest.removeprefix("sha256:"):
            raise AdapterContractError(f"artifact URI and digest differ for {name}")
    if set(record.cleanup_obligations) != _CLEANUP_FIELDS:
        raise AdapterContractError("cleanup obligation fields differ")
    if any(type(value) is not bool for value in record.cleanup_obligations.values()):
        raise AdapterContractError("cleanup obligations must be exact booleans")


def _validate_result(result: HarborReplayResult) -> None:
    if type(result.status) is not AdapterStatus:
        raise AdapterContractError("result status must be AdapterStatus")
    if set(result.obligations) != _OBLIGATION_FIELDS:
        raise AdapterContractError("result obligation fields differ")
    if any(type(value) is not bool for value in result.obligations.values()):
        raise AdapterContractError("result obligations must be exact booleans")
    if not _DIGEST.fullmatch(result.record_sha256):
        raise AdapterContractError("result record digest is invalid")
    if type(result.task_invalid_candidate) is not bool:
        raise AdapterContractError("task_invalid_candidate must be an exact boolean")


_OBLIGATION_FIELDS = {
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


def _exact_object(value: object, label: str) -> JsonObject:
    if type(value) is not dict:
        raise AdapterContractError(f"{label} must be an exact dict")
    try:
        return clone_object(value, path=f"$/{label}")
    except Exception as error:
        raise AdapterContractError(f"{label} is not JSON builtins") from error


def _require_exact_fields(value: JsonObject, expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise AdapterContractError(
            f"{label} fields differ: missing={sorted(expected - set(value))}, "
            f"unknown={sorted(set(value) - expected)}"
        )


def _bounded_string(value: object, label: str) -> str:
    if type(value) is not str or not value or len(value) > 512:
        raise AdapterContractError(f"{label} must be a bounded non-empty string")
    if any(unicodedata.category(char).startswith("C") for char in value):
        raise AdapterContractError(f"{label} contains control characters")
    return value


def _optional_string(value: object, label: str) -> str | None:
    if value is None:
        return None
    return _bounded_string(value, label)


def _exact_int(value: object, label: str) -> int:
    if type(value) is not int:
        raise AdapterContractError(f"{label} must be an exact integer")
    return value


def _optional_int(value: object, label: str) -> int | None:
    if value is None:
        return None
    return _exact_int(value, label)


def _optional_reward(value: object) -> int | None:
    if value is None:
        return None
    if type(value) is not int or value not in {0, 1}:
        raise AdapterContractError("observed_reward must be None, 0 or 1")
    return value


def _json_object(value: object, label: str) -> dict[str, JsonValue]:
    return _exact_object(value, label)


def _string_map(value: object, label: str) -> dict[str, str]:
    data = _exact_object(value, label)
    result: dict[str, str] = {}
    for key, item in data.items():
        if type(key) is not str:
            raise AdapterContractError(f"{label} keys must be strings")
        result[key] = _bounded_string(item, f"{label}.{key}")
    return result


def _bool_map(value: object, label: str) -> dict[str, bool]:
    data = _exact_object(value, label)
    result: dict[str, bool] = {}
    for key, item in data.items():
        if type(key) is not str or type(item) is not bool:
            raise AdapterContractError(f"{label} must contain exact string/bool pairs")
        result[key] = item
    return result
