from __future__ import annotations

import hashlib
import json
import re
import tomllib
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from .errors import AdapterContractError
from .json_boundary import (
    JsonBoundaryError,
    JsonObject,
    JsonValue,
    clone_object,
    validate_cas_uri,
)
from .model import AdapterStatus

HARBOR_VERSION = "0.21.0"
HARBOR_RECORD_VERSION = 2
HARBOR_COMMIT = "64afbbcb62165950301e1a6407c729aa26d844ff"
HARBOR_WHEEL_SHA256 = "c77d779a03f1a9e8ecb3c449e17f39a9728b82238832f1fd28632eb9426c0a21"
TERMINAL_BENCH_COMMIT = "7131e4375048a0e408a8fb404b5f499d726b695b"
TERMINAL_BENCH_REPOSITORY = "harbor-framework/terminal-bench-2-1"
TERMINAL_BENCH_TASK = "terminal-bench/regex-log"
TERMINAL_BENCH_SOURCE_TASK_SHA256 = (
    "sha256:345c3bd09ab6f6fe8c8361a58c0a47bf0a13b3fcb38a5ac7824e44ff855e8f72"
)
TERMINAL_BENCH_NORMALIZED_TASK_SHA256 = (
    "sha256:326420682198ec5d0f07d5e28e1fdbce1549531068a086bfa19cd8c28d3cac11"
)
HARBOR_ENVIRONMENT_IMPORT_PATH = (
    "gs_eval_adapters.harbor_runtime:GitSpaceHarborEnvironment"
)
TERMINAL_BENCH_RUNTIME_FILE_DIGESTS = {
    "task.toml": "sha256:eb71853de4f613a6ad4e2650f12c9d5af39908b20082f6206c3378d5f67538d7",
    "instruction.md": "sha256:4f7ac05e70cf9220ea0f1e5a052c5f908cd0fa884e847d80b0bd51bae2e96f9c",
    "solution/solve.sh": "sha256:7e670d4f2b4bccb1e4db38f2a173e085ceda028c38167912b466b0a84fcc0999",
    "tests/test_outputs.py": "sha256:345c3bd09ab6f6fe8c8361a58c0a47bf0a13b3fcb38a5ac7824e44ff855e8f72",
    "tests/run_test.py": "sha256:249dd2c3896af27b943c4eb7df6d3026da388be064c940a05c812d9b2d99dcce",
    "tests/test.sh": "sha256:32d0433e8eeee0271eb275f6a976f2704530ed3d5de6074535eab9dc01e7f88d",
    "environment/Dockerfile": "sha256:31fa4625b97ec859d0a26b9df931eb0de5b9d313a17413dfadd528e9e9c48cb6",
}
_FIXTURE_ARTIFACT_TO_PATH = {
    "task_toml": "task.toml",
    "instruction_md": "instruction.md",
    "solution_solve_sh": "solution/solve.sh",
    "test_source": "tests/test_outputs.py",
    "verifier_script": "tests/run_test.py",
    "verifier_test_script": "tests/test.sh",
    "environment_dockerfile": "environment/Dockerfile",
}
_EXPECTED_FIXTURE_FILE_DIGESTS = {
    "source-manifest.json": TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
    **TERMINAL_BENCH_RUNTIME_FILE_DIGESTS,
}

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_DOCKER_IMAGE_REFERENCE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?(?::[0-9]+)?/)?"
    r"[a-z0-9](?:[a-z0-9._/-]*[a-z0-9])?@sha256:[0-9a-f]{64}$"
)
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
_EXCEPTION_DISCRIMINANTS = {
    "agent_timeout_exact",
    "agent_setup_timeout_exact",
    "verifier_timeout_exact",
    "environment_start_timeout_exact",
    "policy_violation_exact",
    "other_exception",
}
HARBOR_ARTIFACT_FIELDS = {
    "harbor_stdout",
    "harbor_stderr",
    "job_config",
    "job_result",
    "trial_config",
    "trial_result",
    "agent_stdout",
    "agent_stderr",
    "oracle_exit_status",
    "verifier_stdout",
    "verifier_stderr",
    "verifier_reward_json",
    "verifier_result_json",
    "source_manifest",
    "task_toml",
    "instruction_md",
    "solution_solve_sh",
    "test_source",
    "verifier_script",
    "verifier_test_script",
    "environment_dockerfile",
    "fixture_inventory",
    "exception_boundary",
    "resource_manifest_before",
    "resource_manifest_after",
    "cleanup_report",
}
_REQUIRED_ARTIFACT_FIELDS = {
    "job_config",
    "job_result",
    "trial_config",
    "trial_result",
    "oracle_exit_status",
    "verifier_reward_json",
    "verifier_result_json",
    "source_manifest",
    "task_toml",
    "instruction_md",
    "solution_solve_sh",
    "test_source",
    "verifier_script",
    "verifier_test_script",
    "environment_dockerfile",
    "fixture_inventory",
    "exception_boundary",
    "resource_manifest_before",
    "resource_manifest_after",
    "cleanup_report",
}
_VERIFIER_RESULT_FIELDS = {
    "exception_message_or_null",
    "exception_type_or_null",
    "kind",
    "schema",
    "test_source_sha256",
}
_RUNTIME_IDENTITY_FIELDS = {
    "environment_image_ref",
    "environment_image_id",
    "egress_sidecar_image_ref",
    "egress_sidecar_image_id",
    "environment_platform",
    "runtime_network_mode",
}
_RESOURCE_MANIFEST_SCHEMA = "gitspace.harbor.resource-manifest.v1"
_RESOURCE_MANIFEST_FIELDS = {
    "schema",
    "phase",
    "identity",
    "resources",
    "inventory_complete",
    "inventory_scope",
    "collector",
    "inventory_digest",
}
_RESOURCE_INVENTORY_SCOPE = (
    "process_group",
    "temp_root",
    "container",
    "network",
    "derived_image",
)
_RESOURCE_COLLECTOR = "gitspace.harbor.resource-observer.v1"
_VERIFIER_RESULT_SCHEMA = "gitspace.verifier.v1"
_FIXTURE_INVENTORY_SCHEMA = "gitspace.harbor.fixture-inventory.v1"
_FIXTURE_INVENTORY_FIELDS = {"schema", "task_path", "files"}
_FIXTURE_FILE_FIELDS = {"sha256", "bytes", "mode"}
_TRIAL_EFFECTIVE_FIELDS = {
    "task",
    "trial_name",
    "trials_dir",
    "agent",
    "environment",
    "job_id",
}
_HARBOR_JOB_CONFIG_FIELDS = {
    "job_name",
    "jobs_dir",
    "n_attempts",
    "install_only",
    "timeout_multiplier",
    "agent_timeout_multiplier",
    "verifier_timeout_multiplier",
    "agent_setup_timeout_multiplier",
    "environment_build_timeout_multiplier",
    "debug",
    "n_concurrent_trials",
    "quiet",
    "retry",
    "environment",
    "verifier",
    "metrics",
    "agents",
    "datasets",
    "tasks",
    "artifacts",
    "extra_instruction_paths",
    "source_jobs",
}
_RESOURCE_FIELDS = {"kind", "id", "owner", "state_digest"}
_RESOURCE_KINDS = {
    "process_group",
    "temp_root",
    "container",
    "network",
    "derived_image",
}
_RESOURCE_OWNERS = {"gitspace", "foreign"}
_EXCEPTION_TYPE_BY_DISCRIMINANT = {
    "agent_timeout_exact": "AgentTimeoutError",
    "agent_setup_timeout_exact": "AgentSetupTimeoutError",
    "verifier_timeout_exact": "VerifierTimeoutError",
    "environment_start_timeout_exact": "EnvironmentStartTimeoutError",
    "policy_violation_exact": "AdapterPolicyViolation",
}
_STAGE_FIELDS = {
    "environment_started",
    "agent_setup_completed",
    "agent_execution_started",
    "agent_execution_completed",
    "verifier_started",
    "verifier_completed",
}
_CLEANUP_FIELDS = {
    "process_group_absent",
    "temp_root_absent",
    "containers_absent",
    "networks_absent",
    "derived_images_absent",
    "foreign_resources_untouched",
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
    "egress_sidecar_image_ref",
    "egress_sidecar_image_id",
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
    "exception_discriminant",
    "exception_type_diagnostic",
    "exception_stage",
    "stage_timings",
    "stage_obligations",
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
    egress_sidecar_image_ref: str
    egress_sidecar_image_id: str
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
    exception_discriminant: str | None
    exception_type_diagnostic: str | None
    exception_stage: str | None
    stage_timings: dict[str, JsonValue]
    stage_obligations: dict[str, bool]
    artifacts: dict[str, str]
    artifact_sha256: dict[str, str]
    cleanup_obligations: dict[str, bool]

    def __post_init__(self) -> None:
        _validate_record(self)
        object.__setattr__(self, "stage_timings", dict(self.stage_timings))
        object.__setattr__(self, "stage_obligations", dict(self.stage_obligations))
        object.__setattr__(self, "artifacts", dict(self.artifacts))
        object.__setattr__(self, "artifact_sha256", dict(self.artifact_sha256))
        object.__setattr__(self, "cleanup_obligations", dict(self.cleanup_obligations))

    @classmethod
    def from_json(cls, value: object) -> HarborReplayRecord:
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
            egress_sidecar_image_ref=_bounded_string(
                data["egress_sidecar_image_ref"], "egress_sidecar_image_ref"
            ),
            egress_sidecar_image_id=_bounded_string(
                data["egress_sidecar_image_id"], "egress_sidecar_image_id"
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
            exception_discriminant=_optional_string(
                data["exception_discriminant"], "exception_discriminant"
            ),
            exception_type_diagnostic=_optional_string(
                data["exception_type_diagnostic"], "exception_type_diagnostic"
            ),
            exception_stage=_optional_string(
                data["exception_stage"], "exception_stage"
            ),
            stage_timings=_json_object(data["stage_timings"], "stage_timings"),
            stage_obligations=_bool_map(data["stage_obligations"], "stage_obligations"),
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
                "egress_sidecar_image_ref": self.egress_sidecar_image_ref,
                "egress_sidecar_image_id": self.egress_sidecar_image_id,
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
                "exception_discriminant": self.exception_discriminant,
                "exception_type_diagnostic": self.exception_type_diagnostic,
                "exception_stage": self.exception_stage,
                "stage_timings": self.stage_timings,
                "stage_obligations": self.stage_obligations,
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
    obligations = {name: False for name in _OBLIGATION_FIELDS}
    obligations["qualification_pinned"] = _qualification_pinned(record)
    obligations["run_purpose_valid"] = _run_purpose_valid(record)
    obligations["process_exit_zero"] = record.harbor_process_return_code == 0
    obligations["oracle_exit_consistent"] = False
    obligations["policy_clear"] = (
        record.exception_discriminant != "policy_violation_exact"
    )
    obligations["artifact_integrity"] = _required_artifact_fields(record).issubset(
        record.artifacts
    )
    artifact_contents: dict[str, bytes] = {}

    if read_artifact is None:
        obligations["artifact_integrity"] = False
    else:
        for name, uri in record.artifacts.items():
            try:
                content = read_artifact(uri)
            except Exception:  # noqa: BLE001 - unreadable CAS is an infra outcome
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
    if (
        not obligations["artifact_integrity"]
        or not obligations["qualification_pinned"]
        or not obligations["run_purpose_valid"]
        or not obligations["exception_boundary_consistent"]
        or not obligations["trial_exception_consistent"]
    ):
        status = AdapterStatus.INFRA
    elif not obligations["policy_clear"]:
        status = AdapterStatus.POLICY
    elif not obligations["process_exit_zero"]:
        status = AdapterStatus.INFRA
    elif not obligations["oracle_exit_consistent"]:
        task_invalid_candidate = record.run_purpose == "qualification_oracle"
        status = AdapterStatus.INFRA
    elif (
        not obligations["network_closed"]
        or not obligations["job_cardinality_one"]
        or not obligations["trial_cardinality_one"]
        or not obligations["reward_well_typed"]
        or not obligations["cleanup_complete"]
        or not obligations["stage_obligations_consistent"]
    ):
        status = AdapterStatus.INFRA
    elif record.exception_discriminant == "agent_timeout_exact":
        obligations["timeout_attribution_valid"] = _timeout_attribution_valid(record)
        status = (
            AdapterStatus.TIMEOUT
            if obligations["timeout_attribution_valid"]
            else AdapterStatus.INFRA
        )
    elif (
        record.exception_discriminant is not None
        or record.harbor_status == "exception"
        or record.observed_reward is None
    ):
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


def _qualification_pinned(record: HarborReplayRecord) -> bool:
    return (
        record.framework == "harbor"
        and record.framework_version == HARBOR_VERSION
        and record.framework_commit == HARBOR_COMMIT
        and record.framework_wheel_sha256 == HARBOR_WHEEL_SHA256
        and record.dataset_repository == TERMINAL_BENCH_REPOSITORY
        and record.dataset_commit == TERMINAL_BENCH_COMMIT
        and record.task_name == TERMINAL_BENCH_TASK
        and record.source_task_sha256 == TERMINAL_BENCH_SOURCE_TASK_SHA256
        and record.normalized_task_sha256 == TERMINAL_BENCH_NORMALIZED_TASK_SHA256
        and record.environment_platform == "linux/amd64"
        and record.runtime_network_mode == "no-network"
        and record.verifier_environment_mode == "shared"
        and record.verifier_python == "3.13.15"
        and _image_reference_matches(
            record.environment_image_ref, record.environment_image_id
        )
        and _image_reference_matches(
            record.egress_sidecar_image_ref, record.egress_sidecar_image_id
        )
    )


def _required_artifact_fields(record: HarborReplayRecord) -> set[str]:
    required = set(_REQUIRED_ARTIFACT_FIELDS)
    if record.exception_discriminant == "agent_timeout_exact":
        required -= {"verifier_reward_json", "verifier_result_json"}
    return required


def _run_purpose_valid(record: HarborReplayRecord) -> bool:
    return record.run_purpose in _RUN_PURPOSES and (
        record.run_purpose != "qualification_oracle" or record.agent == "oracle"
    )


def _image_reference_matches(reference: str, image_id: str) -> bool:
    return (
        _DIGEST.fullmatch(image_id) is not None
        and _DOCKER_IMAGE_REFERENCE.fullmatch(reference) is not None
        and reference.rsplit("@", 1)[1] == image_id
    )


def _stage_obligations_from_trial_result(
    trial_result: JsonObject,
) -> dict[str, bool]:
    environment_started, _ = _timing_obligations(trial_result.get("environment_setup"))
    agent_setup_started, agent_setup_completed = _timing_obligations(
        trial_result.get("agent_setup")
    )
    agent_started, agent_completed = _timing_obligations(
        trial_result.get("agent_execution")
    )
    verifier_started, verifier_completed = _timing_obligations(
        trial_result.get("verifier")
    )
    return {
        "environment_started": environment_started,
        "agent_setup_completed": agent_setup_started and agent_setup_completed,
        "agent_execution_started": agent_started,
        "agent_execution_completed": agent_completed,
        "verifier_started": verifier_started,
        "verifier_completed": verifier_completed,
    }


def _timing_obligations(value: object) -> tuple[bool, bool]:
    started_at, finished_at, valid = _timing_values(value)
    return valid and started_at is not None, valid and finished_at is not None


def _timing_values(
    value: object,
) -> tuple[datetime | None, datetime | None, bool]:
    if value is None:
        return None, None, True
    if type(value) is not dict or set(value) - {"started_at", "finished_at"}:
        return None, None, False
    if "started_at" not in value:
        return None, None, False
    started_at = _parse_timestamp(value["started_at"])
    if started_at is None:
        return None, None, False
    raw_finished_at = value.get("finished_at")
    if raw_finished_at is None:
        return started_at, None, True
    finished_at = _parse_timestamp(raw_finished_at)
    if finished_at is None or finished_at < started_at:
        return None, None, False
    return started_at, finished_at, True


def _parse_timestamp(value: object) -> datetime | None:
    if type(value) is not str or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _phase_timings_valid(trial_result: JsonObject) -> bool:
    previous_finished: datetime | None = None
    previous_incomplete = False
    for name in ("environment_setup", "agent_setup", "agent_execution", "verifier"):
        started_at, finished_at, valid = _timing_values(trial_result.get(name))
        if not valid:
            return False
        if started_at is None:
            continue
        if previous_incomplete:
            return False
        if previous_finished is not None and started_at < previous_finished:
            return False
        previous_finished = finished_at
        previous_incomplete = finished_at is None
    return True


def _expected_exception_stage_obligations(stage: str) -> dict[str, bool]:
    values = {name: False for name in _STAGE_FIELDS}
    if stage == "agent_setup":
        values["environment_started"] = True
    elif stage == "agent_execution":
        values.update(
            {
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
            }
        )
    elif stage == "verifier":
        values.update(
            {
                "environment_started": True,
                "agent_setup_completed": True,
                "agent_execution_started": True,
                "agent_execution_completed": True,
                "verifier_started": True,
            }
        )
    return values


def _stage_obligations_consistent(
    record: HarborReplayRecord,
    observed: dict[str, bool] | None = None,
) -> bool:
    if observed is None or observed != record.stage_obligations:
        return False
    if record.harbor_status == "completed":
        return (
            record.exception_discriminant is None
            and record.exception_type_diagnostic is None
            and record.exception_stage is None
            and all(record.stage_obligations.values())
        )
    if record.harbor_status != "exception":
        return False
    if record.exception_discriminant not in _EXCEPTION_DISCRIMINANTS:
        return False
    if record.exception_type_diagnostic is None or record.exception_stage is None:
        return False
    expected = _expected_exception_stage_obligations(record.exception_stage)
    return record.stage_obligations == expected


def _stage_timings_consistent(
    record: HarborReplayRecord, trial_result: JsonObject
) -> bool:
    observed: dict[str, JsonValue] = {}
    for stage in ("environment_setup", "agent_setup", "agent_execution", "verifier"):
        value = trial_result.get(stage)
        if value is not None:
            try:
                observed[stage] = clone_object(value, path=f"$/trial_result/{stage}")
            except JsonBoundaryError:
                return False
    return observed == record.stage_timings


def _timeout_attribution_valid(record: HarborReplayRecord) -> bool:
    return (
        record.exception_discriminant == "agent_timeout_exact"
        and record.harbor_status == "exception"
        and record.exception_stage == "agent_execution"
        and record.observed_reward is None
        and record.stage_obligations
        == {
            "environment_started": True,
            "agent_setup_completed": True,
            "agent_execution_started": True,
            "agent_execution_completed": False,
            "verifier_started": False,
            "verifier_completed": False,
        }
    )


def _validate_observed_artifacts(
    record: HarborReplayRecord,
    contents: dict[str, bytes],
    obligations: dict[str, bool],
) -> None:
    job_config = _decode_object(contents.get("job_config"))
    job_result = _decode_object(contents.get("job_result"))
    trial_config = _decode_object(contents.get("trial_config"))
    trial_result = _decode_object(contents.get("trial_result"))
    if (
        job_config is None
        or job_result is None
        or trial_config is None
        or trial_result is None
    ):
        return

    job_cardinality_one, network_closed = _validate_effective_job_config(
        record, job_config
    )
    trial_cardinality_one, trial_exception_consistent = _validate_trial_artifacts(
        record, job_result, trial_config, trial_result, job_config
    )
    obligations["job_cardinality_one"] = job_cardinality_one
    obligations["trial_cardinality_one"] = trial_cardinality_one
    obligations["trial_exception_consistent"] = trial_exception_consistent
    obligations["network_closed"] = network_closed

    observed_stage_obligations = _stage_obligations_from_trial_result(trial_result)
    obligations["stage_obligations_consistent"] = (
        _phase_timings_valid(trial_result)
        and _stage_timings_consistent(record, trial_result)
        and _stage_obligations_consistent(record, observed_stage_obligations)
    )
    obligations["timeout_attribution_valid"] = _timeout_attribution_valid(record)

    before_manifest = _decode_object(contents.get("resource_manifest_before"))
    after_manifest = _decode_object(contents.get("resource_manifest_after"))
    identity_observed, manifests_valid, derived_cleanup = _validate_runtime_manifests(
        record, before_manifest, after_manifest
    )
    cleanup = _decode_object(contents.get("cleanup_report"))
    cleanup_valid = _validate_cleanup(record, cleanup, derived_cleanup)
    obligations["cleanup_complete"] = (
        manifests_valid
        and cleanup_valid
        and identity_observed
        and all(derived_cleanup.values())
    )
    obligations["qualification_pinned"] = (
        obligations["qualification_pinned"]
        and identity_observed
        and _validate_source_manifest(record, contents.get("source_manifest"))
        and _validate_fixture_artifacts(record, contents, job_config)
    )

    oracle_content = contents.get("oracle_exit_status")
    oracle_valid = False
    if oracle_content is not None:
        try:
            value = json.loads(oracle_content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        else:
            if type(value) is not dict or set(value) != {"present", "value"}:
                pass
            else:
                present = value["present"]
                exit_value = value["value"]
                if type(present) is not bool:
                    pass
                elif not present:
                    oracle_valid = (
                        exit_value is None and record.oracle_exit_code is None
                    )
                elif (
                    type(exit_value) is not int or record.oracle_exit_code != exit_value
                ):
                    pass
                else:
                    oracle_valid = record.oracle_exit_code in {None, 0}
    obligations["oracle_exit_consistent"] = oracle_valid

    obligations["reward_well_typed"] = _validate_verifier_artifacts(
        record,
        contents.get("verifier_reward_json"),
        contents.get("verifier_result_json"),
    )

    boundary_content = contents.get("exception_boundary")
    if boundary_content is None or boundary_content == b"":
        obligations["exception_boundary_consistent"] = False
    else:
        try:
            boundary = json.loads(boundary_content)
        except (UnicodeDecodeError, json.JSONDecodeError):
            obligations["exception_boundary_consistent"] = False
        else:
            if (
                type(boundary) is not dict
                or set(boundary)
                != {
                    "discriminant",
                    "stage",
                }
                or (
                    boundary["discriminant"] != record.exception_discriminant
                    or boundary["stage"] != record.exception_stage
                    or (
                        boundary["discriminant"] is not None
                        and type(boundary["discriminant"]) is not str
                    )
                    or (
                        boundary["stage"] is not None
                        and type(boundary["stage"]) is not str
                    )
                )
            ):
                obligations["exception_boundary_consistent"] = False
            else:
                obligations["exception_boundary_consistent"] = True


def _decode_object(content: bytes | None) -> JsonObject | None:
    if content is None or content == b"":
        return None
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if type(value) is dict else None


def _validate_effective_job_config(
    record: HarborReplayRecord, job: JsonObject
) -> tuple[bool, bool]:
    if not set(job).issubset(_HARBOR_JOB_CONFIG_FIELDS):
        return False, False
    n_attempts = job.get("n_attempts", 1)
    retry = job.get("retry", {"max_retries": 0})
    environment = job.get("environment")
    agents = job.get("agents")
    datasets = job.get("datasets", [])
    tasks = job.get("tasks")
    task = tasks[0] if type(tasks) is list and len(tasks) == 1 else None
    job_cardinality = (
        type(n_attempts) is int
        and n_attempts == 1
        and type(job.get("n_concurrent_trials")) is int
        and job["n_concurrent_trials"] == 1
        and type(retry) is dict
        and type(retry.get("max_retries")) is int
        and retry["max_retries"] == 0
        and type(agents) is list
        and len(agents) == 1
        and type(agents[0]) is dict
        and agents[0].get("name") == "oracle"
        and type(agents[0].get("n_concurrent")) is int
        and agents[0]["n_concurrent"] == 1
        and datasets == []
        and type(tasks) is list
        and len(tasks) == 1
        and type(task) is dict
        and set(task) == {"path"}
        and type(task["path"]) is str
        and bool(task["path"])
        and job.get("job_name") == "gitspace-p00-task-012-oracle"
        and (
            "jobs_dir" not in job
            or (type(job["jobs_dir"]) is str and bool(job["jobs_dir"]))
        )
        and job.get("install_only", False) is False
        and job.get("debug", False) is False
        and job.get("quiet", False) is False
        and type(job.get("timeout_multiplier", 1.0)) is float
        and job.get("timeout_multiplier", 1.0) == 1.0
        and job.get("agent_timeout_multiplier") is None
        and job.get("verifier_timeout_multiplier") is None
        and job.get("agent_setup_timeout_multiplier") is None
        and job.get("environment_build_timeout_multiplier") is None
        and job.get("verifier") is None
        and job.get("metrics", []) == []
        and job.get("artifacts", []) == []
        and job.get("source_jobs") is None
        and job.get("extra_instruction_paths", []) == []
    )
    environment_kwargs = (
        environment.get("kwargs") if type(environment) is dict else None
    )
    network_closed = (
        type(environment) is dict
        and set(environment) == {"import_path", "kwargs"}
        and environment.get("import_path") == HARBOR_ENVIRONMENT_IMPORT_PATH
        and type(environment_kwargs) is dict
        and set(environment_kwargs)
        == {
            "gitspace_environment_image_ref",
            "gitspace_environment_image_id",
            "gitspace_egress_sidecar_image_ref",
            "gitspace_egress_sidecar_image_id",
        }
        and environment_kwargs.get("gitspace_environment_image_ref")
        == record.environment_image_ref
        and environment_kwargs.get("gitspace_environment_image_id")
        == record.environment_image_id
        and environment_kwargs.get("gitspace_egress_sidecar_image_ref")
        == record.egress_sidecar_image_ref
        and environment_kwargs.get("gitspace_egress_sidecar_image_id")
        == record.egress_sidecar_image_id
        and _image_reference_matches(
            record.environment_image_ref, record.environment_image_id
        )
        and _image_reference_matches(
            record.egress_sidecar_image_ref, record.egress_sidecar_image_id
        )
    )
    return job_cardinality, network_closed


def _validate_trial_artifacts(
    record: HarborReplayRecord,
    job_result: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
    job_config: JsonObject,
) -> tuple[bool, bool]:
    trial_results = job_result.get("trial_results")
    if (
        type(job_result.get("n_total_trials")) is not int
        or job_result["n_total_trials"] != 1
        or type(trial_results) is not list
        or len(trial_results) != 1
        or type(trial_results[0]) is not dict
    ):
        return False, False
    summary = trial_results[0]
    config_identity_valid = _validate_effective_trial_config(
        record, job_config, trial_config, trial_result
    )
    cardinality_valid = (
        summary.get("id") == record.trial_id
        and job_result.get("id") == record.job_id
        and trial_result.get("id") == record.trial_id
        and trial_result.get("task_name") == record.task_name
        and config_identity_valid
    )
    return cardinality_valid, _trial_exception_consistent(record, trial_result)


def _validate_effective_trial_config(
    record: HarborReplayRecord,
    job_config: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
) -> bool:
    if set(trial_config) != _TRIAL_EFFECTIVE_FIELDS:
        return False
    job_tasks = job_config.get("tasks")
    task = trial_config.get("task")
    if (
        type(job_tasks) is not list
        or len(job_tasks) != 1
        or type(job_tasks[0]) is not dict
        or set(job_tasks[0]) != {"path"}
        or type(job_tasks[0]["path"]) is not str
        or type(task) is not dict
        or set(task) != {"path"}
        or task.get("path") != job_tasks[0]["path"]
    ):
        return False
    trial_name = trial_config.get("trial_name")
    if (
        type(trial_name) is not str
        or not trial_name
        or trial_result.get("trial_name") != trial_name
    ):
        return False
    if (
        type(trial_config.get("trials_dir")) is not str
        or not trial_config["trials_dir"]
    ):
        return False
    if trial_config.get("job_id") != record.job_id:
        return False
    agent = trial_config.get("agent")
    if (
        type(agent) is not dict
        or set(agent) != {"name", "n_concurrent"}
        or agent.get("name") != "oracle"
        or type(agent.get("n_concurrent")) is not int
        or agent["n_concurrent"] != 1
    ):
        return False
    return _validate_environment_extension(trial_config.get("environment"), record)


def _validate_environment_extension(value: object, record: HarborReplayRecord) -> bool:
    if type(value) is not dict or set(value) != {"import_path", "kwargs"}:
        return False
    kwargs = value.get("kwargs")
    return (
        value.get("import_path") == HARBOR_ENVIRONMENT_IMPORT_PATH
        and type(kwargs) is dict
        and set(kwargs)
        == {
            "gitspace_environment_image_ref",
            "gitspace_environment_image_id",
            "gitspace_egress_sidecar_image_ref",
            "gitspace_egress_sidecar_image_id",
        }
        and kwargs.get("gitspace_environment_image_ref") == record.environment_image_ref
        and kwargs.get("gitspace_environment_image_id") == record.environment_image_id
        and kwargs.get("gitspace_egress_sidecar_image_ref")
        == record.egress_sidecar_image_ref
        and kwargs.get("gitspace_egress_sidecar_image_id")
        == record.egress_sidecar_image_id
    )


def _trial_exception_consistent(
    record: HarborReplayRecord, trial_result: JsonObject
) -> bool:
    exception_info = trial_result.get("exception_info")
    raw_stage = trial_result.get("exception_stage")
    if record.harbor_status == "completed":
        return (
            exception_info is None
            and raw_stage is None
            and record.exception_discriminant is None
            and record.exception_type_diagnostic is None
            and record.exception_stage is None
        )
    if record.harbor_status != "exception" or type(exception_info) is not dict:
        return False
    observed_type = exception_info.get("exception_type")
    if type(observed_type) is not str or not observed_type:
        return False
    if raw_stage is None:
        observed_stage = "unknown"
    elif type(raw_stage) is str and raw_stage in _EXCEPTION_STAGES:
        observed_stage = raw_stage
    else:
        return False
    observed_message = exception_info.get("exception_message")
    if observed_message is not None and type(observed_message) is not str:
        return False
    expected_type = _EXCEPTION_TYPE_BY_DISCRIMINANT.get(
        record.exception_discriminant or ""
    )
    return (
        record.exception_type_diagnostic == observed_type
        and record.exception_stage == observed_stage
        and (expected_type is None or observed_type == expected_type)
    )


def _validate_runtime_manifests(
    record: HarborReplayRecord,
    before: JsonObject | None,
    after: JsonObject | None,
) -> tuple[bool, bool, dict[str, bool]]:
    empty_cleanup = {name: False for name in _CLEANUP_FIELDS}
    if before is None or after is None:
        return False, False, empty_cleanup
    if (
        set(before) != _RESOURCE_MANIFEST_FIELDS
        or before.get("schema") != _RESOURCE_MANIFEST_SCHEMA
        or before.get("phase") != "before"
        or before.get("identity") is not None
        or type(before.get("resources")) is not list
        or not _resource_inventory_valid(before["resources"], before)
    ):
        return False, False, empty_cleanup
    identity = after.get("identity")
    if (
        set(after) != _RESOURCE_MANIFEST_FIELDS
        or after.get("schema") != _RESOURCE_MANIFEST_SCHEMA
        or after.get("phase") != "after"
        or type(after.get("resources")) is not list
        or type(identity) is not dict
        or set(identity) != _RUNTIME_IDENTITY_FIELDS
        or not _resource_inventory_valid(after["resources"], after)
    ):
        return False, False, empty_cleanup
    before_resources = _resource_map(before["resources"])
    after_resources = _resource_map(after["resources"])
    if before_resources is None or after_resources is None:
        return False, False, empty_cleanup
    if not all(
        _owned_kind_present(before_resources, kind)
        for kind in ("process_group", "temp_root")
    ):
        return False, False, empty_cleanup
    expected = {name: getattr(record, name) for name in _RUNTIME_IDENTITY_FIELDS}
    observed = all(identity.get(name) == value for name, value in expected.items())
    return (
        observed,
        observed,
        _derive_cleanup_obligations(before_resources, after_resources),
    )


def _resource_inventory_valid(resources: object, manifest: JsonObject) -> bool:
    return (
        type(manifest.get("inventory_complete")) is bool
        and manifest["inventory_complete"] is True
        and manifest.get("inventory_scope") == list(_RESOURCE_INVENTORY_SCOPE)
        and manifest.get("collector") == _RESOURCE_COLLECTOR
        and type(manifest.get("inventory_digest")) is str
        and manifest["inventory_digest"] == _resource_inventory_digest(resources)
    )


def _resource_inventory_digest(resources: object) -> str | None:
    if type(resources) is not list or any(type(item) is not dict for item in resources):
        return None
    try:
        encoded = json.dumps(
            resources,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError):
        return None
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _resource_map(value: object) -> dict[tuple[str, str, str], JsonObject] | None:
    if type(value) is not list:
        return None
    resources: dict[tuple[str, str, str], JsonObject] = {}
    for item in value:
        if type(item) is not dict or set(item) != _RESOURCE_FIELDS:
            return None
        kind = item.get("kind")
        resource_id = item.get("id")
        owner = item.get("owner")
        state_digest = item.get("state_digest")
        if (
            type(kind) is not str
            or kind not in _RESOURCE_KINDS
            or type(resource_id) is not str
            or not resource_id
            or type(owner) is not str
            or owner not in _RESOURCE_OWNERS
            or type(state_digest) is not str
            or _DIGEST.fullmatch(state_digest) is None
        ):
            return None
        key = (kind, resource_id, owner)
        if key in resources:
            return None
        resources[key] = dict(item)
    return resources


def _derive_cleanup_obligations(
    before: dict[tuple[str, str, str], JsonObject],
    after: dict[tuple[str, str, str], JsonObject],
) -> dict[str, bool]:
    return {
        "process_group_absent": not _owned_kind_present(after, "process_group"),
        "temp_root_absent": not _owned_kind_present(after, "temp_root"),
        "containers_absent": not _owned_kind_present(after, "container"),
        "networks_absent": not _owned_kind_present(after, "network"),
        "derived_images_absent": not _owned_kind_present(after, "derived_image"),
        "foreign_resources_untouched": {
            key: value for key, value in before.items() if key[2] == "foreign"
        }
        == {key: value for key, value in after.items() if key[2] == "foreign"},
    }


def _owned_kind_present(
    resources: dict[tuple[str, str, str], JsonObject], kind: str
) -> bool:
    return any(key[0] == kind and key[2] == "gitspace" for key in resources)


def _validate_cleanup(
    record: HarborReplayRecord,
    cleanup: JsonObject | None,
    derived: dict[str, bool],
) -> bool:
    return (
        cleanup is not None
        and set(cleanup) == _CLEANUP_FIELDS
        and all(type(cleanup[name]) is bool for name in _CLEANUP_FIELDS)
        and all(cleanup[name] == derived[name] for name in _CLEANUP_FIELDS)
        and record.cleanup_obligations == derived
    )


def _validate_source_manifest(
    record: HarborReplayRecord, content: bytes | None
) -> bool:
    if content is None or hashlib.sha256(content).hexdigest() != (
        TERMINAL_BENCH_NORMALIZED_TASK_SHA256.removeprefix("sha256:")
    ):
        return False
    manifest = _decode_object(content)
    if manifest is None:
        return False
    source_files = manifest.get("source_files")
    if type(source_files) is not dict:
        return False
    runtime_files = manifest.get("runtime_files")
    test_source = source_files.get("tests/test_outputs.py")
    return (
        manifest.get("source_repository") == TERMINAL_BENCH_REPOSITORY
        and manifest.get("source_commit") == TERMINAL_BENCH_COMMIT
        and manifest.get("source_task_name") == TERMINAL_BENCH_TASK
        and runtime_files == TERMINAL_BENCH_RUNTIME_FILE_DIGESTS
        and type(test_source) is dict
        and test_source.get("sha256") == record.source_task_sha256
        and record.source_task_sha256 == TERMINAL_BENCH_SOURCE_TASK_SHA256
    )


def _validate_fixture_artifacts(
    record: HarborReplayRecord,
    contents: dict[str, bytes],
    job_config: JsonObject,
) -> bool:
    if record.normalized_task_sha256 != TERMINAL_BENCH_NORMALIZED_TASK_SHA256:
        return False
    for artifact_name, relative_path in _FIXTURE_ARTIFACT_TO_PATH.items():
        content = contents.get(artifact_name)
        expected = TERMINAL_BENCH_RUNTIME_FILE_DIGESTS.get(relative_path)
        if content is None or expected is None:
            return False
        if "sha256:" + hashlib.sha256(content).hexdigest() != expected:
            return False
    inventory = _decode_object(contents.get("fixture_inventory"))
    if inventory is None or set(inventory) != _FIXTURE_INVENTORY_FIELDS:
        return False
    if inventory.get("schema") != _FIXTURE_INVENTORY_SCHEMA:
        return False
    tasks = job_config.get("tasks")
    if (
        type(tasks) is not list
        or len(tasks) != 1
        or type(tasks[0]) is not dict
        or set(tasks[0]) != {"path"}
        or type(tasks[0]["path"]) is not str
        or not tasks[0]["path"]
        or inventory.get("task_path") != tasks[0]["path"]
    ):
        return False
    files = inventory.get("files")
    if type(files) is not dict or set(files) != set(_EXPECTED_FIXTURE_FILE_DIGESTS):
        return False
    artifact_for_path = {
        "source-manifest.json": "source_manifest",
        **{
            relative_path: artifact_name
            for artifact_name, relative_path in _FIXTURE_ARTIFACT_TO_PATH.items()
        },
    }
    for relative_path, expected_digest in _EXPECTED_FIXTURE_FILE_DIGESTS.items():
        entry = files.get(relative_path)
        if type(entry) is not dict or set(entry) != _FIXTURE_FILE_FIELDS:
            return False
        artifact_name = artifact_for_path[relative_path]
        content = contents.get(artifact_name)
        mode = entry.get("mode")
        if (
            content is None
            or entry.get("sha256") != expected_digest
            or entry.get("bytes") != len(content)
            or type(mode) is not str
            or re.fullmatch(r"[0-7]{4}", mode) is None
        ):
            return False
    task_toml = contents.get("task_toml")
    if task_toml is None:
        return False
    try:
        task = tomllib.loads(task_toml.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    environment = task.get("environment")
    agent = task.get("agent")
    verifier = task.get("verifier")
    return (
        type(environment) is dict
        and environment.get("network_mode") == "no-network"
        and type(agent) is dict
        and agent.get("network_mode") == "no-network"
        and type(verifier) is dict
        and verifier.get("network_mode") == "no-network"
        and verifier.get("environment_mode") == "shared"
    )


def _validate_verifier_artifacts(
    record: HarborReplayRecord,
    reward_content: bytes | None,
    result_content: bytes | None,
) -> bool:
    if reward_content in {None, b""} and result_content in {None, b""}:
        return (
            record.exception_discriminant == "agent_timeout_exact"
            and record.harbor_status == "exception"
            and record.observed_reward is None
        )
    result = _decode_object(result_content)
    if result is None or set(result) != _VERIFIER_RESULT_FIELDS:
        return False
    if (
        result.get("schema") != _VERIFIER_RESULT_SCHEMA
        or result.get("test_source_sha256") != TERMINAL_BENCH_SOURCE_TASK_SHA256
        or (
            result.get("exception_type_or_null") is not None
            and type(result.get("exception_type_or_null")) is not str
        )
        or (
            result.get("exception_message_or_null") is not None
            and type(result.get("exception_message_or_null")) is not str
        )
    ):
        return False
    kind = result.get("kind")
    if kind not in {"functional_pass", "functional_assertion", "harness_infra"}:
        return False
    if reward_content in {None, b""}:
        reward = None
    else:
        reward_value = _decode_object(reward_content)
        if (
            reward_value is None
            or set(reward_value) != {"reward"}
            or type(reward_value.get("reward")) is not int
            or reward_value["reward"] not in {0, 1}
        ):
            return False
        reward = reward_value["reward"]
    if reward != record.observed_reward:
        return False
    if reward == 1:
        return (
            kind == "functional_pass"
            and result["exception_type_or_null"] is None
            and result["exception_message_or_null"] is None
        )
    if reward == 0:
        return kind == "functional_assertion" and isinstance(
            result["exception_type_or_null"], str
        )
    return kind == "harness_infra" and isinstance(result["exception_type_or_null"], str)


def _validate_record(record: HarborReplayRecord) -> None:
    if type(record.stage_timings) is not dict:
        raise AdapterContractError("stage_timings must be an exact dict")
    if type(record.stage_obligations) is not dict:
        raise AdapterContractError("stage_obligations must be an exact dict")
    if type(record.artifacts) is not dict or type(record.artifact_sha256) is not dict:
        raise AdapterContractError("artifacts must be exact dicts")
    if type(record.cleanup_obligations) is not dict:
        raise AdapterContractError("cleanup_obligations must be an exact dict")
    if record.version != HARBOR_RECORD_VERSION:
        raise AdapterContractError(f"version must be exactly {HARBOR_RECORD_VERSION}")
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
        "egress_sidecar_image_id",
    ):
        if not _DIGEST.fullmatch(getattr(record, name)):
            raise AdapterContractError(f"{name} must be a sha256 digest")
    _image_reference(
        record.environment_image_ref,
        "environment_image_ref",
        record.environment_image_id,
    )
    _image_reference(
        record.egress_sidecar_image_ref,
        "egress_sidecar_image_ref",
        record.egress_sidecar_image_id,
    )
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
    if record.exception_discriminant is not None and not isinstance(
        record.exception_discriminant, str
    ):
        raise AdapterContractError("exception discriminant must be a string or None")
    if (
        record.exception_discriminant is not None
        and record.exception_discriminant not in _EXCEPTION_DISCRIMINANTS
    ):
        raise AdapterContractError("exception discriminant is invalid")
    if (
        record.exception_stage is not None
        and record.exception_stage not in _EXCEPTION_STAGES
    ):
        raise AdapterContractError("exception stage is invalid")
    if set(record.artifacts) != set(record.artifact_sha256):
        raise AdapterContractError("artifact and digest keys differ")
    if not set(record.artifacts).issubset(HARBOR_ARTIFACT_FIELDS):
        raise AdapterContractError("artifact fields differ")
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
    if set(record.stage_obligations) != _STAGE_FIELDS:
        raise AdapterContractError("stage obligation fields differ")
    if any(type(value) is not bool for value in record.stage_obligations.values()):
        raise AdapterContractError("stage obligations must be exact booleans")
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


def _image_reference(value: object, label: str, image_id: object) -> str:
    reference = _bounded_string(value, label)
    digest = _bounded_string(image_id, f"{label}.id")
    if not _DIGEST.fullmatch(digest):
        raise AdapterContractError(f"{label}.id must be a sha256 digest")
    if "@" not in reference or reference.rsplit("@", 1)[1] != digest:
        raise AdapterContractError(f"{label} must be bound to its image digest")
    if _DOCKER_IMAGE_REFERENCE.fullmatch(reference) is None:
        raise AdapterContractError(f"{label} must be a valid Docker reference")
    return reference


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
