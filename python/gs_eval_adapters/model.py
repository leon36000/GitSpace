from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from .errors import AdapterContractError, JsonBoundaryError
from .json_boundary import (
    SAFE_INTEGER,
    JsonObject,
    JsonValue,
    clone_object,
    validate_cas_uri,
    validate_extensions,
    validate_name,
)

_DESCRIPTOR_NAME = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class AdapterStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"
    POLICY = "policy"
    INFRA = "infra"


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    name: str
    version: str
    protocol_version: int
    implementation_digest: str

    def __post_init__(self) -> None:
        if type(self.name) is not str or not _DESCRIPTOR_NAME.fullmatch(self.name):
            raise AdapterContractError("adapter descriptor name is invalid")
        if (
            type(self.version) is not str
            or not self.version
            or not all(32 <= ord(char) <= 126 for char in self.version)
        ):
            raise AdapterContractError("adapter descriptor version is invalid")
        if type(self.protocol_version) is not int or self.protocol_version != 1:
            raise AdapterContractError("adapter protocol_version must be the exact integer 1")
        if (
            type(self.implementation_digest) is not str
            or not _DIGEST.fullmatch(self.implementation_digest)
        ):
            raise AdapterContractError("adapter implementation_digest is invalid")

    @property
    def identity(self) -> str:
        return (
            f"{self.name}@{self.version}/protocol-{self.protocol_version}/"
            f"{self.implementation_digest}"
        )


@dataclass(frozen=True, slots=True)
class AdapterRequest:
    task: dict[str, JsonValue]
    agent: dict[str, JsonValue]
    seed: int
    extensions: dict[str, JsonValue] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AdapterResult:
    adapter_identity: str
    status: AdapterStatus
    summary: str
    artifacts: dict[str, str]
    metrics: dict[str, int | float]
    extensions: dict[str, JsonValue]

    def __post_init__(self) -> None:
        if (
            type(self.adapter_identity) is not str
            or not self.adapter_identity
            or len(self.adapter_identity) > 512
            or any(
                ord(character) < 32
                or ord(character) > 126
                or unicodedata.category(character).startswith("C")
                for character in self.adapter_identity
            )
        ):
            raise AdapterContractError("adapter result identity is invalid")
        if type(self.status) is not AdapterStatus:
            raise AdapterContractError("adapter result status must be an AdapterStatus")
        if (
            type(self.summary) is not str
            or len(self.summary) > 512
            or any(
                character in "\r\n\t"
                or unicodedata.category(character).startswith("C")
                for character in self.summary
            )
        ):
            raise AdapterContractError(
                "adapter result summary must be bounded single-line Unicode text"
            )
        if type(self.artifacts) is not dict:
            raise AdapterContractError("adapter result artifacts must be an exact dict")
        if type(self.metrics) is not dict:
            raise AdapterContractError("adapter result metrics must be an exact dict")

        artifacts: dict[str, str] = {}
        for name, uri in self.artifacts.items():
            if type(name) is not str:
                name_type = type(name)
                raise AdapterContractError(
                    "$/artifacts: key type "
                    f"{name_type.__module__}.{name_type.__qualname__} "
                    "is not an exact string"
                )
            path = f"$/artifacts/{name}"
            try:
                validated_name = validate_name(name, path=path)
                artifacts[validated_name] = validate_cas_uri(uri, path=path)
            except JsonBoundaryError as error:
                raise AdapterContractError(str(error)) from error

        metrics: dict[str, int | float] = {}
        for name, metric in self.metrics.items():
            if type(name) is not str:
                name_type = type(name)
                raise AdapterContractError(
                    "$/metrics: key type "
                    f"{name_type.__module__}.{name_type.__qualname__} "
                    "is not an exact string"
                )
            path = f"$/metrics/{name}"
            try:
                validated_name = validate_name(name, path=path)
            except JsonBoundaryError as error:
                raise AdapterContractError(str(error)) from error
            if type(metric) not in (int, float):
                raise AdapterContractError(
                    f"{path}: expected exact non-bool number"
                )
            if type(metric) is int and not -SAFE_INTEGER <= metric <= SAFE_INTEGER:
                raise AdapterContractError(
                    f"{path}: unsafe interoperable integer"
                )
            if type(metric) is float and not math.isfinite(metric):
                raise AdapterContractError(f"{path}: non-finite metric")
            if (
                type(metric) is float
                and metric == 0.0
                and math.copysign(1.0, metric) < 0.0
            ):
                raise AdapterContractError(f"{path}: negative zero is forbidden")
            metrics[validated_name] = metric

        try:
            extensions = validate_extensions(self.extensions, path="$/extensions")
        except JsonBoundaryError as error:
            raise AdapterContractError(str(error)) from error

        object.__setattr__(self, "artifacts", artifacts)
        object.__setattr__(self, "metrics", metrics)
        object.__setattr__(self, "extensions", extensions)

    def to_json(self) -> JsonObject:
        return clone_object(
            {
                "adapter_identity": self.adapter_identity,
                "status": self.status.value,
                "summary": self.summary,
                "artifacts": dict(self.artifacts),
                "metrics": dict(self.metrics),
                "extensions": self.extensions,
            },
            path="$",
        )
