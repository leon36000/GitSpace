#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "python" / "gs_eval_adapters"


@dataclass(frozen=True, slots=True)
class Mutation:
    name: str
    path: str
    old: str
    new: str


MUTATIONS = (
    Mutation(
        "skip-task-schema",
        "sdk.py",
        "    validate_task(task)\n",
        "",
    ),
    Mutation(
        "skip-agent-schema",
        "sdk.py",
        "    validate_agent(agent)\n",
        "",
    ),
    Mutation(
        "skip-semantic-snapshot",
        "sdk.py",
        "    if snapshot != canonical_request:\n",
        "    if False:\n",
    ),
    Mutation(
        "allow-unnamespaced-extension",
        "json_boundary.py",
        "        if not EXTENSION_KEY.fullmatch(key):\n",
        "        if False:\n",
    ),
    Mutation(
        "allow-unsafe-integer",
        "json_boundary.py",
        "        if not -SAFE_INTEGER <= value <= SAFE_INTEGER:\n",
        "        if False:\n",
    ),
    Mutation(
        "allow-nonfinite-float",
        "json_boundary.py",
        "        if not math.isfinite(value):\n",
        "        if False:\n",
    ),
    Mutation(
        "allow-negative-zero",
        "json_boundary.py",
        "        if value == 0.0 and math.copysign(1.0, value) < 0.0:\n",
        "        if False:\n",
    ),
    Mutation(
        "allow-nonstr-key",
        "json_boundary.py",
        "                if type(key) is not str:\n",
        "                if False:\n",
    ),
    Mutation(
        "allow-arbitrary-artifact-uri",
        "json_boundary.py",
        "    if type(value) is not str or not CAS_URI.fullmatch(value):\n",
        "    if False:\n",
    ),
    Mutation(
        "allow-prepared-core-fields",
        "sdk.py",
        "    _require_exact_keys(prepared, _PREPARED_KEYS, path=\"$/prepared\")\n",
        "",
    ),
    Mutation(
        "allow-incomplete-adapter",
        "registry.py",
        "    if missing:\n",
        "    if False:\n",
    ),
    Mutation(
        "allow-descriptor-subclass",
        "registry.py",
        "    if type(descriptor) is not AdapterDescriptor:\n",
        "    if False:\n",
    ),
    Mutation(
        "allow-scalar-subclass",
        "json_boundary.py",
        "    if value_type is str:\n",
        "    if isinstance(value, str):\n",
    ),
    Mutation(
        "drop-result-core-check",
        "sdk.py",
        "    _require_exact_keys(payload, _RESULT_KEYS, path=\"$/result\")\n",
        "",
    ),
)


def mutate(root: Path, mutation: Mutation) -> None:
    path = root / "python" / "gs_eval_adapters" / mutation.path
    content = path.read_text(encoding="utf-8")
    count = content.count(mutation.old)
    if count != 1:
        raise RuntimeError(
            f"{mutation.name}: expected one mutation site in {mutation.path}, found {count}"
        )
    path.write_text(content.replace(mutation.old, mutation.new, 1), encoding="utf-8")


def run_suite(root: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(root / "python")
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(ROOT / "tests" / "adapters"),
            "-p",
            "test_*.py",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def main() -> int:
    if not SOURCE.is_dir():
        raise RuntimeError(f"missing adapter source at {SOURCE}")

    survivors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gitspace-task10-mutations-") as temporary:
        temporary_root = Path(temporary)
        for mutation in MUTATIONS:
            mutant_root = temporary_root / mutation.name
            package_root = mutant_root / "python" / "gs_eval_adapters"
            package_root.parent.mkdir(parents=True)
            shutil.copytree(SOURCE, package_root)
            mutate(mutant_root, mutation)
            result = run_suite(mutant_root)
            if result.returncode == 0:
                survivors.append(mutation.name)
                print(f"SURVIVED {mutation.name}")
            else:
                print(f"KILLED   {mutation.name}")

    print(f"mutations={len(MUTATIONS)} killed={len(MUTATIONS) - len(survivors)}")
    if survivors:
        print("survivors=" + ",".join(survivors))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
