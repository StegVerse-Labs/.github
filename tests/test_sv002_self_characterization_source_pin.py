from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "handoffs" / "SHWP-SV002-SELF-CHARACTERIZATION-001.json"
PIN = "4acbf42ad321311e14b0a736220874bae34ac998"


class SV002SelfCharacterizationSourcePinTests(unittest.TestCase):
    def test_resident_handoff_pins_validated_principal_source(self) -> None:
        data = json.loads(HANDOFF.read_text(encoding="utf-8"))
        refs = data["task"]["source_refs"]
        self.assertIn(f"StegVerse-002/micro-node-runtime@{PIN}", refs)
        for path in (
            "experiments/self-characterization-001/EXPERIMENT_CONTRACT.v0.1.json",
            "experiments/self-characterization-001/SUBJECT_IDENTITY_MANIFEST.v0.1.json",
            "schemas/self_characterization_runtime_identity.schema.json",
            "tools/verify_self_characterization_runtime_identity.py",
            "tools/run_self_characterization_principal.py",
        ):
            self.assertIn(f"StegVerse-002/micro-node-runtime@{PIN}:{path}", refs)

    def test_old_principal_source_pin_is_absent(self) -> None:
        text = HANDOFF.read_text(encoding="utf-8")
        self.assertNotIn("a99e930ffebb8460536b1e5fee632449b4ba33e7", text)


if __name__ == "__main__":
    unittest.main()
