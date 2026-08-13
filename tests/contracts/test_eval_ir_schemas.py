from __future__ import annotations

import json
import pathlib
import unittest

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT / "schemas" / "v1"
DRAFT = "https://json-schema.org/draft/2020-12/schema"
DIGEST = "sha256:" + "a" * 64
CAS = "cas://sha256/" + "b" * 64
ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
FILES = {
    "EvalTaskSpec": "eval-task-spec.schema.json",
    "WorldFixture": "world-fixture.schema.json",
    "OracleBundle": "oracle-bundle.schema.json",
    "AgentConfiguration": "agent-configuration.schema.json",
    "EvalRunManifest": "eval-run-manifest.schema.json",
    "RunEvent": "run-event.schema.json",
    "EvidenceBundle": "evidence-bundle.schema.json",
    "EvalVerdict": "eval-verdict.schema.json",
}


def world() -> dict:
    return {"version": 1, "base_artifact_digest": DIGEST, "environment_digest": DIGEST,
            "services": [], "initial_state_digest": DIGEST, "extensions": {"gitspace.test": {}}}


def oracle() -> dict:
    return {"version": 1, "public_checks": ["check://smoke"], "hidden_oracles": ["oracle://hidden"],
            "mutation_set": [], "adversarial_variants": [], "cleanup_oracle": "oracle://cleanup",
            "replay_oracle": "oracle://replay", "extensions": {}}


def agent() -> dict:
    return {"version": 1, "harness": "native", "harness_version": "0.1.0", "model": "test",
            "model_version": "1", "provider": "test", "model_parameters": {},
            "system_instructions_digest": DIGEST, "tools_digest": DIGEST,
            "context_digest": DIGEST, "memory_digest": DIGEST, "extensions": {}}


def task() -> dict:
    return {"id": "GS-TASK-000001", "version": 1, "lane": "L05",
            "origin": {"kind": "native", "source": "GitSpace", "license": "UNKNOWN", "contamination_risk": "low"},
            "intent": {"owner_outcome": "Expected behavior", "explicit_requirements": ["REQ-1"],
                       "latent_requirements": [], "non_goals": [], "allowed_ambiguities": []},
            "world_fixture": world(),
            "authority": {"allowed_actions": ["repository.read"], "forbidden_actions": ["oracle.write"],
                          "scope_boundaries": ["workspace://task"], "required_approvals": []},
            "obligations": {"visible": ["O1"], "protected": ["O2"], "runtime": []},
            "budgets": {"wall_time_seconds": 60, "token_limit": 1000, "cost_limit_usd": 1.0, "tool_calls": 20},
            "evaluation": oracle(),
            "qa": {"author_id": "reviewer://author/1", "independent_reviewer_id": "reviewer://independent/1",
                   "human_solution_digest": DIGEST, "known_exploits": []}, "extensions": {}}


def run() -> dict:
    return {"id": f"GS-RUN-{ULID}", "version": 1, "task_id": "GS-TASK-000001", "task_version": 1,
            "agent": agent(),
            "environment": {"image_digest": DIGEST, "architecture": "x86_64",
                            "dependency_lock_digest": DIGEST, "network_policy_digest": DIGEST},
            "execution": {"seed": 0, "started_at": "2026-08-13T20:30:00Z",
                          "ended_at": "2026-08-13T20:31:00Z", "interruption_schedule": [], "retries": 0},
            "artifacts": {"trace": CAS, "state_before": CAS, "state_after": CAS, "patch": CAS, "evidence_bundle": CAS},
            "extensions": {}}


def event() -> dict:
    return {"version": 1, "run_id": f"GS-RUN-{ULID}", "sequence": 0, "event_type": "RUN_CREATED",
            "occurred_at": "2026-08-13T20:30:00Z", "payload": {"task_id": "GS-TASK-000001"},
            "payload_digest": DIGEST, "extensions": {}}


def evidence() -> dict:
    return {"id": f"GS-EVIDENCE-{ULID}", "version": 1, "run_id": f"GS-RUN-{ULID}",
            "task_id": "GS-TASK-000001", "run_manifest_digest": DIGEST, "environment_digest": DIGEST,
            "commit_sha": "c" * 40, "artifacts": {"trace": CAS}, "extensions": {}}


def verdict() -> dict:
    return {"id": f"GS-VERDICT-{ULID}", "version": 1, "run_id": f"GS-RUN-{ULID}",
            "functional_outcome": "pass", "declared_outcome": "success", "false_done": False,
            "safe_success": True, "scope_respected": True, "authority_respected": True,
            "regression_free": True, "replay_passed": True, "independent_verification_passed": True,
            "obligation_coverage": 1.0, "evidence_coverage": 1.0, "exploit_detected": False,
            "cleanup_passed": True, "task_validity": "valid", "residual_risks": [], "extensions": {}}


EXAMPLES = {"EvalTaskSpec": task, "WorldFixture": world, "OracleBundle": oracle,
            "AgentConfiguration": agent, "EvalRunManifest": run, "RunEvent": event,
            "EvidenceBundle": evidence, "EvalVerdict": verdict}


class EvaluationIRSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schemas = {}
        registry = Registry()
        for name, filename in FILES.items():
            path = SCHEMA_DIR / filename
            if not path.is_file():
                raise AssertionError(f"missing required schema: {filename}")
            schema = json.loads(path.read_text(encoding="utf-8"))
            cls.schemas[name] = schema
            registry = registry.with_resource(schema["$id"], DRAFT202012.create_resource(schema))
        cls.registry = registry

    def validator(self, name: str) -> Draft202012Validator:
        return Draft202012Validator(self.schemas[name], registry=self.registry)

    def assert_invalid(self, name: str, value: dict) -> None:
        with self.assertRaises(ValidationError):
            self.validator(name).validate(value)

    def test_meta_schemas_and_unique_offline_ids(self) -> None:
        ids = set()
        self.assertEqual(len(self.schemas), 8)
        for schema in self.schemas.values():
            self.assertEqual(schema["$schema"], DRAFT)
            self.assertTrue(schema["$id"].startswith("urn:gitspace:schema:v1:"))
            self.assertNotIn(schema["$id"], ids)
            ids.add(schema["$id"])
            try:
                Draft202012Validator.check_schema(schema)
            except SchemaError as exc:
                self.fail(str(exc))

    def test_positive_examples_validate_offline(self) -> None:
        for name, factory in EXAMPLES.items():
            with self.subTest(schema=name):
                self.validator(name).validate(factory())

    def test_structured_core_objects_are_closed(self) -> None:
        def walk(node: object, path: str = "$") -> None:
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIs(node.get("additionalProperties"), False, path)
                for key, value in node.items():
                    walk(value, f"{path}/{key}")
            elif isinstance(node, list):
                for index, value in enumerate(node):
                    walk(value, f"{path}/{index}")
        for schema in self.schemas.values():
            walk(schema)

    def test_invalid_task_id(self) -> None:
        value = task(); value["id"] = "task-1"; self.assert_invalid("EvalTaskSpec", value)

    def test_version_zero(self) -> None:
        value = world(); value["version"] = 0; self.assert_invalid("WorldFixture", value)

    def test_malformed_digest(self) -> None:
        value = agent(); value["context_digest"] = "sha256:abc"; self.assert_invalid("AgentConfiguration", value)

    def test_unknown_core_property(self) -> None:
        value = run(); value["unexpected"] = True; self.assert_invalid("EvalRunManifest", value)

    def test_extensions_must_be_namespaced(self) -> None:
        value = oracle(); value["extensions"] = {"plain": {}}; self.assert_invalid("OracleBundle", value)

    def test_safe_success_requires_authority(self) -> None:
        value = verdict(); value["authority_respected"] = False; self.assert_invalid("EvalVerdict", value)

    def test_false_done_is_not_safe_success(self) -> None:
        value = verdict(); value["false_done"] = True; self.assert_invalid("EvalVerdict", value)

    def test_malformed_cas_uri(self) -> None:
        value = evidence(); value["artifacts"]["trace"] = "cas://sha256/short"; self.assert_invalid("EvidenceBundle", value)


if __name__ == "__main__":
    unittest.main()
