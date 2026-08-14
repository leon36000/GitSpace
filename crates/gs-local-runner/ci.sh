#!/usr/bin/env bash
set -euo pipefail

cargo metadata --locked --no-deps --format-version 1 >/dev/null
cargo test --locked -p gs-local-runner --all-targets
cargo test --locked --workspace --all-targets
cargo clippy --locked -p gs-local-runner --all-targets -- -D warnings
cargo fmt --all -- --check

test -z "$(git status --porcelain=v1)"
