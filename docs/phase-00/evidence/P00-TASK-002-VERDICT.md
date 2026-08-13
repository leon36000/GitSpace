---
evidence_id: GS-EVIDENCE-P00-TASK-002-VERDICT
status: VERIFIED_PENDING_MERGE
verified_at: 2026-08-13
base_commit: 9317bf17ae49bb29a12d9b885cdeaea759353c70
head_commit: aa32825d6c2cba79fcb4da0f00b3bf65566bf4a1
merge_candidate: 5629dbe1e8fcf574245a1b580bc003a06ea7e53d
---
# P00-TASK-002 — Verdict evidence

Task 2 defines eight Draft 2020-12 contracts and no runtime implementation.

RED run `31740828840`: expected failure because `eval-task-spec.schema.json` did not exist.

Negative evidence `NEG-P00-005`: after schemas were added, run `31741417616` proved all schemas meta-valid and all negative controls valid, but composed examples failed because the test harness had no local registry for cross-schema URNs. The harness was replaced with `referencing.Registry` plus `DRAFT202012.create_resource`; schema semantics were not weakened.

GREEN run `31741906065`: PASS. It verified Python 3.12.13, `jsonschema==4.26.0`, 11/11 contract tests and a clean repository against GitHub merge candidate `5629dbe1e8fcf574245a1b580bc003a06ea7e53d`, built from base `9317bf17ae49bb29a12d9b885cdeaea759353c70` and head `aa32825d6c2cba79fcb4da0f00b3bf65566bf4a1`.

The contracts verify offline URN IDs, closed structured core objects, strict SHA-256 digests and CAS URIs, namespaced extensions, positive graph resolution, invalid IDs/versions/properties, and two obvious contradictory `safe_success` cases.

Full non-compensable verdict semantics remain Task 7 responsibility; Task 2 does not create a second Verdict Engine in JSON Schema.

GitHub pull-request CI attests the synthetic merge candidate, not the branch head; both identities are recorded separately.

Remaining gates: final CI on this evidence closure, final diff review, merge, post-merge verification, then state/RAGLite synchronization before Task 3.
