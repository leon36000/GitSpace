from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from importlib import import_module
from threading import Lock
from typing import Any, Callable, Iterator

from .errors import AdapterContractError

_INSPECT_CLEANUP_LOCK = Lock()


@dataclass(frozen=True, slots=True)
class _InspectHookApi:
    hooks: Any
    original: Any
    sample_active: Callable[[], Any]
    anyio: Any
    emit_to_all: Callable[[Callable[..., Any]], Any]
    logger: Any


@contextmanager
def inspect_event_stream_cleanup() -> Iterator[None]:
    """Install and restore the pinned Inspect 0.3.258 cleanup shim.

    The replacement targets private release-pinned symbols, so installation and
    the entire controlled eval are serialized. The original function is always
    restored before another caller can enter.
    """

    with _INSPECT_CLEANUP_LOCK:
        api = _load_hook_api()
        setattr(api.hooks, "drain_sample_events", _drain_function(api))
        try:
            yield
        finally:
            setattr(api.hooks, "drain_sample_events", api.original)


def _load_hook_api() -> _InspectHookApi:
    try:
        hooks = import_module("inspect_ai.hooks._hooks")
        original = getattr(hooks, "drain_sample_events")
        sample_active = getattr(hooks, "sample_active")
        anyio = getattr(hooks, "anyio")
        emit_to_all = getattr(hooks, "_emit_to_all")
        logger = getattr(hooks, "logger")
    except (ImportError, AttributeError) as error:
        raise AdapterContractError(
            "Inspect 0.3.258 event cleanup internals are unavailable"
        ) from error

    return _InspectHookApi(
        hooks=hooks,
        original=original,
        sample_active=sample_active,
        anyio=anyio,
        emit_to_all=emit_to_all,
        logger=logger,
    )


def _drain_function(api: _InspectHookApi) -> Callable[[], Any]:
    async def drain_sample_events() -> None:
        await _drain_active_sample(api)

    return drain_sample_events


async def _drain_active_sample(api: _InspectHookApi) -> None:
    active = api.sample_active()
    if active is None:
        return

    receive = active.event_receive
    try:
        await _close_sender(active)
        await _wait_for_emitter(active, api)
        await _emit_pending_events(receive, api)
    except Exception as error:
        api.logger.warning("Exception draining sample events: %s", error)
    finally:
        await _close_receiver(receive, api.anyio)
        _reset_active_streams(active)


async def _close_sender(active: Any) -> None:
    sender = active.event_send
    if sender is not None:
        await sender.aclose()


async def _wait_for_emitter(active: Any, api: _InspectHookApi) -> None:
    done = active.event_done
    if done is None:
        return

    with api.anyio.move_on_after(5):
        await done.wait()
    if not done.is_set():
        api.logger.warning("Timed out waiting for sample event emitter to drain")


async def _emit_pending_events(receive: Any, api: _InspectHookApi) -> None:
    if receive is None:
        return

    while True:
        try:
            event = receive.receive_nowait()
        except (
            api.anyio.WouldBlock,
            api.anyio.EndOfStream,
            api.anyio.ClosedResourceError,
        ):
            return

        async def emit_event(hook: Any, event: Any = event) -> None:
            await hook.on_sample_event(event)

        await api.emit_to_all(emit_event)


async def _close_receiver(receive: Any, anyio: Any) -> None:
    if receive is None:
        return

    try:
        await receive.aclose()
    except (anyio.ClosedResourceError, anyio.BrokenResourceError):
        pass


def _reset_active_streams(active: Any) -> None:
    active.event_receive = None
    active.event_send = None
    active.event_done = None
