pub fn source_commit() -> String {
    std::env::var("GITSPACE_TEST_SOURCE_COMMIT").unwrap_or_else(|_| {
        // Direct cargo invocations and clean archives may not have Git metadata.
        // This valid synthetic digest exercises the contract without claiming
        // repository provenance; ci.sh always overrides it with git rev-parse HEAD.
        "0000000000000000000000000000000000000000".to_owned()
    })
}
