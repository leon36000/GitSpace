from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import unittest
from copy import deepcopy
from pathlib import Path

from common import canonical_json_bytes, load_static_projection
from gs_eval_adapters import AdapterContractError, AdapterStatus
from gs_eval_adapters.inspect_replay import (
    InspectReplayRecord,
    build_replay_record,
    canonical_record_bytes,
    rescore_inspect_record,
)


def record_for(projection: dict[str, object] | None = None) -> InspectReplayRecord:
    value = load_static_projection() if projection is None else projection
    log_bytes = canonical_json_bytes(value)
    uri = "cas://sha256/" + hashlib.sha256(log_bytes).hexdigest()
    return build_replay_record(value, log_bytes=log_bytes, log_uri=uri)


class InspectReplayWithoutInspectTests(unittest.TestCase):
    def test_module_ast_contains_no_inspect_import(self) -> None:
        path = (
            Path(__file__).resolve().parents[3]
            / "python"
            / "gs_eval_adapters"
            / "inspect_replay.py"
        )
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        self.assertFalse(
            any(name == "inspect_ai" or name.startswith("inspect_ai.") for name in imports),
            imports,
        )

    def test_subprocess_rescores_with_every_inspect_import_blocked(self) -> None:
        projection = load_static_projection()
        environment = os.environ.copy()
        root = Path(__file__).resolve().parents[3]
        environment["PYTHONPATH"] = str(root / "python")
        script = r'''
import hashlib
import importlib.abc
import json
import sys

class BlockInspect(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "inspect_ai" or fullname.startswith("inspect_ai."):
            raise ImportError("inspect imports are blocked")
        return None

sys.meta_path.insert(0, BlockInspect())
from gs_eval_adapters.inspect_replay import build_replay_record, rescore_inspect_record
projection = json.loads(sys.stdin.read())
log_bytes = json.dumps(projection, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
uri = "cas://sha256/" + hashlib.sha256(log_bytes).hexdigest()
record = build_replay_record(projection, log_bytes=log_bytes, log_uri=uri)
print(json.dumps(rescore_inspect_record(record).to_json(), sort_keys=True))
'''
        result = subprocess.run(
            [sys.executable, "-c", script],
            input=json.dumps(projection),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["score"], "C")
        self.assertTrue(all(payload["obligations"].values()))

    def test_record_unknown_missing_and_wrong_fields_fail_closed(self) -> None:
        canonical = record_for().to_json()
        cases = []

        unknown = deepcopy(canonical)
        unknown["unknown"] = True
        cases.append(unknown)

        missing = deepcopy(canonical)
        del missing["task_id"]
        cases.append(missing)

        wrong = deepcopy(canonical)
        wrong["event_types"] = "model"
        cases.append(wrong)

        for value in cases:
            with self.subTest(keys=sorted(value)):
                with self.assertRaises(AdapterContractError):
                    InspectReplayRecord.from_json(value)

    def test_qualification_and_mapping_mutations_fail_closed(self) -> None:
        fields = {
            "framework": "other",
            "framework_version": "0.3.257",
            "framework_commit": "0" * 40,
            "model": "external/model",
            "solver": "chain",
            "scorer": "includes",
        }
        canonical = record_for().to_json()
        for field, value in fields.items():
            with self.subTest(field=field):
                mutated = deepcopy(canonical)
                mutated[field] = value
                with self.assertRaises(AdapterContractError):
                    InspectReplayRecord.from_json(mutated)

    def test_unsupported_scorer_options_fail_closed(self) -> None:
        canonical = record_for().to_json()
        mutations = [
            {"location": "any", "ignore_case": True, "numeric": False},
            {"location": "exact", "ignore_case": False, "numeric": False},
            {"location": "exact", "ignore_case": True, "numeric": True},
        ]
        for options in mutations:
            with self.subTest(options=options):
                mutated = deepcopy(canonical)
                mutated["scorer_options"] = options
                with self.assertRaises(AdapterContractError):
                    InspectReplayRecord.from_json(mutated)

    def test_output_mutation_changes_independent_score(self) -> None:
        canonical = record_for().to_json()
        canonical["output"] = "wrong answer"
        canonical["inspect_score"] = "I"
        record = InspectReplayRecord.from_json(canonical)
        result = rescore_inspect_record(record)
        self.assertEqual(result.status, AdapterStatus.FAIL)
        self.assertEqual(result.score, "I")
        self.assertFalse(result.obligations["output_matches_target"])

    def test_log_digest_and_uri_must_match_exact_bytes(self) -> None:
        projection = load_static_projection()
        log_bytes = canonical_json_bytes(projection)
        good_uri = "cas://sha256/" + hashlib.sha256(log_bytes).hexdigest()
        bad_uri = "cas://sha256/" + "0" * 64

        with self.assertRaises(AdapterContractError):
            build_replay_record(projection, log_bytes=log_bytes, log_uri=bad_uri)

        record = build_replay_record(
            projection,
            log_bytes=log_bytes,
            log_uri=good_uri,
        )
        mutated = record.to_json()
        mutated["log_sha256"] = "sha256:" + "0" * 64
        with self.assertRaises(AdapterContractError):
            InspectReplayRecord.from_json(mutated)

    def test_event_order_changes_record_digest(self) -> None:
        first = record_for()
        projection = load_static_projection()
        projection["sample"]["event_types"].reverse()
        second = record_for(projection)

        self.assertNotEqual(
            hashlib.sha256(canonical_record_bytes(first)).hexdigest(),
            hashlib.sha256(canonical_record_bytes(second)).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
