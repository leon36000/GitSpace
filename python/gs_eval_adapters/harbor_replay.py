from __future__ import annotations

import hashlib
import json
import posixpath
import re
import tomllib
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import cast
from urllib.parse import unquote, urlparse

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
    "sha256:dd86c081c48cc81b0d472122f791786d86bd6d2c9615948e8b32b3fdfafcf194"
)
HARBOR_ENVIRONMENT_IMPORT_PATH = (
    "gs_eval_adapters.harbor_runtime:GitSpaceHarborEnvironment"
)
_DIGEST_PREFIX = "sha256:"
_SOURCE_MANIFEST_PATH = "source-manifest.json"
_TEST_OUTPUTS_PATH = "tests/test_outputs.py"
TERMINAL_BENCH_RUNTIME_FILE_DIGESTS = {
    "task.toml": "sha256:eb71853de4f613a6ad4e2650f12c9d5af39908b20082f6206c3378d5f67538d7",
    "instruction.md": "sha256:4f7ac05e70cf9220ea0f1e5a052c5f908cd0fa884e847d80b0bd51bae2e96f9c",
    "solution/solve.sh": "sha256:7e670d4f2b4bccb1e4db38f2a173e085ceda028c38167912b466b0a84fcc0999",
    _TEST_OUTPUTS_PATH: "sha256:345c3bd09ab6f6fe8c8361a58c0a47bf0a13b3fcb38a5ac7824e44ff855e8f72",
    "tests/run_test.py": "sha256:249dd2c3896af27b943c4eb7df6d3026da388be064c940a05c812d9b2d99dcce",
    "tests/test.sh": "sha256:4bea61a4c4c3787a3b97ef62a98437e854c91172cd8d4b184460d387a6165f71",
    "environment/Dockerfile": "sha256:d8f1d7d34c169daa44b338e066cfc69c7d6808eb65e093bb91e06f4c6133c3a2",
}
TERMINAL_BENCH_FIXTURE_FILE_MODES = {
    _SOURCE_MANIFEST_PATH: "0644",
    **dict.fromkeys(TERMINAL_BENCH_RUNTIME_FILE_DIGESTS, "0644"),
}
_FIXTURE_ARTIFACT_TO_PATH = {
    "task_toml": "task.toml",
    "instruction_md": "instruction.md",
    "solution_solve_sh": "solution/solve.sh",
    "test_source": _TEST_OUTPUTS_PATH,
    "verifier_script": "tests/run_test.py",
    "verifier_test_script": "tests/test.sh",
    "environment_dockerfile": "environment/Dockerfile",
}
_EXPECTED_FIXTURE_FILE_DIGESTS = {
    _SOURCE_MANIFEST_PATH: TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
    **TERMINAL_BENCH_RUNTIME_FILE_DIGESTS,
}

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_DOCKER_NAME_COMPONENT = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*"
_DOCKER_DOMAIN_COMPONENT = r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
_DOCKER_DOMAIN = (
    rf"{_DOCKER_DOMAIN_COMPONENT}(?:\.{_DOCKER_DOMAIN_COMPONENT})*(?::[0-9]+)?"
)
_DOCKER_TAG = r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}"
_DOCKER_IMAGE_REFERENCE = re.compile(
    rf"^(?:(?:{_DOCKER_DOMAIN})/)?"
    rf"{_DOCKER_NAME_COMPONENT}(?:/{_DOCKER_NAME_COMPONENT})*"
    rf"(?::{_DOCKER_TAG})?@sha256:[0-9a-f]{{64}}$"
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
_TRIAL_RESULT_CONFIG_FIELDS = {
    "task",
    "trial_name",
    "trials_dir",
    "install_only",
    "timeout_multiplier",
    "agent_timeout_multiplier",
    "verifier_timeout_multiplier",
    "agent_setup_timeout_multiplier",
    "environment_build_timeout_multiplier",
    "agent",
    "environment",
    "verifier",
    "artifacts",
    "extra_instruction_paths",
    "job_id",
    "source_trial",
}
_TRIAL_RESULT_TASK_FIELDS = {
    "path",
    "git_url",
    "git_commit_id",
    "name",
    "ref",
    "overwrite",
    "download_dir",
    "source",
}
_TRIAL_RESULT_AGENT_FIELDS = {
    "name",
    "import_path",
    "model_name",
    "n_concurrent",
    "concurrency_group",
    "skills",
    "override_timeout_sec",
    "override_setup_timeout_sec",
    "max_timeout_sec",
    "resume_trajectory",
    "load_trajectory",
    "extra_allowed_hosts",
    "kwargs",
    "mcp_servers",
}
_TRIAL_RESULT_ENVIRONMENT_FIELDS = {
    "type",
    "import_path",
    "force_build",
    "delete",
    "cpu_enforcement_policy",
    "memory_enforcement_policy",
    "override_cpus",
    "override_memory_mb",
    "override_storage_mb",
    "override_gpus",
    "override_tpu",
    "mounts",
    "extra_docker_compose",
    "kwargs",
    "extra_allowed_hosts",
}
_TRIAL_RESULT_VERIFIER_FIELDS = {"override_timeout_sec", "max_timeout_sec", "disable"}
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
        digest = _DIGEST_PREFIX + hashlib.sha256(content).hexdigest()
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
        _DIGEST_PREFIX + hashlib.sha256(canonical_record_bytes(record)).hexdigest()
    )
    obligations = dict.fromkeys(_OBLIGATION_FIELDS, False)
    obligations["qualification_pinned"] = _qualification_pinned(record)
    obligations["run_purpose_valid"] = _run_purpose_valid(record)
    obligations["process_exit_zero"] = record.harbor_process_return_code == 0
    obligations["oracle_exit_consistent"] = False
    obligations["policy_clear"] = (
        record.exception_discriminant != "policy_violation_exact"
    )
    artifact_contents, artifact_integrity = _read_record_artifacts(
        record, read_artifact
    )
    obligations["artifact_integrity"] = artifact_integrity
    if artifact_integrity:
        _validate_observed_artifacts(record, artifact_contents, obligations)

    status, task_invalid_candidate = _classify_record_status(record, obligations)

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


def _read_record_artifacts(
    record: HarborReplayRecord,
    read_artifact: Callable[[str], bytes] | None,
) -> tuple[dict[str, bytes], bool]:
    if read_artifact is None:
        return {}, False
    if not _required_artifact_fields(record).issubset(record.artifacts):
        return {}, False
    artifact_contents: dict[str, bytes] = {}
    for name, uri in record.artifacts.items():
        try:
            content = read_artifact(uri)
        except Exception:  # noqa: BLE001 - unreadable CAS is an infra outcome
            return artifact_contents, False
        if type(content) is not bytes:
            return artifact_contents, False
        expected_digest = record.artifact_sha256[name].removeprefix(_DIGEST_PREFIX)
        if hashlib.sha256(content).hexdigest() != expected_digest:
            return artifact_contents, False
        artifact_contents[name] = content
    return artifact_contents, True


def _classify_record_status(
    record: HarborReplayRecord, obligations: dict[str, bool]
) -> tuple[AdapterStatus, bool]:
    if _record_infra_obligation_failed(obligations):
        return AdapterStatus.INFRA, False
    if not obligations["policy_clear"]:
        return AdapterStatus.POLICY, False
    if not obligations["process_exit_zero"]:
        return AdapterStatus.INFRA, False
    if not obligations["oracle_exit_consistent"]:
        return AdapterStatus.INFRA, record.run_purpose == "qualification_oracle"
    if _record_execution_obligation_failed(obligations):
        return AdapterStatus.INFRA, False
    if record.exception_discriminant == "agent_timeout_exact":
        obligations["timeout_attribution_valid"] = _timeout_attribution_valid(record)
        status = (
            AdapterStatus.TIMEOUT
            if obligations["timeout_attribution_valid"]
            else AdapterStatus.INFRA
        )
        return status, False
    if _record_exception_observed(record):
        return AdapterStatus.INFRA, False
    if record.run_purpose == "qualification_oracle" and record.observed_reward == 0:
        return AdapterStatus.INFRA, True
    if record.observed_reward == 1:
        return AdapterStatus.PASS, False
    if record.run_purpose == "status_control" and record.observed_reward == 0:
        return AdapterStatus.FAIL, False
    return AdapterStatus.INFRA, False


def _record_infra_obligation_failed(obligations: dict[str, bool]) -> bool:
    return (
        not obligations["artifact_integrity"]
        or not obligations["qualification_pinned"]
        or not obligations["run_purpose_valid"]
        or not obligations["exception_boundary_consistent"]
        or not obligations["trial_exception_consistent"]
    )


def _record_execution_obligation_failed(obligations: dict[str, bool]) -> bool:
    return (
        not obligations["network_closed"]
        or not obligations["job_cardinality_one"]
        or not obligations["trial_cardinality_one"]
        or not obligations["reward_well_typed"]
        or not obligations["cleanup_complete"]
        or not obligations["stage_obligations_consistent"]
    )


def _record_exception_observed(record: HarborReplayRecord) -> bool:
    return (
        record.exception_discriminant is not None
        or record.harbor_status == "exception"
        or record.observed_reward is None
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
        and is_digest_bound_docker_reference(reference)
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


def _is_exact_one_float(value: object) -> bool:
    return type(value) is float and value.as_integer_ratio() == (1, 1)


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
    values = dict.fromkeys(_STAGE_FIELDS, False)
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
    decoded = _decode_required_artifacts(contents)
    if decoded is None:
        return
    job_config, job_result, trial_config, trial_result = decoded

    _set_observed_execution_obligations(
        record, job_config, job_result, trial_config, trial_result, obligations
    )
    _set_observed_cleanup_obligations(record, contents, job_config, obligations)
    obligations["oracle_exit_consistent"] = _oracle_exit_status_consistent(
        record, contents.get("oracle_exit_status")
    )

    obligations["reward_well_typed"] = _validate_verifier_artifacts(
        record,
        contents.get("verifier_reward_json"),
        contents.get("verifier_result_json"),
    )
    obligations["exception_boundary_consistent"] = (
        _exception_boundary_consistent(
            record, contents.get("exception_boundary")
        )
    )


def _decode_required_artifacts(
    contents: dict[str, bytes],
) -> tuple[JsonObject, JsonObject, JsonObject, JsonObject] | None:
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
        return None
    return job_config, job_result, trial_config, trial_result


def _set_observed_execution_obligations(
    record: HarborReplayRecord,
    job_config: JsonObject,
    job_result: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
    obligations: dict[str, bool],
) -> None:
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


def _set_observed_cleanup_obligations(
    record: HarborReplayRecord,
    contents: dict[str, bytes],
    job_config: JsonObject,
    obligations: dict[str, bool],
) -> None:
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


def _oracle_exit_status_consistent(
    record: HarborReplayRecord, content: bytes | None
) -> bool:
    if content is None:
        return False
    try:
        value = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if type(value) is not dict or set(value) != {"present", "value"}:
        return False
    present = value["present"]
    exit_value = value["value"]
    if type(present) is not bool:
        return False
    if not present:
        return exit_value is None and record.oracle_exit_code is None
    if type(exit_value) is not int or record.oracle_exit_code != exit_value:
        return False
    return record.oracle_exit_code in {None, 0}


def _exception_boundary_consistent(
    record: HarborReplayRecord, content: bytes | None
) -> bool:
    if content is None or content == b"":
        return False
    try:
        boundary = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if type(boundary) is not dict or set(boundary) != {"discriminant", "stage"}:
        return False
    discriminant = boundary["discriminant"]
    stage = boundary["stage"]
    if discriminant != record.exception_discriminant or stage != record.exception_stage:
        return False
    return (
        (discriminant is None or type(discriminant) is str)
        and (stage is None or type(stage) is str)
    )


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
    return _job_cardinality_valid(job), _job_network_closed(record, job)


def _job_cardinality_valid(job: JsonObject) -> bool:
    return (
        _job_attempts_and_retry_valid(job)
        and _job_agent_cardinality_valid(job)
        and _job_task_cardinality_valid(job)
        and _job_runtime_defaults_valid(job)
    )


def _job_attempts_and_retry_valid(job: JsonObject) -> bool:
    attempts = job.get("n_attempts", 1)
    concurrent = job.get("n_concurrent_trials")
    retry = job.get("retry", {"max_retries": 0})
    return (
        type(attempts) is int
        and attempts == 1
        and type(concurrent) is int
        and concurrent == 1
        and type(retry) is dict
        and set(retry) == {"max_retries"}
        and type(retry.get("max_retries")) is int
        and retry["max_retries"] == 0
    )


def _job_agent_cardinality_valid(job: JsonObject) -> bool:
    agents = job.get("agents")
    if type(agents) is not list or len(agents) != 1 or type(agents[0]) is not dict:
        return False
    agent = agents[0]
    return (
        set(agent) == {"name", "n_concurrent"}
        and agent.get("name") == "oracle"
        and type(agent.get("n_concurrent")) is int
        and agent["n_concurrent"] == 1
    )


def _job_task_cardinality_valid(job: JsonObject) -> bool:
    if job.get("datasets", []) != []:
        return False
    tasks = job.get("tasks")
    if type(tasks) is not list or len(tasks) != 1 or type(tasks[0]) is not dict:
        return False
    task = tasks[0]
    return (
        set(task) == {"path"}
        and type(task["path"]) is str
        and bool(task["path"])
    )


def _job_runtime_defaults_valid(job: JsonObject) -> bool:
    return (
        job.get("job_name") == "gitspace-p00-task-012-oracle"
        and _job_directory_default_valid(job)
        and _job_boolean_defaults_valid(job)
        and _job_timeout_defaults_valid(job)
        and _job_collection_defaults_valid(job)
    )


def _job_directory_default_valid(job: JsonObject) -> bool:
    return "jobs_dir" not in job or (
        type(job["jobs_dir"]) is str and bool(job["jobs_dir"])
    )


def _job_boolean_defaults_valid(job: JsonObject) -> bool:
    return (
        job.get("install_only", False) is False
        and job.get("debug", False) is False
        and job.get("quiet", False) is False
        and job.get("verifier") is None
        and job.get("source_jobs") is None
    )


def _job_timeout_defaults_valid(job: JsonObject) -> bool:
    return (
        _is_exact_one_float(job.get("timeout_multiplier", 1.0))
        and job.get("agent_timeout_multiplier") is None
        and job.get("verifier_timeout_multiplier") is None
        and job.get("agent_setup_timeout_multiplier") is None
        and job.get("environment_build_timeout_multiplier") is None
    )


def _job_collection_defaults_valid(job: JsonObject) -> bool:
    return job.get("metrics", []) == [] and job.get("artifacts", []) == [] and job.get(
        "extra_instruction_paths", []
    ) == []


def _job_network_closed(record: HarborReplayRecord, job: JsonObject) -> bool:
    environment = job.get("environment")
    if type(environment) is not dict or set(environment) != {"import_path", "kwargs"}:
        return False
    if environment.get("import_path") != HARBOR_ENVIRONMENT_IMPORT_PATH:
        return False
    return _job_image_kwargs_match(record, environment.get("kwargs"))


def _job_image_kwargs_match(record: HarborReplayRecord, value: object) -> bool:
    if type(value) is not dict:
        return False
    if set(value) != {
        "gitspace_environment_image_ref",
        "gitspace_environment_image_id",
        "gitspace_egress_sidecar_image_ref",
        "gitspace_egress_sidecar_image_id",
    }:
        return False
    return (
        value.get("gitspace_environment_image_ref") == record.environment_image_ref
        and value.get("gitspace_environment_image_id") == record.environment_image_id
        and value.get("gitspace_egress_sidecar_image_ref")
        == record.egress_sidecar_image_ref
        and value.get("gitspace_egress_sidecar_image_id")
        == record.egress_sidecar_image_id
        and _image_reference_matches(
            record.environment_image_ref, record.environment_image_id
        )
        and _image_reference_matches(
            record.egress_sidecar_image_ref, record.egress_sidecar_image_id
        )
    )


def _validate_trial_artifacts(
    record: HarborReplayRecord,
    job_result: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
    job_config: JsonObject,
) -> tuple[bool, bool]:
    summary_id = _job_result_trial_summary_id(job_result)
    if summary_id is False:
        return False, False
    config_identity_valid = _validate_effective_trial_config(
        record, job_config, trial_config, trial_result
    )
    cardinality_valid = (
        (summary_id is None or summary_id == record.trial_id)
        and job_result.get("id") == record.job_id
        and trial_result.get("id") == record.trial_id
        and trial_result.get("task_name") == record.task_name
        and config_identity_valid
    )
    return cardinality_valid, _trial_exception_consistent(record, trial_result)


def _job_result_trial_summary_id(job_result: JsonObject) -> str | bool | None:
    """Return a legacy trial id, ``None`` for Harbor 0.21 aggregate results."""

    if (
        type(job_result.get("n_total_trials")) is not int
        or job_result["n_total_trials"] != 1
    ):
        return False
    if "trial_results" in job_result:
        trial_results = job_result["trial_results"]
        if (
            type(trial_results) is not list
            or len(trial_results) != 1
            or type(trial_results[0]) is not dict
        ):
            return False
        summary = trial_results[0]
        summary_id = summary.get("id")
        return summary_id if type(summary_id) is str and summary_id else False

    stats = job_result.get("stats")
    if type(stats) is not dict:
        return False
    completed = stats.get("n_completed_trials")
    errored = stats.get("n_errored_trials")
    running = stats.get("n_running_trials")
    pending = stats.get("n_pending_trials")
    cancelled = stats.get("n_cancelled_trials")
    counts = {
        "n_completed_trials": completed,
        "n_errored_trials": errored,
        "n_running_trials": running,
        "n_pending_trials": pending,
        "n_cancelled_trials": cancelled,
    }
    if any(type(value) is not int or value < 0 for value in counts.values()):
        return False
    retries = stats.get("n_retries")
    if (
        type(retries) is not int
        or retries < 0
        or completed != 1
        or running != 0
        or pending != 0
        or type(errored) is not int
        or type(cancelled) is not int
        or errored > completed
        or cancelled > errored
        or retries != 0
        or type(stats.get("evals")) is not dict
    ):
        return False
    return None


def _validate_effective_trial_config(
    record: HarborReplayRecord,
    job_config: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
) -> bool:
    if set(trial_config) != _TRIAL_EFFECTIVE_FIELDS:
        return False
    return (
        _trial_task_identity_valid(job_config, trial_config)
        and _trial_config_identity_valid(record, job_config, trial_config, trial_result)
        and _trial_uri_valid(trial_config, trial_result)
        and _trial_agent_valid(trial_config)
        and _validate_environment_extension(trial_config.get("environment"), record)
        and _validate_trial_result_config(
            trial_result.get("config"), trial_config, record
        )
    )


def _trial_task_identity_valid(
    job_config: JsonObject, trial_config: JsonObject
) -> bool:
    job_tasks = job_config.get("tasks")
    task = trial_config.get("task")
    return not (
        type(job_tasks) is not list
        or len(job_tasks) != 1
        or type(job_tasks[0]) is not dict
        or set(job_tasks[0]) != {"path"}
        or type(job_tasks[0]["path"]) is not str
        or type(task) is not dict
        or set(task) != {"path"}
        or task.get("path") != job_tasks[0]["path"]
    )


def _trial_config_identity_valid(
    record: HarborReplayRecord,
    job_config: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
) -> bool:
    trial_name = trial_config.get("trial_name")
    validated_trial_name = _posix_component(trial_name)
    if (
        validated_trial_name is None
        or trial_name == record.trial_id
        or trial_result.get("trial_name") != trial_name
    ):
        return False
    trials_dir = trial_config.get("trials_dir")
    trials_path = _absolute_posix_path(trials_dir)
    if trials_path is None:
        return False
    jobs_dir = job_config.get("jobs_dir")
    job_name = job_config.get("job_name")
    if jobs_dir is not None:
        jobs_path = _absolute_posix_path(jobs_dir)
        validated_job_name = _posix_component(job_name)
        if (
            jobs_path is None
            or validated_job_name is None
            or trials_path != posixpath.join(jobs_path, validated_job_name)
        ):
            return False
    if trial_config.get("job_id") != record.job_id:
        return False
    return True


def _trial_uri_valid(
    trial_config: JsonObject, trial_result: JsonObject
) -> bool:
    trial_name = _posix_component(trial_config.get("trial_name"))
    trials_path = _absolute_posix_path(trial_config.get("trials_dir"))
    if trial_name is None or trials_path is None:
        return False
    trial_uri = trial_result.get("trial_uri")
    if type(trial_uri) is not str or any(
        ord(character) <= 32
        or ord(character) == 127
        or character.isspace()
        for character in trial_uri
    ):
        return False
    try:
        parsed_uri = urlparse(trial_uri)
    except ValueError:
        return False
    if (
        parsed_uri.scheme != "file"
        or parsed_uri.netloc not in {"", "localhost"}
        or parsed_uri.params
        or parsed_uri.query
        or parsed_uri.fragment
    ):
        return False
    trial_dir = _absolute_posix_path(unquote(parsed_uri.path))
    if (
        trial_dir is None
        or trial_dir != posixpath.join(trials_path, trial_name)
    ):
        return False
    return True


def _trial_agent_valid(trial_config: JsonObject) -> bool:
    agent = trial_config.get("agent")
    return not (
        type(agent) is not dict
        or set(agent) != {"name", "n_concurrent"}
        or agent.get("name") != "oracle"
        or type(agent.get("n_concurrent")) is not int
        or agent["n_concurrent"] != 1
    )


def _absolute_posix_path(value: object) -> str | None:
    """Normalize a fixture path without consulting the host filesystem."""

    if type(value) is not str or not value.startswith("/"):
        return None
    text = cast(str, value)
    if "\\" in text or "\x00" in text:
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        return None
    return posixpath.normpath(text)


def _posix_component(value: object) -> str | None:
    if type(value) is not str or not value or value in {".", ".."}:
        return None
    text = cast(str, value)
    if "/" in text or "\\" in text or "\x00" in text:
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in text):
        return None
    return text


def _validate_trial_result_config(
    value: object, trial_config: JsonObject, record: HarborReplayRecord
) -> bool:
    if type(value) is not dict or set(value) != _TRIAL_RESULT_CONFIG_FIELDS:
        return False
    if (
        value.get("trial_name") != trial_config.get("trial_name")
        or value.get("trials_dir") != trial_config.get("trials_dir")
        or value.get("job_id") != record.job_id
        or value.get("install_only") is not False
        or not _is_exact_one_float(value.get("timeout_multiplier"))
        or value.get("agent_timeout_multiplier") is not None
        or value.get("verifier_timeout_multiplier") is not None
        or value.get("agent_setup_timeout_multiplier") is not None
        or value.get("environment_build_timeout_multiplier") is not None
        or value.get("artifacts") != []
        or value.get("extra_instruction_paths") != []
        or value.get("source_trial") is not None
    ):
        return False
    trial_task = trial_config.get("task")
    trial_task_path = (
        trial_task.get("path") if type(trial_task) is dict else None
    )
    if type(trial_task_path) is not str:
        return False
    task = value.get("task")
    if (
        type(task) is not dict
        or set(task) != _TRIAL_RESULT_TASK_FIELDS
        or task.get("path") != trial_task_path
        or task.get("git_url") is not None
        or task.get("git_commit_id") is not None
        or task.get("name") is not None
        or task.get("ref") is not None
        or task.get("overwrite") is not False
        or task.get("download_dir") is not None
        or task.get("source") is not None
    ):
        return False
    agent = value.get("agent")
    if (
        type(agent) is not dict
        or set(agent) != _TRIAL_RESULT_AGENT_FIELDS
        or agent.get("name") != "oracle"
        or agent.get("import_path") is not None
        or agent.get("model_name") is not None
        or type(agent.get("n_concurrent")) is not int
        or agent.get("n_concurrent") != 1
        or agent.get("concurrency_group") is not None
        or agent.get("skills") != []
        or agent.get("override_timeout_sec") is not None
        or agent.get("override_setup_timeout_sec") is not None
        or agent.get("max_timeout_sec") is not None
        or agent.get("resume_trajectory") is not False
        or agent.get("load_trajectory") is not None
        or agent.get("extra_allowed_hosts") != []
        or agent.get("kwargs") != {}
        or agent.get("mcp_servers") != []
    ):
        return False
    environment = value.get("environment")
    if (
        type(environment) is not dict
        or set(environment) != _TRIAL_RESULT_ENVIRONMENT_FIELDS
        or environment.get("type") is not None
        or environment.get("import_path") != HARBOR_ENVIRONMENT_IMPORT_PATH
        or environment.get("force_build") is not False
        or environment.get("delete") is not True
        or environment.get("cpu_enforcement_policy") != "auto"
        or environment.get("memory_enforcement_policy") != "auto"
        or environment.get("override_cpus") is not None
        or environment.get("override_memory_mb") is not None
        or environment.get("override_storage_mb") is not None
        or environment.get("override_gpus") is not None
        or environment.get("override_tpu") is not None
        or environment.get("mounts") is not None
        or environment.get("extra_docker_compose") != []
        or environment.get("extra_allowed_hosts") != []
        or not _validate_environment_kwargs(environment.get("kwargs"), record)
    ):
        return False
    verifier = value.get("verifier")
    return (
        type(verifier) is dict
        and set(verifier) == _TRIAL_RESULT_VERIFIER_FIELDS
        and verifier.get("override_timeout_sec") is None
        and verifier.get("max_timeout_sec") is None
        and verifier.get("disable") is False
    )


def _validate_environment_extension(value: object, record: HarborReplayRecord) -> bool:
    if type(value) is not dict or set(value) != {"import_path", "kwargs"}:
        return False
    return (
        value.get("import_path") == HARBOR_ENVIRONMENT_IMPORT_PATH
        and _validate_environment_kwargs(value.get("kwargs"), record)
    )


def _validate_environment_kwargs(value: object, record: HarborReplayRecord) -> bool:
    if type(value) is not dict:
        return False
    return (
        set(value)
        == {
            "gitspace_environment_image_ref",
            "gitspace_environment_image_id",
            "gitspace_egress_sidecar_image_ref",
            "gitspace_egress_sidecar_image_id",
        }
        and value.get("gitspace_environment_image_ref")
        == record.environment_image_ref
        and value.get("gitspace_environment_image_id") == record.environment_image_id
        and value.get("gitspace_egress_sidecar_image_ref")
        == record.egress_sidecar_image_ref
        and value.get("gitspace_egress_sidecar_image_id")
        == record.egress_sidecar_image_id
    )


def _trial_exception_consistent(
    record: HarborReplayRecord, trial_result: JsonObject
) -> bool:
    exception_info = trial_result.get("exception_info")
    raw_stage = trial_result.get("exception_stage")
    if record.harbor_status == "completed":
        return _completed_trial_exception_consistent(record, exception_info, raw_stage)
    if record.harbor_status != "exception" or type(exception_info) is not dict:
        return False
    return _exception_details_consistent(record, exception_info, raw_stage)


def _completed_trial_exception_consistent(
    record: HarborReplayRecord,
    exception_info: object,
    raw_stage: object,
) -> bool:
    return (
        exception_info is None
        and raw_stage is None
        and record.exception_discriminant is None
        and record.exception_type_diagnostic is None
        and record.exception_stage is None
    )


def _exception_details_consistent(
    record: HarborReplayRecord,
    exception_info: dict[str, JsonValue],
    raw_stage: object,
) -> bool:
    observed_type = exception_info.get("exception_type")
    if type(observed_type) is not str or not observed_type:
        return False
    observed_stage = _observed_exception_stage(record, raw_stage)
    if observed_stage is None:
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


def _observed_exception_stage(
    record: HarborReplayRecord, raw_stage: object
) -> str | None:
    if raw_stage is None:
        return (
            record.exception_stage
            if record.exception_discriminant is not None
            and record.exception_stage in _EXCEPTION_STAGES
            else "unknown"
        )
    if type(raw_stage) is str and raw_stage in _EXCEPTION_STAGES:
        return raw_stage
    return None


def _validate_runtime_manifests(
    record: HarborReplayRecord,
    before: JsonObject | None,
    after: JsonObject | None,
) -> tuple[bool, bool, dict[str, bool]]:
    empty_cleanup = dict.fromkeys(_CLEANUP_FIELDS, False)
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
    return _DIGEST_PREFIX + hashlib.sha256(encoded).hexdigest()


def _resource_map(value: object) -> dict[tuple[str, str, str], JsonObject] | None:
    if type(value) is not list:
        return None
    resources: dict[tuple[str, str, str], JsonObject] = {}
    for item in cast(list[object], value):
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
        TERMINAL_BENCH_NORMALIZED_TASK_SHA256.removeprefix(_DIGEST_PREFIX)
    ):
        return False
    manifest = _decode_object(content)
    if manifest is None:
        return False
    source_files = manifest.get("source_files")
    if type(source_files) is not dict:
        return False
    runtime_files = manifest.get("runtime_files")
    test_source = source_files.get(_TEST_OUTPUTS_PATH)
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
    return (
        record.normalized_task_sha256 == TERMINAL_BENCH_NORMALIZED_TASK_SHA256
        and _fixture_runtime_artifacts_valid(contents)
        and _fixture_inventory_valid(contents, job_config)
        and _fixture_task_config_valid(contents.get("task_toml"))
    )


def _fixture_runtime_artifacts_valid(contents: dict[str, bytes]) -> bool:
    for artifact_name, relative_path in _FIXTURE_ARTIFACT_TO_PATH.items():
        content = contents.get(artifact_name)
        expected = TERMINAL_BENCH_RUNTIME_FILE_DIGESTS.get(relative_path)
        if content is None or expected is None:
            return False
        if _DIGEST_PREFIX + hashlib.sha256(content).hexdigest() != expected:
            return False
    return True


def _fixture_inventory_valid(
    contents: dict[str, bytes], job_config: JsonObject
) -> bool:
    inventory = _decode_object(contents.get("fixture_inventory"))
    if inventory is None or not _fixture_inventory_header_valid(inventory):
        return False
    if not _fixture_inventory_task_valid(inventory, job_config):
        return False
    return _fixture_inventory_files_valid(inventory, contents)


def _fixture_inventory_header_valid(inventory: JsonObject | None) -> bool:
    return (
        inventory is not None
        and set(inventory) == _FIXTURE_INVENTORY_FIELDS
        and inventory.get("schema") == _FIXTURE_INVENTORY_SCHEMA
    )


def _fixture_inventory_task_valid(
    inventory: JsonObject, job_config: JsonObject
) -> bool:
    tasks = job_config.get("tasks")
    if type(tasks) is not list or len(tasks) != 1 or type(tasks[0]) is not dict:
        return False
    task = tasks[0]
    return (
        set(task) == {"path"}
        and type(task["path"]) is str
        and bool(task["path"])
        and inventory.get("task_path") == task["path"]
    )


def _fixture_inventory_files_valid(
    inventory: JsonObject, contents: dict[str, bytes]
) -> bool:
    files = inventory.get("files")
    if type(files) is not dict or set(files) != set(_EXPECTED_FIXTURE_FILE_DIGESTS):
        return False
    artifact_for_path = _fixture_artifact_map()
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
            or mode != TERMINAL_BENCH_FIXTURE_FILE_MODES[relative_path]
        ):
            return False
    return True


def _fixture_artifact_map() -> dict[str, str]:
    artifact_for_path = {_SOURCE_MANIFEST_PATH: "source_manifest"}
    for artifact_name, relative_path in _FIXTURE_ARTIFACT_TO_PATH.items():
        artifact_for_path[relative_path] = artifact_name
    return artifact_for_path


def _fixture_task_config_valid(content: bytes | None) -> bool:
    if content is None:
        return False
    try:
        task = tomllib.loads(content.decode("utf-8"))
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
    if _verifier_artifacts_absent(reward_content, result_content):
        return _verifier_artifacts_absent_for_timeout(record)
    result = _decode_object(result_content)
    if result is None or not _verifier_result_valid(result):
        return False
    reward_valid, reward = _verifier_reward_value(reward_content)
    if not reward_valid or reward != record.observed_reward:
        return False
    return _verifier_outcome_valid(result, reward)


def _verifier_artifacts_absent(
    reward_content: bytes | None, result_content: bytes | None
) -> bool:
    return reward_content in {None, b""} and result_content in {None, b""}


def _verifier_artifacts_absent_for_timeout(record: HarborReplayRecord) -> bool:
    return (
        record.exception_discriminant == "agent_timeout_exact"
        and record.harbor_status == "exception"
        and record.observed_reward is None
    )


def _verifier_result_valid(result: JsonObject | None) -> bool:
    if result is None or set(result) != _VERIFIER_RESULT_FIELDS:
        return False
    if result.get("schema") != _VERIFIER_RESULT_SCHEMA:
        return False
    if result.get("test_source_sha256") != TERMINAL_BENCH_SOURCE_TASK_SHA256:
        return False
    if not _optional_string_value_valid(result.get("exception_type_or_null")):
        return False
    if not _optional_string_value_valid(result.get("exception_message_or_null")):
        return False
    return result.get("kind") in {
        "functional_pass",
        "functional_assertion",
        "harness_infra",
    }


def _optional_string_value_valid(value: object) -> bool:
    return value is None or type(value) is str


def _verifier_reward_value(value: bytes | None) -> tuple[bool, int | None]:
    if value in {None, b""}:
        return True, None
    reward_value = _decode_object(value)
    if reward_value is None or set(reward_value) != {"reward"}:
        return False, None
    reward = reward_value.get("reward")
    if type(reward) is not int or reward not in {0, 1}:
        return False, None
    return True, reward


def _verifier_outcome_valid(result: JsonObject, reward: int | None) -> bool:
    kind = result["kind"]
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
    _validate_record_shape(record)
    _validate_record_pins(record)
    _validate_record_runtime(record)
    _validate_record_exception_fields(record)
    _validate_record_artifacts(record)
    _validate_record_obligations(record)


def _validate_record_shape(record: HarborReplayRecord) -> None:
    if type(record.stage_timings) is not dict:
        raise AdapterContractError("stage_timings must be an exact dict")
    if type(record.stage_obligations) is not dict:
        raise AdapterContractError("stage_obligations must be an exact dict")
    if type(record.artifacts) is not dict or type(record.artifact_sha256) is not dict:
        raise AdapterContractError("artifacts must be exact dicts")
    if type(record.cleanup_obligations) is not dict:
        raise AdapterContractError("cleanup_obligations must be an exact dict")


def _validate_record_pins(record: HarborReplayRecord) -> None:
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


def _validate_record_runtime(record: HarborReplayRecord) -> None:
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


def _validate_record_exception_fields(record: HarborReplayRecord) -> None:
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


def _validate_record_artifacts(record: HarborReplayRecord) -> None:
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
        if uri != _CAS_URI_PREFIX + digest.removeprefix(_DIGEST_PREFIX):
            raise AdapterContractError(f"artifact URI and digest differ for {name}")


def _validate_record_obligations(record: HarborReplayRecord) -> None:
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
    text = cast(str, value)
    if any(unicodedata.category(char).startswith("C") for char in text):
        raise AdapterContractError(f"{label} contains control characters")
    return text


def _image_reference(value: object, label: str, image_id: object) -> str:
    reference = _bounded_string(value, label)
    digest = _bounded_string(image_id, f"{label}.id")
    if not _DIGEST.fullmatch(digest):
        raise AdapterContractError(f"{label}.id must be a sha256 digest")
    if "@" not in reference or reference.rsplit("@", 1)[1] != digest:
        raise AdapterContractError(f"{label} must be bound to its image digest")
    if not is_digest_bound_docker_reference(reference):
        raise AdapterContractError(f"{label} must be a valid Docker reference")
    return reference


def is_digest_bound_docker_reference(value: object) -> bool:
    return type(value) is str and _DOCKER_IMAGE_REFERENCE.fullmatch(value) is not None


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
