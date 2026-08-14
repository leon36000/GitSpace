use crate::{
    FoundryError, NativeFoundry, ReplayReport, RunReceipt, ScoringInput,
    artifacts::{get_bytes, get_json},
    native::to_verdict_input,
};
use gs_canonical_json::{canonical_bytes, sha256_digest};
use gs_cas::LocalCas;
use gs_eval_ir::{
    EvalRunManifest, EvalVerdict, EvidenceBundle, SchemaName, validate_named_json,
    validate_task_json,
};
use gs_event_journal::{
    EventOffset, EventSource, LocalEventJournal, projection_bytes, rebuild_run_projection,
};
use gs_verdict::issue_verdict;

impl NativeFoundry {
    pub fn replay(&self, receipt: &RunReceipt) -> Result<ReplayReport, FoundryError> {
        validate_receipt_shape(receipt)?;
        if receipt.source_commit != self.source_commit() {
            return Err(FoundryError::InvalidReceipt(
                "receipt source commit does not match the opened Foundry".to_owned(),
            ));
        }
        let cas = LocalCas::open(self.cas_root())?;

        let task_bytes = get_bytes(&cas, &receipt.task_uri)?;
        let task_value: serde_json::Value = serde_json::from_slice(&task_bytes)?;
        validate_task_json(&task_value)?;

        let scoring: ScoringInput = get_json(&cas, &receipt.scoring_uri)?;
        if scoring.scenario != receipt.scenario || scoring.classification != receipt.classification
        {
            return Err(FoundryError::Inconsistency(
                "receipt classification disagrees with persisted scoring input".to_owned(),
            ));
        }

        let verdict_bytes = get_bytes(&cas, &receipt.verdict_uri)?;
        let stored_verdict: EvalVerdict = serde_json::from_slice(&verdict_bytes)?;
        validate_named_json(
            SchemaName::EvalVerdict,
            &serde_json::to_value(&stored_verdict)?,
        )?;
        if stored_verdict.run_id != receipt.run_id {
            return Err(FoundryError::Inconsistency(
                "stored verdict run_id disagrees with receipt".to_owned(),
            ));
        }
        let derived = issue_verdict(to_verdict_input(
            &scoring,
            stored_verdict.id.clone(),
            receipt.run_id.clone(),
        ))?;
        if canonical_bytes(&serde_json::to_value(&derived)?)? != verdict_bytes {
            return Err(FoundryError::Inconsistency(
                "reissued verdict bytes differ from persisted verdict".to_owned(),
            ));
        }

        let evidence_bytes = get_bytes(&cas, &receipt.evidence_uri)?;
        let evidence: EvidenceBundle = serde_json::from_slice(&evidence_bytes)?;
        validate_named_json(
            SchemaName::EvidenceBundle,
            &serde_json::to_value(&evidence)?,
        )?;
        verify_evidence(receipt, &evidence)?;

        let manifest_bytes = get_bytes(&cas, &receipt.manifest_uri)?;
        let manifest: EvalRunManifest = serde_json::from_slice(&manifest_bytes)?;
        validate_named_json(
            SchemaName::EvalRunManifest,
            &serde_json::to_value(&manifest)?,
        )?;
        verify_manifest(receipt, &manifest)?;

        for uri in [
            &receipt.plan_uri,
            &receipt.trace_uri,
            &receipt.state_before_uri,
            &receipt.state_after_uri,
            &receipt.patch_uri,
        ] {
            let _ = get_bytes(&cas, uri)?;
        }

        let journal_root = self
            .cas_root()
            .parent()
            .ok_or_else(|| {
                FoundryError::Inconsistency("CAS root has no Foundry parent".to_owned())
            })?
            .join("journal");
        let journal_path = journal_path(&journal_root, &receipt.run_id);
        if !journal_path.is_file() {
            return Err(FoundryError::InvalidReceipt(format!(
                "journal is missing for run {}",
                receipt.run_id
            )));
        }
        let journal = LocalEventJournal::open(
            &journal_root,
            LocalCas::open(self.cas_root())?,
            receipt.run_id.clone(),
        )?;
        let records = journal.read_from(EventOffset::new(0))?;
        if records.len() != 3
            || records
                .iter()
                .enumerate()
                .any(|(index, record)| record.offset.get() != index as u64)
        {
            return Err(FoundryError::Inconsistency(
                "Task 9 replay requires exactly three contiguous journal events".to_owned(),
            ));
        }
        let expected_types = ["RUN_PREPARED", "RUN_EXECUTED", "VERDICT_ISSUED"];
        for (record, expected) in records.iter().zip(expected_types) {
            if record.event.event_type != expected {
                return Err(FoundryError::Inconsistency(format!(
                    "unexpected journal event type: expected {expected}, observed {}",
                    record.event.event_type
                )));
            }
        }
        let rebuilt_trace = projection_bytes(&rebuild_run_projection(&journal)?)?;
        let stored_trace = get_bytes(&cas, &receipt.trace_uri)?;
        if rebuilt_trace != stored_trace {
            return Err(FoundryError::Inconsistency(
                "rebuilt journal projection differs from persisted trace".to_owned(),
            ));
        }

        Ok(ReplayReport {
            version: 1,
            scenario: receipt.scenario,
            classification: receipt.classification,
            run_id: receipt.run_id.clone(),
            verdict: derived,
            manifest_uri: receipt.manifest_uri.clone(),
            evidence_uri: receipt.evidence_uri.clone(),
            journal_event_count: records.len() as u64,
            replay_verified: true,
            evidence_verified: true,
        })
    }
}

fn validate_receipt_shape(receipt: &RunReceipt) -> Result<(), FoundryError> {
    if receipt.version != 1 || receipt.run_id != format!("GS-RUN-{}", receipt.scenario.ulid()) {
        return Err(FoundryError::InvalidReceipt(
            "receipt version or deterministic run ID is invalid".to_owned(),
        ));
    }
    if !matches!(receipt.source_commit.len(), 40 | 64)
        || !receipt
            .source_commit
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(FoundryError::InvalidReceipt(
            "receipt source commit is invalid".to_owned(),
        ));
    }
    Ok(())
}

fn verify_evidence(receipt: &RunReceipt, evidence: &EvidenceBundle) -> Result<(), FoundryError> {
    if evidence.run_id != receipt.run_id
        || evidence.task_id != "GS-TASK-000009"
        || evidence.commit_sha != receipt.source_commit
    {
        return Err(FoundryError::Inconsistency(
            "EvidenceBundle identity disagrees with receipt".to_owned(),
        ));
    }
    for (name, expected) in [
        ("task", &receipt.task_uri),
        ("plan", &receipt.plan_uri),
        ("scoring", &receipt.scoring_uri),
        ("verdict", &receipt.verdict_uri),
        ("trace", &receipt.trace_uri),
        ("state_before", &receipt.state_before_uri),
        ("state_after", &receipt.state_after_uri),
        ("patch", &receipt.patch_uri),
    ] {
        if evidence.artifacts.get(name) != Some(expected) {
            return Err(FoundryError::Inconsistency(format!(
                "EvidenceBundle artifact {name} disagrees with receipt"
            )));
        }
    }
    Ok(())
}

fn verify_manifest(receipt: &RunReceipt, manifest: &EvalRunManifest) -> Result<(), FoundryError> {
    if manifest.id != receipt.run_id || manifest.task_id != "GS-TASK-000009" {
        return Err(FoundryError::Inconsistency(
            "EvalRunManifest identity disagrees with receipt".to_owned(),
        ));
    }
    let artifacts = &manifest.artifacts;
    for (name, actual, expected) in [
        ("trace", &artifacts.trace, &receipt.trace_uri),
        (
            "state_before",
            &artifacts.state_before,
            &receipt.state_before_uri,
        ),
        (
            "state_after",
            &artifacts.state_after,
            &receipt.state_after_uri,
        ),
        ("patch", &artifacts.patch, &receipt.patch_uri),
        (
            "evidence_bundle",
            &artifacts.evidence_bundle,
            &receipt.evidence_uri,
        ),
    ] {
        if actual != expected {
            return Err(FoundryError::Inconsistency(format!(
                "EvalRunManifest artifact {name} disagrees with receipt"
            )));
        }
    }
    Ok(())
}

fn journal_path(root: &std::path::Path, run_id: &str) -> std::path::PathBuf {
    let digest = sha256_digest(run_id.as_bytes()).to_string();
    let hex = digest.strip_prefix("sha256:").expect("digest prefix");
    root.join("runs").join(format!("{hex}.gsej"))
}
