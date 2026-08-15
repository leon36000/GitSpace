from __future__ import annotations

import asyncio
import unittest
from threading import Barrier, BrokenBarrierError, Thread
from types import SimpleNamespace
from unittest.mock import patch

from gs_eval_adapters.inspect_cleanup import (
    _InspectHookApi,
    _close_receiver,
    _close_sender,
    _load_hook_api,
    _reset_active_streams,
    inspect_event_stream_cleanup,
)


class Receiver:
    def __init__(self) -> None:
        self.closed = 0

    async def aclose(self) -> None:
        self.closed += 1


class Sender:
    def __init__(self) -> None:
        self.closed = 0

    async def aclose(self) -> None:
        self.closed += 1


class CleanupContractTests(unittest.TestCase):
    def test_hook_api_matches_the_pinned_official_release(self) -> None:
        api = _load_hook_api()

        self.assertEqual(api.hooks.__name__, "inspect_ai.hooks._hooks")
        self.assertEqual(api.original.__name__, "drain_sample_events")
        self.assertEqual(api.sample_active.__module__, "inspect_ai.log._samples")
        self.assertEqual(api.emit_to_all.__name__, "_emit_to_all")
        self.assertEqual(api.anyio.__name__, "anyio")

    def test_cleanup_context_serializes_concurrent_installs(self) -> None:
        async def original() -> None:
            return None

        hooks = SimpleNamespace(drain_sample_events=original)
        api = _InspectHookApi(
            hooks=hooks,
            original=original,
            sample_active=lambda: None,
            anyio=SimpleNamespace(),
            emit_to_all=lambda callback: callback,
            logger=SimpleNamespace(),
        )
        start = Barrier(2)
        simultaneous_entry = Barrier(2)
        overlaps: list[bool] = []

        def worker() -> None:
            start.wait()
            with inspect_event_stream_cleanup():
                try:
                    simultaneous_entry.wait(timeout=1.0)
                except BrokenBarrierError:
                    return
                overlaps.append(True)

        with patch(
            "gs_eval_adapters.inspect_cleanup._load_hook_api",
            return_value=api,
        ):
            threads = [Thread(target=worker), Thread(target=worker)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=3.0)

        self.assertTrue(all(not thread.is_alive() for thread in threads))
        self.assertEqual(overlaps, [], "cleanup shim was installed concurrently")
        self.assertIs(hooks.drain_sample_events, original)

    def test_receiver_is_closed_exactly_once(self) -> None:
        receiver = Receiver()
        anyio = SimpleNamespace(
            ClosedResourceError=RuntimeError,
            BrokenResourceError=ConnectionError,
        )

        asyncio.run(_close_receiver(receiver, anyio))

        self.assertEqual(receiver.closed, 1)

    def test_sender_is_closed_exactly_once(self) -> None:
        sender = Sender()
        active = SimpleNamespace(event_send=sender)

        asyncio.run(_close_sender(active))

        self.assertEqual(sender.closed, 1)

    def test_active_stream_references_are_cleared(self) -> None:
        active = SimpleNamespace(
            event_receive=object(),
            event_send=object(),
            event_done=object(),
        )

        _reset_active_streams(active)

        self.assertIsNone(active.event_receive)
        self.assertIsNone(active.event_send)
        self.assertIsNone(active.event_done)


if __name__ == "__main__":
    unittest.main()
