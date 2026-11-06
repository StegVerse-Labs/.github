"""Retired KV -> SKAP Vault client names stay absent (no aliases).

The SKAP Vault sits inside KV, so the KV -> SKAP Vault step is the in-KV SKAP gate, never an InTr hop
(InTr runs only between distinct orgs). The client names for that step therefore describe the gate.
"""
from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RETIRED = (
    "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
    "SKAP Vault InTr custody event",
)

# Registry component kv-skap-bidirectional-intr -> kv-skap-gate-roundtrip (Coordination ruling (1), #167 c6393224851):
# renamed at canonical-task-registry generation 321 in the registry, the STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001 record,
# the KV-SKAP-VAULT-FUNCTIONAL-001 adjacency ruling and its i1 request, with the six i1 requests re-sealed at 321.
RETIRED_COMPONENT = "kv-skap-bidirectional-" + "intr"
RENAMED_COMPONENT = "kv-skap-gate-roundtrip"
RENAMED_COMPONENT_FILES = (
    "control/adjacency-rulings/KV-SKAP-VAULT-FUNCTIONAL-001.json",
    "data/canonical-task-records/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json",
    "data/canonical-task-registry.json",
    "tests/fixtures/canonical_task_registration/i1-goal-manifests/KV-SKAP-VAULT-FUNCTIONAL-001.request.json",
)
# Files that name the retired component only to retire it.
RETIRING_COMPONENT = {"tests/test_kv_skap_gate_client_naming.py", "docs/KV_SKAP_OPERATIONAL_INTR_TRANSPORT_MIRROR_HANDOFF.md"}

# Sealed text that may keep a retired token: request.json is a sealed observation of main 86382e60 whose
# request_sha256 is pinned in the i1 MANIFEST; this test and the handoff doc name the retired tokens to retire them.
SEALED_OR_RETIRING = {
    "tests/fixtures/canonical_task_registration/i1-goal-manifests/KV-SKAP-VAULT-FUNCTIONAL-001.request.json",
    "tests/test_kv_skap_gate_client_naming.py",
    "docs/KV_SKAP_OPERATIONAL_INTR_TRANSPORT_MIRROR_HANDOFF.md",
}


def _tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [p for p in out.decode().split("\0") if p and not p.startswith("evidence/")]


class KvSkapGateClientNamingTests(unittest.TestCase):
    def test_retired_names_absent_outside_sealed_text(self) -> None:
        found = []
        for rel in _tracked():
            if rel in SEALED_OR_RETIRING:
                continue
            path = ROOT / rel
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
                continue
            found.extend(f"{rel}:{token}" for token in RETIRED if token in text)
        self.assertEqual(found, [])

    def test_retired_component_name_is_gone_with_no_alias(self) -> None:
        found = []
        for rel in _tracked():
            if rel in RETIRING_COMPONENT:
                continue
            try:
                text = (ROOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
                continue
            if RETIRED_COMPONENT in text:
                found.append(rel)
        self.assertEqual(found, [])
        for rel in RENAMED_COMPONENT_FILES:
            self.assertEqual((ROOT / rel).read_text(encoding="utf-8").count(RENAMED_COMPONENT), 1, rel)
        record = json.loads((ROOT / "data/canonical-task-records/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json").read_text())
        self.assertIn("device-kv-bidirectional-intr", json.dumps(record))  # Device -> KV is the one InTr hop
        self.assertIn('"%s"' % RENAMED_COMPONENT, json.dumps(record))

    def test_worker_reads_the_gate_env_only(self) -> None:
        worker = (ROOT / "workers/run_device_kv_skap_canonical_runtime_worker.py").read_text()
        self.assertIn("STEGVERSE_DEVICE_KV_SKAP_MATERIALIZATION", worker)

    def test_handoff_drops_universal_intr_framing(self) -> None:
        doc = (ROOT / "docs/KV_SKAP_OPERATIONAL_INTR_TRANSPORT_MIRROR_HANDOFF.md").read_text()
        self.assertNotIn("Universal InTr", doc)
        self.assertNotIn("Operational InTr Transport", doc)

    def test_dispatch_docstring_names_the_gate(self) -> None:
        head = (ROOT / "scripts/dispatch_kv_skap_custody_materialization.py").read_text().split('"""')[1]
        self.assertIn("in-KV SKAP gate", head)
        self.assertNotIn("Universal-InTr", head)


if __name__ == "__main__":
    unittest.main()
