#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "python" / "gs_eval_adapters"
TESTS = ROOT / "tests" / "adapters" / "inspect"
QUALIFICATION = (
    ROOT
    / "docs"
    / "phase-00"
    / "qualifications"
    / "inspect-ai-0.3.258.json"
)


@dataclass(frozen=True, slots=True)
class Mutation:
    name: str
    path: str
    old: str
    new: str


MUTATIONS = (
    Mutation(
        "skip-installed-version",
        "inspect_adapter.py",
        '        if metadata.version("inspect-ai") != INSPECT_VERSION:\n',
        "        if False:\n",
    ),
    Mutation(
        "allow-arbitrary-log-wrapper",
        "inspect_adapter.py",
        "    if logs_type is not list:\n",
        "    if False:\n",
    ),
    Mutation(
        "allow-non-eval-log",
        "inspect_adapter.py",
        "    if type(log) is not EvalLog:\n",
        "    if False:\n",
    ),
    Mutation(
        "skip-published-artifact-digest",
        "inspect_adapter.py",
        "        if uri != expected:\n",
        "        if False:\n",
    ),
    Mutation(
        "skip-record-uri-digest",
        "inspect_adapter.py",
        "        if record_uri != expected_record_uri:\n",
        "        if False:\n",
    ),
    Mutation(
        "skip-independent-score-agreement",
        "inspect_adapter.py",
        '        elif not replay.obligations["inspect_score_agrees"]:\n',
        "        elif False:\n",
    ),
    Mutation(
        "skip-framework-mapping-check",
        "inspect_adapter.py",
        "            if value.get(key) != item:\n",
        "            if False:\n",
    ),
    Mutation(
        "bind-wrong-cleanup-api",
        "inspect_cleanup.py",
        '        sample_active = getattr(hooks, "sample_active")\n',
        '        sample_active = getattr(\n            import_module("inspect_ai.util._sandbox.context"), "sample_active"\n        )\n',
    ),
    Mutation(
        "drop-cleanup-serialization",
        "inspect_cleanup.py",
        "    with _INSPECT_CLEANUP_LOCK:\n",
        "    if True:\n",
    ),
    Mutation(
        "drop-event-receiver-close",
        "inspect_cleanup.py",
        "        await receive.aclose()\n",
        "",
    ),
    Mutation(
        "drop-cleanup-shim-restore",
        "inspect_cleanup.py",
        '            setattr(api.hooks, "drain_sample_events", api.original)\n',
        "",
    ),
    Mutation(
        "accept-multiple-full-log-samples",
        "inspect_replay.py",
        "    if type(samples) is not list or len(samples) != 1:\n",
        "    if type(samples) is not list or not samples:\n",
    ),
    Mutation(
        "route-full-log-as-static-projection",
        "inspect_replay.py",
        '    if "projection_version" in data:\n',
        "    if True:\n",
    ),
    Mutation(
        "allow-projection-bool-version",
        "inspect_replay.py",
        '    if _exact_int(\n        projection["projection_version"], "projection_version"\n    ) != 1:\n',
        '    if projection["projection_version"] != 1:\n',
    ),
    Mutation(
        "allow-projection-bool-epoch",
        "inspect_replay.py",
        '        or _exact_int(sample["epoch"], "sample.epoch") != 1\n',
        '        or sample["epoch"] != 1\n',
    ),
    Mutation(
        "allow-projection-scorer-options",
        "inspect_replay.py",
        '    if options != _OPTIONS:\n        raise AdapterContractError("projection scorer options mismatch")\n',
        '    if False:\n        raise AdapterContractError("projection scorer options mismatch")\n',
    ),
    Mutation(
        "allow-record-scorer-options",
        "inspect_replay.py",
        '    if options != _OPTIONS:\n        raise AdapterContractError("record scorer options mismatch")\n',
        '    if False:\n        raise AdapterContractError("record scorer options mismatch")\n',
    ),
    Mutation(
        "allow-record-string-subclasses",
        "inspect_replay.py",
        "        if type(actual) is not str or actual != expected:\n",
        "        if actual != expected:\n",
    ),
    Mutation(
        "drop-record-json-revalidation",
        "inspect_replay.py",
        "    def to_json(self) -> JsonObject:\n        _validate_record(self)\n",
        "    def to_json(self) -> JsonObject:\n",
    ),
    Mutation(
        "drop-replay-result-revalidation",
        "inspect_replay.py",
        "    def to_json(self) -> JsonObject:\n        _validate_replay_result(self)\n",
        "    def to_json(self) -> JsonObject:\n",
    ),
    Mutation(
        "allow-incomplete-replay-obligations",
        "inspect_replay.py",
        "    if set(result.obligations) != _OBLIGATION_FIELDS:\n",
        "    if False:\n",
    ),
    Mutation(
        "force-independent-match",
        "inspect_replay.py",
        "    matched = _normalize(parsed.output) == _normalize(parsed.target)\n",
        "    matched = True\n",
    ),
    Mutation(
        "force-score-agreement",
        "inspect_replay.py",
        "    agrees = parsed.inspect_score == score\n",
        "    agrees = True\n",
    ),
    Mutation(
        "drop-record-field-closure",
        "inspect_replay.py",
        '        _exact_fields(data, _RECORD_FIELDS, "inspect_record")\n',
        "",
    ),
    Mutation(
        "sort-event-order",
        "inspect_replay.py",
        '        event_types=tuple(_exact_string(item, "event_type") for item in events),\n',
        '        event_types=tuple(sorted(_exact_string(item, "event_type") for item in events)),\n',
    ),
    Mutation(
        "couple-replay-to-inspect",
        "inspect_replay.py",
        "from __future__ import annotations\n",
        "from __future__ import annotations\n\nimport inspect_ai\n",
    ),
)


def prepare_mutant(root: Path) -> None:
    package_root = root / "python" / "gs_eval_adapters"
    tests_root = root / "tests" / "adapters" / "inspect"
    qualification_root = root / "docs" / "phase-00" / "qualifications"
    package_root.parent.mkdir(parents=True)
    tests_root.parent.mkdir(parents=True)
    qualification_root.mkdir(parents=True)
    shutil.copytree(SOURCE, package_root)
    shutil.copytree(TESTS, tests_root)
    shutil.copy2(QUALIFICATION, qualification_root / QUALIFICATION.name)
    shutil.copy2(ROOT / "uv.lock", root / "uv.lock")


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
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        [
            str(root / "python"),
            str(root / "tests" / "adapters" / "inspect"),
        ]
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(root / "tests" / "adapters" / "inspect"),
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


def main() -> int:
    survivors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="gitspace-task11-mutations-") as temporary:
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
