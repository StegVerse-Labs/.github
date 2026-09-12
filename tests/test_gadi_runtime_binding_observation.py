from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import materialize_gadi_runtime_binding as module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def canonical_node(char: str = "a") -> str:
    return "SV-NODE-" + char * 24


def seed_discovery(runtime: Path, *, node_id: str | None = None, state: str = "CURRENT_RETAINED_NODE_DISCOVERY_OBSERVED") -> None:
    node = node_id or canonical_node()
    write_json(runtime / module.DISCOVERY_REL, {
        "schema": module.DISCOVERY_SCHEMA,
        "task_id": module.TASK_ID,
        "parent_task_id": module.PARENT_TASK_ID,
        "state": state,
        "node_ref": node,
        "observation_ref": "runtime://gadi/retained-node-discovery/test",
        "runtime_presence_observed": False,
        "runtime_supervision_observed": False,
        "runtime_subject_bound": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    })


def seed_presence(runtime: Path, *, node_id: str | None = None, runtime_root: str | None = None, worker_runtime: str | None = None) -> None:
    node = node_id or canonical_node()
    supervision = runtime / "receipts/sovereign-host/ephemeral-process.latest.json"
    write_json(supervision, {
        "active": True,
        "carrier_active": True,
        "worker_active": True,
        "worker_task_capable_cycle_observed": True,
        "separate_carrier_and_worker_processes": True,
        "canonical_carrier_runtime": module.CANONICAL_CARRIER_RUNTIME,
        "worker_runtime": worker_runtime or module.CANONICAL_WORKER_RUNTIME,
        "third_party_process_host_required": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_SUPERVISION_ONLY",
    })
    write_json(runtime / module.PRESENCE_REL, {
        "schema": "stegverse.hb-runtime-presence-resident-observability/v1",
        "runtime_root": runtime_root or str(runtime.resolve()),
        "resident": {
            "node_id": node,
            "runtime_alive_observed": True,
            "present_worker_runtime_observed": True,
            "worker_cycle_fresh": True,
            "runtime_evidence_kind": "CARRIER_SELF_HEAL_SUPERVISION_RECEIPT",
            "runtime_evidence_ref": str(supervision),
        },
        "heartbeat_reference": {"heartbeat_grants_authority": False},
        "governed_progress": {"runtime_signal_is_execution_receipt": False},
        "authority": {
            "credential_authority": "TV/TVC",
            "hb_authority_effect": "NONE_REFERENCE_ONLY",
            "projection_authority_effect": "NONE_OBSERVATION_ONLY",
            "github_token_runtime_authority": "NONE",
        },
    })


class GADIRuntimeBindingObservationTests(unittest.TestCase):
    def test_exact_discovered_runtime_subject_materializes_non_authorizing_binding(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            seed_presence(runtime)
            result = module.materialize(runtime)
            written = json.loads((runtime / module.OUTPUT_REL).read_text())
        self.assertEqual(result["state"], "CURRENT_RUNTIME_SUBJECT_BOUND")
        self.assertEqual(written["runtime_binding_ref"], result["runtime_binding_ref"])
        self.assertTrue(result["runtime_binding_ref"].startswith("runtime://gadi/"))
        self.assertEqual(result["node_id"], canonical_node())
        self.assertEqual(result["discovered_node_ref"], canonical_node())
        self.assertTrue(result["discovered_node_matches_runtime_subject"])
        self.assertFalse(result["claim_or_fence_granted"])
        self.assertFalse(result["runtime_lease_granted"])
        self.assertFalse(result["execution_authority_granted"])
        self.assertEqual(result["authority_effect"], "NONE_OBSERVATION_ONLY")

    def test_missing_discovery_observation_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_presence(runtime)
            result = module.materialize(runtime)
        self.assertEqual(result["state"], "RUNTIME_BINDING_UNOBSERVED_FAIL_CLOSED")
        self.assertIn("RETAINED_NODE_DISCOVERY_OBSERVATION_MISSING", result["blockers"])

    def test_discovered_node_runtime_subject_mismatch_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime, node_id=canonical_node("a"))
            seed_presence(runtime, node_id=canonical_node("b"))
            result = module.materialize(runtime)
        self.assertEqual(result["state"], "RUNTIME_BINDING_UNOBSERVED_FAIL_CLOSED")
        self.assertIn("DISCOVERED_NODE_RUNTIME_SUBJECT_MISMATCH", result["blockers"])

    def test_noncanonical_runtime_node_id_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            seed_presence(runtime, node_id="node:gadi:1")
            result = module.materialize(runtime)
        self.assertIn("RESIDENT_NODE_ID_NOT_CANONICAL_STEGBROWSER_NODE", result["blockers"])

    def test_discovery_authority_drift_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            discovery = json.loads((runtime / module.DISCOVERY_REL).read_text())
            discovery["runtime_subject_bound"] = True
            write_json(runtime / module.DISCOVERY_REL, discovery)
            seed_presence(runtime)
            result = module.materialize(runtime)
        self.assertIn("DISCOVERY_RUNTIME_BINDING_AUTHORITY_DRIFT", result["blockers"])

    def test_runtime_root_mismatch_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            seed_presence(runtime, runtime_root="/different/runtime")
            result = module.materialize(runtime)
        self.assertIn("RUNTIME_ROOT_SUBJECT_MISMATCH", result["blockers"])
        self.assertIsNone(result["runtime_binding_ref"])

    def test_missing_node_identity_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            seed_presence(runtime, node_id="")
            result = module.materialize(runtime)
        self.assertIn("RESIDENT_NODE_ID_MISSING", result["blockers"])

    def test_noncanonical_worker_runtime_identity_fails_closed(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            seed_presence(runtime, worker_runtime="other.worker.Runtime")
            result = module.materialize(runtime)
        self.assertIn("CANONICAL_WORKER_RUNTIME_IDENTITY_MISSING", result["blockers"])

    def test_binding_changes_when_exact_discovery_bytes_change(self) -> None:
        with TemporaryDirectory() as temporary:
            runtime = Path(temporary)
            seed_discovery(runtime)
            seed_presence(runtime)
            first = module.materialize(runtime)["runtime_binding_ref"]
            discovery = json.loads((runtime / module.DISCOVERY_REL).read_text())
            discovery["observation_ref"] = "runtime://gadi/retained-node-discovery/changed"
            write_json(runtime / module.DISCOVERY_REL, discovery)
            second = module.materialize(runtime)["runtime_binding_ref"]
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
