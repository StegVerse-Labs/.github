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
    "kv-skap-bidirectional-intr",
    "STEGVERSE_DEVICE_KV_SKAP_INTR_MATERIALIZATION",
    "SKAP Vault InTr custody event",
)

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

    def test_roundtrip_component_is_the_gate_name(self) -> None:
        record = json.loads((ROOT / "data/canonical-task-records/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json").read_text())
        components = json.dumps(record)
        self.assertIn('"kv-skap-gate-roundtrip"', components)
        self.assertIn('"device-kv-bidirectional-intr"', components)  # Device -> KV is the one InTr hop

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
