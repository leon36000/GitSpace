import copy
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
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


def cases():
    registry = Registry()
    schemas = {}
    for name, filename in FILES.items():
        schema = json.loads((ROOT / "schemas/v1" / filename).read_text())
        schemas[name] = schema
        registry = registry.with_resource(schema["$id"], DRAFT202012.create_resource(schema))

    raw_cases = json.loads((ROOT / "tests/contracts/eval_ir_parity.json").read_text())["cases"]
    values = {}
    result = []
    for raw in raw_cases:
        if "value" in raw:
            value = copy.deepcopy(raw["value"])
        else:
            mutation = raw["mutate"]
            value = copy.deepcopy(values[mutation["from"]])
            tokens = [part.replace("~1", "/").replace("~0", "~") for part in mutation["path"][1:].split("/")]
            target = value
            for token in tokens[:-1]:
                target = target[int(token)] if isinstance(target, list) else target[token]
            if isinstance(target, list):
                target[int(tokens[-1])] = copy.deepcopy(mutation["value"])
            else:
                target[tokens[-1]] = copy.deepcopy(mutation["value"])
        values[raw["id"]] = value
        result.append((raw, value))
    return schemas, registry, result


class ParityTests(unittest.TestCase):
    def test_python_matches_shared_corpus(self):
        schemas, registry, materialized = cases()
        self.assertEqual(set(FILES), {raw["schema"] for raw, _ in materialized})
        self.assertEqual(len(materialized), len({raw["id"] for raw, _ in materialized}))
        self.assertEqual({True, False}, {raw["valid"] for raw, _ in materialized})
        mismatches = []
        for raw, value in materialized:
            actual = Draft202012Validator(schemas[raw["schema"]], registry=registry).is_valid(value)
            if actual != raw["valid"]:
                mismatches.append((raw["id"], raw["valid"], actual))
        self.assertEqual([], mismatches)


if __name__ == "__main__":
    unittest.main()
