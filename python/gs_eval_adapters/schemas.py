from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Final

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

from .errors import SchemaValidationError, ValidationIssue
from .json_boundary import JsonObject

TASK_SCHEMA_ID: Final = "urn:gitspace:schema:v1:eval-task-spec"
AGENT_SCHEMA_ID: Final = "urn:gitspace:schema:v1:agent-configuration"

_SCHEMA_FILES: Final = (
    "eval-task-spec.schema.json",
    "world-fixture.schema.json",
    "oracle-bundle.schema.json",
    "agent-configuration.schema.json",
    "eval-run-manifest.schema.json",
    "run-event.schema.json",
    "evidence-bundle.schema.json",
    "eval-verdict.schema.json",
)


@lru_cache(maxsize=1)
def _validators() -> dict[str, Draft202012Validator]:
    schema_dir = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    schemas: dict[str, dict[str, object]] = {}
    registry = Registry()

    for filename in _SCHEMA_FILES:
        path = schema_dir / filename
        if not path.is_file():
            raise RuntimeError(f"missing sovereign Evaluation IR schema: {filename}")
        schema = json.loads(path.read_text(encoding="utf-8"))
        schema_id = schema.get("$id")
        if not isinstance(schema_id, str):
            raise RuntimeError(f"schema {filename} has no string $id")
        Draft202012Validator.check_schema(schema)
        schemas[schema_id] = schema
        registry = registry.with_resource(
            schema_id,
            DRAFT202012.create_resource(schema),
        )

    if len(schemas) != len(_SCHEMA_FILES):
        raise RuntimeError("Evaluation IR schema IDs are not unique")

    return {
        schema_id: Draft202012Validator(schema, registry=registry)
        for schema_id, schema in schemas.items()
    }


def validate_document(schema_id: str, value: JsonObject) -> None:
    validator = _validators().get(schema_id)
    if validator is None:
        issue = ValidationIssue(
            path="",
            code="schema.unknown",
            message=f"unknown offline schema {schema_id}",
        )
        raise SchemaValidationError(schema_id, (issue,))

    errors = sorted(
        validator.iter_errors(value),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            str(error.validator),
            error.message,
        ),
    )
    if not errors:
        return

    issues = tuple(
        ValidationIssue(
            path=_pointer(error.absolute_path),
            code=f"schema.{error.validator}",
            message=error.message,
        )
        for error in errors
    )
    raise SchemaValidationError(schema_id, issues)


def validate_task(value: JsonObject) -> None:
    validate_document(TASK_SCHEMA_ID, value)


def validate_agent(value: JsonObject) -> None:
    validate_document(AGENT_SCHEMA_ID, value)


def _pointer(parts: object) -> str:
    output = ""
    for part in parts:
        text = str(part).replace("~", "~0").replace("/", "~1")
        output += f"/{text}"
    return output
