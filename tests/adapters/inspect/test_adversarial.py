from __future__ import annotations

import hashlib
import json
import math
import unittest
from copy import deepcopy
from unittest.mock import patch

from common import MemoryCas, load_static_projection, task11_request
from gs_eval_adapters import AdapterContractError, AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter
from gs_eval_adapters.inspect_replay import InspectReplayRecord, rescore_inspect_record


class FixedSink:
    def __init__(self, uri: str) -> None:
        self.uri = uri
        self.values: list[bytes] = []

    def __call__(self, value: bytes) -> str:
        self.values.append(value)
        return self.uri


class InspectAdapterAdversarialTests(unittest.TestCase):
    def test_artifact_sink_must_return_matching_canonical_cas_uri(self) -> None:
        invalid = [
            "relative/path",
            "https://example.test/object",
            "cas://sha256/short",
            "cas://sha256/" + "A" * 64,
            "cas://sha256/" + "0" * 64,
        ]
        for uri in invalid:
            with self.subTest(uri=uri[:40]):
                result = execute_adapter(InspectAdapter(FixedSink(uri)), task11_request())
                self.assertEqual(result.status, AdapterStatus.INFRA)
                self.assertFalse(result.artifacts)

    def test_installed_version_mismatch_fails_before_eval(self) -> None:
        cas = MemoryCas()
        adapter = InspectAdapter(cas.publish)
        with patch(
            "gs_eval_adapters.inspect_adapter.metadata.version",
            return_value="0.3.257",
        ), patch(
            "gs_eval_adapters.inspect_adapter.inspect_eval",
            side_effect=AssertionError("Inspect eval should not run"),
        ):
            result = execute_adapter(adapter, task11_request())
        self.assertEqual(result.status, AdapterStatus.INFRA)
        self.assertIn("0.3.258", result.summary)
        self.assertFalse(cas.objects)

    def test_zero_or_multiple_logs_fail_as_infrastructure(self) -> None:
        for logs in ([], [object(), object()]):
            with self.subTest(count=len(logs)):
                cas = MemoryCas()
                with patch(
                    "gs_eval_adapters.inspect_adapter.inspect_eval",
                    return_value=logs,
                ):
                    result = execute_adapter(
                        InspectAdapter(cas.publish),
                        task11_request(),
                    )
                self.assertEqual(result.status, AdapterStatus.INFRA)

    def test_eval_error_and_cancelled_are_infrastructure_not_agent_fail(self) -> None:
        projection = load_static_projection()
        for status in ("error", "cancelled"):
            with self.subTest(status=status):
                mutated = deepcopy(projection)
                mutated["eval_status"] = status
                adapter = InspectAdapter(MemoryCas().publish)
                record = adapter.record_from_projection_for_test(mutated)
                raw = {
                    "record": record.to_json(),
                    "log_uri": record.log_uri,
                    "record_uri": "cas://sha256/" + "b" * 64,
                }
                collected = adapter.collect(raw)
                self.assertEqual(collected["status"], "infra")

    def test_missing_score_and_unknown_score_fail_closed(self) -> None:
        canonical = InspectAdapter.record_from_static_fixture_for_test().to_json()
        cases = []
        missing = deepcopy(canonical)
        del missing["inspect_score"]
        cases.append(missing)
        unknown = deepcopy(canonical)
        unknown["inspect_score"] = "UNKNOWN"
        cases.append(unknown)
        for value in cases:
            with self.subTest(keys=sorted(value)):
                with self.assertRaises(AdapterContractError):
                    InspectReplayRecord.from_json(value)

    def test_inspect_score_disagreement_is_not_silently_accepted(self) -> None:
        record = InspectAdapter.record_from_static_fixture_for_test().to_json()
        record["inspect_score"] = "I"
        parsed = InspectReplayRecord.from_json(record)
        replay = rescore_inspect_record(parsed)
        self.assertEqual(replay.score, "C")
        self.assertEqual(replay.status, AdapterStatus.INFRA)
        self.assertFalse(replay.obligations["inspect_score_agrees"])

        adapter = InspectAdapter(MemoryCas().publish)
        with self.assertRaises(AdapterContractError):
            adapter.collect(
                {
                    "record": parsed.to_json(),
                    "log_uri": parsed.log_uri,
                    "record_uri": "cas://sha256/" + "b" * 64,
                }
            )

    def test_non_json_inspect_object_cannot_cross_task10_boundary(self) -> None:
        class InspectLikeObject:
            pass

        cas = MemoryCas()
        adapter = InspectAdapter(cas.publish)
        with patch.object(
            adapter,
            "invoke",
            return_value={"inspect_object": InspectLikeObject()},
        ):
            with self.assertRaises(Exception):
                execute_adapter(adapter, task11_request())

    def test_non_finite_log_value_fails_canonicalization(self) -> None:
        projection = load_static_projection()
        projection["sample"]["output"] = math.nan
        adapter = InspectAdapter(MemoryCas().publish)
        with self.assertRaises(AdapterContractError):
            adapter.record_from_projection_for_test(projection)

    def test_model_provider_environment_is_not_required(self) -> None:
        cas = MemoryCas()
        with patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "",
                "ANTHROPIC_API_KEY": "",
                "INSPECT_EVAL_MODEL": "",
            },
            clear=False,
        ):
            result = execute_adapter(InspectAdapter(cas.publish), task11_request())
        self.assertEqual(result.status, AdapterStatus.PASS)
        self.assertIn("inspect_log", result.artifacts)

    def test_record_artifact_digest_matches_published_bytes(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(InspectAdapter(cas.publish), task11_request())
        record_uri = result.artifacts["inspect_record"]
        record_bytes = cas.read(record_uri)
        self.assertEqual(
            record_uri,
            "cas://sha256/" + hashlib.sha256(record_bytes).hexdigest(),
        )
        json.loads(record_bytes)


if __name__ == "__main__":
    unittest.main()
