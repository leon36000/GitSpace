from __future__ import annotations

import unittest

from fixtures import IMPLEMENTATION_DIGEST, request_values
from gs_eval_adapters import (
    AdapterContractError,
    AdapterDescriptor,
    AdapterRegistry,
    AdapterRequest,
    AdapterStatus,
    JsonBoundaryError,
    RegistrationError,
    execute_adapter,
)


class DictSubclass(dict):
    pass


class ListSubclass(list):
    pass


class StringSubclass(str):
    pass


class IntegerSubclass(int):
    pass


class FloatSubclass(float):
    pass


class BaseAdapter:
    descriptor = AdapterDescriptor(
        name="hardening",
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
        return {"value": 1}

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        return {
            "status": "pass",
            "summary": "ok",
            "artifacts": {},
            "metrics": {},
            "extensions": {},
        }


class ExplodingStringError(Exception):
    def __str__(self) -> str:
        raise RuntimeError("stringification trap")


class HostileExceptionAdapter(BaseAdapter):
    def invoke(self, prepared: dict[str, object]) -> dict[str, object]:
        raise ExplodingStringError()


class DescriptorTrap:
    @property
    def descriptor(self) -> object:
        raise RuntimeError("descriptor trap")

    def prepare(self, request: dict[str, object]) -> dict[str, object]:
        return {}

    def invoke(self, prepared: dict[str, object]) -> dict[str, object]:
        return {}

    def collect(self, raw: dict[str, object]) -> dict[str, object]:
        return {}


def request_with(value: object) -> AdapterRequest:
    task, agent = request_values()
    return AdapterRequest(
        task=task,
        agent=agent,
        seed=0,
        extensions={"gitspace.adapter-test": {"value": value}},
    )


class BoundaryHardeningTests(unittest.TestCase):
    def test_subclasses_of_json_builtins_do_not_cross_the_boundary(self) -> None:
        cases: list[object] = [
            DictSubclass({"key": "value"}),
            ListSubclass(["value"]),
            StringSubclass("value"),
            IntegerSubclass(1),
            FloatSubclass(1.0),
            {StringSubclass("key"): "value"},
        ]
        for value in cases:
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(JsonBoundaryError):
                    execute_adapter(BaseAdapter(), request_with(value))

    def test_descriptor_fields_require_exact_builtin_types(self) -> None:
        with self.assertRaises(AdapterContractError):
            AdapterDescriptor(
                name=StringSubclass("subclass"),
                version="1.0.0",
                protocol_version=1,
                implementation_digest=IMPLEMENTATION_DIGEST,
            )
        with self.assertRaises(AdapterContractError):
            AdapterDescriptor(
                name="boolean-protocol",
                version="1.0.0",
                protocol_version=True,
                implementation_digest=IMPLEMENTATION_DIGEST,
            )

    def test_exception_with_unprintable_message_is_still_normalized(self) -> None:
        result = execute_adapter(HostileExceptionAdapter(), request_with("ok"))
        self.assertEqual(result.status, AdapterStatus.INFRA)
        self.assertLessEqual(len(result.summary), 512)
        self.assertIn("invoke", result.summary)
        self.assertIn("ExplodingStringError", result.summary)

    def test_descriptor_property_exception_is_wrapped_by_sdk_boundaries(self) -> None:
        with self.assertRaises(AdapterContractError):
            execute_adapter(DescriptorTrap(), request_with("ok"))
        with self.assertRaises(RegistrationError):
            AdapterRegistry().register(DescriptorTrap())


if __name__ == "__main__":
    unittest.main()
