use crate::model::NativeScenario;
use gs_canonical_json::sha256_digest;

const IDENTITY_DOMAIN: &[u8] = b"gitspace:p00-task-009:identity:v1";
const CROCKFORD_BASE32: &[u8; 32] = b"0123456789ABCDEFGHJKMNPQRSTVWXYZ";

impl NativeScenario {
    pub(crate) fn identity_suffix(self, source_commit: &str) -> String {
        let mut material =
            Vec::with_capacity(IDENTITY_DOMAIN.len() + source_commit.len() + self.slug().len() + 2);
        material.extend_from_slice(IDENTITY_DOMAIN);
        material.push(0);
        material.extend_from_slice(source_commit.as_bytes());
        material.push(0);
        material.extend_from_slice(self.slug().as_bytes());

        encode_crockford_128(sha256_digest(&material).as_bytes())
    }
}

fn encode_crockford_128(digest: &[u8; 32]) -> String {
    let mut prefix = [0_u8; 16];
    prefix.copy_from_slice(&digest[..16]);
    let mut value = u128::from_be_bytes(prefix);
    let mut encoded = [b'0'; 26];

    for slot in encoded.iter_mut().rev() {
        *slot = CROCKFORD_BASE32[(value & 0x1f) as usize];
        value >>= 5;
    }

    String::from_utf8(encoded.to_vec()).expect("Crockford alphabet is valid UTF-8")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn suffix_is_schema_compatible_and_domain_separated() {
        let commit_a = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
        let commit_b = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
        let pass_a = NativeScenario::Pass.identity_suffix(commit_a);
        let pass_b = NativeScenario::Pass.identity_suffix(commit_b);
        let fail_a = NativeScenario::Fail.identity_suffix(commit_a);

        assert_eq!(pass_a.len(), 26);
        assert!(pass_a.bytes().all(|byte| CROCKFORD_BASE32.contains(&byte)));
        assert_ne!(pass_a, pass_b);
        assert_ne!(pass_a, fail_a);
        assert_eq!(
            NativeScenario::Pass.identity_suffix(commit_a),
            NativeScenario::Pass.identity_suffix(commit_a)
        );
    }
}
