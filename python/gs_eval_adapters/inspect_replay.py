from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Final

from .errors import AdapterContractError, JsonBoundaryError
from .json_boundary import JsonObject, JsonValue, clone_object, validate_cas_uri
from .model import AdapterStatus

INSPECT_VERSION: Final = "0.3.258"
INSPECT_TAG: Final = "0.3.258"
INSPECT_COMMIT: Final = "e72c73f8a514c53ddf55da180e4bedaf8f0362b4"
INSPECT_WHEEL_SHA256: Final = (
    "638da28a5f3a021152481c5aa22d440a2855e462804dce2d49a44e6e47be16a4"
)

_CAS_URI_PREFIX = "cas://sha256/"
_EXPECTED = {
    "framework": "inspect-ai",
    "framework_version": INSPECT_VERSION,
    "framework_commit": INSPECT_COMMIT,
    "task_id": "GS-TASK-000011",
    "task_name": "gitspace_inspect_controlled",
    "sample_id": "GS-SAMPLE-000011",
    "model": "mockllm/model",
    "solver": "generate",
    "scorer": "match",
}
_OPTIONS: JsonObject = {
    "location": "exact",
    "ignore_case": True,
    "numeric": False,
}
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_RECORD_FIELDS = {
    "version",
    "framework",
    "framework_version",
    "framework_commit",
    "task_id",
    "task_name",
    "sample_id",
    "model",
    "solver",
    "scorer",
    "scorer_options",
    "input",
    "target",
    "output",
    "inspect_status",
    "inspect_score",
    "event_types",
    "log_sha256",
    "log_uri",
}
_PROJECTION_FIELDS = {
    "projection_version",
    "framework",
    "framework_version",
    "framework_commit",
    "eval_status",
    "task",
    "model",
    "solver",
    "scorer",
    "sample",
}
_OBLIGATION_FIELDS = {
    "qualification_pinned",
    "status_success",
    "events_present",
    "log_content_addressed",
    "output_matches_target",
    "inspect_score_agrees",
}


@dataclass(frozen=True, slots=True)
class InspectReplayRecord:
    version: int
    framework: str
    framework_version: str
    framework_commit: str
    task_id: str
    task_name: str
    sample_id: str
    model: str
    solver: str
    scorer: str
    scorer_options: dict[str, JsonValue]
    input: str
    target: str
    output: str
    inspect_status: str
    inspect_score: str
    event_types: tuple[str, ...]
    log_sha256: str
    log_uri: str

    def __post_init__(self) -> None:
        _validate_record(self)
        object.__setattr__(self, "scorer_options", dict(self.scorer_options))
        object.__setattr__(self, "event_types", tuple(self.event_types))

    @classmethod
    def from_json(cls, value: object) -> "InspectReplayRecord":
        data = clone_object(value, path="$/inspect_record")
        _exact_fields(data, _RECORD_FIELDS, "inspect_record")
        events = data["event_types"]
        if type(events) is not list:
            raise AdapterContractError("event_types must be an array")
        return cls(
            version=_exact_int(data["version"], "version"),
            framework=_exact_string(data["framework"], "framework"),
            framework_version=_exact_string(
                data["framework_version"], "framework_version"
            ),
            framework_commit=_exact_string(
                data["framework_commit"], "framework_commit"
            ),
            task_id=_exact_string(data["task_id"], "task_id"),
            task_name=_exact_string(data["task_name"], "task_name"),
            sample_id=_exact_string(data["sample_id"], "sample_id"),
            model=_exact_string(data["model"], "model"),
            solver=_exact_string(data["solver"], "solver"),
            scorer=_exact_string(data["scorer"], "scorer"),
            scorer_options=clone_object(
                data["scorer_options"], path="$/inspect_record/scorer_options"
            ),
            input=_exact_string(data["input"], "input"),
            target=_exact_string(data["target"], "target"),
            output=_exact_string(data["output"], "output"),
            inspect_status=_exact_string(data["inspect_status"], "inspect_status"),
            inspect_score=_exact_string(data["inspect_score"], "inspect_score"),
            event_types=tuple(
                _exact_string(item, "event_type") for item in events
            ),
            log_sha256=_exact_string(data["log_sha256"], "log_sha256"),
            log_uri=_exact_string(data["log_uri"], "log_uri"),
        )

    def to_json(self) -> JsonObject:
        _validate_record(self)
        return {
            "version": self.version,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "framework_commit": self.framework_commit,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "sample_id": self.sample_id,
            "model": self.model,
            "solver": self.solver,
            "scorer": self.scorer,
            "scorer_options": dict(self.scorer_options),
            "input": self.input,
            "target": self.target,
            "output": self.output,
            "inspect_status": self.inspect_status,
            "inspect_score": self.inspect_score,
            "event_types": list(self.event_types),
            "log_sha256": self.log_sha256,
            "log_uri": self.log_uri,
        }


@dataclass(frozen=True, slots=True)
class InspectReplayResult:
    status: AdapterStatus
    score: str
    obligations: dict[str, bool]
    record_sha256: str

    def __post_init__(self) -> None:
        _validate_replay_result(self)
        object.__setattr__(self, "obligations", dict(self.obligations))

    def to_json(self) -> JsonObject:
        _validate_replay_result(self)
        return {
            "status": self.status.value,
            "score": self.score,
            "obligations": dict(self.obligations),
            "record_sha256": self.record_sha256,
        }


def project_inspect_log(log_value: object) -> JsonObject:
    data = clone_object(log_value, path="$/inspect_log")
    if "projection_version" in data:
        return _validate_projection(data)
    return _project_full_eval_log(data)


def build_replay_record(
    projection: object,
    *,
    log_bytes: bytes,
    log_uri: str,
) -> InspectReplayRecord:
    if type(log_bytes) is not bytes:
        raise AdapterContractError("log_bytes must be exact bytes")
    projected = project_inspect_log(projection)
    try:
        uri = validate_cas_uri(log_uri, path="$/log_uri")
    except JsonBoundaryError as error:
        raise AdapterContractError(str(error)) from error
    digest = hashlib.sha256(log_bytes).hexdigest()
    if uri != f"{_CAS_URI_PREFIX}{digest}":
        raise AdapterContractError("log URI does not match log bytes")

    task = clone_object(projected["task"], path="$/projection/task")
    solver = clone_object(projected["solver"], path="$/projection/solver")
    scorer = clone_object(projected["scorer"], path="$/projection/scorer")
    sample = clone_object(projected["sample"], path="$/projection/sample")
    events = sample["event_types"]
    if type(events) is not list:
        raise AdapterContractError("projection event_types must be an array")

    return InspectReplayRecord(
        version=1,
        framework=_exact_string(projected["framework"], "framework"),
        framework_version=_exact_string(
            projected["framework_version"], "framework_version"
        ),
        framework_commit=_exact_string(
            projected["framework_commit"], "framework_commit"
        ),
        task_id=_exact_string(task["id"], "task_id"),
        task_name=_exact_string(task["name"], "task_name"),
        sample_id=_exact_string(sample["id"], "sample_id"),
        model=_exact_string(projected["model"], "model"),
        solver=_exact_string(solver["name"], "solver"),
        scorer=_exact_string(scorer["name"], "scorer"),
        scorer_options=clone_object(
            scorer["options"], path="$/projection/scorer/options"
        ),
        input=_exact_string(sample["input"], "input"),
        target=_exact_string(sample["target"], "target"),
        output=_exact_string(sample["output"], "output"),
        inspect_status=_exact_string(projected["eval_status"], "inspect_status"),
        inspect_score=_exact_string(sample["inspect_score"], "inspect_score"),
        event_types=tuple(_exact_string(item, "event_type") for item in events),
        log_sha256=f"sha256:{digest}",
        log_uri=uri,
    )


def canonical_record_bytes(record: InspectReplayRecord) -> bytes:
    if type(record) is not InspectReplayRecord:
        raise AdapterContractError("expected InspectReplayRecord")
    _validate_record(record)
    return _canonical_json_bytes(record.to_json())


def rescore_inspect_record(
    record: InspectReplayRecord | object,
) -> InspectReplayResult:
    parsed = (
        record
        if type(record) is InspectReplayRecord
        else InspectReplayRecord.from_json(record)
    )
    _validate_record(parsed)
    matched = _normalize(parsed.output) == _normalize(parsed.target)
    score = "C" if matched else "I"
    agrees = parsed.inspect_score == score
    obligations = {
        "qualification_pinned": all(
            getattr(parsed, key) == value for key, value in _EXPECTED.items()
        ),
        "status_success": parsed.inspect_status == "success",
        "events_present": bool(parsed.event_types),
        "log_content_addressed": (
            parsed.log_uri
            == f"{_CAS_URI_PREFIX}{parsed.log_sha256.removeprefix('sha256:')}"
        ),
        "output_matches_target": matched,
        "inspect_score_agrees": agrees,
    }
    if parsed.inspect_status != "success" or not agrees:
        status = AdapterStatus.INFRA
    else:
        status = AdapterStatus.PASS if matched else AdapterStatus.FAIL
    return InspectReplayResult(
        status=status,
        score=score,
        obligations=obligations,
        record_sha256=(
            "sha256:" + hashlib.sha256(canonical_record_bytes(parsed)).hexdigest()
        ),
    )


def _project_full_eval_log(log: JsonObject) -> JsonObject:
    status = _exact_string(log.get("status"), "status")
    eval_spec = clone_object(log.get("eval"), path="$/inspect_log/eval")
    plan = clone_object(log.get("plan"), path="$/inspect_log/plan")
    samples = log.get("samples")
    if type(samples) is not list or len(samples) != 1:
        raise AdapterContractError("Inspect log must contain exactly one sample")
    sample = clone_object(samples[0], path="$/inspect_log/samples/0")

    metadata = clone_object(
        eval_spec.get("metadata"), path="$/inspect_log/eval/metadata"
    )
    required_metadata: JsonObject = {
        "gitspace_task_id": _EXPECTED["task_id"],
        "gitspace_task_name": _EXPECTED["task_name"],
        "gitspace_sample_id": _EXPECTED["sample_id"],
        "gitspace_framework_version": INSPECT_VERSION,
        "gitspace_framework_commit": INSPECT_COMMIT,
        "gitspace_solver": _EXPECTED["solver"],
        "gitspace_scorer": _EXPECTED["scorer"],
        "gitspace_scorer_options": dict(_OPTIONS),
    }
    for key, expected in required_metadata.items():
        if metadata.get(key) != expected:
            raise AdapterContractError(f"Inspect log metadata mismatch for {key}")

    steps = plan.get("steps")
    if type(steps) is not list or len(steps) != 1:
        raise AdapterContractError("Inspect plan must contain exactly one solver step")
    step = clone_object(steps[0], path="$/inspect_log/plan/steps/0")
    solver_name = _exact_string(step.get("solver"), "plan.solver")
    if not solver_name.endswith(_EXPECTED["solver"]):
        raise AdapterContractError("Inspect plan solver is not generate")

    sample_id = _exact_string(sample.get("id"), "sample.id")
    input_value = _exact_string(sample.get("input"), "sample.input")
    target_value = _exact_string(sample.get("target"), "sample.target")
    output_value = clone_object(
        sample.get("output"), path="$/inspect_log/sample/output"
    )
    completion = _exact_string(
        output_value.get("completion"), "sample.output.completion"
    )

    scores = clone_object(sample.get("scores"), path="$/inspect_log/sample/scores")
    if len(scores) != 1:
        raise AdapterContractError("Inspect sample must contain exactly one score")
    score_name, score_raw = next(iter(scores.items()))
    if not score_name.endswith(_EXPECTED["scorer"]):
        raise AdapterContractError("Inspect sample score is not match")
    score_value = clone_object(score_raw, path="$/inspect_log/sample/score")
    inspect_score = _exact_string(score_value.get("value"), "sample.score.value")

    events_value = sample.get("events")
    if type(events_value) is not list or not events_value:
        raise AdapterContractError("Inspect sample events must be non-empty")
    event_types: list[JsonValue] = []
    for index, event_value in enumerate(events_value):
        event = clone_object(
            event_value, path=f"$/inspect_log/sample/events/{index}"
        )
        event_types.append(
            _exact_string(event.get("event"), f"event[{index}].event")
        )

    return _validate_projection(
        {
            "projection_version": 1,
            "framework": _EXPECTED["framework"],
            "framework_version": INSPECT_VERSION,
            "framework_commit": INSPECT_COMMIT,
            "eval_status": status,
            "task": {
                "id": metadata["gitspace_task_id"],
                "name": metadata["gitspace_task_name"],
                "version": 1,
            },
            "model": _exact_string(eval_spec.get("model"), "eval.model"),
            "solver": {"name": _EXPECTED["solver"]},
            "scorer": {
                "name": _EXPECTED["scorer"],
                "options": dict(_OPTIONS),
            },
            "sample": {
                "id": sample_id,
                "epoch": _exact_int(sample.get("epoch"), "sample.epoch"),
                "input": input_value,
                "target": target_value,
                "output": completion,
                "inspect_score": inspect_score,
                "event_types": event_types,
            },
        }
    )


def _validate_projection(projection: JsonObject) -> JsonObject:
    _exact_fields(projection, _PROJECTION_FIELDS, "inspect_projection")
    _validate_projection_header(projection)
    _validate_projection_task(projection["task"])
    _validate_projection_model(projection["model"])
    _validate_projection_solver(projection["solver"])
    _validate_projection_scorer(projection["scorer"])
    _validate_projection_sample(projection["sample"])
    return clone_object(projection, path="$/projection")


def _validate_projection_header(projection: JsonObject) -> None:
    if _exact_int(
        projection["projection_version"], "projection_version"
    ) != 1:
        raise AdapterContractError("projection version mismatch")
    expected = {
        "framework": _EXPECTED["framework"],
        "framework_version": INSPECT_VERSION,
        "framework_commit": INSPECT_COMMIT,
    }
    for field, value in expected.items():
        if projection[field] != value:
            raise AdapterContractError(f"projection {field} mismatch")
    if projection["eval_status"] not in {"success", "error", "cancelled"}:
        raise AdapterContractError("projection status invalid")


def _validate_projection_task(value: JsonValue) -> None:
    task = clone_object(value, path="$/projection/task")
    _exact_fields(task, {"id", "name", "version"}, "projection.task")
    if (
        task["id"] != _EXPECTED["task_id"]
        or task["name"] != _EXPECTED["task_name"]
        or _exact_int(task["version"], "task.version") != 1
    ):
        raise AdapterContractError("projection task mismatch")


def _validate_projection_model(value: JsonValue) -> None:
    if value != _EXPECTED["model"]:
        raise AdapterContractError("projection model mismatch")


def _validate_projection_solver(value: JsonValue) -> None:
    solver = clone_object(value, path="$/projection/solver")
    if solver != {"name": _EXPECTED["solver"]}:
        raise AdapterContractError("projection solver mismatch")


def _validate_projection_scorer(value: JsonValue) -> None:
    scorer = clone_object(value, path="$/projection/scorer")
    _exact_fields(scorer, {"name", "options"}, "projection.scorer")
    if scorer["name"] != _EXPECTED["scorer"]:
        raise AdapterContractError("projection scorer mismatch")
    options = clone_object(
        scorer["options"], path="$/projection/scorer/options"
    )
    if options != _OPTIONS:
        raise AdapterContractError("projection scorer options mismatch")


def _validate_projection_sample(value: JsonValue) -> None:
    sample = clone_object(value, path="$/projection/sample")
    _exact_fields(
        sample,
        {
            "id",
            "epoch",
            "input",
            "target",
            "output",
            "inspect_score",
            "event_types",
        },
        "projection.sample",
    )
    if (
        sample["id"] != _EXPECTED["sample_id"]
        or _exact_int(sample["epoch"], "sample.epoch") != 1
    ):
        raise AdapterContractError("projection sample mismatch")
    for field in ("input", "target", "output"):
        _exact_nonempty_string(sample[field], f"sample.{field}")
    if sample["inspect_score"] not in {"C", "I"}:
        raise AdapterContractError("projection score invalid")
    events = sample["event_types"]
    if type(events) is not list or not events:
        raise AdapterContractError("projection event_types invalid")
    for event_type in events:
        _exact_nonempty_string(event_type, "sample.event_type")


def _validate_record(record: InspectReplayRecord) -> None:
    _validate_record_version_and_identity(record)
    _validate_record_options(record)
    _validate_record_text(record)
    _validate_record_status_and_score(record)
    _validate_record_events(record)
    _validate_record_log_reference(record)


def _validate_record_version_and_identity(record: InspectReplayRecord) -> None:
    if type(record.version) is not int or record.version != 1:
        raise AdapterContractError("record version mismatch")
    for field, expected in _EXPECTED.items():
        actual = getattr(record, field)
        if type(actual) is not str or actual != expected:
            raise AdapterContractError(f"record {field} mismatch")


def _validate_record_options(record: InspectReplayRecord) -> None:
    if type(record.scorer_options) is not dict:
        raise AdapterContractError("record scorer options must be an exact dict")
    try:
        options = clone_object(
            record.scorer_options, path="$/inspect_record/scorer_options"
        )
    except JsonBoundaryError as error:
        raise AdapterContractError(str(error)) from error
    if options != _OPTIONS:
        raise AdapterContractError("record scorer options mismatch")


def _validate_record_text(record: InspectReplayRecord) -> None:
    for field in ("input", "target", "output"):
        _exact_nonempty_string(getattr(record, field), f"record.{field}")


def _validate_record_status_and_score(record: InspectReplayRecord) -> None:
    if type(record.inspect_status) is not str or record.inspect_status not in {
        "success",
        "error",
        "cancelled",
    }:
        raise AdapterContractError("record status invalid")
    if type(record.inspect_score) is not str or record.inspect_score not in {
        "C",
        "I",
    }:
        raise AdapterContractError("record score invalid")


def _validate_record_events(record: InspectReplayRecord) -> None:
    if type(record.event_types) is not tuple or not record.event_types:
        raise AdapterContractError("record event_types invalid")
    for event_type in record.event_types:
        _exact_nonempty_string(event_type, "record.event_type")


def _validate_record_log_reference(record: InspectReplayRecord) -> None:
    if type(record.log_sha256) is not str or not _DIGEST.fullmatch(
        record.log_sha256
    ):
        raise AdapterContractError("record log digest invalid")
    try:
        log_uri = validate_cas_uri(
            record.log_uri, path="$/inspect_record/log_uri"
        )
    except JsonBoundaryError as error:
        raise AdapterContractError(str(error)) from error
    expected_uri = f"{_CAS_URI_PREFIX}{record.log_sha256.removeprefix('sha256:')}"
    if log_uri != expected_uri:
        raise AdapterContractError("record log digest and URI disagree")


def _validate_replay_result(result: InspectReplayResult) -> None:
    if type(result.status) is not AdapterStatus:
        raise AdapterContractError("replay status must be AdapterStatus")
    if type(result.score) is not str or result.score not in {"C", "I", "INFRA"}:
        raise AdapterContractError("replay score is invalid")
    if result.status is AdapterStatus.PASS and result.score != "C":
        raise AdapterContractError("PASS replay requires score C")
    if result.status is AdapterStatus.FAIL and result.score != "I":
        raise AdapterContractError("FAIL replay requires score I")
    if type(result.obligations) is not dict:
        raise AdapterContractError("replay obligations must be an exact dict")
    if set(result.obligations) != _OBLIGATION_FIELDS:
        raise AdapterContractError("replay obligation fields differ")
    if any(type(value) is not bool for value in result.obligations.values()):
        raise AdapterContractError("replay obligations must contain exact booleans")
    if type(result.record_sha256) is not str or not _DIGEST.fullmatch(
        result.record_sha256
    ):
        raise AdapterContractError("replay record digest is invalid")


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in value.strip().casefold()
        if not unicodedata.category(character).startswith("P")
    )


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise AdapterContractError("value is not canonical JSON") from error


def _exact_fields(value: JsonObject, expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise AdapterContractError(
            f"{label} fields differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def _exact_string(value: object, field: str) -> str:
    if type(value) is not str:
        raise AdapterContractError(f"{field} must be an exact string")
    try:
        clone_object({"value": value}, path=f"$/{field}")
    except JsonBoundaryError as error:
        raise AdapterContractError(str(error)) from error
    return value


def _exact_nonempty_string(value: object, field: str) -> str:
    text = _exact_string(value, field)
    if not text:
        raise AdapterContractError(f"{field} must be non-empty")
    return text


def _exact_int(value: object, field: str) -> int:
    if type(value) is not int:
        raise AdapterContractError(f"{field} must be an exact integer")
    return value
