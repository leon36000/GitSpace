from __future__ import annotations

import gc
import unittest

from anyio.streams.memory import MemoryObjectReceiveStream

from common import MemoryCas, task11_request
from gs_eval_adapters import AdapterStatus, execute_adapter
from gs_eval_adapters.inspect_adapter import InspectAdapter


class InspectResourceLifecycleTests(unittest.TestCase):
    def test_one_controlled_run_leaves_no_unclosed_anyio_stream(self) -> None:
        gc.collect()
        baseline = {
            id(value)
            for value in gc.get_objects()
            if type(value) is MemoryObjectReceiveStream
        }
        gc_was_enabled = gc.isenabled()
        gc.disable()
        leaked: list[MemoryObjectReceiveStream[object]] = []
        details: list[dict[str, object]] = []
        try:
            adapter = InspectAdapter(MemoryCas().publish)
            result = execute_adapter(adapter, task11_request())
            self.assertEqual(result.status, AdapterStatus.PASS, result.summary)
            del result
            del adapter

            leaked = [
                value
                for value in gc.get_objects()
                if type(value) is MemoryObjectReceiveStream
                and id(value) not in baseline
                and not getattr(value, "_closed", True)
            ]
            for stream in leaked:
                statistics = stream.statistics()
                details.append(
                    {
                        "closed": getattr(stream, "_closed", None),
                        "buffered": statistics.current_buffer_used,
                        "open_send_streams": statistics.open_send_streams,
                        "open_receive_streams": statistics.open_receive_streams,
                        "tasks_waiting_send": statistics.tasks_waiting_send,
                        "tasks_waiting_receive": statistics.tasks_waiting_receive,
                    }
                )
        finally:
            for stream in leaked:
                stream.close()
            if gc_was_enabled:
                gc.enable()
            for _ in range(3):
                gc.collect()

        self.assertEqual(
            leaked,
            [],
            f"Inspect 0.3.258 left {len(leaked)} AnyIO receive stream(s) open: "
            f"{details}",
        )


if __name__ == "__main__":
    unittest.main()
