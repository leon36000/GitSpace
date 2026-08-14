from __future__ import annotations

import math
import unittest
from copy import deepcopy

from fixtures import CAS_URI, IMPLEMENTATION_DIGEST, request_values
from gs_eval_adapters import (
    AdapterContractError,
    AdapterDescriptor,
    AdapterRequest,
    AdapterStatus,
    JsonBoundaryError,
    SchemaValidationError,
    SemanticLossError,
    execute_adapter,
)


class BaseAdapter:
    descriptor = AdapterDescriptor(
        name="adversarial",
        version="1.0.0",
        protocol_version=1,
        implementation_digest=IMPLEMENTATION_DIGEST,
    )

    def __init__(self) -> None:
        self.invoke_calls = 0
        self.retained: object | None = None

    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        return {
            "canonical_request": request,
            "framework_request": {"request": "ok"},
            "extensions": {},
        }

    def invoke(self, prepared: dict[str, object]) -> dict[str, object]:
        self.invoke_calls += 1
        return {"value": 1}

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        return {
            "status": "pass",
            "summary": "ok",
            "artifacts": {"trace": CAS_URI},
            "metrics": {"score": raw["value"]},
            "extensions": {},
        }


def valid_request(
    *,
    extensions: dict[str, object] | None = None,
    seed: int = 1,
) -> AdapterRequest:
    task, agent = request_values()
    return AdapterRequest(
        task=task,
        agent=agent,
        seed=seed,
        extensions={} if extensions is None else extensions,
    )


class SemanticLossAdapter(BaseAdapter):
    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        snapshot = deepcopy(request)
        snapshot["task"]["intent"]["owner_outcome"] = "lost"
        return {
            "canonical_request": snapshot,
            "framework_request": {},
            "extensions": {},
        }


class MissingSnapshotAdapter(BaseAdapter):
    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        return {"framework_request": {}, "extensions": {}}


class ExtraPreparedFieldAdapter(BaseAdapter):
    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        prepared = super().prepare(request)
        prepared["unexpected"] = True
        return prepared


class ExternalObject:
    pass


class CustomObjectAdapter(BaseAdapter):
    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        prepared = super().prepare(request)
        prepared["framework_request"] = {"external": ExternalObject()}
        return prepared


class RetainingAdapter(BaseAdapter):
    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        payload = super().collect(raw)
        self.retained = payload
        return payload


class ResultPayloadAdapter(BaseAdapter):
    def __init__(self, **changes: object) -> None:
        super().__init__()
        self.changes = changes

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        payload = super().collect(raw)
        payload.update(self.changes)
        return payload


class AdapterAdversarialTests(unittest.TestCase):
    def test_semantic_loss_is_detected_before_invoke(self) -> None:
        adapter = SemanticLossAdapter()
        with self.assertRaises(SemanticLossError):
            execute_adapter(adapter, valid_request())
        self.assertEqual(adapter.invoke_calls, 0)

    def test_missing_or_unknown_prepared_fields_fail_before_invoke(self) -> None:
        for adapter in (MissingSnapshotAdapter(), ExtraPreparedFieldAdapter()):
            with self.subTest(adapter=type(adapter).__name__):
                with self.assertRaises(AdapterContractError):
                    execute_adapter(adapter, valid_request())
                self.assertEqual(adapter.invoke_calls, 0)

    def test_external_python_object_cannot_cross_prepare_boundary(self) -> None:
        adapter = CustomObjectAdapter()
        with self.assertRaises(JsonBoundaryError):
            execute_adapter(adapter, valid_request())
        self.assertEqual(adapter.invoke_calls, 0)

    def test_adapter_retained_result_reference_cannot_mutate_sdk_result(self) -> None:
        adapter = RetainingAdapter()
        result = execute_adapter(adapter, valid_request())
        retained = adapter.retained
        self.assertIsInstance(retained, dict)
        retained["artifacts"]["trace"] = "mutated"
        retained["extensions"]["adversarial.result"] = {"late": True}

        payload = result.to_json()
        self.assertEqual(payload["artifacts"]["trace"], CAS_URI)
        self.assertNotIn("adversarial.result", payload["extensions"])

    def test_non_json_request_values_and_cycles_fail_closed(self) -> None:
        invalid_values: list[object] = [
            b"bytes",
            ("tuple",),
            {"set"},
            ExternalObject(),
            math.nan,
            math.inf,
            -math.inf,
            9_007_199_254_740_992,
            -9_007_199_254_740_992,
        ]
        for value in invalid_values:
            with self.subTest(value=repr(value)):
                with self.assertRaises(JsonBoundaryError):
                    execute_adapter(
                        BaseAdapter(),
                        valid_request(
                            extensions={"gitspace.adapter-test": {"value": value}}
                        ),
                    )

        cycle: list[object] = []
        cycle.append(cycle)
        with self.assertRaises(JsonBoundaryError):
            execute_adapter(
                BaseAdapter(),
                valid_request(extensions={"gitspace.adapter-test": cycle}),
            )

    def test_excessive_nesting_fails_closed(self) -> None:
        value: object = "leaf"
        for _ in range(70):
            value = [value]
        with self.assertRaises(JsonBoundaryError):
            execute_adapter(
                BaseAdapter(),
                valid_request(extensions={"gitspace.adapter-test": value}),
            )

    def test_dictionary_keys_must_be_strings(self) -> None:
        with self.assertRaises(JsonBoundaryError):
            execute_adapter(
                BaseAdapter(),
                valid_request(extensions={"gitspace.adapter-test": {1: "bad"}}),
            )

    def test_extension_keys_must_be_namespaced_at_every_boundary(self) -> None:
        with self.assertRaises(JsonBoundaryError):
            execute_adapter(BaseAdapter(), valid_request(extensions={"debug": True}))

        class BadPreparedExtension(BaseAdapter):
            def prepare(self, request: dict[str, object]) -> dict[str, object]:
                prepared = super().prepare(request)
                prepared["extensions"] = {"debug": True}
                return prepared

        class BadResultExtension(BaseAdapter):
            def collect(self, raw: dict[str, object]) -> dict[str, object]:
                payload = super().collect(raw)
                payload["extensions"] = {"debug": True}
                return payload

        for adapter in (BadPreparedExtension(), BadResultExtension()):
            with self.subTest(adapter=type(adapter).__name__):
                with self.assertRaises(JsonBoundaryError):
                    execute_adapter(adapter, valid_request())

    def test_unknown_result_field_and_status_casing_fail_closed(self) -> None:
        with self.assertRaises(AdapterContractError):
            execute_adapter(
                ResultPayloadAdapter(unexpected=True),
                valid_request(),
            )
        with self.assertRaises(AdapterContractError):
            execute_adapter(
                ResultPayloadAdapter(status="PASS"),
                valid_request(),
            )
        with self.assertRaises(AdapterContractError):
            execute_adapter(
                ResultPayloadAdapter(status="unknown"),
                valid_request(),
            )

    def test_artifact_names_and_cas_uris_are_strict(self) -> None:
        invalid_artifacts = [
            {"Bad Name": CAS_URI},
            {"trace": "trace.json"},
            {"trace": "https://example.test/object"},
            {"trace": "cas://sha256/short"},
            {"trace": "cas://sha256/" + "A" * 64},
        ]
        for artifacts in invalid_artifacts:
            with self.subTest(artifacts=artifacts):
                with self.assertRaises(AdapterContractError):
                    execute_adapter(
                        ResultPayloadAdapter(artifacts=artifacts),
                        valid_request(),
                    )

    def test_metrics_require_names_and_finite_non_bool_numbers(self) -> None:
        invalid_metrics = [
            {"Bad Name": 1},
            {"score": True},
            {"score": math.nan},
            {"score": math.inf},
            {"score": 9_007_199_254_740_992},
        ]
        for metrics in invalid_metrics:
            with self.subTest(metrics=metrics):
                with self.assertRaises(AdapterContractError):
                    execute_adapter(
                        ResultPayloadAdapter(metrics=metrics),
                        valid_request(),
                    )

    def test_task_and_agent_unknown_core_fields_are_schema_errors(self) -> None:
        task, agent = request_values()
        task["unexpected"] = True
        with self.assertRaises(SchemaValidationError):
            execute_adapter(
                BaseAdapter(),
                AdapterRequest(task=task, agent=agent, seed=0, extensions={}),
            )

        task, agent = request_values()
        agent["unexpected"] = True
        with self.assertRaises(SchemaValidationError):
            execute_adapter(
                BaseAdapter(),
                AdapterRequest(task=task, agent=agent, seed=0, extensions={}),
            )

    def test_result_tree_contains_only_json_values(self) -> None:
        result = execute_adapter(BaseAdapter(), valid_request())
        self.assertEqual(result.status, AdapterStatus.PASS)

        def walk(value: object) -> None:
            if value is None or isinstance(value, (str, bool, int, float)):
                return
            if isinstance(value, list):
                for item in value:
                    walk(item)
                return
            if isinstance(value, dict):
                for key, item in value.items():
                    self.assertIsInstance(key, str)
                    walk(item)
                return
            self.fail(f"non-JSON value crossed result boundary: {type(value)!r}")

        walk(result.to_json())


if __name__ == "__main__":
    unittest.main()
