from __future__ import annotations

import hashlib
import json
import tempfile
from contextlib import contextmanager
from importlib import import_module, metadata
from pathlib import Path
from threading import Lock
from typing import Callable, Iterator

from inspect_ai import Task, eval as inspect_eval
from inspect_ai.dataset import Sample
from inspect_ai.log import EvalLog
from inspect_ai.scorer import match
from inspect_ai.solver import generate

from .errors import AdapterContractError, JsonBoundaryError
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
_INSPECT_EVAL_LOCK = Lock()


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
        with _INSPECT_EVAL_LOCK:
            with _inspect_0_3_258_event_stream_cleanup():
                with tempfile.TemporaryDirectory(
                    prefix="gitspace-inspect-"
                ) as log_dir:
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
        projection = project_inspect_log(log_value)
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
        try:
            log_uri = validate_cas_uri(value["log_uri"], path="$/inspect_raw/log_uri")
            record_uri = validate_cas_uri(
                value["record_uri"], path="$/inspect_raw/record_uri"
            )
        except JsonBoundaryError as error:
            raise AdapterContractError(str(error)) from error
        if log_uri != record.log_uri:
            raise AdapterContractError("Inspect record and raw log URI disagree")
        expected_record_uri = (
            "cas://sha256/"
            + hashlib.sha256(canonical_record_bytes(record)).hexdigest()
        )
        if record_uri != expected_record_uri:
            raise AdapterContractError("Inspect record URI does not match record bytes")
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
        try:
            uri = validate_cas_uri(
                self._publish_artifact(value), path="$/artifact_uri"
            )
        except JsonBoundaryError as error:
            raise AdapterContractError(str(error)) from error
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


@contextmanager
def _inspect_0_3_258_event_stream_cleanup() -> Iterator[None]:
    """Patch the pinned Inspect release to close its drained receive stream.

    Inspect 0.3.258 closes the sample event sender, drains the receive stream,
    then drops the active reference without closing that receiver. The adapter
    is pinned to this exact release, serializes eval calls, installs the narrow
    compatibility function only for the duration of eval, and restores the
    original private function afterwards.
    """

    try:
        hooks = import_module("inspect_ai.hooks._hooks")
        original = getattr(hooks, "drain_sample_events")
        active_sample = getattr(hooks, "active_sample")
        send_sample_events = getattr(hooks, "send_sample_events")
    except (ImportError, AttributeError) as error:
        raise AdapterContractError(
            "Inspect 0.3.258 hook cleanup API is unavailable"
        ) from error

    async def drain_sample_events_with_receiver_close() -> None:
        active = active_sample()
        if active.event_send is not None:
            await active.event_send.aclose()
            active.event_send = None
        if active.event_receive is not None:
            receive = active.event_receive
            try:
                events = [event async for event in receive]
            finally:
                await receive.aclose()
                active.event_receive = None
            await send_sample_events(events)

    setattr(hooks, "drain_sample_events", drain_sample_events_with_receiver_close)
    try:
        yield
    finally:
        setattr(hooks, "drain_sample_events", original)


def _single_eval_log(logs: object) -> EvalLog:
    logs_type = type(logs)
    if logs_type is not list:
        try:
            module = import_module("inspect_ai._eval.eval")
            official_type = getattr(module, "EvalLogs")
        except (ImportError, AttributeError) as error:
            raise AdapterContractError(
                "Inspect official EvalLogs type is unavailable"
            ) from error
        if not isinstance(official_type, type) or logs_type is not official_type:
            raise AdapterContractError(
                "Inspect eval returned an unsupported log collection"
            )
    try:
        count = len(logs)  # type: ignore[arg-type]
    except Exception as error:
        raise AdapterContractError(
            "Inspect log collection has no stable cardinality"
        ) from error
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
