use gs_canonical_json::Digest;

#[test]
fn digest_can_be_reconstructed_from_exact_bytes() {
    let bytes = [0x5a_u8; 32];
    let digest = Digest::from_bytes(bytes);

    assert_eq!(digest.as_bytes(), &bytes);
    assert_eq!(digest.to_string(), format!("sha256:{}", "5a".repeat(32)));
}
