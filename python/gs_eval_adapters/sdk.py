from __future__ import annotations

import math
import unicodedata

from .errors import (
    AdapterContractError,
    AdapterPolicyViolation,
    AdapterTimeout,
    JsonBoundaryError,
    SemanticLossError,
)
from .json_boundary import (
    SAFE_INTEGER,
    JsonObject,
    clone_json,
    clone_object,
    validate_cas_uri,
    validate_extensions,
    validate_name,
)
from .model import AdapterRequest, AdapterResult, AdapterStatus
from .registry import validate_adapter_object
from .schemas import validate_agent, validate_task

_RESULT_KEYS = {"status", "summary", "artifacts", "metrics", "extensions"}
_PREPARED_KEYS = {"canonical_request", "framework_request", "extensions"}


def execute_adapter(adapter: object, request: AdapterRequest) -> AdapterResult:
    descriptor = validate_adapter_object(adapter, error_type=AdapterContractError)
    canonical_request = _canonical_request(request)

    try:
        prepared_raw = adapter.prepare(clone_object(canonical_request))
    except AdapterTimeout as error:
        return _failure(descriptor.identity, AdapterStatus.TIMEOUT, "prepare", error)
    except AdapterPolicyViolation as error:
        return _failure(descriptor.identity, AdapterStatus.POLICY, "prepare", error)
    except Exception as error:
        return _failure(descriptor.identity, AdapterStatus.INFRA, "prepare", error)

    prepared = _prepared_call(prepared_raw, canonical_request)

    try:
        raw_result = adapter.invoke(clone_object(prepared, path="$/prepared"))
    except AdapterTimeout as error:
        return _failure(descriptor.identity, AdapterStatus.TIMEOUT, "invoke", error)
    except AdapterPolicyViolation as error:
        return _failure(descriptor.identity, AdapterStatus.POLICY, "invoke", error)
    except Exception as error:
        return _failure(descriptor.identity, AdapterStatus.INFRA, "invoke", error)

    raw = clone_object(raw_result, path="$/raw")

    try:
        collected = adapter.collect(clone_object(raw, path="$/raw"))
    except AdapterTimeout as error:
        return _failure(descriptor.identity, AdapterStatus.TIMEOUT, "collect", error)
    except AdapterPolicyViolation as error:
        return _failure(descriptor.identity, AdapterStatus.POLICY, "collect", error)
    except Exception as error:
        return _failure(descriptor.identity, AdapterStatus.INFRA, "collect", error)

    return _result_from_payload(descriptor.identity, collected)


def _canonical_request(request: AdapterRequest) -> JsonObject:
    if type(request) is not AdapterRequest:
        raise AdapterContractError("request must be an exact AdapterRequest")

    task = clone_object(request.task, path="$/task")
    agent = clone_object(request.agent, path="$/agent")
    if type(request.seed) is not int:
        raise JsonBoundaryError("$/seed: seed must be an exact integer")
    seed = clone_json(request.seed, path="$/seed")
    extensions = validate_extensions(request.extensions, path="$/extensions")

    validate_task(task)
    validate_agent(agent)

    return {
        "version": 1,
        "task": task,
        "agent": agent,
        "seed": seed,
        "extensions": extensions,
    }


def _prepared_call(value: object, canonical_request: JsonObject) -> JsonObject:
    prepared = clone_object(value, path="$/prepared")
    _require_exact_keys(prepared, _PREPARED_KEYS, path="$/prepared")

    snapshot = clone_object(
        prepared["canonical_request"],
        path="$/prepared/canonical_request",
    )
    if snapshot != canonical_request:
        raise SemanticLossError(
            "prepared canonical_request differs from the validated GitSpace request"
        )

    framework_request = clone_object(
        prepared["framework_request"],
        path="$/prepared/framework_request",
    )
    extensions = validate_extensions(
        prepared["extensions"],
        path="$/prepared/extensions",
    )
    return {
        "canonical_request": snapshot,
        "framework_request": framework_request,
        "extensions": extensions,
    }


def _result_from_payload(adapter_identity: str, value: object) -> AdapterResult:
    try:
        payload = clone_object(value, path="$/result")
    except JsonBoundaryError as error:
        raise AdapterContractError(str(error)) from error
    _require_exact_keys(payload, _RESULT_KEYS, path="$/result")

    status_value = payload["status"]
    if type(status_value) is not str:
        raise AdapterContractError("$/result/status: expected exact status string")
    try:
        status = AdapterStatus(status_value)
    except ValueError as error:
        raise AdapterContractError(
            f"$/result/status: unknown normalized status {status_value!r}"
        ) from error

    summary_value = payload["summary"]
    if type(summary_value) is not str:
        raise AdapterContractError("$/result/summary: expected exact string")
    summary = _sanitize_summary(summary_value)

    artifacts_value = payload["artifacts"]
    if type(artifacts_value) is not dict:
        raise AdapterContractError("$/result/artifacts: expected object")
    artifacts: dict[str, str] = {}
    for name, uri in artifacts_value.items():
        try:
            validated_name = validate_name(name, path=f"$/result/artifacts/{name}")
            artifacts[validated_name] = validate_cas_uri(
                uri,
                path=f"$/result/artifacts/{name}",
            )
        except JsonBoundaryError as error:
            raise AdapterContractError(str(error)) from error

    metrics_value = payload["metrics"]
    if type(metrics_value) is not dict:
        raise AdapterContractError("$/result/metrics: expected object")
    metrics: dict[str, int | float] = {}
    for name, metric in metrics_value.items():
        try:
            validated_name = validate_name(name, path=f"$/result/metrics/{name}")
        except JsonBoundaryError as error:
            raise AdapterContractError(str(error)) from error
        if type(metric) not in (int, float):
            raise AdapterContractError(
                f"$/result/metrics/{name}: expected exact non-bool number"
            )
        if type(metric) is int and not -SAFE_INTEGER <= metric <= SAFE_INTEGER:
            raise AdapterContractError(
                f"$/result/metrics/{name}: unsafe interoperable integer"
            )
        if type(metric) is float and not math.isfinite(metric):
            raise AdapterContractError(
                f"$/result/metrics/{name}: non-finite metric"
            )
        metrics[validated_name] = metric

    extensions = validate_extensions(
        payload["extensions"],
        path="$/result/extensions",
    )
    return AdapterResult(
        adapter_identity=adapter_identity,
        status=status,
        summary=summary,
        artifacts=artifacts,
        metrics=metrics,
        extensions=extensions,
    )


def _failure(
    adapter_identity: str,
    status: AdapterStatus,
    stage: str,
    error: BaseException,
) -> AdapterResult:
    error_type = f"{type(error).__module__}.{type(error).__qualname__}"
    try:
        detail = str(error)
    except Exception:
        detail = "<unprintable exception message>"
    return AdapterResult(
        adapter_identity=adapter_identity,
        status=status,
        summary=_sanitize_summary(f"adapter {stage} failed: {error_type}: {detail}"),
        artifacts={},
        metrics={},
        extensions={},
    )


def _require_exact_keys(value: JsonObject, expected: set[str], *, path: str) -> None:
    actual = set(value)
    if actual == expected:
        return
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    details = []
    if missing:
        details.append(f"missing={missing}")
    if unknown:
        details.append(f"unknown={unknown}")
    raise AdapterContractError(f"{path}: core fields differ ({', '.join(details)})")


def _sanitize_summary(value: str) -> str:
    normalized = []
    for character in value:
        if character in "\r\n\t" or unicodedata.category(character).startswith("C"):
            normalized.append(" ")
        else:
            normalized.append(character)
    return " ".join("".join(normalized).split())[:512]
