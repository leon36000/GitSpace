from __future__ import annotations

import unittest
from unittest.mock import patch

from common import MemoryCas, task11_request
from gs_eval_adapters import AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import (
    InspectAdapter,
    inspect_eval as real_inspect_eval,
)


class SpoofedEvalLogs(list[object]):
    pass


SpoofedEvalLogs.__module__ = "inspect_ai._eval.eval"
SpoofedEvalLogs.__name__ = "EvalLogs"


class InspectRuntimeTypeBoundaryTests(unittest.TestCase):
    def test_module_and_class_name_spoof_does_not_replace_official_wrapper(self) -> None:
        def spoof(*args: object, **kwargs: object) -> object:
            official_logs = real_inspect_eval(*args, **kwargs)
            return SpoofedEvalLogs([official_logs[0]])

        with patch(
            "gs_eval_adapters.inspect_adapter.inspect_eval",
            side_effect=spoof,
        ):
            result = execute_adapter(
                InspectAdapter(MemoryCas().publish),
                task11_request(),
            )

        self.assertEqual(result.status, AdapterStatus.INFRA)
        self.assertIn("unsupported log collection", result.summary)


if __name__ == "__main__":
    unittest.main()
