use gs_eval_ir::{SchemaName, parse_named_json, validate_named_json, validate_task_json};
use serde_json::{Number, Value};
use std::collections::{BTreeMap, BTreeSet};

const CORPUS: &str = include_str!("../../../tests/contracts/eval_ir_parity.json");

#[derive(Debug)]
struct Case {
    id: String,
    schema: SchemaName,
    valid: bool,
    value: Value,
}

fn decode_pointer_token(token: &str) -> String {
    token.replace("~1", "/").replace("~0", "~")
}

fn replace_pointer(document: &mut Value, pointer: &str, value: Value) {
    assert!(
        pointer.starts_with('/') && pointer.len() > 1,
        "mutation path must be a non-root JSON Pointer: {pointer:?}"
    );

    let tokens = pointer[1..]
        .split('/')
        .map(decode_pointer_token)
        .collect::<Vec<_>>();

    let mut current = document;
    for token in &tokens[..tokens.len() - 1] {
        current = match current {
            Value::Object(object) => object
                .get_mut(token)
                .unwrap_or_else(|| panic!("mutation path does not exist: {pointer:?}")),
            Value::Array(array) => &mut array[token.parse::<usize>().expect("array index")],
            _ => panic!("mutation path crosses a scalar: {pointer:?}"),
        };
    }

    let final_token = &tokens[tokens.len() - 1];
    match current {
        Value::Object(object) => {
            object.insert(final_token.clone(), value);
        }
        Value::Array(array) => {
            array[final_token.parse::<usize>().expect("array index")] = value;
        }
        _ => panic!("mutation target is a scalar: {pointer:?}"),
    }
}

fn materialize_cases() -> Vec<Case> {
    let corpus: Value = serde_json::from_str(CORPUS).expect("valid parity corpus");
    let raw_cases = corpus["cases"].as_array().expect("cases array");
    let mut materialized = BTreeMap::<String, Value>::new();
    let mut cases = Vec::with_capacity(raw_cases.len());

    for raw_case in raw_cases {
        let case_id = raw_case["id"].as_str().expect("case id").to_owned();
        assert!(
            !materialized.contains_key(&case_id),
            "duplicate parity case id: {case_id}"
        );

        let schema = SchemaName::try_from(raw_case["schema"].as_str().expect("schema name"))
            .expect("known schema name");
        let valid = raw_case["valid"].as_bool().expect("valid boolean");

        let value = match (raw_case.get("value"), raw_case.get("mutate")) {
            (Some(value), None) => value.clone(),
            (None, Some(mutation)) => {
                let source_id = mutation["from"].as_str().expect("mutation source");
                let mut value = materialized
                    .get(source_id)
                    .unwrap_or_else(|| {
                        panic!("{case_id}: mutation source must be an earlier case: {source_id}")
                    })
                    .clone();
                replace_pointer(
                    &mut value,
                    mutation["path"].as_str().expect("mutation path"),
                    mutation["value"].clone(),
                );
                value
            }
            _ => panic!("{case_id}: exactly one of value or mutate is required"),
        };

        materialized.insert(case_id.clone(), value.clone());
        cases.push(Case {
            id: case_id,
            schema,
            valid,
            value,
        });
    }

    cases
}

#[test]
fn shared_corpus_matches_rust_schema_and_typed_decode() {
    let cases = materialize_cases();
    let mut covered = BTreeSet::new();

    for case in cases {
        covered.insert(case.schema);

        let validation = validate_named_json(case.schema, &case.value);
        assert_eq!(
            validation.is_ok(),
            case.valid,
            "{}: expected valid={}, got {:?}",
            case.id,
            case.valid,
            validation
        );

        if case.valid {
            let parsed = parse_named_json(case.schema, &case.value);
            assert!(
                parsed.is_ok(),
                "{}: schema-valid value failed typed decode: {:?}",
                case.id,
                parsed
            );
        }
    }

    assert_eq!(
        covered.len(),
        8,
        "shared corpus must cover all eight schemas"
    );
}

#[test]
fn required_task_seam_returns_stable_structured_issue_fields() {
    let invalid = materialize_cases()
        .into_iter()
        .find(|case| case.id == "task-invalid-id")
        .expect("task-invalid-id case");

    let report = validate_task_json(&invalid.value).expect_err("invalid task must fail");
    let issue = report
        .issues()
        .iter()
        .find(|issue| issue.path == "/id")
        .expect("pattern issue at /id");

    assert_eq!(issue.code, "schema.pattern");
    assert!(!issue.message.is_empty());
}

#[test]
fn schema_valid_maximum_json_integer_seed_decodes() {
    let mut run = materialize_cases()
        .into_iter()
        .find(|case| case.id == "run-valid")
        .expect("run-valid case");
    replace_pointer(
        &mut run.value,
        "/execution/seed",
        Value::Number(Number::from(u64::MAX)),
    );

    validate_named_json(SchemaName::EvalRunManifest, &run.value)
        .expect("u64::MAX is a schema-valid JSON integer seed");
    let parsed = parse_named_json(SchemaName::EvalRunManifest, &run.value);
    assert!(
        parsed.is_ok(),
        "schema-valid maximum JSON integer seed failed typed decode: {parsed:?}"
    );
}
