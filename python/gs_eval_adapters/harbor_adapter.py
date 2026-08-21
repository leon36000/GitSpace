from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import unquote, urlparse

from .errors import AdapterContractError
from .harbor_replay import (
    HARBOR_ARTIFACT_FIELDS,
    HARBOR_COMMIT,
    HARBOR_ENVIRONMENT_IMPORT_PATH,
    HARBOR_VERSION,
    HARBOR_WHEEL_SHA256,
    TERMINAL_BENCH_COMMIT,
    TERMINAL_BENCH_FIXTURE_FILE_MODES,
    TERMINAL_BENCH_NORMALIZED_TASK_SHA256,
    TERMINAL_BENCH_REPOSITORY,
    TERMINAL_BENCH_RUNTIME_FILE_DIGESTS,
    TERMINAL_BENCH_SOURCE_TASK_SHA256,
    TERMINAL_BENCH_TASK,
    HarborReplayRecord,
    canonical_record_bytes,
    classify_harbor_record,
    is_digest_bound_docker_reference,
    project_harbor_capture,
)
from .json_boundary import JsonObject, JsonValue, clone_object, validate_cas_uri
from .model import AdapterDescriptor, AdapterStatus

_CAS_URI_PREFIX = "cas://sha256/"
_ADAPTER_PACKAGE_ROOT = str(Path(__file__).resolve().parents[1])
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
_ARTIFACT_FIELDS = HARBOR_ARTIFACT_FIELDS
_DIGEST = "sha256:"
_CONFIG_JSON = "config.json"
_RESULT_JSON = "result.json"
_SOURCE_MANIFEST = "source-manifest.json"
_HARBOR_EXTENSION = "gitspace.harbor"
_JOB_CONFIG_PATH = "$/job_config"
_ONE_TRIAL_ERROR = "Harbor job result does not contain one trial"
_STAGE_FIELDS = {
    "environment_started",
    "agent_setup_completed",
    "agent_execution_started",
    "agent_execution_completed",
    "verifier_started",
    "verifier_completed",
}


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
            self, "job_config", clone_object(self.job_config, path=_JOB_CONFIG_PATH)
        )
        _digest_string(self.environment_image_id, "environment_image_id")
        _image_reference(
            self.environment_image_ref,
            "environment_image_ref",
            self.environment_image_id,
        )
        _digest_string(self.egress_sidecar_image_id, "egress_sidecar_image_id")
        _image_reference(
            self.egress_sidecar_image_ref,
            "egress_sidecar_image_ref",
            self.egress_sidecar_image_id,
        )


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
    verifier_result_json_bytes: bytes | None
    source_manifest_bytes: bytes
    task_toml_bytes: bytes
    instruction_md_bytes: bytes
    solution_solve_sh_bytes: bytes
    test_source_bytes: bytes
    verifier_script_bytes: bytes
    verifier_test_script_bytes: bytes
    environment_dockerfile_bytes: bytes
    fixture_inventory_bytes: bytes
    resource_manifest_before_bytes: bytes
    resource_manifest_after_bytes: bytes
    cleanup_report_bytes: bytes
    exception_boundary_bytes: bytes
    exception_discriminant: str | None
    stage_obligations: dict[str, bool]

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
            "source_manifest_bytes",
            "task_toml_bytes",
            "instruction_md_bytes",
            "solution_solve_sh_bytes",
            "test_source_bytes",
            "verifier_script_bytes",
            "verifier_test_script_bytes",
            "environment_dockerfile_bytes",
            "fixture_inventory_bytes",
            "resource_manifest_before_bytes",
            "resource_manifest_after_bytes",
            "cleanup_report_bytes",
            "exception_boundary_bytes",
        ):
            if type(getattr(self, name)) is not bytes:
                raise AdapterContractError(f"{name} must be exact bytes")
        for name in (
            "oracle_exit_code_bytes",
            "verifier_reward_json_bytes",
            "verifier_result_json_bytes",
        ):
            value = getattr(self, name)
            if value is not None and type(value) is not bytes:
                raise AdapterContractError(f"{name} must be bytes or None")
        if (
            self.exception_discriminant is not None
            and type(self.exception_discriminant) is not str
        ):
            raise AdapterContractError(
                "exception discriminant must be an exact string or None"
            )
        if type(self.stage_obligations) is not dict:
            raise AdapterContractError("stage obligations must be an exact dict")
        if set(self.stage_obligations) != _STAGE_FIELDS or any(
            type(value) is not bool for value in self.stage_obligations.values()
        ):
            raise AdapterContractError("stage obligations are not closed booleans")


@dataclass(frozen=True, slots=True)
class HarborProcessResult:
    return_code: int
    stdout: bytes
    stderr: bytes

    def __post_init__(self) -> None:
        if type(self.return_code) is not int:
            raise AdapterContractError(
                "Harbor process return code must be an exact integer"
            )
        if type(self.stdout) is not bytes or type(self.stderr) is not bytes:
            raise AdapterContractError("Harbor process output must be exact bytes")


HarborProcessRunner = Callable[
    [tuple[str, ...], str, dict[str, str]], HarborProcessResult
]


class HarborExecutor(Protocol):
    def run_oracle(self, request: HarborExecutionRequest) -> HarborExecutionCapture: ...


class HarborResourceObserver(Protocol):
    def capture_before(self, request: HarborExecutionRequest) -> JsonObject: ...

    def capture_after(
        self, request: HarborExecutionRequest, process_result: HarborProcessResult
    ) -> JsonObject: ...


class HarborSdkExecutor:
    """Run the pinned Harbor CLI and reduce its filesystem result to the seam.

    The default process runner is the only production path that can start
    Harbor. It is deliberately lazy: importing the adapter and running replay
    tests never starts Docker. Tests and qualification harnesses can inject a
    job or process runner that writes a Harbor-shaped job directory.
    """

    def __init__(
        self,
        *,
        job_runner: Callable[[JsonObject], None] | None = None,
        qualified_venv: str | None = None,
        worker_environment: Mapping[str, str] | None = None,
        process_runner: HarborProcessRunner | None = None,
        resource_observer: HarborResourceObserver | None = None,
    ) -> None:
        if job_runner is not None and not callable(job_runner):
            raise AdapterContractError("job_runner must be callable or None")
        if job_runner is not None and process_runner is not None:
            raise AdapterContractError(
                "job_runner and process_runner cannot both be supplied"
            )
        self._qualified_venv: Path | None
        if qualified_venv is not None:
            qualified_path = Path(_exact_string(qualified_venv, "qualified_venv"))
            if not qualified_path.is_absolute():
                raise AdapterContractError("qualified_venv must be absolute")
            self._qualified_venv = qualified_path
        else:
            self._qualified_venv = None
        worker_values = dict(worker_environment or {})
        if set(worker_values) - {"DOCKER_HOST", "XDG_RUNTIME_DIR"}:
            raise AdapterContractError(
                "worker_environment contains an unauthorized variable"
            )
        for name, value in worker_values.items():
            _exact_string(value, f"worker_environment.{name}")
        self._job_runner = job_runner
        self._worker_environment = worker_values
        self._process_runner = process_runner
        if resource_observer is None:
            raise AdapterContractError("resource_observer is required")
        if not callable(
            getattr(resource_observer, "capture_before", None)
        ) or not callable(getattr(resource_observer, "capture_after", None)):
            raise AdapterContractError(
                "resource_observer must provide capture_before/capture_after"
            )
        self._resource_observer = resource_observer

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

        job_config = clone_object(request.job_config, path=_JOB_CONFIG_PATH)
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
        config_path = root / "job-config.json"
        config_path.write_bytes(job_config_bytes)

        process_result: HarborProcessResult | None = None
        try:
            resource_manifest_before_bytes = _observer_manifest_bytes(
                self._resource_observer.capture_before(request),
                "resource_observer.capture_before",
            )
            if self._job_runner is None:
                if self._qualified_venv is None:
                    raise AdapterContractError(
                        "qualified_venv is required for the real Harbor executor"
                    )
                process_result = self._run_harbor_cli(root, config_path)
            else:
                self._job_runner(job_config)
                process_result = HarborProcessResult(0, b"", b"")
            if process_result is None:
                raise AdapterContractError("Harbor process result was not captured")
            resource_manifest_after_bytes = _observer_manifest_bytes(
                self._resource_observer.capture_after(request, process_result),
                "resource_observer.capture_after",
            )
            return self._capture_from_job(
                root,
                fixture_root,
                jobs_dir,
                job_name,
                job_config_bytes,
                process_result,
                resource_manifest_before_bytes,
                resource_manifest_after_bytes,
            )
        except Exception as error:  # noqa: BLE001 - worker failures become infra evidence
            return _failure_capture(job_config_bytes, error, process_result)

    def _run_harbor_cli(self, root: Path, config_path: Path) -> HarborProcessResult:
        if self._qualified_venv is None:
            raise AdapterContractError(
                "qualified_venv is required for the real Harbor executor"
            )
        venv_bin = self._qualified_venv / "bin"
        for name in ("home", "tmp", "xdg-config", "xdg-cache"):
            (root / name).mkdir(parents=True, exist_ok=True)
        environment = {
            "PATH": f"{venv_bin}:/usr/bin:/bin",
            "PYTHONPATH": _ADAPTER_PACKAGE_ROOT,
            "HOME": str(root / "home"),
            "TMPDIR": str(root / "tmp"),
            "XDG_CONFIG_HOME": str(root / "xdg-config"),
            "XDG_CACHE_HOME": str(root / "xdg-cache"),
            "HARBOR_TELEMETRY": "0",
            **self._worker_environment,
        }
        argv = (
            str(venv_bin / "harbor"),
            "run",
            "--config",
            str(config_path),
        )
        runner = self._process_runner or _run_harbor_process
        result = runner(argv, str(root), environment)
        if type(result) is not HarborProcessResult:
            raise AdapterContractError("process runner returned an unsupported result")
        return result

    @staticmethod
    def _capture_from_job(
        root: Path,
        fixture_root: Path,
        jobs_dir: Path,
        job_name: str,
        job_config_bytes: bytes,
        process_result: HarborProcessResult,
        resource_manifest_before_bytes: bytes,
        resource_manifest_after_bytes: bytes,
    ) -> HarborExecutionCapture:
        job_dir = _validated_job_dir(jobs_dir, job_name)
        job_result_path = job_dir / _RESULT_JSON
        if not job_result_path.is_file():
            raise AdapterContractError("Harbor did not publish job result.json")
        job_result_bytes = job_result_path.read_bytes()
        job_result = _json_object_bytes(job_result_bytes, "job_result")
        trial_dir = _resolve_trial_dir(job_dir, job_result)
        _validate_trial_dir(job_dir, trial_dir)
        trial_config_path, trial_result_path = _trial_artifact_paths(trial_dir)
        trial_result_bytes = trial_result_path.read_bytes()
        trial_result = _json_object_bytes(trial_result_bytes, "trial_result")
        trial_config_bytes = trial_config_path.read_bytes()
        trial_config = _json_object_bytes(trial_config_bytes, "trial_config")
        _validate_trial_capture_binding(job_dir, trial_dir, trial_config, trial_result)
        exception_boundary_bytes = _read_or_default(
            root / "exception-boundary.json",
            _default_exception_boundary_bytes(trial_result),
        )
        exception_discriminant = _parse_exception_boundary(exception_boundary_bytes)

        agent_dir = trial_dir / "agent"
        verifier_dir = trial_dir / "verifier"
        return HarborExecutionCapture(
            process_return_code=process_result.return_code,
            harbor_stdout=process_result.stdout or _read_or_empty(job_dir / "job.log"),
            harbor_stderr=process_result.stderr
            or _read_or_empty(job_dir / "harbor-stderr.txt"),
            job_config_bytes=_read_or_empty(job_dir / _CONFIG_JSON)
            or job_config_bytes,
            job_result_bytes=job_result_bytes,
            trial_config_bytes=trial_config_bytes,
            trial_result_bytes=trial_result_bytes,
            agent_stdout=_read_or_empty(agent_dir / "oracle.txt"),
            agent_stderr=_read_or_empty(agent_dir / "stderr.txt"),
            oracle_exit_code_bytes=_read_optional(agent_dir / "exit-code.txt"),
            verifier_stdout=_read_or_empty(verifier_dir / "test-stdout.txt"),
            verifier_stderr=_read_or_empty(verifier_dir / "test-stderr.txt"),
            verifier_reward_json_bytes=_read_optional(verifier_dir / "reward.json"),
            verifier_result_json_bytes=_read_optional(
                verifier_dir / "gitspace-result.json"
            ),
            source_manifest_bytes=_read_or_default(
                fixture_root / _SOURCE_MANIFEST, b""
            ),
            task_toml_bytes=_read_or_default(fixture_root / "task.toml", b""),
            instruction_md_bytes=_read_or_default(fixture_root / "instruction.md", b""),
            solution_solve_sh_bytes=_read_or_default(
                fixture_root / "solution" / "solve.sh", b""
            ),
            test_source_bytes=_read_or_default(
                fixture_root / "tests" / "test_outputs.py", b""
            ),
            verifier_script_bytes=_read_or_default(
                fixture_root / "tests" / "run_test.py", b""
            ),
            verifier_test_script_bytes=_read_or_default(
                fixture_root / "tests" / "test.sh", b""
            ),
            environment_dockerfile_bytes=_read_or_default(
                fixture_root / "environment" / "Dockerfile", b""
            ),
            fixture_inventory_bytes=_fixture_inventory_bytes(fixture_root),
            resource_manifest_before_bytes=resource_manifest_before_bytes,
            resource_manifest_after_bytes=resource_manifest_after_bytes,
            cleanup_report_bytes=_read_or_default(
                root / "cleanup-report.json",
                _derived_cleanup_report_bytes(
                    resource_manifest_before_bytes,
                    resource_manifest_after_bytes,
                ),
            ),
            exception_boundary_bytes=exception_boundary_bytes,
            exception_discriminant=exception_discriminant,
            stage_obligations=_stage_obligations_from_trial_result(trial_result),
        )


def _validated_job_dir(jobs_dir: Path, job_name: str) -> Path:
    job_dir = (jobs_dir / job_name).resolve()
    try:
        job_dir.relative_to(jobs_dir.resolve())
    except ValueError as error:
        raise AdapterContractError(
            "Harbor job directory escaped jobs_dir"
        ) from error
    return job_dir


def _resolve_trial_dir(job_dir: Path, job_result: JsonObject) -> Path:
    summary_id = _job_result_trial_summary_id(job_result)
    if summary_id is not None:
        trial_results = job_result.get("trial_results")
        if type(trial_results) is not list or len(trial_results) != 1:
            raise AdapterContractError(_ONE_TRIAL_ERROR)
        trial_summary = _exact_object(
            trial_results[0], "job_result.trial_results[0]"
        )
        trial_uri = _exact_string(trial_summary.get("trial_uri"), "trial_uri")
        parsed_uri = urlparse(trial_uri)
        if parsed_uri.scheme != "file" or parsed_uri.netloc not in {"", "localhost"}:
            raise AdapterContractError("Harbor trial URI must be a local file URI")
        return Path(unquote(parsed_uri.path)).resolve()
    trial_dirs = sorted(
        (
            path
            for path in job_dir.iterdir()
            if path.is_dir()
            and (path / _CONFIG_JSON).is_file()
            and (path / _RESULT_JSON).is_file()
        ),
        key=lambda path: str(path),
    )
    if len(trial_dirs) != 1:
        raise AdapterContractError(
            "Harbor job result does not contain one trial directory"
        )
    return trial_dirs[0].resolve()


def _validate_trial_dir(job_dir: Path, trial_dir: Path) -> None:
    try:
        trial_dir.relative_to(job_dir)
    except ValueError as error:
        raise AdapterContractError(
            "Harbor trial URI escaped the job directory"
        ) from error


def _trial_artifact_paths(trial_dir: Path) -> tuple[Path, Path]:
    trial_config_path = trial_dir / _CONFIG_JSON
    trial_result_path = trial_dir / _RESULT_JSON
    if not trial_config_path.is_file() or not trial_result_path.is_file():
        raise AdapterContractError("Harbor trial configuration/result is incomplete")
    return trial_config_path, trial_result_path


def _validate_trial_capture_binding(
    job_dir: Path,
    trial_dir: Path,
    trial_config: JsonObject,
    trial_result: JsonObject,
) -> None:
    trial_uri = _exact_string(trial_result.get("trial_uri"), "trial_uri")
    parsed_trial_uri = urlparse(trial_uri)
    if parsed_trial_uri.scheme != "file" or parsed_trial_uri.netloc not in {
        "",
        "localhost",
    }:
        raise AdapterContractError("Harbor trial URI must be a local file URI")
    if Path(unquote(parsed_trial_uri.path)).resolve() != trial_dir:
        raise AdapterContractError("Harbor trial URI differs from trial directory")
    trials_dir = _exact_string(trial_config.get("trials_dir"), "trials_dir")
    if Path(trials_dir).resolve() != job_dir:
        raise AdapterContractError("Harbor trial directory is not bound to job")


def _run_harbor_process(
    argv: tuple[str, ...], cwd: str, environment: dict[str, str]
) -> HarborProcessResult:
    completed = subprocess.run(
        argv,
        cwd=cwd,
        env=environment,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
        shell=False,
    )
    return HarborProcessResult(
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _failure_capture(
    job_config_bytes: bytes,
    error: Exception,
    process_result: HarborProcessResult | None = None,
) -> HarborExecutionCapture:
    message = f"{type(error).__name__}: {error}".encode("utf-8", errors="replace")
    job_id = "job-failed"
    trial_id = "trial-failed"
    cleanup = _false_cleanup_bytes()
    return HarborExecutionCapture(
        process_return_code=process_result.return_code if process_result else 1,
        harbor_stdout=process_result.stdout if process_result else b"",
        harbor_stderr=(process_result.stderr + b"\n" + message)
        if process_result
        else message,
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
        verifier_result_json_bytes=None,
        source_manifest_bytes=b"",
        task_toml_bytes=b"",
        instruction_md_bytes=b"",
        solution_solve_sh_bytes=b"",
        test_source_bytes=b"",
        verifier_script_bytes=b"",
        verifier_test_script_bytes=b"",
        environment_dockerfile_bytes=b"",
        fixture_inventory_bytes=b"",
        resource_manifest_before_bytes=b"",
        resource_manifest_after_bytes=b"",
        cleanup_report_bytes=cleanup,
        exception_boundary_bytes=_json_bytes(
            {"discriminant": "other_exception", "stage": "unknown"}
        ),
        exception_discriminant="other_exception",
        stage_obligations=dict.fromkeys(_STAGE_FIELDS, False),
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
            "process_group_absent": False,
            "temp_root_absent": False,
            "containers_absent": False,
            "networks_absent": False,
            "derived_images_absent": False,
            "foreign_resources_untouched": False,
        }
    )


def _derived_cleanup_report_bytes(before: bytes, after: bytes) -> bytes:
    false_cleanup: dict[str, JsonValue] = {
        "process_group_absent": False,
        "temp_root_absent": False,
        "containers_absent": False,
        "networks_absent": False,
        "derived_images_absent": False,
        "foreign_resources_untouched": False,
    }
    before_resources = _resource_state_map(before)
    after_resources = _resource_state_map(after)
    if before_resources is None or after_resources is None:
        return _json_bytes(false_cleanup)

    def absent(kind: str) -> bool:
        return not any(
            resource_kind == kind and owner == "gitspace"
            for resource_kind, _resource_id, owner in after_resources
        )

    foreign_before = {
        key: state
        for key, state in before_resources.items()
        if key[2] == "foreign"
    }
    foreign_after = {
        key: state
        for key, state in after_resources.items()
        if key[2] == "foreign"
    }
    return _json_bytes(
        {
            "process_group_absent": absent("process_group"),
            "temp_root_absent": absent("temp_root"),
            "containers_absent": absent("container"),
            "networks_absent": absent("network"),
            "derived_images_absent": absent("derived_image"),
            "foreign_resources_untouched": foreign_before == foreign_after,
        }
    )


def _resource_state_map(value: bytes) -> dict[tuple[str, str, str], str] | None:
    try:
        manifest = _json_object_bytes(value, "resource_manifest")
    except AdapterContractError:
        return None
    resources = manifest.get("resources")
    if type(resources) is not list:
        return None
    result: dict[tuple[str, str, str], str] = {}
    for resource in resources:
        if type(resource) is not dict or set(resource) != {
            "kind",
            "id",
            "owner",
            "state_digest",
        }:
            return None
        kind = resource.get("kind")
        resource_id = resource.get("id")
        owner = resource.get("owner")
        state_digest = resource.get("state_digest")
        if (
            type(kind) is not str
            or kind
            not in {"process_group", "temp_root", "container", "network", "derived_image"}
            or type(resource_id) is not str
            or not resource_id
            or type(owner) is not str
            or owner not in {"gitspace", "foreign"}
            or type(state_digest) is not str
            or len(state_digest) != 71
            or not state_digest.startswith(_DIGEST)
        ):
            return None
        try:
            int(state_digest.removeprefix(_DIGEST), 16)
        except ValueError:
            return None
        key = (kind, resource_id, owner)
        if key in result:
            return None
        result[key] = state_digest
    return result


def _default_exception_boundary_bytes(trial_result: JsonObject) -> bytes:
    return _json_bytes(
        {
            "discriminant": None,
            "stage": "unknown"
            if trial_result.get("exception_info") is not None
            else None,
        }
    )


def _observer_manifest_bytes(value: object, label: str) -> bytes:
    if type(value) is not dict:
        raise AdapterContractError(f"{label} must return an exact dict")
    return _json_bytes(clone_object(value, path=f"$/{label}"))


def _fixture_inventory_bytes(fixture_root: Path) -> bytes:
    root = fixture_root.resolve()
    if not root.is_dir():
        raise AdapterContractError("Harbor fixture root must be an existing directory")
    files: dict[str, JsonValue] = {}
    for path in sorted(root.rglob("*"), key=lambda item: str(item.relative_to(root))):
        relative = path.relative_to(root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise AdapterContractError(
                f"Harbor fixture contains an unsupported runtime entry: {relative}"
            )
        if path.is_dir():
            continue
        if not path.is_file():
            raise AdapterContractError(
                f"Harbor fixture contains an unsupported runtime entry: {relative}"
            )
        content = path.read_bytes()
        files[str(relative)] = {
            "sha256": _DIGEST + hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
            "mode": TERMINAL_BENCH_FIXTURE_FILE_MODES[str(relative)],
        }
    if set(files) != {_SOURCE_MANIFEST, *TERMINAL_BENCH_RUNTIME_FILE_DIGESTS}:
        raise AdapterContractError(
            "Harbor fixture inventory is not the locked file set"
        )
    return _json_bytes(
        {
            "schema": "gitspace.harbor.fixture-inventory.v1",
            "task_path": str(root),
            "files": files,
        }
    )


def _job_result_trial_summary_id(job_result: JsonObject) -> str | None:
    """Validate Harbor's one-trial job result and return a legacy summary id.

    Harbor 0.21.0 stores the trial result in a child directory and exposes
    aggregate counts in the job result. Older test doubles used a
    ``trial_results`` array with a file URI. Both shapes remain accepted only
    when they prove exactly one trial.
    """

    if (
        type(job_result.get("n_total_trials")) is not int
        or job_result["n_total_trials"] != 1
    ):
        raise AdapterContractError("Harbor job must report exactly one total trial")
    if "trial_results" in job_result:
        trial_results = job_result["trial_results"]
        if type(trial_results) is not list or len(trial_results) != 1:
            raise AdapterContractError(_ONE_TRIAL_ERROR)
        trial_summary = _exact_object(
            trial_results[0], "job_result.trial_results[0]"
        )
        return _exact_string(trial_summary.get("id"), "trial summary id")

    stats = _exact_object(job_result.get("stats"), "job_result.stats")
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
        raise AdapterContractError("job_result.stats counters are invalid")
    retries = stats.get("n_retries")
    if type(retries) is not int or retries < 0:
        raise AdapterContractError("job_result.stats.n_retries is invalid")
    if (
        completed != 1
        or running != 0
        or pending != 0
        or type(errored) is not int
        or type(cancelled) is not int
        or errored > completed
        or cancelled > errored
        or retries != 0
    ):
        raise AdapterContractError(_ONE_TRIAL_ERROR)
    if type(stats.get("evals")) is not dict:
        raise AdapterContractError("job_result.stats.evals is invalid")
    return None


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
        environment_image_ref = _exact_string(
            profile["environment_image_ref"], "environment_image_ref"
        )
        environment_image_id = _exact_string(
            profile["environment_image_id"], "environment_image_id"
        )
        egress_sidecar_image_ref = _exact_string(
            profile["egress_sidecar_image_ref"], "egress_sidecar_image_ref"
        )
        egress_sidecar_image_id = _exact_string(
            profile["egress_sidecar_image_id"], "egress_sidecar_image_id"
        )
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
            "job_config": _job_config(
                fixture_root,
                environment_image_ref=environment_image_ref,
                environment_image_id=environment_image_id,
                egress_sidecar_image_ref=egress_sidecar_image_ref,
                egress_sidecar_image_id=egress_sidecar_image_id,
            ),
        }
        return {
            "canonical_request": canonical,
            "framework_request": framework_request,
            "extensions": {
                _HARBOR_EXTENSION: {
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
                job_config=clone_object(framework["job_config"], path=_JOB_CONFIG_PATH),
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
        artifacts: JsonObject = {"harbor_record": record_uri, **record.artifacts}
        metrics: JsonObject = {
            "task_invalid_candidate": int(replay.task_invalid_candidate),
            "artifact_integrity": int(replay.obligations["artifact_integrity"]),
        }
        if record.observed_reward is not None:
            metrics["reward"] = record.observed_reward
        harbor_extension: JsonObject = {
            "framework_version": HARBOR_VERSION,
            "framework_commit": HARBOR_COMMIT,
            "dataset_commit": TERMINAL_BENCH_COMMIT,
            "task_name": TERMINAL_BENCH_TASK,
            "run_purpose": record.run_purpose,
            "record_sha256": replay.record_sha256,
            "task_invalid_candidate": replay.task_invalid_candidate,
            "obligations": dict(replay.obligations),
        }
        result: JsonObject = {
            "status": replay.status.value,
            "summary": _summary(replay.status, replay.task_invalid_candidate),
            "artifacts": artifacts,
            "metrics": metrics,
            "extensions": {_HARBOR_EXTENSION: harbor_extension},
        }
        return result

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
            "verifier_result_json": capture.verifier_result_json_bytes or b"",
            "source_manifest": capture.source_manifest_bytes,
            "task_toml": capture.task_toml_bytes,
            "instruction_md": capture.instruction_md_bytes,
            "solution_solve_sh": capture.solution_solve_sh_bytes,
            "test_source": capture.test_source_bytes,
            "verifier_script": capture.verifier_script_bytes,
            "verifier_test_script": capture.verifier_test_script_bytes,
            "environment_dockerfile": capture.environment_dockerfile_bytes,
            "fixture_inventory": capture.fixture_inventory_bytes,
            "exception_boundary": capture.exception_boundary_bytes,
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
    boundary_details = _parse_exception_boundary_details(
        capture.exception_boundary_bytes
    )
    job_id, trial_id, task_name = _capture_identity(
        job_result, trial_config, trial_result
    )
    (
        exception_present,
        observed_reward,
        exception_discriminant,
        exception_type_diagnostic,
        exception_stage,
    ) = _capture_outcome(capture, trial_result, boundary_details)
    stage_timings = _capture_stage_timings(trial_result)
    artifact_values: JsonObject = dict(artifacts)
    artifact_digest_values: JsonObject = dict(artifact_sha256)
    return {
        "version": 2,
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
        "egress_sidecar_image_ref": framework["egress_sidecar_image_ref"],
        "egress_sidecar_image_id": framework["egress_sidecar_image_id"],
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
        "exception_discriminant": exception_discriminant,
        "exception_type_diagnostic": exception_type_diagnostic,
        "exception_stage": exception_stage,
        "stage_timings": stage_timings,
        "stage_obligations": dict(capture.stage_obligations),
        "artifacts": artifact_values,
        "artifact_sha256": artifact_digest_values,
        "cleanup_obligations": cleanup,
    }


def _capture_identity(
    job_result: JsonObject,
    trial_config: JsonObject,
    trial_result: JsonObject,
) -> tuple[str, str, str]:
    summary_id = _job_result_trial_summary_id(job_result)
    if _exact_string(job_result.get("id"), "job_result.id") == "":
        raise AdapterContractError("Harbor job id is empty")
    job_id = _exact_string(job_result["id"], "job_result.id")
    trial_id = _exact_string(trial_result.get("id"), "trial_result.id")
    if summary_id is not None and trial_id != summary_id:
        raise AdapterContractError("Harbor job/result trial IDs differ")
    for config_id_name in ("id", "trial_id"):
        if config_id_name in trial_config and trial_id != _exact_string(
            trial_config[config_id_name], f"trial_config.{config_id_name}"
        ):
            raise AdapterContractError("Harbor trial config/result IDs differ")
    task_name = _exact_string(trial_result.get("task_name"), "trial_result.task_name")
    if task_name != TERMINAL_BENCH_TASK:
        raise AdapterContractError("Harbor trial task name is not pinned")
    return job_id, trial_id, task_name


def _capture_outcome(
    capture: HarborExecutionCapture,
    trial_result: JsonObject,
    boundary_details: tuple[str | None, str | None] | None,
) -> tuple[bool, int | None, str | None, str | None, str | None]:
    exception_info = trial_result.get("exception_info")
    if exception_info is None:
        exception_present = False
        exception_type_diagnostic = None
        exception_stage = None
    else:
        info = _exact_object(exception_info, "trial_result.exception_info")
        exception_present = True
        exception_type_diagnostic = _exact_string(
            info.get("exception_type"), "exception_type"
        )
        raw_stage = trial_result.get("exception_stage")
        boundary_stage = boundary_details[1] if boundary_details is not None else None
        exception_stage = (
            boundary_stage or "unknown"
            if raw_stage is None
            else _exact_string(raw_stage, "exception_stage")
        )

    observed_reward, reward_error = _parse_reward(capture.verifier_reward_json_bytes)
    if reward_error and not exception_present:
        exception_present = True
        exception_type_diagnostic = "VerifierOutputParseError"
        exception_stage = "verifier"
    exception_discriminant = capture.exception_discriminant
    if reward_error and exception_discriminant is None:
        exception_discriminant = "other_exception"
    return (
        exception_present,
        observed_reward,
        exception_discriminant,
        exception_type_diagnostic,
        exception_stage,
    )


def _capture_stage_timings(trial_result: JsonObject) -> dict[str, JsonValue]:
    stage_timings: dict[str, JsonValue] = {}
    for stage in ("environment_setup", "agent_setup", "agent_execution", "verifier"):
        if stage in trial_result and trial_result[stage] is not None:
            stage_timings[stage] = clone_object(
                trial_result[stage], path=f"$/trial_result/{stage}"
            )
    return stage_timings


def _profile(extensions: object) -> JsonObject:
    value = clone_object(extensions, path="$/canonical_request/extensions")
    profile = value.get(_HARBOR_EXTENSION)
    profile_object = _exact_object(profile, _HARBOR_EXTENSION)
    _require_exact_keys(profile_object, _PROFILE_FIELDS, _HARBOR_EXTENSION)
    _bounded_string(profile_object["run_purpose"], "run_purpose")
    if profile_object["run_purpose"] not in {"qualification_oracle", "status_control"}:
        raise AdapterContractError("run_purpose is invalid")
    for name in ("source_task_sha256", "normalized_task_sha256"):
        _digest_string(profile_object[name], name)
    for name in ("environment_image_id", "egress_sidecar_image_id"):
        _digest_string(profile_object[name], name)
    _image_reference(
        profile_object["environment_image_ref"],
        "environment_image_ref",
        profile_object["environment_image_id"],
    )
    _image_reference(
        profile_object["egress_sidecar_image_ref"],
        "egress_sidecar_image_ref",
        profile_object["egress_sidecar_image_id"],
    )
    return profile_object


def _job_config(
    fixture_root: str,
    *,
    environment_image_ref: str,
    environment_image_id: str,
    egress_sidecar_image_ref: str,
    egress_sidecar_image_id: str,
) -> JsonObject:
    return {
        "job_name": "gitspace-p00-task-012-oracle",
        "n_attempts": 1,
        "n_concurrent_trials": 1,
        "retry": {"max_retries": 0},
        "environment": {
            "import_path": HARBOR_ENVIRONMENT_IMPORT_PATH,
            "kwargs": {
                "gitspace_environment_image_ref": environment_image_ref,
                "gitspace_environment_image_id": environment_image_id,
                "gitspace_egress_sidecar_image_ref": egress_sidecar_image_ref,
                "gitspace_egress_sidecar_image_id": egress_sidecar_image_id,
            },
        },
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
    if value["source_task_sha256"] != TERMINAL_BENCH_SOURCE_TASK_SHA256:
        raise AdapterContractError("source task digest is not locked")
    if value["normalized_task_sha256"] != TERMINAL_BENCH_NORMALIZED_TASK_SHA256:
        raise AdapterContractError("normalized task digest is not locked")
    _digest_string(value["environment_image_id"], "environment_image_id")
    _digest_string(value["egress_sidecar_image_id"], "egress_sidecar_image_id")
    _image_reference(
        value["environment_image_ref"],
        "environment_image_ref",
        value["environment_image_id"],
    )
    _image_reference(
        value["egress_sidecar_image_ref"],
        "egress_sidecar_image_ref",
        value["egress_sidecar_image_id"],
    )
    _validate_job_config(
        value["job_config"],
        environment_image_ref=value["environment_image_ref"],
        environment_image_id=value["environment_image_id"],
        egress_sidecar_image_ref=value["egress_sidecar_image_ref"],
        egress_sidecar_image_id=value["egress_sidecar_image_id"],
    )


def _validate_job_config(
    value: object,
    *,
    environment_image_ref: object | None = None,
    environment_image_id: object | None = None,
    egress_sidecar_image_ref: object | None = None,
    egress_sidecar_image_id: object | None = None,
) -> None:
    job = _exact_object(value, "job_config")
    _require_exact_keys(
        job,
        {
            "job_name",
            "n_attempts",
            "n_concurrent_trials",
            "retry",
            "environment",
            "agents",
            "datasets",
            "tasks",
        },
        "job_config",
    )
    _validate_job_basics(job)
    _validate_job_environment(
        job,
        environment_image_ref=environment_image_ref,
        environment_image_id=environment_image_id,
        egress_sidecar_image_ref=egress_sidecar_image_ref,
        egress_sidecar_image_id=egress_sidecar_image_id,
    )
    _validate_job_agents_and_tasks(job)


def _validate_job_basics(job: JsonObject) -> None:
    _exact_string(job["job_name"], "job_config.job_name")
    if type(job["n_attempts"]) is not int or job["n_attempts"] != 1:
        raise AdapterContractError("Harbor job must use exactly one attempt")
    if type(job["n_concurrent_trials"]) is not int or job["n_concurrent_trials"] != 1:
        raise AdapterContractError("Harbor job must use exactly one concurrent trial")

    retry = _exact_object(job["retry"], "job_config.retry")
    _require_exact_keys(retry, {"max_retries"}, "job_config.retry")
    if type(retry["max_retries"]) is not int or retry["max_retries"] != 0:
        raise AdapterContractError("Harbor job retries must be disabled")


def _validate_job_environment(
    job: JsonObject,
    *,
    environment_image_ref: object | None,
    environment_image_id: object | None,
    egress_sidecar_image_ref: object | None,
    egress_sidecar_image_id: object | None,
) -> None:
    environment = _exact_object(job["environment"], "job_config.environment")
    _require_exact_keys(
        environment,
        {"import_path", "kwargs"},
        "job_config.environment",
    )
    if environment["import_path"] != HARBOR_ENVIRONMENT_IMPORT_PATH:
        raise AdapterContractError("Harbor environment import path is not pinned")
    gitspace = _exact_object(environment["kwargs"], "job_config.environment.kwargs")
    _require_exact_keys(
        gitspace,
        {
            "gitspace_environment_image_ref",
            "gitspace_environment_image_id",
            "gitspace_egress_sidecar_image_ref",
            "gitspace_egress_sidecar_image_id",
        },
        "job_config.environment.kwargs",
    )
    environment_ref = _exact_string(
        gitspace["gitspace_environment_image_ref"],
        "job_config.environment.kwargs.gitspace_environment_image_ref",
    )
    environment_image_id_value = _exact_string(
        gitspace["gitspace_environment_image_id"],
        "job_config.environment.kwargs.gitspace_environment_image_id",
    )
    sidecar_image_id = _exact_string(
        gitspace["gitspace_egress_sidecar_image_id"],
        "job_config.environment.kwargs.gitspace_egress_sidecar_image_id",
    )
    sidecar_image_ref = _exact_string(
        gitspace["gitspace_egress_sidecar_image_ref"],
        "job_config.environment.kwargs.gitspace_egress_sidecar_image_ref",
    )
    _image_reference(
        environment_ref,
        "job_config.environment.kwargs.gitspace_environment_image_ref",
        environment_image_id_value,
    )
    _image_reference(
        sidecar_image_ref,
        "job_config.environment.kwargs.gitspace_egress_sidecar_image_ref",
        sidecar_image_id,
    )
    _validate_job_request_image_matches(
        environment_ref,
        environment_image_id_value,
        sidecar_image_ref,
        sidecar_image_id,
        environment_image_ref,
        environment_image_id,
        egress_sidecar_image_ref,
        egress_sidecar_image_id,
    )


def _validate_job_request_image_matches(
    environment_ref: str,
    environment_image_id_value: str,
    sidecar_image_ref: str,
    sidecar_image_id: str,
    environment_image_ref: object | None,
    environment_image_id: object | None,
    egress_sidecar_image_ref: object | None,
    egress_sidecar_image_id: object | None,
) -> None:
    if environment_image_ref is not None and environment_ref != environment_image_ref:
        raise AdapterContractError(
            "Harbor job environment image differs from the framework request"
        )
    if (
        environment_image_id is not None
        and environment_image_id_value != environment_image_id
    ):
        raise AdapterContractError(
            "Harbor job environment image identity differs from the framework request"
        )
    if (
        egress_sidecar_image_ref is not None
        and sidecar_image_ref != egress_sidecar_image_ref
    ):
        raise AdapterContractError(
            "Harbor job sidecar image differs from the framework request"
        )
    if (
        egress_sidecar_image_id is not None
        and sidecar_image_id != egress_sidecar_image_id
    ):
        raise AdapterContractError(
            "Harbor job sidecar identity differs from the framework request"
        )


def _validate_job_agents_and_tasks(job: JsonObject) -> None:
    agents = job["agents"]
    if type(agents) is not list or len(agents) != 1 or type(agents[0]) is not dict:
        raise AdapterContractError("Harbor job must contain exactly one agent")
    agent = _exact_object(agents[0], "job_config.agents[0]")
    _require_exact_keys(agent, {"name", "n_concurrent"}, "job_config.agents[0]")
    if (
        agent["name"] != "oracle"
        or type(agent["n_concurrent"]) is not int
        or agent["n_concurrent"] != 1
    ):
        raise AdapterContractError("Harbor job must use one concurrent oracle")

    if type(job["datasets"]) is not list or job["datasets"] != []:
        raise AdapterContractError("Harbor job datasets must be empty")
    tasks = job["tasks"]
    if type(tasks) is not list or len(tasks) != 1 or type(tasks[0]) is not dict:
        raise AdapterContractError("Harbor job must contain exactly one task")
    task = _exact_object(tasks[0], "job_config.tasks[0]")
    _require_exact_keys(task, {"path"}, "job_config.tasks[0]")
    _exact_string(task["path"], "job_config.tasks[0].path")


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


def _parse_exception_boundary_details(
    value: bytes,
) -> tuple[str | None, str | None] | None:
    if value == b"":
        return None
    try:
        data = _json_object_bytes(value, "exception_boundary")
    except AdapterContractError:
        return None
    if set(data) != {"discriminant", "stage"}:
        return None
    discriminant = data["discriminant"]
    stage = data["stage"]
    if discriminant is not None and type(discriminant) is not str:
        return None
    if stage is not None and type(stage) is not str:
        return None
    return discriminant, stage


def _parse_exception_boundary(value: bytes) -> str | None:
    details = _parse_exception_boundary_details(value)
    return details[0] if details is not None else None


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
    if type(value) is not dict:
        return False, False
    started = value.get("started_at") is not None
    completed = value.get("finished_at") is not None
    return started, completed


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


def _image_reference(value: object, label: str, image_id: object) -> str:
    reference = _exact_string(value, label)
    digest = _digest_string(image_id, f"{label}.id")
    if "@" not in reference or reference.rsplit("@", 1)[1] != digest:
        raise AdapterContractError(f"{label} must be bound to its image digest")
    if not is_digest_bound_docker_reference(reference):
        raise AdapterContractError(f"{label} must be a valid Docker reference")
    return reference


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
