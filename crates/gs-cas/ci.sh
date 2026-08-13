#!/usr/bin/env bash
set -euo pipefail

rustc --version | grep -E '^rustc 1\.97\.1 '
cargo --version | grep -E '^cargo 1\.97\.1 '

cargo test -p gs-cas --all-targets
cargo clippy -p gs-cas --all-targets -- -D warnings
cargo fmt --all -- --check
cat Cargo.lock
