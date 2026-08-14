use gs_eval_ir::{
    AgentConfiguration, EvalRunManifest, EvalTaskSpec, EvalVerdict, EvidenceBundle,
    OracleBundle, RunEvent, WorldFixture,
};

#[test]
fn all_eight_document_types_are_public() {
    fn assert_send_sync<T: Send + Sync>() {}
    assert_send_sync::<EvalTaskSpec>();
    assert_send_sync::<WorldFixture>();
    assert_send_sync::<OracleBundle>();
    assert_send_sync::<AgentConfiguration>();
    assert_send_sync::<EvalRunManifest>();
    assert_send_sync::<RunEvent>();
    assert_send_sync::<EvidenceBundle>();
    assert_send_sync::<EvalVerdict>();
}
