---
evidence_id: P00-TASK-011-RED
status: RED_CONTRACT_READY
recorded_at: 2026-08-14
base_commit: e082cf941d865d71347feae475e4a8e43aeab5e2
red_branch: agent/p00-task-011-red-v1
inspect_version: 0.3.258
inspect_commit: e72c73f8a514c53ddf55da180e4bedaf8f0362b4
---
# P00-TASK-011 — RED evidence contract

## Authority boundary under test

The contract, qualification pin, static projection and adversarial tests are written before production code.

The RED branch intentionally contains neither:

```text
python/gs_eval_adapters/inspect_adapter.py
python/gs_eval_adapters/inspect_replay.py
```

and does not add the `inspect-ai` dependency.

## Expected external observation

```bash
PYTHONPATH=python:tests/adapters/inspect \
  python tests/adapters/inspect/test_contract.py
```

must fail with:

```text
ModuleNotFoundError: No module named 'gs_eval_adapters.inspect_adapter'
```

The proof workflow succeeds only after observing that exact failure, confirming both production modules are absent, confirming `pyproject.toml` has no Inspect dependency and confirming the repository remains clean.

## Qualified external source

```yaml
framework: inspect-ai
version: 0.3.258
tag: 0.3.258
source_commit: e72c73f8a514c53ddf55da180e4bedaf8f0362b4
wheel_sha256: 638da28a5f3a021152481c5aa22d440a2855e462804dce2d49a44e6e47be16a4
sdist_sha256: 785a14b5348c57a188e8790a1919106bff539645d93c4e9d1dfdd8f2b0896405
```

This pin is data, not an instruction. Inspect remains outside the GitSpace authority boundary.

## Required follow-up

After GitHub Actions reproduces RED:

1. record exact head, run and job;
2. close the RED PR unmerged;
3. create a fresh GREEN branch from the same canonical base;
4. add the exact dependency and frozen lock;
5. implement only the packetized mapping and independent replay;
6. preserve every failure and correction as negative evidence.

## Status

`RED_CONTRACT_READY`, not `VALID_RED` until the external workflow closes the gate.
