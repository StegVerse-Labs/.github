#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


validator = load_module("runtime_profile_validator", "scripts/validate_runtime_profile_map.py")
matcher = load_module("runtime_profile_matcher", "scripts/match_runtime_profile.py")
builder = load_module("runtime_profile_builder", "scripts/build_runtime_profile_map.py")


class RuntimeProfileMapTests(unittest.TestCase):
    def test_checked_in_map_validates(self):
        data = json.loads((ROOT / "control/runtime-profile-map.json").read_text(encoding="utf-8"))
        result = validator.validate(data)
        self.assertEqual(result["state"], "PASS")

    def test_builder_preserves_non_authority(self):
        data = builder.build(ROOT)
        self.assertFalse(data["authority"]["map_grants_execution_authority"])
        self.assertFalse(data["authority"]["capability_match_grants_authority"])
        self.assertEqual(data["authority"]["worker_claim_authority"], "WORKERCOORDINATOR")
        self.assertEqual(data["authority"]["credential_authority"], "TV/TVC")
        self.assertTrue(any(p["profile_class"] == "OBSERVABILITY_CONSUMER" for p in data["profiles"]))

    def test_matcher_rejects_missing_capability(self):
        profile = {
            "profile_id": "x",
            "declared": {"capabilities": ["read"], "mutation_allowed": False, "deployment_allowed": False, "environment_classes": ["SOVEREIGN_RESIDENT"], "directions": ["INTERNAL"]},
            "observed": {"state": "OBSERVED"}
        }
        row = matcher.evaluate(profile, {"write"}, "SOVEREIGN_RESIDENT", "INTERNAL", False, False, False)
        self.assertFalse(row["compatible"])
        self.assertIn("write", row["missing_capabilities"])

    def test_matcher_does_not_turn_observation_into_authority(self):
        profile = {
            "profile_id": "x",
            "declared": {"capabilities": ["read"], "mutation_allowed": False, "deployment_allowed": False, "environment_classes": ["SOVEREIGN_RESIDENT"], "directions": ["INTERNAL"]},
            "observed": {"state": "OBSERVED"}
        }
        row = matcher.evaluate(profile, {"read"}, "SOVEREIGN_RESIDENT", "INTERNAL", False, False, True)
        self.assertTrue(row["compatible"])
        self.assertEqual(row["authority_effect"], "NONE_CANDIDATE_MATCH_ONLY")

    def test_no_duplicate_profile_ids_in_generated_projection(self):
        data = builder.build(ROOT)
        ids = [p["profile_id"] for p in data["profiles"]]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
