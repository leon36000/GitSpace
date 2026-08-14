from __future__ import annotations

import hashlib
import json
import socket
import unittest
from pathlib import Path
from unittest.mock import patch

from common import (
    INSPECT_COMMIT,
    INSPECT_VERSION,
    INSPECT_WHEEL_SHA256,
    MODEL_OUTPUT,
    MemoryCas,
    canonical_json_bytes,
    load_static_projection,
    task11_request,
)
from gs_eval_adapters import AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter
from gs_eval_adapters.inspect_replay import (
    InspectReplayRecord,
    build_replay_record,
    canonical_record_bytes,
    rescore_inspect_record,
)


class InspectAdapterContractTests(unittest.TestCase):
    def test_qualification_manifest_matches_adapter_constants(self) -> None:
        path = (
            Path(__file__).resolve().parents[3]
            / "docs"
            / "phase-00"
            / "qualifications"
            / "inspect-ai-0.3.258.json"
        )
        qualification = json.loads(path.read_text(encoding="utf-8"))
        adapter = InspectAdapter(MemoryCas().publish)

        self.assertEqual(qualification["version"], INSPECT_VERSION)
        self.assertEqual(qualification["tag"], INSPECT_VERSION)
        self.assertEqual(qualification["source_commit"], INSPECT_COMMIT)
        self.assertEqual(
            qualification["package"]["wheel"]["sha256"],
            INSPECT_WHEEL_SHA256,
        )
        self.assertEqual(adapter.descriptor.name, "inspect-ai")
        self.assertEqual(adapter.descriptor.version, INSPECT_VERSION)
        self.assertEqual(
            adapter.descriptor.implementation_digest,
            f"sha256:{INSPECT_WHEEL_SHA256}",
        )

    def test_prepare_preserves_canonical_request_and_exact_mapping(self) -> None:
        adapter = InspectAdapter(MemoryCas().publish)
        request = task11_request()
        canonical_request = {
            "version": 1,
            "task": request.task,
            "agent": request.agent,
            "seed": request.seed,
            "extensions": request.extensions,
        }

        prepared = adapter.prepare(canonical_request)
        self.assertEqual(set(prepared), {
            "canonical_request",
            "framework_request",
            "extensions",
        })
        self.assertEqual(prepared["canonical_request"], canonical_request)
        framework = prepared["framework_request"]
        self.assertEqual(framework["framework"], "inspect-ai")
        self.assertEqual(framework["framework_version"], INSPECT_VERSION)
        self.assertEqual(framework["framework_commit"], INSPECT_COMMIT)
        self.assertEqual(framework["task_id"], "GS-TASK-000011")
        self.assertEqual(framework["task_name"], "gitspace_inspect_controlled")
        self.assertEqual(framework["sample_id"], "GS-SAMPLE-000011")
        self.assertEqual(framework["target"], MODEL_OUTPUT)
        self.assertEqual(framework["model"], "mockllm/model")
        self.assertEqual(framework["solver"], "generate")
        self.assertEqual(framework["scorer"], "match")
        self.assertEqual(
            framework["scorer_options"],
            {"location": "exact", "ignore_case": True, "numeric": False},
        )

    def test_static_projection_builds_byte_stable_record_and_passes(self) -> None:
        projection = load_static_projection()
        log_bytes = canonical_json_bytes(projection)
        log_uri = "cas://sha256/" + hashlib.sha256(log_bytes).hexdigest()

        record = build_replay_record(
            projection,
            log_bytes=log_bytes,
            log_uri=log_uri,
        )
        decoded = InspectReplayRecord.from_json(record.to_json())
        result = rescore_inspect_record(decoded)

        self.assertEqual(result.status, AdapterStatus.PASS)
        self.assertEqual(result.score, "C")
        self.assertTrue(all(result.obligations.values()))
        self.assertEqual(canonical_record_bytes(record), canonical_record_bytes(decoded))
        self.assertEqual(
            rescore_inspect_record(decoded).to_json(),
            rescore_inspect_record(decoded).to_json(),
        )

    def test_controlled_run_succeeds_without_socket_connection(self) -> None:
        cas = MemoryCas()
        adapter = InspectAdapter(cas.publish)

        with patch.object(
            socket.socket,
            "connect",
            side_effect=AssertionError("Inspect attempted a network connection"),
        ) as connect:
            result = execute_adapter(adapter, task11_request())

        connect.assert_not_called()
        self.assertEqual(result.status, AdapterStatus.PASS)
        self.assertEqual(result.metrics["inspect_correct"], 1)
        self.assertEqual(result.metrics["replay_correct"], 1)
        self.assertGreaterEqual(result.metrics["event_count"], 1)
        self.assertEqual(set(result.artifacts), {"inspect_log", "inspect_record"})

        for uri in result.artifacts.values():
            payload = cas.read(uri)
            self.assertEqual(
                uri,
                "cas://sha256/" + hashlib.sha256(payload).hexdigest(),
            )

        record = InspectReplayRecord.from_json(
            json.loads(cas.read(result.artifacts["inspect_record"]))
        )
        self.assertEqual(record.output, MODEL_OUTPUT)
        self.assertEqual(record.target, MODEL_OUTPUT)
        self.assertEqual(record.inspect_score, "C")
        self.assertEqual(record.framework_version, INSPECT_VERSION)
        self.assertEqual(record.framework_commit, INSPECT_COMMIT)
        self.assertEqual(rescore_inspect_record(record).status, AdapterStatus.PASS)

    def test_complete_log_artifact_is_json_and_contains_one_sample(self) -> None:
        cas = MemoryCas()
        result = execute_adapter(InspectAdapter(cas.publish), task11_request())
        log_value = json.loads(cas.read(result.artifacts["inspect_log"]))

        self.assertEqual(log_value["status"], "success")
        self.assertEqual(len(log_value["samples"]), 1)
        self.assertEqual(log_value["eval"]["model"], "mockllm/model")
        self.assertEqual(log_value["samples"][0]["output"]["completion"], MODEL_OUTPUT)
        self.assertTrue(log_value["samples"][0]["events"])


if __name__ == "__main__":
    unittest.main()
