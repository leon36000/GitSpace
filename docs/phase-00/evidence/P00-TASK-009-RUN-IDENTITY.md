---
evidence_id: GS-EVIDENCE-P00-TASK-009-RUN-IDENTITY
subject: P00-TASK-009
status: GREEN_VERIFIED_PRE_REVIEW
updated: 2026-08-14
---
# P00-TASK-009 — Provenance-derived run identity

## Finding

**EVIDENCE:** the initial deterministic fixture used one static run, verdict and evidence suffix per scenario. Opening the same Foundry root with a second source commit therefore reused the same run identity.

This was a semantic provenance alias: two different source commits could claim the same `GS-RUN-*` identity even though `RunReceipt.source_commit` and `EvidenceBundle.commit_sha` differed.

## RED

```text
commit: a9b49834f68e5593d9a6dcb30a5018ffbd82e2f3
workflow run: 31786942430
job: 94724858179
checkout: exact detached head
permissions: contents: read
failing test: one_deterministic_run_id_cannot_alias_two_source_commits
failure: the same deterministic run ID accepted two source commits
```

The other Task 9 contract, replay and substitution tests passed before this new assertion failed. The RED therefore isolated the identity defect rather than a general build failure.

## Correction

The qualified identity suffix is now derived from:

```text
SHA-256(
  "gitspace:p00-task-009:identity:v1"
  || NUL
  || source_commit
  || NUL
  || scenario_slug
)[0..128 bits]
→ 26-character Crockford Base32
```

The shared suffix is used by:

```text
GS-RUN-<suffix>
GS-VERDICT-<suffix>
GS-EVIDENCE-<suffix>
```

The full source commit remains present in the receipt and EvidenceBundle and is independently checked during replay.

## GREEN

```text
commit: 2ecaac67f7da20e634fd83228afbeec74c4e85bc
Task 9 workflow run: 31788423233
Task 9 job: 94729528366
checkout: exact detached head
permissions: contents: read
Task 9 result: success
all eight Phase 00 workflows at this head: success
```

Fresh assertions prove:

- same source commit plus scenario reproduces the same schema-compatible suffix;
- changing the source commit changes the run identity;
- changing the scenario changes the run identity;
- two commits can coexist in one Foundry store without aliasing;
- each matching Foundry replays its own receipt;
- cross-commit replay fails closed;
- the existing idempotent rerun contract remains green;
- workspace tests, Clippy `-D warnings`, rustfmt and clean-tree gates pass.

## Limits and residual risk

- **ASSUMPTION:** 128-bit truncated SHA-256 identity is sufficient for the bounded M0 fixture. Full provenance is not truncated in the evidence record.
- **LIMIT:** outside the exact-head CI harness, the CLI caller supplies `source_commit`; Task 9 does not sign or independently discover repository provenance.
- **BLOCKED:** this evidence does not satisfy role-separated review, signed merge, fresh post-merge replay, canonical state promotion or RAGLite projection.

## Status

`P00-TASK-009` remains `PARTIALLY_VERIFIED`. This finding is closed at the implementation and exact-head CI boundary only.
