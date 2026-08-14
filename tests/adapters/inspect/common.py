from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from gs_eval_adapters import AdapterRequest

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
INSPECT_VERSION = "0.3.258"
INSPECT_COMMIT = "e72c73f8a514c53ddf55da180e4bedaf8f0362b4"
INSPECT_WHEEL_SHA256 = "638da28a5f3a021152481c5aa22d440a2855e462804dce2d49a44e6e47be16a4"
MODEL_OUTPUT = "Default output from mockllm/model"


class MemoryCas:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def publish(self, value: bytes) -> str:
        if type(value) is not bytes:
            raise TypeError("MemoryCas accepts exact bytes")
        digest = hashlib.sha256(value).hexdigest()
        uri = f"cas://sha256/{digest}"
        self.objects[uri] = value
        return uri

    def read(self, uri: str) -> bytes:
        return self.objects[uri]


def task11_request() -> AdapterRequest:
    task = {
        "id": "GS-TASK-000011",
        "version": 1,
        "lane": "L01",
        "origin": {
            "kind": "imported",
            "source": "inspect-ai@0.3.258",
            "license": "MIT",
            "contamination_risk": "low",
        },
        "intent": {
            "owner_outcome": "Return exactly the deterministic mock output.",
            "explicit_requirements": [
                "one Inspect sample",
                "generate solver",
                "exact match scorer",
                "replay without Inspect",
            ],
            "latent_requirements": [],
            "non_goals": ["external model provider", "network use"],
            "allowed_ambiguities": [],
        },
        "world_fixture": {
            "version": 1,
            "base_artifact_digest": DIGEST_A,
            "environment_digest": DIGEST_B,
            "services": [],
            "initial_state_digest": DIGEST_A,
            "extensions": {},
        },
        "authority": {
            "allowed_actions": ["adapter.invoke", "artifact.publish"],
            "forbidden_actions": ["network.use", "external_model.invoke"],
            "scope_boundaries": ["adapter://inspect-ai/controlled"],
            "required_approvals": [],
        },
        "obligations": {
            "visible": ["model output equals target"],
            "protected": ["independent replay agrees"],
            "runtime": ["no network", "artifacts content-addressed"],
        },
        "budgets": {
            "wall_time_seconds": 30,
            "token_limit": 1000,
            "cost_limit_usd": 0.0,
            "tool_calls": 4,
        },
        "evaluation": {
            "version": 1,
            "public_checks": ["check://inspect/exact-match"],
            "hidden_oracles": ["oracle://inspect/replay"],
            "mutation_set": ["mutation://inspect/output"],
            "adversarial_variants": ["variant://inspect/import-blocked"],
            "cleanup_oracle": "oracle://inspect/cleanup",
            "replay_oracle": "oracle://inspect/replay",
            "extensions": {},
        },
        "qa": {
            "author_id": "reviewer://task11/author",
            "independent_reviewer_id": "reviewer://task11/verifier",
            "human_solution_digest": DIGEST_A,
            "known_exploits": [],
        },
        "extensions": {
            "gitspace.inspect": {
                "version": INSPECT_VERSION,
                "commit": INSPECT_COMMIT,
            }
        },
    }
    agent = {
        "version": 1,
        "harness": "inspect-ai",
        "harness_version": INSPECT_VERSION,
        "model": "mockllm/model",
        "model_version": "builtin",
        "provider": "inspect-ai",
        "model_parameters": {},
        "system_instructions_digest": DIGEST_A,
        "tools_digest": DIGEST_B,
        "context_digest": DIGEST_A,
        "memory_digest": DIGEST_B,
        "extensions": {
            "gitspace.inspect": {
                "source_commit": INSPECT_COMMIT,
                "network": "forbidden",
            }
        },
    }
    return AdapterRequest(
        task=deepcopy(task),
        agent=deepcopy(agent),
        seed=11,
        extensions={"gitspace.inspect": {"qualification": INSPECT_VERSION}},
    )


def load_static_projection() -> dict[str, object]:
    path = Path(__file__).with_name("fixtures") / "inspect-log-projection-0.3.258.json"
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
