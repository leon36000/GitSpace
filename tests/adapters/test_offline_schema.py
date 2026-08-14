from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

from fixtures import IMPLEMENTATION_DIGEST, request_values
from gs_eval_adapters import (
    AdapterDescriptor,
    AdapterRequest,
    AdapterStatus,
    SchemaValidationError,
    execute_adapter,
)
from gs_eval_adapters.schemas import validate_document


class OfflineAdapter:
    descriptor = AdapterDescriptor(
        name="offline",
        version="1.0.0",
        protocol_version=1,
        implementation_digest=IMPLEMENTATION_DIGEST,
    )

    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        return {
            "canonical_request": request,
            "framework_request": {},
            "extensions": {},
        }

    def invoke(self, prepared: dict[str, object]) -> dict[str, object]:
        return {}

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        return {
            "status": "pass",
            "summary": "offline",
            "artifacts": {},
            "metrics": {},
            "extensions": {},
        }


class OfflineSchemaTests(unittest.TestCase):
    def test_valid_contract_never_opens_a_socket(self) -> None:
        task, agent = request_values()
        request = AdapterRequest(task=task, agent=agent, seed=0, extensions={})

        with patch.object(
            socket.socket,
            "connect",
            side_effect=AssertionError("schema validation attempted network access"),
        ) as connect:
            result = execute_adapter(OfflineAdapter(), request)

        self.assertEqual(result.status, AdapterStatus.PASS)
        connect.assert_not_called()

    def test_unknown_http_or_urn_schema_fails_locally_without_resolution(self) -> None:
        for schema_id in (
            "https://attacker.invalid/schema.json",
            "urn:gitspace:schema:v1:missing",
        ):
            with self.subTest(schema_id=schema_id):
                with patch.object(
                    socket.socket,
                    "connect",
                    side_effect=AssertionError("unknown schema attempted network access"),
                ) as connect:
                    with self.assertRaises(SchemaValidationError) as context:
                        validate_document(schema_id, {})
                self.assertEqual(context.exception.issues[0].code, "schema.unknown")
                connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
