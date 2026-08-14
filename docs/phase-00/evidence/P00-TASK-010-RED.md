---
evidence_id: P00-TASK-010-RED
status: VALID_RED
recorded_at: 2026-08-14
base_commit: a5dc165ff78df74db35779695dd116c0b085a6a5
red_branch: agent/p00-task-010-red-v1
red_pr: 44
red_head: 07bcba61a25fa3a32a4b92cdddbff58b2aaa881e
workflow_run: 31825786291
workflow_job: 94849477467
---
# P00-TASK-010 — RED evidence

## Intended boundary

The complete provider-neutral SDK contract and adversarial fixtures were written before production code. The RED branch intentionally contained no `python/gs_eval_adapters` directory.

## First observation and harness defect

Workflow run `31825706535`, job `94849213767`, observed the expected import failure and confirmed the production path was absent. Its final clean-tree gate failed because the workflow wrote `task10-red.log` inside the checkout.

This was classified as a proof-harness defect, not an implementation failure. The log path moved to `/tmp`; no production package or dependency was added.

## Corrected external RED

```yaml
head: 07bcba61a25fa3a32a4b92cdddbff58b2aaa881e
workflow_run: 31825786291
workflow_job: 94849477467
python: 3.12.13
permissions:
  contents: read
conclusion: success
```

The inner command:

```bash
PYTHONPATH=python python tests/adapters/test_contract.py
```

failed exactly with:

```text
ModuleNotFoundError: No module named 'gs_eval_adapters'
```

The workflow succeeded only after asserting the non-zero result, the exact missing package, absence of `python/gs_eval_adapters`, and a clean repository.

PR #44 was closed unmerged. GREEN starts from the same canonical base.

## Verdict

`VALID_RED`.
