from __future__ import annotations

from copy import deepcopy

DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64
IMPLEMENTATION_DIGEST = "sha256:" + "c" * 64
CAS_URI = "cas://sha256/" + "d" * 64


def valid_world_fixture() -> dict[str, object]:
    return {
        "version": 1,
        "base_artifact_digest": DIGEST_A,
        "environment_digest": DIGEST_B,
        "services": [],
        "initial_state_digest": DIGEST_A,
        "extensions": {},
    }


def valid_oracle_bundle() -> dict[str, object]:
    return {
        "version": 1,
        "public_checks": ["check://adapter-contract"],
        "hidden_oracles": ["oracle://adapter-hidden"],
        "mutation_set": [],
        "adversarial_variants": [],
        "cleanup_oracle": "oracle://cleanup",
        "replay_oracle": "oracle://replay",
        "extensions": {},
    }


def valid_task() -> dict[str, object]:
    return {
        "id": "GS-TASK-000010",
        "version": 1,
        "lane": "L00",
        "origin": {
            "kind": "native",
            "source": "GitSpace",
            "license": "UNKNOWN",
            "contamination_risk": "low",
        },
        "intent": {
            "owner_outcome": "Preserve the canonical adapter request",
            "explicit_requirements": ["JSON-only boundary"],
            "latent_requirements": [],
            "non_goals": [],
            "allowed_ambiguities": [],
        },
        "world_fixture": valid_world_fixture(),
        "authority": {
            "allowed_actions": ["adapter.invoke"],
            "forbidden_actions": ["network.use"],
            "scope_boundaries": ["adapter://fake"],
            "required_approvals": [],
        },
        "obligations": {
            "visible": ["preserve request"],
            "protected": [],
            "runtime": ["normalize result"],
        },
        "budgets": {
            "wall_time_seconds": 5,
            "token_limit": 0,
            "cost_limit_usd": 0.0,
            "tool_calls": 3,
        },
        "evaluation": valid_oracle_bundle(),
        "qa": {
            "author_id": "reviewer://task10/author",
            "independent_reviewer_id": "reviewer://task10/verifier",
            "human_solution_digest": DIGEST_A,
            "known_exploits": [],
        },
        "extensions": {"gitspace.adapter-test": {"fixture": 1}},
    }


def valid_agent() -> dict[str, object]:
    return {
        "version": 1,
        "harness": "gitspace-adapter-sdk",
        "harness_version": "0.1.0",
        "model": "none",
        "model_version": "none",
        "provider": "none",
        "model_parameters": {"temperature": 0},
        "system_instructions_digest": DIGEST_A,
        "tools_digest": DIGEST_B,
        "context_digest": DIGEST_A,
        "memory_digest": DIGEST_B,
        "extensions": {"gitspace.adapter-test": {"agent": True}},
    }


def request_values() -> tuple[dict[str, object], dict[str, object]]:
    return deepcopy(valid_task()), deepcopy(valid_agent())
