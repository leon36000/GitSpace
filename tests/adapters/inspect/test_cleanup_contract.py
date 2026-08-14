from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace

from gs_eval_adapters.inspect_cleanup import (
    _close_receiver,
    _close_sender,
    _reset_active_streams,
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
            event_emitter=object(),
        )

        _reset_active_streams(active)

        self.assertIsNone(active.event_receive)
        self.assertIsNone(active.event_send)
        self.assertIsNone(active.event_emitter)


if __name__ == "__main__":
    unittest.main()
