from __future__ import annotations

import gc
import unittest
import warnings

from common import MemoryCas, task11_request
from gs_eval_adapters import AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter


class InspectResourceLifecycleTests(unittest.TestCase):
    def test_one_controlled_run_leaves_no_unclosed_anyio_stream(self) -> None:
        with warnings.catch_warnings(record=True) as observed:
            warnings.simplefilter("always", ResourceWarning)
            adapter = InspectAdapter(MemoryCas().publish)
            result = execute_adapter(adapter, task11_request())
            self.assertEqual(result.status, AdapterStatus.PASS, result.summary)
            del result
            del adapter
            for _ in range(3):
                gc.collect()

        leaks = [
            warning
            for warning in observed
            if warning.category is ResourceWarning
            and "MemoryObjectReceiveStream" in str(warning.message)
        ]
        self.assertEqual(
            leaks,
            [],
            "Inspect 0.3.258 left AnyIO receive streams unclosed: "
            + "; ".join(str(warning.message) for warning in leaks),
        )


if __name__ == "__main__":
    unittest.main()
