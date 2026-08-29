from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SystemAIEntityRegistryTests(unittest.TestCase):
    def test_registry_declares_stegverse_002_without_false_activation(self) -> None:
        registry = json.loads((ROOT / "control" / "system-ai-entity-registry.json").read_text())
        entity = next(x for x in registry["entities"] if x["entity_id"] == "StegVerse-002")
        self.assertEqual(entity["runtime_repository"], "StegVerse-002/micro-node-runtime")
        self.assertEqual(entity["entity_class"], "SOVEREIGN_AI_RUNTIME_ENTITY")
        self.assertEqual(entity["lifecycle_state"], "FEDERATION_REGISTERED")
        self.assertTrue(entity["activation"]["federation_membership_established"])
        self.assertFalse(entity["activation"]["heartbeat_presence_proven"])
        self.assertFalse(entity["activation"]["governed_inference_proven"])
        self.assertFalse(entity["activation"]["same_execution_reconstruction_proven"])
        self.assertFalse(entity["activation"]["active"])
        self.assertFalse(entity["heartbeat"]["grants_execution_authority"])
        self.assertEqual(entity["authority"]["model_output_authority"], "NONE")

    def test_runtime_is_required_heartbeat_participant(self) -> None:
        hb = json.loads((ROOT / "control" / "repo-heartbeat-federation.json").read_text())
        participant = next(x for x in hb["required_participants"] if x["repository"] == "StegVerse-002/micro-node-runtime")
        self.assertEqual(participant["participant_class"], "RUNTIME")
        self.assertTrue(participant["required"])

    def test_registry_validator_passes(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "validate_system_ai_entities.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("PASS:", proc.stdout)

if __name__ == "__main__":
    unittest.main()
