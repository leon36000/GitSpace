from __future__ import annotations

import hashlib
import json
import tempfile
from importlib import metadata
from pathlib import Path
from typing import Callable

from inspect_ai import Task, eval as inspect_eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.scorer import match
from inspect_ai.solver import generate

from .errors import AdapterContractError
from .inspect_replay import (
    INSPECT_COMMIT,
    INSPECT_VERSION,
    INSPECT_WHEEL_SHA256,
    InspectReplayRecord,
    build_replay_record,
    canonical_record_bytes,
    project_inspect_log,
    rescore_inspect_record,
)
from .json_boundary import JsonObject, JsonValue, clone_object, validate_cas_uri
from .model import AdapterDescriptor, AdapterStatus

_MODEL_OUTPUT = "Default output from mockllm/model"
_TASK_NAME = "gitspace_inspect_controlled"
_SAMPLE_ID = "GS-SAMPLE-000011"
_OPTIONS: JsonObject = {"location": "exact", "ignore_case": True, "numeric": False}


class InspectAdapter:
    descriptor = AdapterDescriptor(
        name="inspect-ai",
        version=INSPECT_VERSION,
        protocol_version=1,
        implementation_digest=f"sha256:{INSPECT_WHEEL_SHA256}",
    )

    def __init__(self, publish_artifact: Callable[[bytes], str]) -> None:
        if not callable(publish_artifact):
            raise AdapterContractError("publish_artifact must be callable")
        self._publish_artifact = publish_artifact

    def prepare(self, request: dict[str, JsonValue]) -> dict[str, JsonValue]:
        canonical = clone_object(request, path="$/canonical_request")
        task = clone_object(canonical.get("task"), path="$/canonical_request/task")
        agent = clone_object(canonical.get("agent"), path="$/canonical_request/agent")
        if task.get("id") != "GS-TASK-000011":
            raise AdapterContractError("Inspect adapter requires GS-TASK-000011")
        if agent.get("model") != "mockllm/model":
            raise AdapterContractError("Inspect adapter requires mockllm/model")
        intent = clone_object(task.get("intent"), path="$/canonical_request/task/intent")
        input_text = intent.get("owner_outcome")
        if type(input_text) is not str or not input_text:
            raise AdapterContractError("Inspect input must be non-empty text")
        return {
            "canonical_request": canonical,
            "framework_request": {
                "framework": "inspect-ai",
                "framework_version": INSPECT_VERSION,
                "framework_commit": INSPECT_COMMIT,
                "task_id": "GS-TASK-000011",
                "task_name": _TASK_NAME,
                "sample_id": _SAMPLE_ID,
                "input": input_text,
                "target": _MODEL_OUTPUT,
                "model": "mockllm/model",
                "solver": "generate",
                "scorer": "match",
                "scorer_options": dict(_OPTIONS),
            },
            "extensions": {
                "gitspace.inspect": {"qualification": f"inspect-ai-{INSPECT_VERSION}"}
            },
        }

    def invoke(self, prepared: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if metadata.version("inspect-ai") != INSPECT_VERSION:
            raise AdapterContractError(
                f"Inspect {INSPECT_VERSION} is required for this qualification"
            )
        prepared_value = clone_object(prepared, path="$/prepared")
        request = clone_object(
            prepared_value.get("framework_request"), path="$/prepared/framework_request"
        )
        self._validate_framework_request(request)

        task_metadata = {
            "gitspace_task_id": request["task_id"],
            "gitspace_task_name": request["task_name"],
            "gitspace_sample_id": request["sample_id"],
            "gitspace_framework_version": INSPECT_VERSION,
            "gitspace_framework_commit": INSPECT_COMMIT,
            "gitspace_solver": "generate",
            "gitspace_scorer": "match",
            "gitspace_scorer_options": dict(_OPTIONS),
        }
        task = Task(
            dataset=[
                Sample(
                    id=request["sample_id"],
                    input=request["input"],
                    target=request["target"],
                    metadata={"gitspace_sample_id": request["sample_id"]},
                )
            ],
            solver=generate(),
            scorer=match(location="exact", ignore_case=True, numeric=False),
            model="mockllm/model",
            name=_TASK_NAME,
            version=1,
            metadata=task_metadata,
            epochs=1,
        )
        with tempfile.TemporaryDirectory(prefix="gitspace-inspect-") as log_dir:
            logs = inspect_eval(
                task,
                model="mockllm/model",
                display="none",
                log_dir=log_dir,
                log_format="json",
                limit=1,
                epochs=1,
                fail_on_error=True,
                max_samples=1,
                log_model_api=True,
                log_realtime=False,
                acp_server=False,
                ctl_server=False,
                notification=False,
                trace=False,
            )
        log = _single_eval_log(logs)
        log_value = log.model_dump(mode="json", exclude_none=True)
        log_bytes = _json_bytes(log_value)
        log_uri = self._publish_verified(log_bytes)
        projection = self._projection_from_log(log_value)
        record = build_replay_record(projection, log_bytes=log_bytes, log_uri=log_uri)
        record_bytes = canonical_record_bytes(record)
        record_uri = self._publish_verified(record_bytes)
        return {
            "record": record.to_json(),
            "log_uri": log_uri,
            "record_uri": record_uri,
        }

    def collect(self, raw: dict[str, JsonValue]) -> dict[str, JsonValue]:
        value = clone_object(raw, path="$/inspect_raw")
        if set(value) != {"record", "log_uri", "record_uri"}:
            raise AdapterContractError("Inspect raw result fields differ")
        record = InspectReplayRecord.from_json(value["record"])
        log_uri = validate_cas_uri(value["log_uri"], path="$/inspect_raw/log_uri")
        record_uri = validate_cas_uri(
            value["record_uri"], path="$/inspect_raw/record_uri"
        )
        if log_uri != record.log_uri:
            raise AdapterContractError("Inspect record and raw log URI disagree")
        replay = rescore_inspect_record(record)
        if record.inspect_status != "success":
            status = AdapterStatus.INFRA
        elif not replay.obligations["inspect_score_agrees"]:
            raise AdapterContractError("Inspect score disagrees with independent replay")
        else:
            status = replay.status
        return {
            "status": status.value,
            "summary": (
                f"Inspect {INSPECT_VERSION} controlled run and independent replay agree"
                if status in {AdapterStatus.PASS, AdapterStatus.FAIL}
                else f"Inspect {INSPECT_VERSION} evaluation did not complete successfully"
            ),
            "artifacts": {
                "inspect_log": log_uri,
                "inspect_record": record_uri,
            },
            "metrics": {
                "inspect_correct": 1 if record.inspect_score == "C" else 0,
                "replay_correct": 1 if replay.score == "C" else 0,
                "event_count": len(record.event_types),
            },
            "extensions": {
                "gitspace.inspect": {
                    "version": INSPECT_VERSION,
                    "commit": INSPECT_COMMIT,
                    "model": record.model,
                    "solver": record.solver,
                    "scorer": record.scorer,
                }
            },
        }

    @staticmethod
    def record_from_projection_for_test(projection: object) -> InspectReplayRecord:
        log_bytes = _json_bytes(projection)
        log_uri = "cas://sha256/" + hashlib.sha256(log_bytes).hexdigest()
        return build_replay_record(projection, log_bytes=log_bytes, log_uri=log_uri)

    @staticmethod
    def record_from_static_fixture_for_test() -> InspectReplayRecord:
        path = (
            Path(__file__).resolve().parents[2]
            / "tests"
            / "adapters"
            / "inspect"
            / "fixtures"
            / "inspect-log-projection-0.3.258.json"
        )
        return InspectAdapter.record_from_projection_for_test(
            json.loads(path.read_text(encoding="utf-8"))
        )

    def _publish_verified(self, value: bytes) -> str:
        uri = validate_cas_uri(self._publish_artifact(value), path="$/artifact_uri")
        expected = "cas://sha256/" + hashlib.sha256(value).hexdigest()
        if uri != expected:
            raise AdapterContractError("artifact URI digest does not match published bytes")
        return uri

    @staticmethod
    def _validate_framework_request(value: JsonObject) -> None:
        expected = {
            "framework": "inspect-ai",
            "framework_version": INSPECT_VERSION,
            "framework_commit": INSPECT_COMMIT,
            "task_id": "GS-TASK-000011",
            "task_name": _TASK_NAME,
            "sample_id": _SAMPLE_ID,
            "target": _MODEL_OUTPUT,
            "model": "mockllm/model",
            "solver": "generate",
            "scorer": "match",
            "scorer_options": _OPTIONS,
        }
        for key, item in expected.items():
            if value.get(key) != item:
                raise AdapterContractError(f"Inspect framework request mismatch: {key}")
        if type(value.get("input")) is not str or not value["input"]:
            raise AdapterContractError("Inspect framework input is invalid")
        if set(value) != set(expected) | {"input"}:
            raise AdapterContractError("Inspect framework request fields differ")

    @staticmethod
    def _projection_from_log(log_value: object) -> JsonObject:
        log = clone_object(log_value, path="$/eval_log")
        samples = log.get("samples")
        if type(samples) is not list or len(samples) != 1:
            raise AdapterContractError("Inspect EvalLog must contain exactly one sample")
        sample = clone_object(samples[0], path="$/eval_log/samples/0")
        eval_spec = clone_object(log.get("eval"), path="$/eval_log/eval")
        metadata_value = clone_object(
            eval_spec.get("metadata"), path="$/eval_log/eval/metadata"
        )
        required_metadata = {
            "gitspace_task_id": "GS-TASK-000011",
            "gitspace_task_name": _TASK_NAME,
            "gitspace_sample_id": _SAMPLE_ID,
            "gitspace_framework_version": INSPECT_VERSION,
            "gitspace_framework_commit": INSPECT_COMMIT,
            "gitspace_solver": "generate",
            "gitspace_scorer": "match",
            "gitspace_scorer_options": _OPTIONS,
        }
        for key, expected in required_metadata.items():
            if metadata_value.get(key) != expected:
                raise AdapterContractError(f"Inspect EvalLog metadata mismatch: {key}")
        plan = clone_object(log.get("plan"), path="$/eval_log/plan")
        steps = plan.get("steps")
        if type(steps) is not list or len(steps) != 1:
            raise AdapterContractError("Inspect EvalLog plan must have one step")
        solver_name = clone_object(steps[0]).get("solver")
        if type(solver_name) is not str or not solver_name.endswith("generate"):
            raise AdapterContractError("Inspect EvalLog solver mismatch")
        output = clone_object(sample.get("output"), path="$/eval_log/sample/output")
        scores = clone_object(sample.get("scores"), path="$/eval_log/sample/scores")
        if len(scores) != 1:
            raise AdapterContractError("Inspect EvalLog must contain one score")
        score_name, score_raw = next(iter(scores.items()))
        if not score_name.endswith("match"):
            raise AdapterContractError("Inspect EvalLog scorer mismatch")
        score = clone_object(score_raw, path="$/eval_log/sample/score")
        events_value = sample.get("events")
        if type(events_value) is not list or not events_value:
            raise AdapterContractError("Inspect EvalLog events are missing")
        events = [clone_object(event).get("event") for event in events_value]
        if any(type(event) is not str or not event for event in events):
            raise AdapterContractError("Inspect EvalLog event type is invalid")
        projection = {
            "projection_version": 1,
            "framework": "inspect-ai",
            "framework_version": INSPECT_VERSION,
            "framework_commit": INSPECT_COMMIT,
            "eval_status": log.get("status"),
            "task": {"id": "GS-TASK-000011", "name": _TASK_NAME, "version": 1},
            "model": eval_spec.get("model"),
            "solver": {"name": "generate"},
            "scorer": {"name": "match", "options": dict(_OPTIONS)},
            "sample": {
                "id": sample.get("id"),
                "epoch": sample.get("epoch"),
                "input": sample.get("input"),
                "target": sample.get("target"),
                "output": output.get("completion"),
                "inspect_score": score.get("value"),
                "event_types": events,
            },
        }
        return project_inspect_log(projection)


def _single_eval_log(logs: object) -> EvalLog:
    logs_type = type(logs)
    official_wrapper = (
        type.__getattribute__(logs_type, "__module__") == "inspect_ai._eval.eval"
        and type.__getattribute__(logs_type, "__name__") == "EvalLogs"
    )
    if logs_type is not list and not official_wrapper:
        raise AdapterContractError("Inspect eval returned an unsupported log collection")
    try:
        count = len(logs)  # type: ignore[arg-type]
    except Exception as error:
        raise AdapterContractError("Inspect log collection has no stable cardinality") from error
    if count != 1:
        raise AdapterContractError("Inspect must return exactly one EvalLog")
    try:
        log = logs[0]  # type: ignore[index]
    except Exception as error:
        raise AdapterContractError("Inspect log collection is not indexable") from error
    if type(log) is not EvalLog:
        raise AdapterContractError("Inspect eval returned a non-EvalLog object")
    return log


def _json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as error:
        raise AdapterContractError("Inspect value is not canonical JSON") from error
