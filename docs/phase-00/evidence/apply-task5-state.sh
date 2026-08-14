#!/usr/bin/env bash
set -euo pipefail

cat > 00_GITSPACE_START_HERE.md <<'EOF'
---
doc_id: GS-00
title: GitSpace — Start Here
authority: ROUTER
status: ACTIVE
version: 0.4.5
updated: 2026-08-13
---
# GitSpace — START HERE

GitSpace est un **Native Software World Engine pour contributeurs IA**. Architecture C et C0 sont acceptées. L’humain reste souverain sur intention, valeurs, budget et risque irréversible; ChatGPT maintient recherche, canon et plans; les exécuteurs restent remplaçables.

## Amorçage

1. Lire `00_GITSPACE_START_HERE.md`.
2. Lire `02_GITSPACE_NOW_DECISIONS_ROADMAP.md`.
3. Construire le `WORKING_SET` : objectif, non-scope, décisions, invariants, risques, preuves, blocages et prochaine action.
4. Charger uniquement les autres sources nécessaires.
5. Ne jamais substituer une conversation à une source canonique.

## Routage

- architecture/mission : `01_GITSPACE_MASTER_CANON.md` + ADR Register;
- état courant : `02_GITSPACE_NOW_DECISIONS_ROADMAP.md`;
- recherche : `03_GITSPACE_RESEARCH_ATLAS.md`;
- planification/handoff : `04_GITSPACE_AGENT_PROTOCOL.md` + plan Phase 00;
- preuves Tasks 1–5 : `docs/phase-00/evidence/`;
- canonical JSON et digests : `crates/gs-canonical-json/`;
- types et validation Evaluation IR : `crates/gs-eval-ir/`;
- stockage adressé par contenu local : `crates/gs-cas/`;
- projection mobile : `raglite/RAGLITE-MANIFEST.yaml`.

## Invariants

- Git reste périphérique au produit.
- Evaluation IR GitSpace reste souverain.
- Une mémoire n’est pas une vérité; une conversation n’est pas un état.
- Un agent ne se déclare jamais lui-même `PROVEN`.
- Test avant code pour tout comportement.
- Chaque tâche est packetisée depuis un commit frais.
- Les écritures persistantes doivent être absentes ou intégralement vérifiables; aucun overwrite silencieux.
- Faux `DONE = 0`.

## État

`P00-TASK-001` à `P00-TASK-005` sont fusionnées et prouvées. Task 5 a ajouté le premier backend `Cas` local immuable : identité SHA-256 GitSpace, layout sharded déterministe, temporaires non adressables, commit hard-link sans remplacement, lecture re-hashée, déduplication et contrôles de corruption, concurrence, interruption, permissions et symlinks. Son merge GitHub signé est `c8b1a1a50040ce757e44eb2867257c14b270dc8a`.

La prochaine unité est `P00-TASK-006` : journal local append-only et enveloppes d’événements reproductibles. La Phase 00 globale reste `PARTIALLY_VERIFIED`.

Le manifeste RAGLite porte l’identité exacte de la paire canon/projection active; toute projection de cet état doit suivre dans une PR séparée.
EOF

cat > 02_GITSPACE_NOW_DECISIONS_ROADMAP.md <<'EOF'
---
doc_id: GS-02
title: GitSpace — Maintenant
authority: CURRENT_STATE_AND_DECISIONS
status: ACTIVE
version: 0.4.5
updated: 2026-08-13
---
# GitSpace — Maintenant

Architecture C et C0 restent `ACCEPTED`.

- P00-TASK-001 : `PROVEN`.
- P00-TASK-002 : `PROVEN`.
- P00-TASK-003 : `PROVEN`.
- P00-TASK-004 : `PROVEN`.
- P00-TASK-005 : `PROVEN`, merge signé `c8b1a1a50040ce757e44eb2867257c14b270dc8a`.
- Evaluation IR v1 : huit schémas Draft 2020-12 et types Rust schema-first fusionnés.
- Canonical JSON + SHA-256 : seam Rust fusionné et verrouillé.
- CAS local v1 : stockage immuable sharded, commit sans remplacement, lecture vérifiée et suite adversariale fusionnés.
- `hermesclaw-ci` : préservée et hors scope.
- Phase 00 : `PARTIALLY_VERIFIED`.
- prochaine tâche : `P00-TASK-006` — journal local append-only et enveloppes d’événements reproductibles.

## Prochaine action exacte

Fusionner cet état post-merge, le projeter séparément dans RAGLite depuis le nouveau SHA de `main`, puis packetiser `P00-TASK-006` depuis le `main` résultant. Task 7 reste bloquée jusqu’au verdict frais Task 6.

```yaml
completed_tasks: [P00-TASK-001, P00-TASK-002, P00-TASK-003, P00-TASK-004, P00-TASK-005]
next_task: P00-TASK-006
phase_status: PARTIALLY_VERIFIED
canonical_task5_merge: c8b1a1a50040ce757e44eb2867257c14b270dc8a
```
EOF

cat > docs/phase-00/evidence/P00-TASK-005-POSTMERGE.md <<'EOF'
---
evidence_id: P00-TASK-005-POSTMERGE
status: POSTMERGE_VERIFIED
source_pr: 17
implementation_head: 7cd421aaebedb10a0752acc5982cf5b9dc654aa8
merge_commit: c8b1a1a50040ce757e44eb2867257c14b270dc8a
merge_tree: 79023989d03f36ff5a2c40e20453cbb5bf784bdf
merge_parent: 2bf674b4bd4f95214c59e9196b9d9ab2f2c324a5
postmerge_run: 31756042061
recorded_at: 2026-08-13
---
# P00-TASK-005 — Post-merge verification

## Signed merge facts

- PR `#17` was squash-merged into canonical `main` as `c8b1a1a50040ce757e44eb2867257c14b270dc8a`.
- GitHub reports `verification.verified=true` with reason `valid`.
- The merge has parent `2bf674b4bd4f95214c59e9196b9d9ab2f2c324a5` and tree `79023989d03f36ff5a2c40e20453cbb5bf784bdf`.
- The merged implementation head had the Task 1, Task 3, Task 4 and Task 5 pull-request workflows successful.
- `hermesclaw-ci` remained outside the packet and unchanged.

## Fresh reproduction from the signed merge

PR `#18` was rooted directly at the signed merge and initially changed only this evidence path. Its Task 5 workflow run `31756042061` concluded `success` with the read-only, locked gate:

```text
cargo metadata --locked --no-deps --format-version 1
cargo test --locked -p gs-cas --all-targets
cargo clippy --locked -p gs-cas --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --locked --workspace --all-targets
clean repository assertion
```

The run therefore reproduced the merged CAS behavior rather than a pre-merge branch approximation.

## Post-merge result

- signed merge identity: PASS;
- canonical parent/tree relationship: PASS;
- locked dependency graph: PASS;
- focused CAS contract/adversarial suite: PASS;
- Clippy and rustfmt: PASS;
- full workspace regression: PASS;
- repository cleanliness: PASS;
- unrelated protected branch preservation: PASS.

`P00-TASK-005` may now be promoted to `PROVEN` in the canonical current-state files. The overall Phase 00 remains `PARTIALLY_VERIFIED`; this verdict does not prove Task 6 or later units.
EOF

rm -f .github/workflows/p00-task-005-state-update.yml
rm -f docs/phase-00/evidence/apply-task5-state.sh

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A
git commit -m "docs: promote Task 5 and advance state to Task 6"
git push origin HEAD:docs/p00-task-005-postmerge
