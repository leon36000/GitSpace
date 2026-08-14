#!/usr/bin/env bash
set -euo pipefail

if git rev-parse --verify HEAD >/dev/null 2>&1; then
  export GITSPACE_TEST_SOURCE_COMMIT="$(git rev-parse HEAD)"
else
  # Clean archive replays intentionally have no Git metadata. A synthetic
  # valid digest keeps the runtime contract testable without pretending it is
  # repository provenance.
  export GITSPACE_TEST_SOURCE_COMMIT="${GITSPACE_TEST_SOURCE_COMMIT:-0000000000000000000000000000000000000000}"
fi

cargo metadata --locked --no-deps --format-version 1 >/dev/null
cargo test --locked -p gs-foundry-cli --all-targets
cargo test --locked --workspace --all-targets
cargo clippy --locked -p gs-foundry-cli --all-targets -- -D warnings
cargo fmt --all -- --check

test -z "$(git status --porcelain=v1 2>/dev/null || true)"
