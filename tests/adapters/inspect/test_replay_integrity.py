from __future__ import annotations

import hashlib
import json
import unittest
from copy import deepcopy
from dataclasses import replace

from common import MemoryCas, load_static_projection, task11_request
from gs_eval_adapters import AdapterContractError, AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter
from gs_eval_adapters.inspect_replay import (
    InspectReplayRecord,
    InspectReplayResult,
    build_replay_record,
    canonical_record_bytes,
    project_inspect_log,
    rescore_inspect_record,
)


class StringSubclass(str):
    pass


class InspectReplayIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cas = MemoryCas()
        cls.adapter = InspectAdapter(cls.cas.publish)
        cls.result = execute_adapter(cls.adapter, task11_request())
        if cls.result.status is not AdapterStatus.PASS:
            raise AssertionError(cls.result.summary)
        cls.log_bytes = cls.cas.read(cls.result.artifacts["inspect_log"])
        cls.log_value = json.loads(cls.log_bytes)

    def test_complete_eval_log_projects_in_the_inspect_free_module(self) -> None:
        projection = project_inspect_log(self.log_value)
        record = build_replay_record(
            projection,
            log_bytes=self.log_bytes,
            log_uri=self.result.artifacts["inspect_log"],
        )

        self.assertEqual(record.task_id, "GS-TASK-000011")
        self.assertEqual(record.sample_id, "GS-SAMPLE-000011")
        self.assertEqual(record.model, "mockllm/model")
        self.assertEqual(rescore_inspect_record(record).status, AdapterStatus.PASS)

    def test_complete_eval_log_requires_exactly_one_sample(self) -> None:
        for samples in ([], self.log_value["samples"] * 2):
            with self.subTest(count=len(samples)):
                log_value = deepcopy(self.log_value)
                log_value["samples"] = samples
                with self.assertRaises(AdapterContractError):
                    project_inspect_log(log_value)

    def test_collect_rejects_record_uri_that_does_not_match_record_bytes(self) -> None:
        record = InspectAdapter.record_from_static_fixture_for_test()
        with self.assertRaises(AdapterContractError):
            self.adapter.collect(
                {
                    "record": record.to_json(),
                    "log_uri": record.log_uri,
                    "record_uri": "cas://sha256/" + "0" * 64,
                }
            )

    def test_record_is_revalidated_after_nested_option_mutation(self) -> None:
        record = InspectAdapter.record_from_static_fixture_for_test()
        record.scorer_options["ignore_case"] = False

        with self.assertRaises(AdapterContractError):
            record.to_json()
        with self.assertRaises(AdapterContractError):
            canonical_record_bytes(record)
        with self.assertRaises(AdapterContractError):
            rescore_inspect_record(record)

    def test_projection_integer_fields_reject_boolean_aliases(self) -> None:
        for path in ("projection_version", "sample.epoch"):
            with self.subTest(path=path):
                projection = load_static_projection()
                if path == "projection_version":
                    projection["projection_version"] = True
                else:
                    projection["sample"]["epoch"] = True
                with self.assertRaises(AdapterContractError):
                    project_inspect_log(projection)

    def test_direct_record_requires_exact_builtin_qualification_strings(self) -> None:
        record = InspectAdapter.record_from_static_fixture_for_test()
        with self.assertRaises(AdapterContractError):
            replace(record, framework=StringSubclass("inspect-ai"))

    def test_replay_result_constructor_is_fail_closed(self) -> None:
        digest = "sha256:" + hashlib.sha256(b"record").hexdigest()
        invalid = (
            {
                "status": "pass",
                "score": "C",
                "obligations": {"qualification_pinned": True},
                "record_sha256": digest,
            },
            {
                "status": AdapterStatus.PASS,
                "score": "UNKNOWN",
                "obligations": {"qualification_pinned": True},
                "record_sha256": digest,
            },
            {
                "status": AdapterStatus.PASS,
                "score": "C",
                "obligations": {},
                "record_sha256": digest,
            },
            {
                "status": AdapterStatus.PASS,
                "score": "C",
                "obligations": {"qualification_pinned": True},
                "record_sha256": "sha256:bad",
            },
        )
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(AdapterContractError):
                    InspectReplayResult(**values)  # type: ignore[arg-type]

    def test_replay_result_is_revalidated_after_obligation_mutation(self) -> None:
        replay = rescore_inspect_record(
            InspectAdapter.record_from_static_fixture_for_test()
        )
        replay.obligations["qualification_pinned"] = "yes"  # type: ignore[assignment]
        with self.assertRaises(AdapterContractError):
            replay.to_json()


if __name__ == "__main__":
    unittest.main()
