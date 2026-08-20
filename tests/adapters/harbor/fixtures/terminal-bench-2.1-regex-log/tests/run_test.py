#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path
from types import ModuleType

DEFAULT_WORKSPACE_ROOT = Path("/app")
DEFAULT_TEST_SOURCE = Path("/tests/test_outputs.py")
DEFAULT_REWARD_PATH = Path("/logs/verifier/reward.json")
DEFAULT_RESULT_PATH = Path("/logs/verifier/gitspace-result.json")
RESULT_SCHEMA = "gitspace.verifier.v1"


def run_verifier(
    *,
    workspace_root: Path = DEFAULT_WORKSPACE_ROOT,
    test_source: Path = DEFAULT_TEST_SOURCE,
    reward_path: Path = DEFAULT_REWARD_PATH,
    result_path: Path = DEFAULT_RESULT_PATH,
) -> int:
    source_digest: str | None = None
    try:
        _require_clean_output_paths(reward_path, result_path)
        _require_workspace(workspace_root)
        source_digest = _sha256_file(test_source)
        module = _load_test_module(test_source)
        test_callable = getattr(module, "test_regex_matches_dates", None)
        if not callable(test_callable):
            raise RuntimeError("locked verifier callable is missing")
        test_callable()
    except AssertionError as error:
        _write_result(
            reward_path,
            result_path,
            b'{"reward":0}\n',
            _result_bytes(
                kind="functional_assertion",
                source_digest=source_digest,
                error=error,
            ),
        )
        return 0
    except BaseException as error:
        _write_infra_result(
            result_path,
            source_digest=source_digest,
            error=error,
        )
        return 70
    else:
        _write_result(
            reward_path,
            result_path,
            b'{"reward":1}\n',
            _result_bytes(
                kind="functional_pass",
                source_digest=source_digest,
                error=None,
            ),
        )
        return 0


def main() -> int:
    return run_verifier()


def _require_clean_output_paths(reward_path: Path, result_path: Path) -> None:
    if reward_path.exists() or reward_path.is_symlink():
        raise RuntimeError("reward artifact already exists")
    if result_path.exists() or result_path.is_symlink():
        raise RuntimeError("verifier result artifact already exists")


def _require_workspace(workspace_root: Path) -> None:
    if Path.cwd().resolve() != workspace_root.resolve():
        raise RuntimeError("verifier cwd is not the declared workspace")


def _sha256_file(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError("locked verifier source is not a regular file")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_test_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("gitspace_locked_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("locked verifier source cannot be imported")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_infra_result(
    result_path: Path,
    *,
    source_digest: str | None,
    error: BaseException,
) -> None:
    _atomic_write(
        result_path,
        _result_bytes(
            kind="harness_infra",
            source_digest=source_digest,
            error=error,
        ),
    )


def _write_result(
    reward_path: Path,
    result_path: Path,
    reward: bytes,
    result: bytes,
) -> None:
    _atomic_write(result_path, result)
    _atomic_write(reward_path, reward)


def _result_bytes(
    *,
    kind: str,
    source_digest: str | None,
    error: BaseException | None,
) -> bytes:
    if error is None:
        error_type = None
        error_message = None
    else:
        error_type = type(error).__name__
        error_message = str(error)[:512]
    value = {
        "exception_message_or_null": error_message,
        "exception_type_or_null": error_type,
        "kind": kind,
        "schema": RESULT_SCHEMA,
        "test_source_sha256": source_digest,
    }
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        + b"\n"
    )


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
