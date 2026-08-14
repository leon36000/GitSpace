---
evidence_id: P00-TASK-011-RED
status: VALID_RED
recorded_at: 2026-08-14
base_commit: e082cf941d865d71347feae475e4a8e43aeab5e2
red_branch: agent/p00-task-011-red-v1
red_pr: 48
red_head: 5c3ba0e74c214b478e539936e3bef335e4187bde
workflow_run: 31838641477
workflow_job: 94890506040
inspect_version: 0.3.258
inspect_commit: e72c73f8a514c53ddf55da180e4bedaf8f0362b4
---
# P00-TASK-011 — RED evidence

## Contract written before production

The Task 11 packet, official qualification pin, static projection, contract tests, replay-without-Inspect tests and adversarial tests were committed before either production module existed.

The RED branch contained neither:

```text
python/gs_eval_adapters/inspect_adapter.py
python/gs_eval_adapters/inspect_replay.py
```

and did not add `inspect-ai` to `pyproject.toml`.

## First harness finding

Workflow `31838580017`, job `94890314317`, failed too early because it had not installed Task 10's existing `jsonschema` dependency. The observed error was `ModuleNotFoundError: jsonschema`.

This was a proof-harness defect. The workflow alone was corrected to install uv 0.12.0 and sync the existing frozen Task 10 graph. No Inspect dependency or production module was added.

## Corrected external RED

```yaml
head: 5c3ba0e74c214b478e539936e3bef335e4187bde
workflow_run: 31838641477
workflow_job: 94890506040
python: 3.12.13
uv: 0.12.0
permissions:
  contents: read
conclusion: success
```

The inner command failed exactly with:

```text
ModuleNotFoundError: No module named 'gs_eval_adapters.inspect_adapter'
```

The workflow then confirmed:

- Task 10 dependencies were present in frozen mode;
- both Task 11 production modules were absent;
- the Inspect dependency was absent;
- the checkout remained clean.

PR #48 was closed unmerged. GREEN starts from the same canonical base.

## Verdict

`VALID_RED`.
