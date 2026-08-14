from __future__ import annotations

import json
import unittest
from copy import deepcopy

from fixtures import CAS_URI, IMPLEMENTATION_DIGEST, request_values
from gs_eval_adapters import (
    AdapterDescriptor,
    AdapterPolicyViolation,
    AdapterRegistry,
    AdapterRequest,
    AdapterResult,
    AdapterStatus,
    AdapterTimeout,
    RegistrationError,
    SchemaValidationError,
    execute_adapter,
)


class PassAdapter:
    descriptor = AdapterDescriptor(
        name="fake",
        version="1.0.0",
        protocol_version=1,
        implementation_digest=IMPLEMENTATION_DIGEST,
    )

    def __init__(self) -> None:
        self.prepare_calls = 0
        self.invoke_calls = 0
        self.collect_calls = 0
        self.prepared_seen: dict[str, object] | None = None

    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        self.prepare_calls += 1
        return {
            "canonical_request": request,
            "framework_request": {
                "prompt": request["task"]["intent"]["owner_outcome"],
                "seed": request["seed"],
            },
            "extensions": {"fake.prepare": {"version": 1}},
        }

    def invoke(self, prepared: dict[str, object]) -> dict[str, object]:
        self.invoke_calls += 1
        self.prepared_seen = prepared
        return {"answer": "ok", "score": 1}

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        self.collect_calls += 1
        return {
            "status": "pass",
            "summary": f"answer={raw['answer']}",
            "artifacts": {"trace": CAS_URI},
            "metrics": {"score": raw["score"]},
            "extensions": {"fake.result": {"normalized": True}},
        }


class StaticStatusAdapter(PassAdapter):
    def __init__(self, status: str) -> None:
        super().__init__()
        self.status = status

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        self.collect_calls += 1
        return {
            "status": self.status,
            "summary": self.status,
            "artifacts": {},
            "metrics": {},
            "extensions": {},
        }


class RaisingAdapter(PassAdapter):
    def __init__(self, stage: str, error: Exception) -> None:
        super().__init__()
        self.stage = stage
        self.error = error

    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        if self.stage == "prepare":
            raise self.error
        return super().prepare(request)

    def invoke(self, prepared: dict[str, object]) -> dict[str, object]:
        if self.stage == "invoke":
            raise self.error
        return super().invoke(prepared)

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        if self.stage == "collect":
            raise self.error
        return super().collect(raw)


def valid_request() -> AdapterRequest:
    task, agent = request_values()
    return AdapterRequest(
        task=task,
        agent=agent,
        seed=7,
        extensions={"gitspace.adapter-test": {"request": True}},
    )


class AdapterContractTests(unittest.TestCase):
    def test_valid_pass_adapter_returns_json_only_deterministic_result(self) -> None:
        adapter = PassAdapter()
        result = execute_adapter(adapter, valid_request())

        self.assertIsInstance(result, AdapterResult)
        self.assertEqual(result.status, AdapterStatus.PASS)
        self.assertEqual(result.adapter_identity, adapter.descriptor.identity)
        self.assertEqual(result.artifacts, {"trace": CAS_URI})
        self.assertEqual(result.metrics, {"score": 1})
        self.assertEqual(adapter.prepare_calls, 1)
        self.assertEqual(adapter.invoke_calls, 1)
        self.assertEqual(adapter.collect_calls, 1)

        payload = result.to_json()
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["adapter_identity"], adapter.descriptor.identity)
        json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",", ":"))

    def test_task_and_agent_are_schema_validated_before_prepare(self) -> None:
        for field in ("task", "agent"):
            with self.subTest(field=field):
                task, agent = request_values()
                if field == "task":
                    task["id"] = "not-a-task"
                else:
                    agent["context_digest"] = "sha256:bad"
                adapter = PassAdapter()
                with self.assertRaises(SchemaValidationError):
                    execute_adapter(
                        adapter,
                        AdapterRequest(
                            task=task,
                            agent=agent,
                            seed=0,
                            extensions={},
                        ),
                    )
                self.assertEqual(adapter.prepare_calls, 0)
                self.assertEqual(adapter.invoke_calls, 0)
                self.assertEqual(adapter.collect_calls, 0)

    def test_all_five_normalized_statuses_are_supported(self) -> None:
        cases = {
            "pass": AdapterStatus.PASS,
            "fail": AdapterStatus.FAIL,
            "timeout": AdapterStatus.TIMEOUT,
            "policy": AdapterStatus.POLICY,
            "infra": AdapterStatus.INFRA,
        }
        for value, expected in cases.items():
            with self.subTest(status=value):
                result = execute_adapter(StaticStatusAdapter(value), valid_request())
                self.assertEqual(result.status, expected)

    def test_timeout_and_policy_exceptions_are_normalized_at_every_stage(self) -> None:
        for stage in ("prepare", "invoke", "collect"):
            for error, expected in (
                (AdapterTimeout("deadline"), AdapterStatus.TIMEOUT),
                (AdapterPolicyViolation("denied"), AdapterStatus.POLICY),
            ):
                with self.subTest(stage=stage, expected=expected):
                    result = execute_adapter(RaisingAdapter(stage, error), valid_request())
                    self.assertEqual(result.status, expected)
                    self.assertIn(str(error), result.summary)

    def test_unexpected_external_exceptions_become_bounded_infra(self) -> None:
        hostile = RuntimeError("line one\nline two\x00" + "x" * 1000)
        for stage in ("prepare", "invoke", "collect"):
            with self.subTest(stage=stage):
                result = execute_adapter(RaisingAdapter(stage, hostile), valid_request())
                self.assertEqual(result.status, AdapterStatus.INFRA)
                self.assertLessEqual(len(result.summary), 512)
                self.assertNotIn("\n", result.summary)
                self.assertNotIn("\x00", result.summary)
                self.assertIn(stage, result.summary)

    def test_caller_values_are_not_mutated(self) -> None:
        task, agent = request_values()
        original_task = deepcopy(task)
        original_agent = deepcopy(agent)
        request = AdapterRequest(
            task=task,
            agent=agent,
            seed=9,
            extensions={"gitspace.adapter-test": {"copy": True}},
        )

        execute_adapter(PassAdapter(), request)
        self.assertEqual(task, original_task)
        self.assertEqual(agent, original_agent)

    def test_result_to_json_returns_a_fresh_deep_copy(self) -> None:
        result = execute_adapter(PassAdapter(), valid_request())
        first = result.to_json()
        first["artifacts"]["trace"] = "changed"
        first["extensions"]["fake.result"]["normalized"] = False

        second = result.to_json()
        self.assertEqual(second["artifacts"]["trace"], CAS_URI)
        self.assertTrue(second["extensions"]["fake.result"]["normalized"])

    def test_identical_input_produces_byte_equivalent_json(self) -> None:
        first = execute_adapter(PassAdapter(), valid_request()).to_json()
        second = execute_adapter(PassAdapter(), valid_request()).to_json()
        first_bytes = json.dumps(
            first,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        second_bytes = json.dumps(
            second,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        self.assertEqual(first_bytes, second_bytes)

    def test_descriptor_identity_is_reproducible_and_complete(self) -> None:
        first = PassAdapter.descriptor
        second = AdapterDescriptor(
            name="fake",
            version="1.0.0",
            protocol_version=1,
            implementation_digest=IMPLEMENTATION_DIGEST,
        )
        self.assertEqual(first.identity, second.identity)
        self.assertIn("fake", first.identity)
        self.assertIn("1.0.0", first.identity)
        self.assertIn("protocol-1", first.identity)
        self.assertIn(IMPLEMENTATION_DIGEST, first.identity)

    def test_registry_is_deterministic_and_rejects_duplicates(self) -> None:
        registry = AdapterRegistry()
        adapter = PassAdapter()
        registry.register(adapter)
        self.assertIs(registry.resolve("fake"), adapter)
        self.assertEqual(registry.identities(), (adapter.descriptor.identity,))

        with self.assertRaises(RegistrationError):
            registry.register(PassAdapter())

        class SameIdentityDifferentName(PassAdapter):
            descriptor = AdapterDescriptor(
                name="other",
                version="1.0.0",
                protocol_version=1,
                implementation_digest=IMPLEMENTATION_DIGEST,
            )

            @property
            def forced_identity(self) -> str:
                return adapter.descriptor.identity

        class IncompleteAdapter:
            descriptor = AdapterDescriptor(
                name="incomplete",
                version="1",
                protocol_version=1,
                implementation_digest=IMPLEMENTATION_DIGEST,
            )

            def prepare(self, request: dict[str, object]) -> dict[str, object]:
                return request

        with self.assertRaises(RegistrationError):
            registry.register(IncompleteAdapter())


if __name__ == "__main__":
    unittest.main()
