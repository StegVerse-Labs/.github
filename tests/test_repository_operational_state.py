import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "repository_operational_state",
    ROOT / "scripts" / "repository_operational_state.py",
)
ros = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ros)

def sample():
    return {
        "schema": "stegverse.repository-operational-state/v1",
        "repository": {
            "org": "StegVerse-Labs",
            "name": ".github",
            "commit": "0123456789abcdef",
            "default_branch": "main"
        },
        "authority": {
            "repository_handoff": "docs/ORG_MIRROR_HANDOFF.md",
            "cosv_profile": "management/COSV_PROFILE_V1.json",
            "credential_authority": "TV/TVC",
            "github_token_runtime_authority": "NONE"
        },
        "cosv": {
            "repository": {
                "identity": "StegVerse-Labs/.github",
                "profile": "aggregate.v1",
                "level": "system",
                "vector": "59999999900000",
                "evidence_refs": ["docs/ORG_MIRROR_HANDOFF.md"],
                "observed_at": "2026-09-02T12:00:00Z",
                "exact_metrics": {
                    "developed": 100,
                    "validation": 100,
                    "integration": 100,
                    "propagation": 100,
                    "activation": 100,
                    "readiness": 100,
                    "ownership": 100,
                    "evidence": 100
                }
            },
            "tasks": [{
                "identity": "TASK-1",
                "profile": "task.v1",
                "level": "task",
                "vector": "50000000100000",
                "evidence_refs": ["handoffs/TASK-1.json"],
                "observed_at": "2026-09-02T12:00:00Z",
                "exact_metrics": {}
            }],
            "transition": None
        },
        "implementation": {
            "developed_files": 8,
            "scaffolding_files": 1,
            "stub_files": 1,
            "unknown_files": 0,
            "completion_percent": 80.0
        },
        "operational_state": {
            "source_complete": True,
            "validated": True,
            "integrated": True,
            "released": False,
            "propagated": False,
            "activated": False,
            "runtime_proven": False
        },
        "evidence": {
            "receipts": [],
            "manifests": ["control/example.json"],
            "validation_runs": ["local:test"],
            "issues": ["#741"],
            "pull_requests": [],
            "release_refs": [],
            "runtime_refs": []
        },
        "dependencies": {
            "upstream": [],
            "downstream": ["master-records/orchestration"],
            "cross_repo_requirements": []
        },
        "work": {
            "active": ["TASK-1"],
            "blocked": [],
            "machine_owned": ["TASK-1"],
            "human_owned": [],
            "unassigned": []
        },
        "next_transition": {
            "state": "MERGE_VALIDATED_SOURCE",
            "admissible": True,
            "requirements": ["exact-head validation"],
            "authority_required": "repository maintainer",
            "target_files": []
        },
        "projections": {
            "mirror_handoff": "docs/COSV_REPOSITORY_OPERATIONAL_STATE_MIRROR_HANDOFF.md",
            "human_summary": "",
            "ai_execution_brief": ""
        }
    }

class RepositoryOperationalStateTests(unittest.TestCase):
    def test_valid_sample(self):
        self.assertTrue(ros.validate_semantics(sample()))

    def test_completion_ratio_is_enforced(self):
        payload = sample()
        payload["implementation"]["completion_percent"] = 90
        with self.assertRaises(ValueError):
            ros.validate_semantics(payload)

    def test_activation_requires_live_evidence(self):
        payload = sample()
        payload["operational_state"]["activated"] = True
        with self.assertRaises(ValueError):
            ros.validate_semantics(payload)

    def test_runtime_proven_requires_runtime_ref(self):
        payload = sample()
        payload["operational_state"]["runtime_proven"] = True
        payload["evidence"]["receipts"] = ["receipt.json"]
        with self.assertRaises(ValueError):
            ros.validate_semantics(payload)

    def test_release_requires_release_ref(self):
        payload = sample()
        payload["operational_state"]["released"] = True
        with self.assertRaises(ValueError):
            ros.validate_semantics(payload)

    def test_projection_is_deterministic(self):
        payload = sample()
        a = ros.hydrate_projections(payload)
        b = ros.hydrate_projections(payload)
        self.assertEqual(a["projections"], b["projections"])
        self.assertIn("COSV repository vector", a["projections"]["ai_execution_brief"])

    def test_zero_denominator_requires_unknown_completion(self):
        payload = sample()
        payload["implementation"] = {
            "developed_files": 0,
            "scaffolding_files": 0,
            "stub_files": 0,
            "unknown_files": 0,
            "completion_percent": None
        }
        self.assertTrue(ros.validate_semantics(payload))

if __name__ == "__main__":
    unittest.main()
