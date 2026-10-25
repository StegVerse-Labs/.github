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

# FAIL_CLOSED KV_SKAP_GATE_COMPONENT_RENAME_BLOCKED_BY_REGISTRY_GENERATION_FENCE (class B): renaming the registry
# component needs canonical-task-registry generation 321 (scripts/check_registry_generation_fence.py), which makes
# every sealed i1 goal manifest request (observed_registry_generation 320) stale. Until that is coordinated, the
# component keeps its name in exactly these files, with these counts, and may not spread.
PENDING_COMPONENT = "kv-skap-bidirectional-" + "intr"
PENDING_COMPONENT_RESIDUALS = {
    "control/adjacency-rulings/KV-SKAP-VAULT-FUNCTIONAL-001.json": 1,
    "data/canonical-task-records/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json": 1,
    "data/canonical-task-registry.json": 1,
    "docs/KV_SKAP_OPERATIONAL_INTR_TRANSPORT_MIRROR_HANDOFF.md": 1,
    "tests/fixtures/canonical_task_registration/i1-goal-manifests/KV-SKAP-VAULT-FUNCTIONAL-001.request.json": 1,
}

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

    def test_pending_component_name_does_not_spread(self) -> None:
        found = {}
        for rel in _tracked():
            try:
                text = (ROOT / rel).read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
                continue
            if text.count(PENDING_COMPONENT):
                found[rel] = text.count(PENDING_COMPONENT)
        self.assertEqual(found, PENDING_COMPONENT_RESIDUALS)
        record = json.loads((ROOT / "data/canonical-task-records/STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001.json").read_text())
        self.assertIn("device-kv-bidirectional-intr", json.dumps(record))  # Device -> KV is the one InTr hop

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
