# gs-event-journal

Local append-only event journal for the GitSpace Phase 00 native vertical slice.

## Authority boundary

- Canonical `RunEvent` JSON bytes are stored in the immutable `gs-cas` store.
- The journal is an ordered append-only index of fixed-width pointers into that CAS.
- Derived `RunProjection` values are disposable and are rebuilt only by replaying verified journal records and CAS objects.
- The filesystem backend is a Phase 00 local pilot, not a distributed log or database replacement.

## Format v1

```text
header: 40 bytes
  magic          8 bytes  GSEJ0001
  run-id digest 32 bytes  SHA-256(run_id UTF-8)

record: 72 bytes
  offset         8 bytes  unsigned big-endian
  event digest  32 bytes  CAS identity of canonical RunEvent JSON
  chain digest  32 bytes  SHA-256 domain-separated chain
```

Journal paths are derived from the run ID digest. Untrusted run IDs are never used directly as filesystem path components.

## Append semantics

1. Verify journal path type and acquire a cooperative exclusive file lock.
2. Validate `run_id`, payload digest and the offline Draft 2020-12 `RunEvent` schema.
3. Canonicalize the complete event and write it to the CAS.
4. Parse and verify the complete existing journal under the lock.
5. Accept an identical retry idempotently, reject a conflicting retry or gap.
6. Append one fixed record and call `sync_all()` before returning success.

A crash after the CAS write but before pointer append may leave an unreferenced CAS object; it cannot make an event visible. Truncated tails and broken chains fail closed and are not repaired automatically.

## Concurrency and durability limits

`std::fs::File::lock()` is used to serialize cooperating GitSpace writers for the full inspect/write/sync sequence. These locks are advisory on some platforms. A process with arbitrary filesystem write access that ignores the lock is outside this Task 6 guarantee.

`sync_all()` attempts to flush file content and metadata. This task does not claim universal power-loss durability across arbitrary filesystems, storage controllers or parent-directory persistence semantics.

## Non-goals

- replication or consensus;
- compaction, retention or garbage collection;
- automatic journal repair;
- persistent snapshots;
- protection from an attacker with arbitrary write access to the store;
- Temporal, Restate, Neon or PostgreSQL integration.

## Verification

```bash
bash crates/gs-event-journal/ci.sh
```

The suite covers round-trip replay, monotonic offsets, idempotent retries, conflicts, gaps, invalid payload digests, orphan CAS objects, deterministic projection rebuild, truncated headers/tails, chain corruption, missing CAS objects, symlink replacement and cooperative concurrent writers.
