from __future__ import annotations

import math
import unicodedata
from collections.abc import Callable
from typing import TypeVar

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

T = TypeVar("T")
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
    if not isinstance(request, AdapterRequest):
        raise AdapterContractError("request must be an AdapterRequest")

    task = clone_object(request.task, path="$/task")
    agent = clone_object(request.agent, path="$/agent")
    if isinstance(request.seed, bool) or not isinstance(request.seed, int):
        raise JsonBoundaryError("$/seed: seed must be an integer")
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
    if not isinstance(status_value, str):
        raise AdapterContractError("$/result/status: expected status string")
    try:
        status = AdapterStatus(status_value)
    except ValueError as error:
        raise AdapterContractError(
            f"$/result/status: unknown normalized status {status_value!r}"
        ) from error

    summary_value = payload["summary"]
    if not isinstance(summary_value, str):
        raise AdapterContractError("$/result/summary: expected string")
    summary = _sanitize_summary(summary_value)

    artifacts_value = payload["artifacts"]
    if not isinstance(artifacts_value, dict):
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
    if not isinstance(metrics_value, dict):
        raise AdapterContractError("$/result/metrics: expected object")
    metrics: dict[str, int | float] = {}
    for name, metric in metrics_value.items():
        try:
            validated_name = validate_name(name, path=f"$/result/metrics/{name}")
        except JsonBoundaryError as error:
            raise AdapterContractError(str(error)) from error
        if isinstance(metric, bool) or not isinstance(metric, (int, float)):
            raise AdapterContractError(
                f"$/result/metrics/{name}: expected non-bool number"
            )
        if isinstance(metric, int) and not -SAFE_INTEGER <= metric <= SAFE_INTEGER:
            raise AdapterContractError(
                f"$/result/metrics/{name}: unsafe interoperable integer"
            )
        if isinstance(metric, float) and not math.isfinite(metric):
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
    return AdapterResult(
        adapter_identity=adapter_identity,
        status=status,
        summary=_sanitize_summary(f"adapter {stage} failed: {error}"),
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
