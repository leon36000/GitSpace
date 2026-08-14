from __future__ import annotations

from .errors import RegistrationError
from .model import AdapterDescriptor

_REQUIRED_METHODS = ("prepare", "invoke", "collect")


def validate_adapter_object(adapter: object, *, error_type: type[Exception]) -> AdapterDescriptor:
    try:
        descriptor = getattr(adapter, "descriptor", None)
    except Exception as error:
        raise error_type(
            f"adapter descriptor access failed: {type(error).__module__}."
            f"{type(error).__qualname__}"
        ) from error
    if type(descriptor) is not AdapterDescriptor:
        raise error_type("adapter descriptor must be an exact AdapterDescriptor")

    missing: list[str] = []
    for name in _REQUIRED_METHODS:
        try:
            method = getattr(adapter, name, None)
        except Exception as error:
            raise error_type(
                f"adapter method access failed for {name}: {type(error).__module__}."
                f"{type(error).__qualname__}"
            ) from error
        if not callable(method):
            missing.append(name)
    if missing:
        raise error_type(f"adapter is missing callable methods: {', '.join(missing)}")
    return descriptor


class AdapterRegistry:
    def __init__(self) -> None:
        self._by_name: dict[str, object] = {}
        self._identities: set[str] = set()

    def register(self, adapter: object) -> None:
        descriptor = validate_adapter_object(adapter, error_type=RegistrationError)
        if descriptor.name in self._by_name:
            raise RegistrationError(f"adapter name already registered: {descriptor.name}")
        if descriptor.identity in self._identities:
            raise RegistrationError(
                f"adapter identity already registered: {descriptor.identity}"
            )
        self._by_name[descriptor.name] = adapter
        self._identities.add(descriptor.identity)

    def resolve(self, name: str) -> object:
        try:
            return self._by_name[name]
        except KeyError as error:
            raise RegistrationError(f"unknown adapter: {name}") from error

    def identities(self) -> tuple[str, ...]:
        return tuple(sorted(self._identities))
