from __future__ import annotations

import unittest
from unittest.mock import patch

from common import MemoryCas, task11_request
from gs_eval_adapters import AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter, inspect_eval as real_inspect_eval


class InspectIntegrationDiagnostics(unittest.TestCase):
    def test_controlled_run_reports_its_normalized_failure_reason(self) -> None:
        observed: dict[str, object] = {}

        def capture(*args: object, **kwargs: object) -> object:
            logs = real_inspect_eval(*args, **kwargs)
            observed["type"] = f"{type(logs).__module__}.{type(logs).__name__}"
            try:
                observed["length"] = len(logs)
            except Exception as error:
                observed["length_error"] = type(error).__name__
            return logs

        with patch(
            "gs_eval_adapters.inspect_adapter.inspect_eval",
            side_effect=capture,
        ):
            result = execute_adapter(InspectAdapter(MemoryCas().publish), task11_request())

        self.assertEqual(
            result.status,
            AdapterStatus.PASS,
            f"{result.summary}; observed={observed}",
        )


if __name__ == "__main__":
    unittest.main()
