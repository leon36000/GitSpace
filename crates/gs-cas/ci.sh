#!/usr/bin/env bash
set -euo pipefail

rustc --version | grep -E '^rustc 1\.97\.1 '
cargo --version | grep -E '^cargo 1\.97\.1 '

cargo metadata --locked --no-deps --format-version 1 > /tmp/gitspace-task5-cargo-metadata.json
cargo test --locked -p gs-cas --all-targets
cargo clippy --locked -p gs-cas --all-targets -- -D warnings
cargo fmt --all -- --check
cargo test --locked --workspace --all-targets
test -z "$(git status --porcelain=v1)"
