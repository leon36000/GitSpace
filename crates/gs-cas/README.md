# gs-cas — GitSpace local immutable CAS

`gs-cas` is the Phase 00 filesystem backend for GitSpace's content-addressed storage seam. It stores complete byte strings under the SHA-256 identity produced by `gs-canonical-json`; Git object identifiers and caller-provided paths are never used as object identity.

## Public seam

```rust
pub trait Cas {
    fn put(&self, bytes: &[u8]) -> Result<Digest, CasError>;
    fn get(&self, digest: &Digest) -> Result<Vec<u8>, CasError>;
}
```

`LocalCas::open(root)` creates or validates this v1 layout:

```text
<root>/objects/sha256/<first-two-hex>/<remaining-sixty-two-hex>
<root>/tmp/<unaddressed-writer-temporaries>
```

Object paths are derived only from the 32 digest bytes. `get` opens a regular file, checks that the opened inode is the one inspected at the object path on Unix, reads all bytes and recomputes SHA-256 before returning them.

## Commit protocol

`put` implements an absent-or-complete, no-replace protocol on a trusted local filesystem:

1. compute the GitSpace SHA-256 digest;
2. verify and reuse an existing object when present;
3. create a unique `create_new` temporary file under `<root>/tmp`;
4. write all bytes, flush and `sync_all` the temporary file;
5. make the temporary inode read-only where supported;
6. create a same-filesystem hard link at the final object path;
7. when another writer won the race, verify the winner instead of replacing it;
8. remove the owned temporary name and sync the affected directories;
9. read and hash the committed object again before reporting success.

A corrupted existing target is preserved as negative evidence and is never healed or overwritten. Distinct bytes resolving to the same digest surface `DigestCollision`.

## Qualified boundary

The implementation is qualified by CI on Ubuntu 24.04 with Rust 1.97.1. It assumes a trusted store root and filesystem support for same-filesystem hard links and directory syncing. It does not claim distributed coordination, remote storage, garbage collection, streaming, chunking, compression, encryption or complete crash-consistency across every filesystem and operating system.

Some I/O failures can be reported after the object link already exists, for example a later directory sync failure. Retrying the same `put` is safe because an existing target is verified and never replaced. Stale foreign files under `tmp` remain non-addressable and do not block later writes; lifecycle cleanup beyond owned temporaries belongs to a later maintenance policy.
