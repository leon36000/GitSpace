#!/usr/bin/env python3
"""Validate the shared Evaluation IR corpus against the eight offline schemas."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import validators
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_DIR = ROOT / "schemas" / "v1"
CORPUS_PATH = Path(__file__).with_name("shared-corpus.json")


def load_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(SCHEMA_DIR.glob("*.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            raise ValueError(f"{path}: missing string $id")
        schemas[schema_id] = schema
    if len(schemas) != 8:
        raise ValueError(f"expected 8 schemas, found {len(schemas)}")
    return schemas


def build_registry(schemas: dict[str, dict[str, Any]]) -> Registry[Any]:
    return Registry().with_resources(
        (schema_id, Resource.from_contents(schema))
        for schema_id, schema in schemas.items()
    )


def main() -> int:
    schemas = load_schemas()
    registry = build_registry(schemas)
    corpus = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
    cases = corpus.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("shared corpus must contain a non-empty cases array")

    failures: list[str] = []
    for case in cases:
        case_id = case["id"]
        schema_id = case["schema_id"]
        expected = case["expected_valid"]
        instance = case["instance"]
        schema = schemas[schema_id]
        validator_cls = validators.validator_for(schema)
        validator_cls.check_schema(schema)
        validator = validator_cls(schema, registry=registry)
        actual = not any(validator.iter_errors(instance))
        if actual != expected:
            failures.append(
                f"{case_id}: expected valid={expected}, observed valid={actual}"
            )

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print(f"validated {len(cases)} shared cases across {len(schemas)} schemas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
