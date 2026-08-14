from __future__ import annotations

import unittest
from copy import deepcopy
from unittest.mock import patch

from common import MemoryCas, task11_request
from gs_eval_adapters import AdapterContractError
from gs_eval_adapters.inspect_adapter import InspectAdapter


def canonical_request() -> dict[str, object]:
    request = task11_request()
    return {
        "version": 1,
        "task": deepcopy(request.task),
        "agent": deepcopy(request.agent),
        "seed": request.seed,
        "extensions": deepcopy(request.extensions),
    }


class InspectMappingBoundaryTests(unittest.TestCase):
    def test_framework_mapping_mutations_fail_before_inspect_eval(self) -> None:
        mutations = {
            "framework": "other",
            "framework_version": "0.3.257",
            "framework_commit": "0" * 40,
            "model": "external/model",
            "solver": "chain",
            "scorer": "includes",
            "target": "different target",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                adapter = InspectAdapter(MemoryCas().publish)
                prepared = adapter.prepare(canonical_request())
                prepared["framework_request"][field] = value
                with patch(
                    "gs_eval_adapters.inspect_adapter.inspect_eval",
                    side_effect=AssertionError("Inspect eval should not run"),
                ):
                    with self.assertRaises(AdapterContractError):
                        adapter.invoke(prepared)

    def test_unknown_framework_mapping_field_fails_before_eval(self) -> None:
        adapter = InspectAdapter(MemoryCas().publish)
        prepared = adapter.prepare(canonical_request())
        prepared["framework_request"]["unknown"] = True
        with patch(
            "gs_eval_adapters.inspect_adapter.inspect_eval",
            side_effect=AssertionError("Inspect eval should not run"),
        ):
            with self.assertRaises(AdapterContractError):
                adapter.invoke(prepared)


if __name__ == "__main__":
    unittest.main()
