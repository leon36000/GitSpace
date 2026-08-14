from __future__ import annotations

from dataclasses import dataclass


class AdapterSdkError(Exception):
    """Base class for deterministic GitSpace adapter SDK failures."""


class JsonBoundaryError(AdapterSdkError):
    """A value cannot cross the canonical JSON boundary."""


class AdapterContractError(AdapterSdkError):
    """An adapter violated the provider-neutral SDK contract."""


class SemanticLossError(AdapterContractError):
    """The prepared canonical request differs from the validated request."""


class RegistrationError(AdapterSdkError):
    """An adapter cannot be registered deterministically."""


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    code: str
    message: str


class SchemaValidationError(AdapterSdkError):
    def __init__(self, schema_id: str, issues: tuple[ValidationIssue, ...]) -> None:
        self.schema_id = schema_id
        self.issues = issues
        detail = "; ".join(
            f"{issue.path or '/'} [{issue.code}] {issue.message}" for issue in issues
        )
        super().__init__(f"{schema_id} validation failed: {detail}")


class AdapterTimeout(Exception):
    """External adapter operation exceeded its declared deadline."""


class AdapterPolicyViolation(Exception):
    """External adapter operation was blocked by policy."""


def safe_type_name(value: object) -> str:
    """Return a bounded ASCII type label without trusting class metadata hooks."""

    value_type = type(value)
    try:
        module = type.__getattribute__(value_type, "__module__")
    except Exception:
        module = None
    try:
        name = type.__getattribute__(value_type, "__name__")
    except Exception:
        name = None

    safe_module = _safe_metadata_text(module, fallback="unknown")
    safe_name = _safe_metadata_text(name, fallback="type")
    return f"{safe_module}.{safe_name}"


def _safe_metadata_text(value: object, *, fallback: str) -> str:
    if type(value) is not str or not value:
        return fallback
    output: list[str] = []
    for character in value[:128]:
        codepoint = ord(character)
        output.append(character if 32 <= codepoint <= 126 else "_")
    return "".join(output) or fallback
