from __future__ import annotations

import asyncio
import hashlib
import json
import os
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Protocol
from urllib.parse import unquote, urlparse

from .errors import AdapterContractError
from .harbor_replay import (
    HARBOR_COMMIT,
    HARBOR_VERSION,
    HARBOR_WHEEL_SHA256,
    TERMINAL_BENCH_COMMIT,
    TERMINAL_BENCH_REPOSITORY,
    TERMINAL_BENCH_TASK,
    HarborReplayRecord,
    canonical_record_bytes,
    classify_harbor_record,
    project_harbor_capture,
)
from .json_boundary import JsonObject, JsonValue, clone_object, validate_cas_uri
from .model import AdapterDescriptor, AdapterStatus

_CAS_URI_PREFIX = "cas://sha256/"
_TASK_ID = "GS-TASK-000012"
_PROFILE_FIELDS = {
    "run_purpose",
    "source_task_sha256",
    "normalized_task_sha256",
    "environment_image_ref",
    "environment_image_id",
    "egress_sidecar_image_ref",
    "egress_sidecar_image_id",
}
_PREPARED_FIELDS = {"canonical_request", "framework_request", "extensions"}
_RAW_FIELDS = {"capture"}
_ARTIFACT_FIELDS = {
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
    "resource_manifest_before",
    "resource_manifest_after",
    "cleanup_report",
}
_DIGEST = "sha256:"


@dataclass(frozen=True, slots=True)
class HarborExecutionRequest:
    run_root: str
    fixture_root: str
    job_config: dict[str, JsonValue]
    environment_image_ref: str
    environment_image_id: str
    egress_sidecar_image_ref: str
    egress_sidecar_image_id: str

    def __post_init__(self) -> None:
        _bounded_string(self.run_root, "run_root")
        _bounded_string(self.fixture_root, "fixture_root")
        object.__setattr__(
            self, "job_config", clone_object(self.job_config, path="$/job_config")
        )
        _bounded_string(self.environment_image_ref, "environment_image_ref")
        _digest_string(self.environment_image_id, "environment_image_id")
        _bounded_string(self.egress_sidecar_image_ref, "egress_sidecar_image_ref")
        _digest_string(self.egress_sidecar_image_id, "egress_sidecar_image_id")


@dataclass(frozen=True, slots=True)
class HarborExecutionCapture:
    process_return_code: int
    harbor_stdout: bytes
    harbor_stderr: bytes
    job_config_bytes: bytes
    job_result_bytes: bytes
    trial_config_bytes: bytes
    trial_result_bytes: bytes
    agent_stdout: bytes
    agent_stderr: bytes
    oracle_exit_code_bytes: bytes | None
    verifier_stdout: bytes
    verifier_stderr: bytes
    verifier_reward_json_bytes: bytes | None
    resource_manifest_before_bytes: bytes
    resource_manifest_after_bytes: bytes
    cleanup_report_bytes: bytes

    def __post_init__(self) -> None:
        if type(self.process_return_code) is not int:
            raise AdapterContractError(
                "Harbor process return code must be an exact integer"
            )
        for name in (
            "harbor_stdout",
            "harbor_stderr",
            "job_config_bytes",
            "job_result_bytes",
            "trial_config_bytes",
            "trial_result_bytes",
            "agent_stdout",
            "agent_stderr",
            "verifier_stdout",
            "verifier_stderr",
            "resource_manifest_before_bytes",
            "resource_manifest_after_bytes",
            "cleanup_report_bytes",
        ):
            if type(getattr(self, name)) is not bytes:
                raise AdapterContractError(f"{name} must be exact bytes")
        for name in ("oracle_exit_code_bytes", "verifier_reward_json_bytes"):
            value = getattr(self, name)
            if value is not None and type(value) is not bytes:
                raise AdapterContractError(f"{name} must be bytes or None")


class HarborExecutor(Protocol):
    def run_oracle(self, request: HarborExecutionRequest) -> HarborExecutionCapture: ...


class HarborSdkExecutor:
    """Run the pinned Harbor SDK and reduce its filesystem result to the seam.

    The default runner is the only production path that can start Harbor. It
    is deliberately lazy: importing the adapter and running replay tests never
    imports or starts Docker. Tests and qualification harnesses can inject a
    runner that writes a Harbor-shaped job directory.
    """

    def __init__(
        self,
        *,
        job_runner: Callable[[JsonObject], None] | None = None,
    ) -> None:
        if job_runner is not None and not callable(job_runner):
            raise AdapterContractError("job_runner must be callable or None")
        self._job_runner = job_runner

    def run_oracle(self, request: HarborExecutionRequest) -> HarborExecutionCapture:
        if type(request) is not HarborExecutionRequest:
            raise AdapterContractError(
                "request must be an exact HarborExecutionRequest"
            )
        root = Path(request.run_root).resolve()
        fixture_root = Path(request.fixture_root).resolve()
        if not fixture_root.is_dir():
            raise AdapterContractError(
                "Harbor fixture root must be an existing directory"
            )
        root.mkdir(parents=True, exist_ok=True)

        job_config = clone_object(request.job_config, path="$/job_config")
        job_name = _exact_string(job_config.get("job_name"), "job_config.job_name")
        if (
            Path(job_name).name != job_name
            or "\\" in job_name
            or job_name in {".", ".."}
        ):
            raise AdapterContractError(
                "job_config.job_name must be a single path component"
            )
        jobs_dir = root / "jobs"
        job_config["jobs_dir"] = str(jobs_dir)
        tasks = job_config.get("tasks")
        if type(tasks) is not list or len(tasks) != 1 or type(tasks[0]) is not dict:
            raise AdapterContractError("Harbor job must contain exactly one task")
        task_config = clone_object(tasks[0], path="$/job_config/tasks/0")
        task_config["path"] = str(fixture_root)
        job_config["tasks"] = [task_config]
        job_config_bytes = _json_bytes(job_config)
        (root / "executor-job-config.json").write_bytes(job_config_bytes)

        try:
            if self._job_runner is None:
                _run_harbor_job(job_config)
            else:
                self._job_runner(job_config)
            return self._capture_from_job(root, jobs_dir, job_name, job_config_bytes)
        except Exception as error:
            return _failure_capture(job_config_bytes, error)

    @staticmethod
    def _capture_from_job(
        root: Path,
        jobs_dir: Path,
        job_name: str,
        job_config_bytes: bytes,
    ) -> HarborExecutionCapture:
        job_dir = (jobs_dir / job_name).resolve()
        try:
            job_dir.relative_to(jobs_dir.resolve())
        except ValueError as error:
            raise AdapterContractError(
                "Harbor job directory escaped jobs_dir"
            ) from error
        job_result_path = job_dir / "result.json"
        if not job_result_path.is_file():
            raise AdapterContractError("Harbor did not publish job result.json")
        job_result_bytes = job_result_path.read_bytes()
        job_result = _json_object_bytes(job_result_bytes, "job_result")
        trial_results = job_result.get("trial_results")
        if type(trial_results) is not list or len(trial_results) != 1:
            raise AdapterContractError("Harbor job result does not contain one trial")
        trial_summary = _exact_object(trial_results[0], "job_result.trial_results[0]")
        trial_uri = _exact_string(trial_summary.get("trial_uri"), "trial_uri")
        parsed_uri = urlparse(trial_uri)
        if parsed_uri.scheme != "file" or parsed_uri.netloc not in {"", "localhost"}:
            raise AdapterContractError("Harbor trial URI must be a local file URI")
        trial_dir = Path(unquote(parsed_uri.path)).resolve()
        try:
            trial_dir.relative_to(job_dir)
        except ValueError as error:
            raise AdapterContractError(
                "Harbor trial URI escaped the job directory"
            ) from error
        trial_config_path = trial_dir / "config.json"
        trial_result_path = trial_dir / "result.json"
        if not trial_config_path.is_file() or not trial_result_path.is_file():
            raise AdapterContractError(
                "Harbor trial configuration/result is incomplete"
            )

        agent_dir = trial_dir / "agent"
        verifier_dir = trial_dir / "verifier"
        return HarborExecutionCapture(
            process_return_code=0,
            harbor_stdout=_read_or_empty(job_dir / "job.log"),
            harbor_stderr=_read_or_empty(job_dir / "harbor-stderr.txt"),
            job_config_bytes=_read_or_empty(job_dir / "config.json")
            or job_config_bytes,
            job_result_bytes=job_result_bytes,
            trial_config_bytes=trial_config_path.read_bytes(),
            trial_result_bytes=trial_result_path.read_bytes(),
            agent_stdout=_read_or_empty(agent_dir / "oracle.txt"),
            agent_stderr=_read_or_empty(agent_dir / "stderr.txt"),
            oracle_exit_code_bytes=_read_optional(agent_dir / "exit-code.txt"),
            verifier_stdout=_read_or_empty(verifier_dir / "test-stdout.txt"),
            verifier_stderr=_read_or_empty(verifier_dir / "test-stderr.txt"),
            verifier_reward_json_bytes=_read_optional(verifier_dir / "reward.json"),
            resource_manifest_before_bytes=_read_or_default(
                root / "resource-manifest-before.json", _json_bytes({"present": False})
            ),
            resource_manifest_after_bytes=_read_or_default(
                root / "resource-manifest-after.json", _json_bytes({"present": False})
            ),
            cleanup_report_bytes=_read_or_default(
                root / "cleanup-report.json", _false_cleanup_bytes()
            ),
        )


def _run_harbor_job(job_config: JsonObject) -> None:
    """Invoke Harbor 0.21.0 without going through a shell or CLI wrapper."""

    from harbor import Job, JobConfig

    async def run() -> None:
        config = JobConfig.model_validate(job_config)
        job = await Job.create(config)
        await job.run()

    previous = os.environ.get("HARBOR_TELEMETRY")
    os.environ["HARBOR_TELEMETRY"] = "0"
    try:
        asyncio.run(run())
    finally:
        if previous is None:
            os.environ.pop("HARBOR_TELEMETRY", None)
        else:
            os.environ["HARBOR_TELEMETRY"] = previous


def _failure_capture(
    job_config_bytes: bytes, error: Exception
) -> HarborExecutionCapture:
    message = f"{type(error).__name__}: {error}".encode("utf-8", errors="replace")
    job_id = "job-failed"
    trial_id = "trial-failed"
    cleanup = _false_cleanup_bytes()
    return HarborExecutionCapture(
        process_return_code=1,
        harbor_stdout=b"",
        harbor_stderr=message,
        job_config_bytes=job_config_bytes,
        job_result_bytes=_json_bytes(
            {
                "id": job_id,
                "n_total_trials": 1,
                "trial_results": [{"id": trial_id}],
            }
        ),
        trial_config_bytes=_json_bytes(
            {"id": trial_id, "task_name": TERMINAL_BENCH_TASK}
        ),
        trial_result_bytes=_json_bytes(
            {
                "id": trial_id,
                "task_name": TERMINAL_BENCH_TASK,
                "exception_info": {
                    "exception_type": type(error).__name__,
                    "exception_message": str(error),
                },
                "exception_stage": "unknown",
            }
        ),
        agent_stdout=b"",
        agent_stderr=b"",
        oracle_exit_code_bytes=None,
        verifier_stdout=b"",
        verifier_stderr=b"",
        verifier_reward_json_bytes=None,
        resource_manifest_before_bytes=_json_bytes({"present": False}),
        resource_manifest_after_bytes=_json_bytes({"present": False}),
        cleanup_report_bytes=cleanup,
    )


def _read_optional(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def _read_or_empty(path: Path) -> bytes:
    return path.read_bytes() if path.is_file() else b""


def _read_or_default(path: Path, default: bytes) -> bytes:
    return path.read_bytes() if path.is_file() else default


def _false_cleanup_bytes() -> bytes:
    return _json_bytes(
        {
            "run_root_clean": False,
            "agent_processes_clean": False,
            "containers_clean": False,
            "foreign_resources_unchanged": False,
            "workspace_removed": False,
        }
    )


class HarborAdapter:
    descriptor = AdapterDescriptor(
        name="harbor",
        version=HARBOR_VERSION,
        protocol_version=1,
        implementation_digest=f"{_DIGEST}{HARBOR_WHEEL_SHA256}",
    )

    def __init__(
        self,
        publish_artifact: Callable[[bytes], str],
        *,
        executor: HarborExecutor,
        read_artifact: Callable[[str], bytes] | None = None,
    ) -> None:
        if not callable(publish_artifact):
            raise AdapterContractError("publish_artifact must be callable")
        if not callable(getattr(executor, "run_oracle", None)):
            raise AdapterContractError("executor must provide run_oracle")
        if read_artifact is not None and not callable(read_artifact):
            raise AdapterContractError("read_artifact must be callable or None")
        self._publish_artifact = publish_artifact
        self._executor = executor
        self._read_artifact = read_artifact

    def prepare(self, request: dict[str, JsonValue]) -> dict[str, JsonValue]:
        canonical = clone_object(request, path="$/canonical_request")
        _require_exact_keys(
            canonical,
            {"version", "task", "agent", "seed", "extensions"},
            "canonical_request",
        )
        task = clone_object(canonical["task"], path="$/canonical_request/task")
        if task.get("id") != _TASK_ID:
            raise AdapterContractError(f"Harbor adapter requires {_TASK_ID}")
        profile = _profile(canonical["extensions"])
        fixture_root = str(_fixture_root())
        framework_request: JsonObject = {
            "framework": "harbor",
            "framework_version": HARBOR_VERSION,
            "framework_commit": HARBOR_COMMIT,
            "framework_wheel_sha256": HARBOR_WHEEL_SHA256,
            "dataset_repository": TERMINAL_BENCH_REPOSITORY,
            "dataset_commit": TERMINAL_BENCH_COMMIT,
            "task_name": TERMINAL_BENCH_TASK,
            "run_purpose": profile["run_purpose"],
            "source_task_sha256": profile["source_task_sha256"],
            "normalized_task_sha256": profile["normalized_task_sha256"],
            "environment_image_ref": profile["environment_image_ref"],
            "environment_image_id": profile["environment_image_id"],
            "environment_platform": "linux/amd64",
            "runtime_network_mode": "no-network",
            "verifier_environment_mode": "shared",
            "verifier_python": "3.13.15",
            "agent": "oracle",
            "egress_sidecar_image_ref": profile["egress_sidecar_image_ref"],
            "egress_sidecar_image_id": profile["egress_sidecar_image_id"],
            "job_config": _job_config(fixture_root),
        }
        return {
            "canonical_request": canonical,
            "framework_request": framework_request,
            "extensions": {
                "gitspace.harbor": {
                    "qualification": "terminal-bench-2.1-regex-log",
                    "source_task_sha256": profile["source_task_sha256"],
                    "normalized_task_sha256": profile["normalized_task_sha256"],
                }
            },
        }

    def invoke(self, prepared: dict[str, JsonValue]) -> dict[str, JsonValue]:
        value = clone_object(prepared, path="$/prepared")
        _require_exact_keys(value, _PREPARED_FIELDS, "prepared")
        framework = clone_object(
            value["framework_request"], path="$/prepared/framework_request"
        )
        _validate_framework_request(framework)
        with tempfile.TemporaryDirectory(prefix="gitspace-harbor-") as run_root:
            execution_request = HarborExecutionRequest(
                run_root=run_root,
                fixture_root=str(_fixture_root()),
                job_config=clone_object(framework["job_config"], path="$/job_config"),
                environment_image_ref=framework["environment_image_ref"],  # type: ignore[arg-type]
                environment_image_id=framework["environment_image_id"],  # type: ignore[arg-type]
                egress_sidecar_image_ref=framework["egress_sidecar_image_ref"],  # type: ignore[arg-type]
                egress_sidecar_image_id=framework["egress_sidecar_image_id"],  # type: ignore[arg-type]
            )
            capture = self._executor.run_oracle(execution_request)
        if type(capture) is not HarborExecutionCapture:
            raise AdapterContractError("executor returned an unsupported capture")
        artifacts, artifact_sha256, oracle_status = self._publish_capture(capture)
        capture_projection = _capture_projection(
            framework,
            capture,
            artifacts=artifacts,
            artifact_sha256=artifact_sha256,
            oracle_status=oracle_status,
        )
        return {"capture": capture_projection}

    def collect(self, raw: dict[str, JsonValue]) -> dict[str, JsonValue]:
        value = clone_object(raw, path="$/harbor_raw")
        _require_exact_keys(value, _RAW_FIELDS, "harbor_raw")
        projection = project_harbor_capture(value["capture"])
        record = HarborReplayRecord.from_json(projection)
        replay = classify_harbor_record(record, read_artifact=self._read_artifact)
        record_uri = self._publish_verified(canonical_record_bytes(record))
        artifacts = {"harbor_record": record_uri, **record.artifacts}
        metrics: dict[str, int] = {
            "task_invalid_candidate": int(replay.task_invalid_candidate),
            "artifact_integrity": int(replay.obligations["artifact_integrity"]),
        }
        if record.observed_reward is not None:
            metrics["reward"] = record.observed_reward
        return {
            "status": replay.status.value,
            "summary": _summary(replay.status, replay.task_invalid_candidate),
            "artifacts": artifacts,
            "metrics": metrics,
            "extensions": {
                "gitspace.harbor": {
                    "framework_version": HARBOR_VERSION,
                    "framework_commit": HARBOR_COMMIT,
                    "dataset_commit": TERMINAL_BENCH_COMMIT,
                    "task_name": TERMINAL_BENCH_TASK,
                    "run_purpose": record.run_purpose,
                    "record_sha256": replay.record_sha256,
                    "task_invalid_candidate": replay.task_invalid_candidate,
                    "obligations": replay.obligations,
                }
            },
        }

    def _publish_capture(
        self, capture: HarborExecutionCapture
    ) -> tuple[dict[str, str], dict[str, str], JsonObject]:
        payloads: dict[str, bytes] = {
            "harbor_stdout": capture.harbor_stdout,
            "harbor_stderr": capture.harbor_stderr,
            "job_config": capture.job_config_bytes,
            "job_result": capture.job_result_bytes,
            "trial_config": capture.trial_config_bytes,
            "trial_result": capture.trial_result_bytes,
            "agent_stdout": capture.agent_stdout,
            "agent_stderr": capture.agent_stderr,
            "verifier_stdout": capture.verifier_stdout,
            "verifier_stderr": capture.verifier_stderr,
            "verifier_reward_json": capture.verifier_reward_json_bytes or b"",
            "resource_manifest_before": capture.resource_manifest_before_bytes,
            "resource_manifest_after": capture.resource_manifest_after_bytes,
            "cleanup_report": capture.cleanup_report_bytes,
        }
        if capture.oracle_exit_code_bytes is None:
            oracle_status: JsonObject = {"present": False, "value": None}
        else:
            oracle_status = {
                "present": True,
                "value": _parse_exit_code(capture.oracle_exit_code_bytes),
            }
        payloads["oracle_exit_status"] = _json_bytes(oracle_status)
        artifacts: dict[str, str] = {}
        artifact_sha256: dict[str, str] = {}
        if set(payloads) != _ARTIFACT_FIELDS:
            raise AdapterContractError("Harbor capture artifact set is not closed")
        for name, content in payloads.items():
            uri = self._publish_verified(content)
            artifacts[name] = uri
            artifact_sha256[name] = _DIGEST + hashlib.sha256(content).hexdigest()
        return artifacts, artifact_sha256, oracle_status

    def _publish_verified(self, content: bytes) -> str:
        if type(content) is not bytes:
            raise AdapterContractError("published artifact must be exact bytes")
        try:
            uri = validate_cas_uri(
                self._publish_artifact(content), path="$/artifact_uri"
            )
        except Exception as error:
            raise AdapterContractError(
                "publisher returned an invalid CAS URI"
            ) from error
        expected = _CAS_URI_PREFIX + hashlib.sha256(content).hexdigest()
        if uri != expected:
            raise AdapterContractError("published artifact URI does not match bytes")
        return uri


def _capture_projection(
    framework: JsonObject,
    capture: HarborExecutionCapture,
    *,
    artifacts: dict[str, str],
    artifact_sha256: dict[str, str],
    oracle_status: JsonObject,
) -> JsonObject:
    job_result = _json_object_bytes(capture.job_result_bytes, "job_result")
    trial_config = _json_object_bytes(capture.trial_config_bytes, "trial_config")
    trial_result = _json_object_bytes(capture.trial_result_bytes, "trial_result")
    cleanup = _json_object_bytes(capture.cleanup_report_bytes, "cleanup_report")
    trial_results = job_result.get("trial_results")
    if type(trial_results) is not list or len(trial_results) != 1:
        raise AdapterContractError("Harbor job must contain exactly one trial result")
    trial_summary = _exact_object(trial_results[0], "job_result.trial_results[0]")
    summary_id = _exact_string(
        trial_summary.get("id"), "job_result.trial_results[0].id"
    )
    if _exact_string(job_result.get("id"), "job_result.id") == "":
        raise AdapterContractError("Harbor job id is empty")
    job_id = _exact_string(job_result["id"], "job_result.id")
    trial_id = _exact_string(trial_result.get("id"), "trial_result.id")
    if trial_id != summary_id:
        raise AdapterContractError("Harbor job/result trial IDs differ")
    for config_id_name in ("id", "trial_id"):
        if config_id_name in trial_config:
            if trial_id != _exact_string(
                trial_config[config_id_name], f"trial_config.{config_id_name}"
            ):
                raise AdapterContractError("Harbor trial config/result IDs differ")
            break
    task_name = _exact_string(trial_result.get("task_name"), "trial_result.task_name")
    if task_name != TERMINAL_BENCH_TASK:
        raise AdapterContractError("Harbor trial task name is not pinned")
    exception_info = trial_result.get("exception_info")
    if exception_info is None:
        exception_present = False
        exception_type = None
        exception_stage = None
    else:
        info = _exact_object(exception_info, "trial_result.exception_info")
        exception_present = True
        exception_type = _exact_string(info.get("exception_type"), "exception_type")
        raw_stage = trial_result.get("exception_stage")
        exception_stage = (
            "unknown"
            if raw_stage is None
            else _exact_string(raw_stage, "exception_stage")
        )

    observed_reward, reward_error = _parse_reward(capture.verifier_reward_json_bytes)
    if reward_error and not exception_present:
        exception_present = True
        exception_type = "VerifierOutputParseError"
        exception_stage = "verifier"
    stage_timings: dict[str, JsonValue] = {}
    for stage in ("environment_setup", "agent_setup", "agent_execution", "verifier"):
        if stage in trial_result and trial_result[stage] is not None:
            stage_timings[stage] = clone_object(
                trial_result[stage], path=f"$/trial_result/{stage}"
            )
    return {
        "version": 1,
        "run_purpose": framework["run_purpose"],
        "framework": framework["framework"],
        "framework_version": framework["framework_version"],
        "framework_commit": framework["framework_commit"],
        "framework_wheel_sha256": framework["framework_wheel_sha256"],
        "dataset_repository": framework["dataset_repository"],
        "dataset_commit": framework["dataset_commit"],
        "task_name": task_name,
        "source_task_sha256": framework["source_task_sha256"],
        "normalized_task_sha256": framework["normalized_task_sha256"],
        "environment_image_ref": framework["environment_image_ref"],
        "environment_image_id": framework["environment_image_id"],
        "environment_platform": framework["environment_platform"],
        "runtime_network_mode": framework["runtime_network_mode"],
        "verifier_environment_mode": framework["verifier_environment_mode"],
        "verifier_python": framework["verifier_python"],
        "agent": framework["agent"],
        "oracle_exit_code": oracle_status["value"]
        if oracle_status["present"]
        else None,
        "job_id": job_id,
        "trial_id": trial_id,
        "harbor_process_return_code": capture.process_return_code,
        "trial_exception_present": exception_present,
        "observed_reward": observed_reward,
        "exception_type": exception_type,
        "exception_stage": exception_stage,
        "stage_timings": stage_timings,
        "artifacts": artifacts,
        "artifact_sha256": artifact_sha256,
        "cleanup_obligations": cleanup,
    }


def _profile(extensions: object) -> JsonObject:
    value = clone_object(extensions, path="$/canonical_request/extensions")
    profile = value.get("gitspace.harbor")
    profile_object = _exact_object(profile, "gitspace.harbor")
    _require_exact_keys(profile_object, _PROFILE_FIELDS, "gitspace.harbor")
    _bounded_string(profile_object["run_purpose"], "run_purpose")
    if profile_object["run_purpose"] not in {"qualification_oracle", "status_control"}:
        raise AdapterContractError("run_purpose is invalid")
    for name in ("source_task_sha256", "normalized_task_sha256"):
        _digest_string(profile_object[name], name)
    for name in ("environment_image_id", "egress_sidecar_image_id"):
        _digest_string(profile_object[name], name)
    for name in ("environment_image_ref", "egress_sidecar_image_ref"):
        _bounded_string(profile_object[name], name)
    return profile_object


def _job_config(fixture_root: str) -> JsonObject:
    return {
        "job_name": "gitspace-p00-task-012-oracle",
        "n_attempts": 1,
        "n_concurrent_trials": 1,
        "retry": {"max_retries": 0},
        "environment": {"type": "docker", "force_build": False, "delete": True},
        "agents": [{"name": "oracle", "n_concurrent": 1}],
        "datasets": [],
        "tasks": [{"path": fixture_root}],
    }


def _validate_framework_request(value: JsonObject) -> None:
    expected = {
        "framework",
        "framework_version",
        "framework_commit",
        "framework_wheel_sha256",
        "dataset_repository",
        "dataset_commit",
        "task_name",
        "run_purpose",
        "source_task_sha256",
        "normalized_task_sha256",
        "environment_image_ref",
        "environment_image_id",
        "environment_platform",
        "runtime_network_mode",
        "verifier_environment_mode",
        "verifier_python",
        "agent",
        "egress_sidecar_image_ref",
        "egress_sidecar_image_id",
        "job_config",
    }
    _require_exact_keys(value, expected, "framework_request")
    if value["framework"] != "harbor" or value["framework_version"] != HARBOR_VERSION:
        raise AdapterContractError("Harbor framework request is not pinned")
    if value["framework_commit"] != HARBOR_COMMIT:
        raise AdapterContractError("Harbor framework commit is not pinned")
    if value["framework_wheel_sha256"] != HARBOR_WHEEL_SHA256:
        raise AdapterContractError("Harbor wheel digest is not pinned")
    if value["dataset_repository"] != TERMINAL_BENCH_REPOSITORY:
        raise AdapterContractError("Terminal-Bench repository is not pinned")
    if (
        value["dataset_commit"] != TERMINAL_BENCH_COMMIT
        or value["task_name"] != TERMINAL_BENCH_TASK
    ):
        raise AdapterContractError("Terminal-Bench source is not pinned")
    if (
        value["environment_platform"] != "linux/amd64"
        or value["runtime_network_mode"] != "no-network"
    ):
        raise AdapterContractError("Harbor environment network is not closed")
    if (
        value["verifier_environment_mode"] != "shared"
        or value["verifier_python"] != "3.13.15"
    ):
        raise AdapterContractError("Harbor verifier environment is not pinned")
    if value["agent"] != "oracle":
        raise AdapterContractError("Harbor qualification must use oracle")
    _digest_string(value["source_task_sha256"], "source_task_sha256")
    _digest_string(value["normalized_task_sha256"], "normalized_task_sha256")
    _digest_string(value["environment_image_id"], "environment_image_id")
    _digest_string(value["egress_sidecar_image_id"], "egress_sidecar_image_id")
    _bounded_string(value["environment_image_ref"], "environment_image_ref")
    _bounded_string(value["egress_sidecar_image_ref"], "egress_sidecar_image_ref")
    clone_object(value["job_config"], path="$/framework_request/job_config")


def _parse_reward(value: bytes | None) -> tuple[int | None, bool]:
    if value is None or value == b"":
        return None, False
    try:
        data = _json_object_bytes(value, "verifier_reward_json")
    except AdapterContractError:
        return None, True
    if set(data) != {"reward"}:
        return None, True
    reward = data["reward"]
    if type(reward) is not int or reward not in {0, 1}:
        return None, True
    return reward, False


def _parse_exit_code(value: bytes) -> int:
    try:
        text = value.decode("ascii").strip()
    except UnicodeDecodeError as error:
        raise AdapterContractError("oracle exit status is not ASCII") from error
    if (
        not text
        or (text.startswith("-") and not text[1:].isdigit())
        or (not text.startswith("-") and not text.isdigit())
    ):
        raise AdapterContractError("oracle exit status is not an exact integer")
    try:
        return int(text)
    except ValueError as error:
        raise AdapterContractError("oracle exit status is not an integer") from error


def _json_object_bytes(value: bytes, label: str) -> JsonObject:
    if type(value) is not bytes:
        raise AdapterContractError(f"{label} must be exact bytes")
    try:
        parsed = json.loads(value)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AdapterContractError(f"{label} is not JSON") from error
    return _exact_object(parsed, label)


def _fixture_root() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "adapters"
        / "harbor"
        / "fixtures"
        / "terminal-bench-2.1-regex-log"
    )


def _summary(status: AdapterStatus, task_invalid_candidate: bool) -> str:
    if task_invalid_candidate:
        return "Harbor oracle or normalized task is invalid; runtime result is not an agent failure"
    if status is AdapterStatus.PASS:
        return "Harbor oracle completed and CAS-bound replay passed"
    if status is AdapterStatus.FAIL:
        return "Harbor status-control trial failed after infrastructure gates"
    if status is AdapterStatus.TIMEOUT:
        return "Harbor agent execution timed out with valid attribution"
    return (
        "Harbor result could not close all non-compensable infrastructure obligations"
    )


def _require_exact_keys(value: JsonObject, expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise AdapterContractError(
            f"{label} fields differ: missing={sorted(expected - set(value))}, "
            f"unknown={sorted(set(value) - expected)}"
        )


def _exact_object(value: object, label: str) -> JsonObject:
    if type(value) is not dict:
        raise AdapterContractError(f"{label} must be an exact dict")
    try:
        return clone_object(value, path=f"$/{label}")
    except Exception as error:
        raise AdapterContractError(f"{label} is not JSON builtins") from error


def _bounded_string(value: object, label: str) -> str:
    if type(value) is not str or not value or len(value) > 512:
        raise AdapterContractError(f"{label} must be a bounded non-empty string")
    return value


def _exact_string(value: object, label: str) -> str:
    result = _bounded_string(value, label)
    if any(ord(char) < 32 or ord(char) == 127 for char in result):
        raise AdapterContractError(f"{label} contains control characters")
    return result


def _digest_string(value: object, label: str) -> str:
    result = _exact_string(value, label)
    if len(result) != 71 or not result.startswith(_DIGEST):
        raise AdapterContractError(f"{label} must be a sha256 digest")
    try:
        int(result[len(_DIGEST) :], 16)
    except ValueError as error:
        raise AdapterContractError(f"{label} must be a sha256 digest") from error
    return result


def _json_bytes(value: JsonObject) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AdapterContractError("value is not canonical JSON") from error
