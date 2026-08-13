from __future__ import annotations

import copy
import json
import pathlib
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "v1"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
DIGEST = "sha256:" + "a" * 64
CAS_URI = "cas://sha256/" + "b" * 64
ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"

SCHEMAS = {
    "EvalTaskSpec": "eval-task-spec.schema.json",
    "WorldFixture": "world-fixture.schema.json",
    "OracleBundle": "oracle-bundle.schema.json",
    "AgentConfiguration": "agent-configuration.schema.json",
    "EvalRunManifest": "eval-run-manifest.schema.json",
    "RunEvent": "run-event.schema.json",
    "EvidenceBundle": "evidence-bundle.schema.json",
    "EvalVerdict": "eval-verdict.schema.json",
}


def world_fixture() -> dict:
    return {
        "version": 1,
        "base_artifact_digest": DIGEST,
        "environment_digest": DIGEST,
        "services": [],
        "initial_state_digest": DIGEST,
        "extensions": {"gitspace.test": {"enabled": True}},
    }


def oracle_bundle() -> dict:
    return {
        "version": 1,
        "public_checks": ["check://public/smoke"],
        "hidden_oracles": ["oracle://hidden/main"],
        "mutation_set": ["mutation://baseline"],
        "adversarial_variants": ["attack://baseline"],
        "cleanup_oracle": "oracle://cleanup/default",
        "replay_oracle": "oracle://replay/default",
        "extensions": {},
    }


def agent_configuration() -> dict:
    return {
        "version": 1,
        "harness": "native",
        "harness_version": "0.1.0",
        "model": "test-model",
        "model_version": "2026-08-13",
        "provider": "test-provider",
        "model_parameters": {"temperature": 0},
        "system_instructions_digest": DIGEST,
        "tools_digest": DIGEST,
        "context_digest": DIGEST,
        "memory_digest": DIGEST,
        "extensions": {},
    }


def eval_task_spec() -> dict:
    return {
        "id": "GS-TASK-000001",
        "version": 1,
        "lane": "L05",
        "origin": {
            "kind": "native",
            "source": "GitSpace",
            "license": "UNKNOWN",
            "contamination_risk": "low",
        },
        "intent": {
            "owner_outcome": "Return the expected behavior.",
            "explicit_requirements": ["REQ-1"],
            "latent_requirements": [],
            "non_goals": [],
            "allowed_ambiguities": [],
        },
        "world_fixture": world_fixture(),
        "authority": {
            "allowed_actions": ["repository.read"],
            "forbidden_actions": ["oracle.write"],
            "scope_boundaries": ["workspace://task"],
            "required_approvals": [],
        },
        "obligations": {
            "visible": ["OBL-VISIBLE-1"],
            "protected": ["OBL-PROTECTED-1"],
            "runtime": [],
        },
        "budgets": {
            "wall_time_seconds": 60,
            "token_limit": 1000,
            "cost_limit_usd": 1.0,
            "tool_calls": 20,
        },
        "evaluation": oracle_bundle(),
        "qa": {
            "author_id": "reviewer://author/1",
            "independent_reviewer_id": "reviewer://independent/1",
            "human_solution_digest": DIGEST,
            "known_exploits": [],
        },
        "extensions": {},
    }


def eval_run_manifest() -> dict:
    return {
        "id": f"GS-RUN-{ULID}",
        "version": 1,
        "task_id": "GS-TASK-000001",
        "task_version": 1,
        "agent": agent_configuration(),
        "environment": {
            "image_digest": DIGEST,
            "architecture": "x86_64",
            "dependency_lock_digest": DIGEST,
            "network_policy_digest": DIGEST,
        },
        "execution": {
            "seed": 0,
            "started_at": "2026-08-13T20:30:00Z",
            "ended_at": "2026-08-13T20:31:00Z",
            "interruption_schedule": [],
            "retries": 0,
        },
        "artifacts": {
            "trace": CAS_URI,
            "state_before": CAS_URI,
            "state_after": CAS_URI,
            "patch": CAS_URI,
            "evidence_bundle": CAS_URI,
        },
        "extensions": {},
    }


def run_event() -> dict:
    return {
        "version": 1,
        "run_id": f"GS-RUN-{ULID}",
        "sequence": 0,
        "event_type": "RUN_CREATED",
        "occurred_at": "2026-08-13T20:30:00Z",
        "payload": {"task_id": "GS-TASK-000001"},
        "payload_digest": DIGEST,
        "extensions": {},
    }


def evidence_bundle() -> dict:
    return {
        "id": f"GS-EVIDENCE-{ULID}",
        "version": 1,
        "run_id": f"GS-RUN-{ULID}",
        "task_id": "GS-TASK-000001",
        "run_manifest_digest": DIGEST,
        "environment_digest": DIGEST,
        "commit_sha": "c" * 40,
        "artifacts": {"trace": CAS_URI, "stdout": CAS_URI},
        "extensions": {},
    }


def eval_verdict() -> dict:
    return {
        "id": f"GS-VERDICT-{ULID}",
        "version": 1,
        "run_id": f"GS-RUN-{ULID}",
        "functional_outcome": "pass",
        "declared_outcome": "success",
        "false_done": False,
        "safe_success": True,
        "scope_respected": True,
        "authority_respected": True,
        "regression_free": True,
        "replay_passed": True,
        "independent_verification_passed": True,
        "obligation_coverage": 1.0,
        "evidence_coverage": 1.0,
        "exploit_detected": False,
        "cleanup_passed": True,
        "task_validity": "valid",
        "residual_risks": [],
        "extensions": {},
    }


VALID_INSTANCES = {
    "EvalTaskSpec": eval_task_spec,
    "WorldFixture": world_fixture,
    "OracleBundle": oracle_bundle,
    "AgentConfiguration": agent_configuration,
    "EvalRunManifest": eval_run_manifest,
    "RunEvent": run_event,
    "EvidenceBundle": evidence_bundle,
    "EvalVerdict": eval_verdict,
}


class EvaluationIRSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas: dict[str, dict] = {}
        for logical_name, filename in SCHEMAS.items():
            path = SCHEMA_DIR / filename
            if not path.is_file():
                raise AssertionError(f"missing required schema: {filename}")
            cls.schemas[logical_name] = json.loads(path.read_text(encoding="utf-8"))

    def validator(self, logical_name: str) -> Draft202012Validator:
        return Draft202012Validator(self.schemas[logical_name])

    def assert_invalid(self, logical_name: str, instance: dict) -> None:
        with self.assertRaises(ValidationError):
            self.validator(logical_name).validate(instance)

    def test_all_eight_schemas_are_valid_draft_2020_12(self) -> None:
        self.assertEqual(set(self.schemas), set(SCHEMAS))
        ids = set()
        for schema in self.schemas.values():
            self.assertEqual(schema["$schema"], DRAFT)
            self.assertNotIn(schema["$id"], ids)
            ids.add(schema["$id"])
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError as exc:
                self.fail(str(exc))

    def test_all_positive_examples_validate(self) -> None:
        for logical_name, factory in VALID_INSTANCES.items():
            with self.subTest(schema=logical_name):
                self.validator(logical_name).validate(factory())

    def test_structured_core_objects_are_closed(self) -> None:
        def walk(node: object, path: str = "$") -> None:
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIs(
                        node.get("additionalProperties"),
                        False,
                        f"structured object must be closed at {path}",
                    )
                for key, value in node.items():
                    walk(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}/{index}")

        for logical_name, schema in self.schemas.items():
            with self.subTest(schema=logical_name):
                walk(schema)

    def test_invalid_id_is_rejected(self) -> None:
        instance = eval_task_spec()
        instance["id"] = "task-1"
        self.assert_invalid("EvalTaskSpec", instance)

    def test_version_zero_is_rejected(self) -> None:
        instance = world_fixture()
        instance["version"] = 0
        self.assert_invalid("WorldFixture", instance)

    def test_malformed_digest_is_rejected(self) -> None:
        instance = agent_configuration()
        instance["context_digest"] = "sha256:abc"
        self.assert_invalid("AgentConfiguration", instance)

    def test_unknown_core_property_is_rejected(self) -> None:
        instance = eval_run_manifest()
        instance["unexpected"] = True
        self.assert_invalid("EvalRunManifest", instance)

    def test_extensions_must_be_namespaced(self) -> None:
        instance = oracle_bundle()
        instance["extensions"] = {"plain": {"enabled": True}}
        self.assert_invalid("OracleBundle", instance)

    def test_contradictory_safe_success_is_rejected(self) -> None:
        instance = eval_verdict()
        instance["authority_respected"] = False
        self.assert_invalid("EvalVerdict", instance)

    def test_false_done_cannot_be_safe_success(self) -> None:
        instance = eval_verdict()
        instance["false_done"] = True
        self.assert_invalid("EvalVerdict", instance)

    def test_malformed_cas_uri_is_rejected(self) -> None:
        instance = evidence_bundle()
        instance["artifacts"]["trace"] = "cas://sha256/short"
        self.assert_invalid("EvidenceBundle", instance)


if __name__ == "__main__":
    unittest.main()
