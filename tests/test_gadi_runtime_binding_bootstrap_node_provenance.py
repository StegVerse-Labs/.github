from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts import materialize_gadi_runtime_binding as module


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def node(char: str = "a") -> str:
    return "SV-NODE-" + char * 24


def seed_runtime(runtime: Path, *, discovered: str | None = None, presence_node=None) -> None:
    discovered = discovered or node()
    write_json(runtime / module.DISCOVERY_REL, {
        "schema": module.DISCOVERY_SCHEMA,
        "task_id": module.TASK_ID,
        "parent_task_id": module.PARENT_TASK_ID,
        "state": "CURRENT_RETAINED_NODE_DISCOVERY_OBSERVED",
        "node_ref": discovered,
        "runtime_presence_observed": False,
        "runtime_supervision_observed": False,
        "runtime_subject_bound": False,
        "execution_authority_granted": False,
        "authority_effect": "NONE_OBSERVATION_ONLY",
    })
    supervision = runtime / "receipts/sovereign-host/ephemeral-process.latest.json"
    write_json(supervision, {
        "carrier_active": True,
        "worker_active": True,
        "separate_carrier_and_worker_processes": True,
        "canonical_carrier_runtime": module.CANONICAL_CARRIER_RUNTIME,
        "worker_runtime": module.CANONICAL_WORKER_RUNTIME,
        "third_party_process_host_required": False,
        "heartbeat_grants_execution_authority": False,
        "authority_effect": "NONE_SUPERVISION_ONLY",
    })
    write_json(runtime / module.PRESENCE_REL, {
        "schema": "stegverse.hb-runtime-presence-resident-observability/v1",
        "runtime_root": str(runtime.resolve()),
        "resident": {
            "node_id": presence_node,
            "runtime_alive_observed": True,
            "present_worker_runtime_observed": True,
            "worker_cycle_fresh": True,
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


def seed_declaration(marker: Path, bootstrap: Path, runtime: Path, *, declared_node: str | None = None, bootstrap_state: str = "COMPLETE") -> None:
    declared_node = declared_node or node()
    write_json(marker, {
        "schema": module.NODE_DECLARATION_SCHEMA,
        "declared": True,
        "node_id": declared_node,
        "credential_authority": "TV/TVC",
        "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
    })
    write_json(bootstrap, {
        "schema": module.BOOTSTRAP_SCHEMA,
        "state": bootstrap_state,
        "runtime_root": str(runtime.resolve()),
        "node_declaration_ref": str(marker.resolve()),
        "credential_authority": "TV/TVC",
    })


class GADIBootstrapNodeProvenanceTests(unittest.TestCase):
    def test_missing_presence_node_uses_exact_bootstrap_bound_declaration(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            marker = root / "node.json"
            bootstrap = root / "bootstrap.latest.json"
            seed_runtime(runtime, presence_node=None)
            seed_declaration(marker, bootstrap, runtime)
            result = module.materialize(runtime, node_marker=marker, bootstrap_receipt=bootstrap)
        self.assertEqual(result["state"], "CURRENT_RUNTIME_SUBJECT_BOUND")
        self.assertEqual(result["node_id"], node())
        self.assertEqual(result["node_identity_source"], "BOOTSTRAP_BOUND_SOVEREIGN_NODE_DECLARATION")
        self.assertTrue(result["discovered_node_matches_runtime_subject"])
        self.assertFalse(result["execution_authority_granted"])

    def test_bootstrap_declaration_must_match_discovered_node(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            marker = root / "node.json"
            bootstrap = root / "bootstrap.latest.json"
            seed_runtime(runtime, discovered=node("a"), presence_node=None)
            seed_declaration(marker, bootstrap, runtime, declared_node=node("b"))
            result = module.materialize(runtime, node_marker=marker, bootstrap_receipt=bootstrap)
        self.assertEqual(result["state"], "RUNTIME_BINDING_UNOBSERVED_FAIL_CLOSED")
        self.assertIn("DISCOVERED_NODE_RUNTIME_SUBJECT_MISMATCH", result["blockers"])

    def test_incomplete_bootstrap_cannot_supply_missing_identity(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            marker = root / "node.json"
            bootstrap = root / "bootstrap.latest.json"
            seed_runtime(runtime, presence_node=None)
            seed_declaration(marker, bootstrap, runtime, bootstrap_state="REVIEW_REQUIRED")
            result = module.materialize(runtime, node_marker=marker, bootstrap_receipt=bootstrap)
        self.assertIn("SOVEREIGN_BOOTSTRAP_NOT_COMPLETE", result["blockers"])
        self.assertIn("RESIDENT_NODE_ID_MISSING", result["blockers"])

    def test_bootstrap_runtime_root_must_match_presence_runtime(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            other = root / "other-runtime"
            marker = root / "node.json"
            bootstrap = root / "bootstrap.latest.json"
            seed_runtime(runtime, presence_node=None)
            seed_declaration(marker, bootstrap, other)
            result = module.materialize(runtime, node_marker=marker, bootstrap_receipt=bootstrap)
        self.assertIn("SOVEREIGN_BOOTSTRAP_RUNTIME_ROOT_MISMATCH", result["blockers"])

    def test_existing_presence_node_does_not_require_bootstrap_fallback(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            seed_runtime(runtime, presence_node=node())
            result = module.materialize(
                runtime,
                node_marker=root / "missing-node.json",
                bootstrap_receipt=root / "missing-bootstrap.json",
            )
        self.assertEqual(result["state"], "CURRENT_RUNTIME_SUBJECT_BOUND")
        self.assertEqual(result["node_identity_source"], "RUNTIME_PRESENCE_RECEIPT")


if __name__ == "__main__":
    unittest.main()
