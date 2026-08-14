from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from workers.formalism_manifold_orchestration_worker import inventory, normalization, crosswalk, governance_mapping


CONFIG = {
    "formalism_authority": "Admissible-Existence repository-local canonical handoffs and formal sources",
    "runtime_authority": "StegVerse-Labs/StegCore canonical StegGate runtime",
    "required_repositories": [
        {"repository": "Admissible-Existence/AE", "required": True},
        {"repository": "StegVerse-Labs/StegCore", "required": True},
    ],
    "relationship_contract": {
        "required_handoff_fields": [
            "formal_role", "inputs", "outputs", "upstream_dependencies", "downstream_consumers",
            "authority_boundary", "composition_relations", "resolution_relationship",
            "continuity_relationship", "mathematical_maturity", "functional_maturity", "collision_rules"
        ]
    },
}


class FormalismManifoldWorkerTests(unittest.TestCase):
    def _roots(self, root: Path) -> dict[str, Path]:
        ae = root / "ae"
        core = root / "core"
        ae.mkdir()
        core.mkdir()
        relationship_text = """# Mirror Handoff
formal role purpose
inputs source refs dependencies
outputs receipts artifacts
upstream dependencies
downstream consumers propagation
authority boundary non-claims
composition compositional relationship
admissible resolution
continuity reconstruction
mathematical maturity theorem formalism
functional maturity status validation
collision rules do not claims
"""
        (ae / "AE_MIRROR_HANDOFF.md").write_text(relationship_text + "StegVerse-Labs/StegCore\n", encoding="utf-8")
        (core / "STEGCORE_MIRROR_HANDOFF.md").write_text(relationship_text + "Admissible-Existence/AE\n", encoding="utf-8")
        return {"Admissible-Existence/AE": ae, "StegVerse-Labs/StegCore": core}

    def test_inventory_requires_materialization_and_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            roots = self._roots(Path(tmp))
            result = inventory(CONFIG, roots)
            self.assertEqual(result["missing_materialization"], [])
            self.assertEqual(result["missing_handoff"], [])

    def test_normalization_reports_complete_for_explicit_relationship_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = normalization(CONFIG, self._roots(Path(tmp)))
            self.assertTrue(result["normalization_complete"])
            self.assertTrue(all(not row["missing_fields"] for row in result["repositories"]))

    def test_crosswalk_is_evidence_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = crosswalk(CONFIG, self._roots(Path(tmp)))
            self.assertEqual(result["authority_effect"], "NONE_RELATIONSHIP_EVIDENCE_ONLY")
            self.assertEqual(len(result["edges"]), 2)

    def test_governance_mapping_preserves_authority_split(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = governance_mapping(CONFIG, self._roots(Path(tmp)))
            self.assertTrue(result["bridge_ready_for_analysis"])
            self.assertIn("Admissible-Existence", result["formalism_authority"])
            self.assertIn("StegCore", result["runtime_authority"])
            self.assertEqual(result["authority_effect"], "NONE_MAPPING_EVIDENCE_ONLY")


if __name__ == "__main__":
    unittest.main()
