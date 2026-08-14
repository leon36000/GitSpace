from __future__ import annotations

from dataclasses import dataclass
import unittest

from fixtures import CAS_URI, IMPLEMENTATION_DIGEST
from gs_eval_adapters import (
    AdapterContractError,
    AdapterDescriptor,
    AdapterResult,
    AdapterStatus,
    execute_adapter,
)


@dataclass(frozen=True, slots=True)
class DescriptorSubclass(AdapterDescriptor):
    pass


class AdapterWithDescriptorSubclass:
    descriptor = DescriptorSubclass(
        name="subclass",
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
            "summary": "ok",
            "artifacts": {},
            "metrics": {},
            "extensions": {},
        }


class PublicModelTests(unittest.TestCase):
    def test_descriptor_subclass_is_not_accepted_as_sdk_authority(self) -> None:
        from test_contract import valid_request

        with self.assertRaises(AdapterContractError):
            execute_adapter(AdapterWithDescriptorSubclass(), valid_request())

    def test_direct_result_construction_rejects_invalid_status(self) -> None:
        with self.assertRaises(AdapterContractError):
            AdapterResult(
                adapter_identity="fake@1/protocol-1/" + IMPLEMENTATION_DIGEST,
                status="pass",  # type: ignore[arg-type]
                summary="ok",
                artifacts={},
                metrics={},
                extensions={},
            )

    def test_direct_result_construction_rejects_invalid_artifact(self) -> None:
        with self.assertRaises(AdapterContractError):
            AdapterResult(
                adapter_identity="fake@1/protocol-1/" + IMPLEMENTATION_DIGEST,
                status=AdapterStatus.PASS,
                summary="ok",
                artifacts={"trace": "relative/path"},
                metrics={},
                extensions={},
            )

    def test_direct_result_construction_rejects_invalid_metric_and_summary(self) -> None:
        for summary, metrics in (
            ("line one\nline two", {}),
            ("ok", {"score": -0.0}),
            ("ok", {"score": True}),
        ):
            with self.subTest(summary=summary, metrics=metrics):
                with self.assertRaises(AdapterContractError):
                    AdapterResult(
                        adapter_identity="fake@1/protocol-1/" + IMPLEMENTATION_DIGEST,
                        status=AdapterStatus.PASS,
                        summary=summary,
                        artifacts={"trace": CAS_URI},
                        metrics=metrics,
                        extensions={},
                    )

    def test_direct_valid_result_still_returns_fresh_json(self) -> None:
        result = AdapterResult(
            adapter_identity="fake@1/protocol-1/" + IMPLEMENTATION_DIGEST,
            status=AdapterStatus.PASS,
            summary="ok",
            artifacts={"trace": CAS_URI},
            metrics={"score": 1},
            extensions={"fake.result": {"ok": True}},
        )
        first = result.to_json()
        first["artifacts"]["trace"] = "changed"
        self.assertEqual(result.to_json()["artifacts"]["trace"], CAS_URI)


if __name__ == "__main__":
    unittest.main()
