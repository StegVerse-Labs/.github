from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "scripts" / "bootstrap_sovereign_runtime.py"
spec = importlib.util.spec_from_file_location("bootstrap_sovereign_runtime", BOOTSTRAP)
bootstrap = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(bootstrap)


class SovereignNodeDeclarationPersistenceTests(unittest.TestCase):
    def _complete_source(self, root: Path) -> None:
        for rel in bootstrap.REQUIRED_SOURCE_FILES:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{}\n" if path.suffix == ".json" else "# source\n", encoding="utf-8")

    def test_resident_bootstrap_can_derive_non_authorizing_local_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            runtime = root / "runtime"
            marker = root / "home" / ".stegverse" / "node.json"
            self._complete_source(source)
            declared, ref, eligibility = bootstrap.derive_node_declaration(
                source, runtime, marker,
                {"HOME": str(root / "home"), "PATH": "/usr/bin"},
            )
            self.assertTrue(declared)
            self.assertEqual(ref, str(marker.resolve()))
            self.assertTrue(marker.is_file())
            self.assertTrue(eligibility["eligible"])
            self.assertEqual(eligibility["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
            self.assertEqual(eligibility["canonical_carrier_runtime"], "heartbeat_runtime.engine_v13.HeartbeatRuntime")
            self.assertEqual(eligibility["heartbeat_progression_dependency"], "OSCILLATOR_ONLY")
            self.assertFalse(eligibility["heartbeat_event_trigger_required"])
            self.assertFalse(eligibility["always_on_external_host_required"])
            body = bootstrap.load_json(marker)
            self.assertEqual(body["schema"], "stegverse.sovereign-node-declaration/v0.4")
            self.assertEqual(body["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
            self.assertEqual(body["credential_authority"], "TV/TVC")
            self.assertFalse(body["github_token_required"])
            self.assertEqual(body["authority_effect"], "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY")

    def test_declaration_is_not_an_oscillator_continuity_prerequisite(self) -> None:
        contract = json.loads((ROOT / "management" / "SHWP_STATE_TRANSITION_CONTINUITY_CONTRACT.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["continuity_model"], "INDEPENDENT_OSCILLATOR_CONTINUITY")
        self.assertEqual(contract["transition_producer"], "scripts/advance_heartbeat_transition.py")
        self.assertFalse(contract["oscillator"]["worker_or_task_gating"])
        self.assertFalse(contract["oscillator"]["admission_gating"])
        self.assertFalse(contract["third_party_fallback_policy"]["required_dependency"])
        self.assertNotIn("node declaration", contract["release_condition"].lower())
        self.assertNotIn("sovereign node", " ".join(contract["carrier_completion_predicates"]).lower())


if __name__ == "__main__":
    unittest.main()
