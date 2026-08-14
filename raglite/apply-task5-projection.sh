#!/usr/bin/env bash
set -euo pipefail

source_commit=$(git rev-parse HEAD)
source_tree=$(git rev-parse "${source_commit}^{tree}")
files=(
  00_GITSPACE_START_HERE.md
  01_GITSPACE_MASTER_CANON.md
  02_GITSPACE_NOW_DECISIONS_ROADMAP.md
  03_GITSPACE_RESEARCH_ATLAS.md
  04_GITSPACE_AGENT_PROTOCOL.md
)

mkdir -p raglite/mobile
for file in "${files[@]}"; do
  cp -- "$file" "raglite/mobile/$file"
  cmp --silent "$file" "raglite/mobile/$file"
done

blob_00=$(git rev-parse "$source_commit:00_GITSPACE_START_HERE.md")
blob_01=$(git rev-parse "$source_commit:01_GITSPACE_MASTER_CANON.md")
blob_02=$(git rev-parse "$source_commit:02_GITSPACE_NOW_DECISIONS_ROADMAP.md")
blob_03=$(git rev-parse "$source_commit:03_GITSPACE_RESEARCH_ATLAS.md")
blob_04=$(git rev-parse "$source_commit:04_GITSPACE_AGENT_PROTOCOL.md")

cat > raglite/RAGLITE-MANIFEST.yaml <<EOF
manifest_version: 0.4.5
source_commit: $source_commit
source_tree: $source_tree
projection:
  00_GITSPACE_START_HERE.md: $blob_00
  01_GITSPACE_MASTER_CANON.md: $blob_01
  02_GITSPACE_NOW_DECISIONS_ROADMAP.md: $blob_02
  03_GITSPACE_RESEARCH_ATLAS.md: $blob_03
  04_GITSPACE_AGENT_PROTOCOL.md: $blob_04
EOF

for file in "${files[@]}"; do
  source_blob=$(git hash-object "$file")
  projected_blob=$(git hash-object "raglite/mobile/$file")
  test "$source_blob" = "$projected_blob"
done

grep -Fx "source_commit: $source_commit" raglite/RAGLITE-MANIFEST.yaml
grep -Fx "source_tree: $source_tree" raglite/RAGLITE-MANIFEST.yaml

rm -f .github/workflows/p00-task-005-raglite-update.yml
rm -f raglite/apply-task5-projection.sh

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git add -A
git commit -m "docs: project proven Task 5 state into RAGLite"
git push origin HEAD:docs/p00-task-005-raglite
