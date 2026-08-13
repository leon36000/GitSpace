---
evidence_id: GS-EVIDENCE-P00-TASK-001-QUALIFICATION
status: PARTIALLY_VERIFIED
checked_at: 2026-08-13
---

# P00-TASK-001 — Toolchain qualification

## Official evidence

### Rust 1.97.1

Source: `https://blog.rust-lang.org/2026/07/16/Rust-1.97.1/`

Classification: `FACT_OFFICIAL`.

Observation: the Rust Release Team published 1.97.1 on 2026-07-16 as a point release. It is selected instead of 1.97.0 because the point release includes a compiler correctness fix.

### Python 3.12.13

Source: `https://www.python.org/downloads/release/python-31213/`

Classification: `FACT_OFFICIAL`.

Observation: 3.12.13 was published on 2026-03-03 as a security release. The 3.12 series is security-only and the official release is source-only. Runtime provisioning must therefore record where its binary or build came from.

### Inspect Evals

Source: `https://github.com/UKGovernmentBEIS/inspect_evals`

Classification: `FACT_OFFICIAL`.

Observation: current Inspect Evals requires at least Python 3.11; its compatibility guidance continues to prefer 3.11/3.12 while newer interpreter series have less coverage. The exact Inspect version is not adopted in Task 1.

### Harbor

Source: `https://github.com/harbor-framework/harbor/blob/main/pyproject.toml`

Classification: `FACT_OFFICIAL`.

Observation: Harbor currently declares `requires-python = ">=3.12"`. The branch is moving; the actual adapter task must pin a release or commit.

### uv 0.12.0

Source: `https://github.com/astral-sh/uv/releases/tag/0.12.0`

Classification: `FACT_OFFICIAL`.

Observation: 0.12.0 was released on 2026-07-28. Task 1 pins it explicitly and verifies the runtime version.

## Decision

`PILOT_ACCEPTED` for Task 1:

```text
Rust   1.97.1
Python 3.12.13
uv     0.12.0
```

This does not promote Inspect or Harbor into canonical dependencies. It only establishes a conservative Python series shared by the planned adapter ecosystem.

## TDD evidence

RED observed locally before manifest creation:

```text
FAIL: test_exact_toolchain_contract
missing required file: toolchains.lock.json
```

GREEN after minimal manifests:

```text
Ran 2 tests
OK
```

## Local environment limitation

```text
rustc: not installed
cargo: not installed
Python: 3.13.5
uv: 0.10.0
```

Therefore local runtime compatibility is not claimed. GitHub Actions is the fresh runtime verifier for this task.

## Open proof obligations

- CI exact Python version PASS;
- CI exact uv version PASS;
- CI exact rustc/cargo version PASS;
- `cargo metadata` PASS;
- repository clean after verification;
- independent review of changed files and CI logs.
