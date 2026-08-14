from __future__ import annotations

import unittest

from common import MemoryCas, task11_request
from gs_eval_adapters import AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter


class InspectIntegrationDiagnostics(unittest.TestCase):
    def test_controlled_run_reports_its_normalized_failure_reason(self) -> None:
        result = execute_adapter(InspectAdapter(MemoryCas().publish), task11_request())
        self.assertEqual(result.status, AdapterStatus.PASS, result.summary)


if __name__ == "__main__":
    unittest.main()
