use gs_eval_ir::{EvalDocument, ValidationReport, validate_json, validate_task_json};
use serde_json::Value;

#[derive(Debug)]
struct Case {
    id: String,
    schema_id: String,
    expected_valid: bool,
    instance: Value,
}

fn cases() -> Vec<Case> {
    let value: Value = serde_json::from_str(include_str!(
        "../../../tests/contracts/eval-ir/shared-corpus.json"
    ))
    .expect("shared corpus must be valid JSON");

    value["cases"]
        .as_array()
        .expect("shared corpus must contain a cases array")
        .iter()
        .map(|case| Case {
            id: case["id"].as_str().expect("case id").to_owned(),
            schema_id: case["schema_id"]
                .as_str()
                .expect("schema id")
                .to_owned(),
            expected_valid: case["expected_valid"]
                .as_bool()
                .expect("expected_valid"),
            instance: case["instance"].clone(),
        })
        .collect()
}

#[test]
fn rust_matches_the_shared_schema_corpus() {
    for case in cases() {
        let result = validate_json(&case.schema_id, &case.instance);
        assert_eq!(
            result.is_ok(),
            case.expected_valid,
            "parity mismatch for {} ({}) — {result:?}",
            case.id,
            case.schema_id,
        );

        if case.expected_valid {
            let document = EvalDocument::try_from_schema_id(&case.schema_id, case.instance)
                .expect("valid case must decode into a typed document");
            assert_eq!(document.schema_id(), case.schema_id);
        }
    }
}

#[test]
fn unknown_schema_is_a_structured_error() {
    let report = validate_json("urn:gitspace:schema:v1:missing", &Value::Null)
        .expect_err("unknown schemas must fail closed");
    assert_eq!(report.issues()[0].path, "");
    assert_eq!(report.issues()[0].code, "schema.unknown");
    assert!(!report.issues()[0].message.is_empty());
}

#[test]
fn task_helper_uses_the_eval_task_schema() {
    let task_case = cases()
        .into_iter()
        .find(|case| case.schema_id.ends_with(":eval-task-spec") && case.expected_valid)
        .expect("corpus must contain a valid EvalTaskSpec");
    validate_task_json(&task_case.instance).expect("valid task case");
}

#[test]
fn validation_report_is_an_error_boundary() {
    fn assert_error<T: std::error::Error + Send + Sync + 'static>() {}
    assert_error::<ValidationReport>();
}
