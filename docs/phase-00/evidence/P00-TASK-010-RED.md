---
evidence_id: P00-TASK-010-RED
status: RED_CONTRACT_READY
recorded_at: 2026-08-14
base_commit: a5dc165ff78df74db35779695dd116c0b085a6a5
red_branch: agent/p00-task-010-red-v1
---
# P00-TASK-010 — RED evidence contract

## Authority boundary under test

The desired provider-neutral Python SDK is specified by contract and adversarial tests before production code.

The RED branch intentionally contains no `python/gs_eval_adapters` path.

## Expected external observation

```bash
PYTHONPATH=python python tests/adapters/test_contract.py
```

must fail with:

```text
ModuleNotFoundError: No module named 'gs_eval_adapters'
```

The GitHub Actions proof succeeds only after asserting that exact non-zero import failure and confirming again that the production package is absent.

## Required follow-up

After external RED:

1. record exact workflow run, job, commit and checkout;
2. close the RED PR unmerged;
3. create a fresh GREEN branch from the same canonical base;
4. implement only the accepted SDK contract;
5. preserve this RED evidence in the GREEN evidence bundle.

## Status

`RED_CONTRACT_READY`, not yet `VALID_RED` until GitHub Actions reproduces the expected failure.
