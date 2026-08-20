#!/usr/bin/env python3
from __future__ import annotations

import shutil
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "python" / "gs_eval_adapters"
TESTS = ROOT / "tests" / "adapters" / "harbor"


@dataclass(frozen=True, slots=True)
class Mutation:
    name: str
    path: str
    old: str
    new: str


MUTATIONS = (
    Mutation(
        "allow-multiple-attempts",
        "harbor_adapter.py",
        '    if type(job["n_attempts"]) is not int or job["n_attempts"] != 1:\n',
        "    if False:\n",
    ),
    Mutation(
        "allow-multiple-total-trials",
        "harbor_adapter.py",
        '    if (\n        type(job_result.get("n_total_trials")) is not int\n        or job_result["n_total_trials"] != 1\n    ):\n',
        "    if False:\n",
    ),
    Mutation(
        "allow-boolean-agent-concurrency",
        "harbor_adapter.py",
        '        or type(agent["n_concurrent"]) is not int\n',
        "        or False\n",
    ),
    Mutation(
        "allow-unauthorized-worker-environment",
        "harbor_adapter.py",
        '        if set(worker_values) - {"DOCKER_HOST", "XDG_RUNTIME_DIR"}:\n',
        "        if False:\n",
    ),
    Mutation(
        "disable-harbor-telemetry-switch",
        "harbor_adapter.py",
        '            "HARBOR_TELEMETRY": "0",\n',
        '            "HARBOR_TELEMETRY": "1",\n',
    ),
    Mutation(
        "change-harbor-run-argv",
        "harbor_adapter.py",
        '            "run",\n',
        '            "job",\n',
    ),
    Mutation(
        "allow-unbound-image-reference",
        "harbor_adapter.py",
        '    if "@" not in reference or reference.rsplit("@", 1)[1] != digest:\n        raise AdapterContractError(f"{label} must be bound to its image digest")\n',
        '    if False:\n        raise AdapterContractError(f"{label} must be bound to its image digest")\n',
    ),
    Mutation(
        "allow-unbound-replay-image-reference",
        "harbor_replay.py",
        '    if "@" not in reference or reference.rsplit("@", 1)[1] != digest:\n        raise AdapterContractError(f"{label} must be bound to its image digest")\n',
        '    if False:\n        raise AdapterContractError(f"{label} must be bound to its image digest")\n',
    ),
    Mutation(
        "skip-stage-obligation-gate",
        "harbor_replay.py",
        '    elif not obligations["stage_obligations_consistent"]:\n',
        "    elif False:\n",
    ),
    Mutation(
        "skip-exception-boundary-gate",
        "harbor_replay.py",
        '    elif not obligations["exception_boundary_consistent"]:\n',
        "    elif False:\n",
    ),
    Mutation(
        "trust-invalid-timeout-attribution",
        "harbor_replay.py",
        '            if obligations["timeout_attribution_valid"]\n            else AdapterStatus.INFRA\n',
        "            if True\n            else AdapterStatus.INFRA\n",
    ),
)


def prepare_mutant(root: Path) -> None:
    package_root = root / "python" / "gs_eval_adapters"
    tests_root = root / "tests" / "adapters" / "harbor"
    package_root.parent.mkdir(parents=True)
    tests_root.parent.mkdir(parents=True)
    shutil.copytree(SOURCE, package_root)
    shutil.copytree(TESTS, tests_root)


def mutate(root: Path, mutation: Mutation) -> None:
    path = root / "python" / "gs_eval_adapters" / mutation.path
    content = path.read_text(encoding="utf-8")
    count = content.count(mutation.old)
    if count != 1:
        raise RuntimeError(
            f"{mutation.name}: expected one site in {mutation.path}, found {count}"
        )
    path.write_text(content.replace(mutation.old, mutation.new, 1), encoding="utf-8")


def run_suite(root: Path) -> subprocess.CompletedProcess[str]:
    environment = {
        "PYTHONHASHSEED": "0",
        "PYTHONPATH": os_pathsep(
            root / "python",
            root / "tests" / "adapters",
            root / "tests" / "adapters" / "harbor",
        ),
    }
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(root / "tests" / "adapters" / "harbor"),
            "-p",
            "test_*.py",
        ],
        cwd=root,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def os_pathsep(*paths: Path) -> str:
    return os.pathsep.join(str(path) for path in paths)


def main() -> int:
    survivors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gitspace-task12-mutations-") as temporary:
        temporary_root = Path(temporary)
        for mutation in MUTATIONS:
            mutant_root = temporary_root / mutation.name
            prepare_mutant(mutant_root)
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
