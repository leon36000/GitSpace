# gs-local-runner

Bounded Phase 00 local runner for GitSpace.

## Security boundary

This crate is **tool-mediated**, not a native-code sandbox. An evaluated agent receives only typed `Read`, `Write` and `Delay` operations interpreted by GitSpace. It does not receive a shell, arbitrary native execution, untrusted WASM, network access or secret handles.

The runner creates a fresh per-run directory containing sibling `workspace/` and `oracle/` directories. Agent operations resolve only below `workspace/`; oracle files are materialized and evaluated internally after operations finish.

Strong process/VM isolation belongs to the later Capability Security + Sandboxes phase.

## Guarantees in Task 8

- strict relative operation, fixture, oracle and check paths;
- component-aware read/write capability prefixes;
- digest-derived run-directory names;
- existing symlinks rejected on traversed workspace paths;
- monotonic cooperative timeout between typed operations;
- ordered attributed effects with CAS digests;
- protected oracle checks after execution;
- deterministic canonical workspace snapshot stored in CAS;
- cleanup after success, policy block, timeout and oracle failure.

## Explicit limits

The authority root is assumed to be owned by GitSpace. A concurrent hostile native process with arbitrary filesystem access is outside this task's contract. Task 8 also makes no claim about containers, seccomp, gVisor, Firecracker, Kata, network isolation, process preemption or distributed execution.

## Verification

```bash
bash crates/gs-local-runner/ci.sh
```
