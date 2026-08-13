use gs_canonical_json::{canonical_bytes, canonical_digest, sha256_digest, CanonicalJsonError};
use serde_json::{Number, Value};

fn parse(input: &str) -> Value {
    serde_json::from_str(input).expect("valid JSON fixture")
}

#[test]
fn object_key_order_does_not_change_canonical_bytes() {
    let left = parse(r#"{"b":2,"a":1}"#);
    let right = parse(r#"{"a":1,"b":2}"#);
    let expected = br#"{"a":1,"b":2}"#.to_vec();
    assert_eq!(canonical_bytes(&left).unwrap(), expected);
    assert_eq!(canonical_bytes(&right).unwrap(), expected);
}

#[test]
fn sorting_is_recursive() {
    let value = parse(r#"{"z":{"b":2,"a":1},"a":[{"d":4,"c":3}]}"#);
    assert_eq!(
        canonical_bytes(&value).unwrap(),
        br#"{"a":[{"c":3,"d":4}],"z":{"a":1,"b":2}}"#.to_vec()
    );
}

#[test]
fn rfc_numbers_use_jcs_format() {
    let value = parse("[333333333.33333329,1E30,4.50,2e-3,0.000000000000000000000000001]");
    assert_eq!(
        canonical_bytes(&value).unwrap(),
        b"[333333333.3333333,1e+30,4.5,0.002,1e-27]".to_vec()
    );
}

#[test]
fn keys_are_sorted_by_utf16_code_units() {
    let value = parse("{\"\\uE000\":1,\"\\uD800\\uDC00\":2}");
    assert_eq!(canonical_bytes(&value).unwrap(), "{\"𐀀\":2,\"\":1}".as_bytes());
}

#[test]
fn sha256_digest_uses_lowercase_prefixed_encoding() {
    let digest = sha256_digest(br#"{"a":1,"b":2}"#);
    assert_eq!(
        digest.to_string(),
        "sha256:43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777"
    );
}

#[test]
fn canonical_digest_hashes_canonical_bytes() {
    let value = parse(r#"{"b":2,"a":1}"#);
    assert_eq!(
        canonical_digest(&value).unwrap(),
        sha256_digest(&canonical_bytes(&value).unwrap())
    );
}

#[test]
fn negative_zero_is_rejected() {
    let number = Number::from_f64(-0.0).expect("representable f64");
    let error = canonical_bytes(&Value::Number(number)).unwrap_err();
    assert_eq!(error, CanonicalJsonError::NegativeZero);
}
