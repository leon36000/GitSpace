from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Final

from .errors import AdapterContractError
from .json_boundary import JsonObject, JsonValue, clone_object, validate_cas_uri
from .model import AdapterStatus

INSPECT_VERSION: Final = "0.3.258"
INSPECT_TAG: Final = "0.3.258"
INSPECT_COMMIT: Final = "e72c73f8a514c53ddf55da180e4bedaf8f0362b4"
INSPECT_WHEEL_SHA256: Final = "638da28a5f3a021152481c5aa22d440a2855e462804dce2d49a44e6e47be16a4"

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
_OPTIONS: JsonObject = {"location": "exact", "ignore_case": True, "numeric": False}
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_RECORD_FIELDS = {
    "version", "framework", "framework_version", "framework_commit", "task_id",
    "task_name", "sample_id", "model", "solver", "scorer", "scorer_options",
    "input", "target", "output", "inspect_status", "inspect_score", "event_types",
    "log_sha256", "log_uri",
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
            version=_int(data["version"], "version"),
            framework=_str(data["framework"], "framework"),
            framework_version=_str(data["framework_version"], "framework_version"),
            framework_commit=_str(data["framework_commit"], "framework_commit"),
            task_id=_str(data["task_id"], "task_id"),
            task_name=_str(data["task_name"], "task_name"),
            sample_id=_str(data["sample_id"], "sample_id"),
            model=_str(data["model"], "model"),
            solver=_str(data["solver"], "solver"),
            scorer=_str(data["scorer"], "scorer"),
            scorer_options=clone_object(data["scorer_options"]),
            input=_str(data["input"], "input"),
            target=_str(data["target"], "target"),
            output=_str(data["output"], "output"),
            inspect_status=_str(data["inspect_status"], "inspect_status"),
            inspect_score=_str(data["inspect_score"], "inspect_score"),
            event_types=tuple(_str(item, "event_type") for item in events),
            log_sha256=_str(data["log_sha256"], "log_sha256"),
            log_uri=_str(data["log_uri"], "log_uri"),
        )

    def to_json(self) -> JsonObject:
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

    def to_json(self) -> JsonObject:
        return {
            "status": self.status.value,
            "score": self.score,
            "obligations": dict(self.obligations),
            "record_sha256": self.record_sha256,
        }


def project_inspect_log(value: object) -> JsonObject:
    projection = clone_object(value, path="$/inspect_projection")
    fields = {
        "projection_version", "framework", "framework_version", "framework_commit",
        "eval_status", "task", "model", "solver", "scorer", "sample",
    }
    _exact_fields(projection, fields, "inspect_projection")
    if projection["projection_version"] != 1:
        raise AdapterContractError("projection version mismatch")
    if projection["framework"] != _EXPECTED["framework"]:
        raise AdapterContractError("projection framework mismatch")
    if projection["framework_version"] != INSPECT_VERSION:
        raise AdapterContractError("projection version mismatch")
    if projection["framework_commit"] != INSPECT_COMMIT:
        raise AdapterContractError("projection commit mismatch")
    if projection["eval_status"] not in {"success", "error", "cancelled"}:
        raise AdapterContractError("projection status invalid")

    task = clone_object(projection["task"])
    if task != {"id": _EXPECTED["task_id"], "name": _EXPECTED["task_name"], "version": 1}:
        raise AdapterContractError("projection task mismatch")
    if projection["model"] != _EXPECTED["model"]:
        raise AdapterContractError("projection model mismatch")
    if clone_object(projection["solver"]) != {"name": _EXPECTED["solver"]}:
        raise AdapterContractError("projection solver mismatch")
    scorer = clone_object(projection["scorer"])
    if scorer != {"name": _EXPECTED["scorer"], "options": _OPTIONS}:
        raise AdapterContractError("projection scorer mismatch")

    sample = clone_object(projection["sample"])
    _exact_fields(
        sample,
        {"id", "epoch", "input", "target", "output", "inspect_score", "event_types"},
        "sample",
    )
    if sample["id"] != _EXPECTED["sample_id"] or sample["epoch"] != 1:
        raise AdapterContractError("projection sample mismatch")
    for field in ("input", "target", "output"):
        if type(sample[field]) is not str or not sample[field]:
            raise AdapterContractError(f"projection {field} invalid")
    if sample["inspect_score"] not in {"C", "I"}:
        raise AdapterContractError("projection score invalid")
    events = sample["event_types"]
    if type(events) is not list or not events or any(type(item) is not str or not item for item in events):
        raise AdapterContractError("projection event_types invalid")
    return clone_object(projection)


def build_replay_record(
    projection: object, *, log_bytes: bytes, log_uri: str
) -> InspectReplayRecord:
    if type(log_bytes) is not bytes:
        raise AdapterContractError("log_bytes must be exact bytes")
    projected = project_inspect_log(projection)
    uri = validate_cas_uri(log_uri, path="$/log_uri")
    digest = hashlib.sha256(log_bytes).hexdigest()
    if uri != f"cas://sha256/{digest}":
        raise AdapterContractError("log URI does not match log bytes")
    task = clone_object(projected["task"])
    solver = clone_object(projected["solver"])
    scorer = clone_object(projected["scorer"])
    sample = clone_object(projected["sample"])
    return InspectReplayRecord(
        version=1,
        framework=_str(projected["framework"], "framework"),
        framework_version=_str(projected["framework_version"], "framework_version"),
        framework_commit=_str(projected["framework_commit"], "framework_commit"),
        task_id=_str(task["id"], "task_id"),
        task_name=_str(task["name"], "task_name"),
        sample_id=_str(sample["id"], "sample_id"),
        model=_str(projected["model"], "model"),
        solver=_str(solver["name"], "solver"),
        scorer=_str(scorer["name"], "scorer"),
        scorer_options=clone_object(scorer["options"]),
        input=_str(sample["input"], "input"),
        target=_str(sample["target"], "target"),
        output=_str(sample["output"], "output"),
        inspect_status=_str(projected["eval_status"], "inspect_status"),
        inspect_score=_str(sample["inspect_score"], "inspect_score"),
        event_types=tuple(_str(item, "event_type") for item in sample["event_types"]),
        log_sha256=f"sha256:{digest}",
        log_uri=uri,
    )


def canonical_record_bytes(record: InspectReplayRecord) -> bytes:
    if type(record) is not InspectReplayRecord:
        raise AdapterContractError("expected InspectReplayRecord")
    return _json_bytes(record.to_json())


def rescore_inspect_record(record: InspectReplayRecord | object) -> InspectReplayResult:
    parsed = record if type(record) is InspectReplayRecord else InspectReplayRecord.from_json(record)
    matched = _normalize(parsed.output) == _normalize(parsed.target)
    score = "C" if matched else "I"
    agrees = parsed.inspect_score == score
    obligations = {
        "qualification_pinned": all(getattr(parsed, key) == value for key, value in _EXPECTED.items()),
        "status_success": parsed.inspect_status == "success",
        "events_present": bool(parsed.event_types),
        "log_content_addressed": parsed.log_uri.endswith(parsed.log_sha256[7:]),
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
        record_sha256="sha256:" + hashlib.sha256(canonical_record_bytes(parsed)).hexdigest(),
    )


def _validate_record(record: InspectReplayRecord) -> None:
    if type(record.version) is not int or record.version != 1:
        raise AdapterContractError("record version mismatch")
    for field, expected in _EXPECTED.items():
        if getattr(record, field) != expected:
            raise AdapterContractError(f"record {field} mismatch")
    if record.scorer_options != _OPTIONS:
        raise AdapterContractError("record scorer options mismatch")
    for field in ("input", "target", "output"):
        if type(getattr(record, field)) is not str or not getattr(record, field):
            raise AdapterContractError(f"record {field} invalid")
    if record.inspect_status not in {"success", "error", "cancelled"}:
        raise AdapterContractError("record status invalid")
    if record.inspect_score not in {"C", "I"}:
        raise AdapterContractError("record score invalid")
    if type(record.event_types) is not tuple or not record.event_types:
        raise AdapterContractError("record event_types invalid")
    if any(type(item) is not str or not item for item in record.event_types):
        raise AdapterContractError("record event type invalid")
    if not _DIGEST.fullmatch(record.log_sha256):
        raise AdapterContractError("record log digest invalid")
    validate_cas_uri(record.log_uri, path="$/inspect_record/log_uri")
    if record.log_uri[13:] != record.log_sha256[7:]:
        raise AdapterContractError("record log digest and URI disagree")


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in value.strip().casefold()
        if not unicodedata.category(character).startswith("P")
    )


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
        raise AdapterContractError("value is not canonical JSON") from error


def _exact_fields(value: JsonObject, expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise AdapterContractError(
            f"{label} fields differ: missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )


def _str(value: object, field: str) -> str:
    if type(value) is not str:
        raise AdapterContractError(f"{field} must be exact string")
    return value


def _int(value: object, field: str) -> int:
    if type(value) is not int:
        raise AdapterContractError(f"{field} must be exact integer")
    return value
