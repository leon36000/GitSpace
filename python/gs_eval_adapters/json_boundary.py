from __future__ import annotations

import math
import re
from typing import TypeAlias

from .errors import JsonBoundaryError

JsonScalar: TypeAlias = None | bool | int | float | str
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
JsonObject: TypeAlias = dict[str, JsonValue]

SAFE_INTEGER = 9_007_199_254_740_991
MAX_DEPTH = 64
EXTENSION_KEY = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9-]+)+$")
NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
CAS_URI = re.compile(r"^cas://sha256/[0-9a-f]{64}$")


def clone_json(value: object, *, path: str = "$", max_depth: int = MAX_DEPTH) -> JsonValue:
    return _clone_json(value, path=path, depth=0, max_depth=max_depth, active=set())


def _clone_json(
    value: object,
    *,
    path: str,
    depth: int,
    max_depth: int,
    active: set[int],
) -> JsonValue:
    if depth > max_depth:
        raise JsonBoundaryError(f"{path}: JSON nesting exceeds {max_depth} levels")

    value_type = type(value)
    if value is None or value_type in (str, bool):
        return value

    if value_type is int:
        if not -SAFE_INTEGER <= value <= SAFE_INTEGER:
            raise JsonBoundaryError(
                f"{path}: integer {value} exceeds the interoperable JSON safe range"
            )
        return value

    if value_type is float:
        if not math.isfinite(value):
            raise JsonBoundaryError(f"{path}: non-finite float is forbidden")
        return value

    if value_type is list:
        identity = id(value)
        if identity in active:
            raise JsonBoundaryError(f"{path}: cyclic JSON array")
        active.add(identity)
        try:
            return [
                _clone_json(
                    item,
                    path=f"{path}/{index}",
                    depth=depth + 1,
                    max_depth=max_depth,
                    active=active,
                )
                for index, item in enumerate(value)
            ]
        finally:
            active.remove(identity)

    if value_type is dict:
        identity = id(value)
        if identity in active:
            raise JsonBoundaryError(f"{path}: cyclic JSON object")
        active.add(identity)
        try:
            output: JsonObject = {}
            for key, item in value.items():
                if type(key) is not str:
                    raise JsonBoundaryError(
                        f"{path}: JSON object key {key!r} is not an exact string"
                    )
                output[key] = _clone_json(
                    item,
                    path=f"{path}/{_escape_pointer(key)}",
                    depth=depth + 1,
                    max_depth=max_depth,
                    active=active,
                )
            return output
        finally:
            active.remove(identity)

    raise JsonBoundaryError(
        f"{path}: {value_type.__module__}.{value_type.__qualname__} is not exact JSON"
    )


def clone_object(value: object, *, path: str = "$") -> JsonObject:
    cloned = clone_json(value, path=path)
    if type(cloned) is not dict:
        raise JsonBoundaryError(f"{path}: expected a JSON object")
    return cloned


def validate_extensions(value: object, *, path: str) -> JsonObject:
    extensions = clone_object(value, path=path)
    for key in extensions:
        if not EXTENSION_KEY.fullmatch(key):
            raise JsonBoundaryError(
                f"{path}/{_escape_pointer(key)}: extension key is not namespaced"
            )
    return extensions


def validate_name(value: object, *, path: str) -> str:
    if type(value) is not str or not NAME.fullmatch(value):
        raise JsonBoundaryError(f"{path}: invalid boundary name")
    return value


def validate_cas_uri(value: object, *, path: str) -> str:
    if type(value) is not str or not CAS_URI.fullmatch(value):
        raise JsonBoundaryError(f"{path}: expected canonical cas://sha256 URI")
    return value


def _escape_pointer(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")
