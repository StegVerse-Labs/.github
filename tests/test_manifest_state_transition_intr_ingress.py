from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from workers import manifest_state_transition_intr_ingress as mod
from workers import universal_intr_profiled_ingress as shared


TASK_ID = "SDK-TT-PURPOSE-BOUND-WORKER-RUNTIME-PROOF-001"


def request(seed: str = "one") -> dict:
    manifest_body = {
        "manifest_profile": "stegverse.ingress-manifest.v1",
        "source_output_id": f"sdk-test1-{seed}",
        "payload": {"text": f"manifest-{seed}"},
    }
    manifest_hash = mod.sha256(manifest_body)
    manifest = dict(manifest_body)
    manifest["canonical_manifest_sha256"] = manifest_hash
    graph = {
        "schema": "stegverse.sdk.installed-state-transition-graph/v1",
        "graph_id": TASK_ID + ":PURPOSE_BOUND_WORKER",
        "canonical_task_id": TASK_ID,
        "processing_capability": "purpose_bound_worker",
        "route_id": "stegverse.route.purpose-bound-worker.v1",
        "request": {
            "schema": "stegverse.sdk.tt-purpose-bound-worker.v1",
            "transition_cell": {"candidate": {"required_capability": "text.integrity_summary"}},
        },
        "ordered_transitions": [
            "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
            "TV_TVC_WARRANT_POLICY_VERIFIED",
            "STEGCORE_INTR_MATERIALIZATION_ADMITTED",
            "PURPOSE_BOUND_WORKER_MATERIALIZED",
            "PURPOSE_BOUND_WORKER_INVOCATION_STARTED",
            "PURPOSE_BOUND_WORKER_TASK_COMPLETED",
            "PURPOSE_BOUND_WORKER_RETIRED",
        ],
        "requires_workercoordinator_claim_fence": True,
        "predecessor_closure_required": True,
        "adapter_executes_lifecycle": False,
    }
    value = {
        "schema": mod.REQUEST_SCHEMA,
        "canonical_manifest": manifest,
        "canonical_manifest_sha256": manifest_hash,
        "processing_capability": "purpose_bound_worker",
        "route_id": "stegverse.route.purpose-bound-worker.v1",
        "route_declaration_hash": "route-" + seed,
        "state_graph": graph,
        "graph_id": graph["graph_id"],
        "canonical_task_id": TASK_ID,
        "requires_workercoordinator_claim_fence": True,
        "predecessor_closure_required": True,
        "credential_authority": "TV/TVC",
        "claim_fence_authority": "WORKERCOORDINATOR",
        "transition_authority": "INTERLOCK_INTR",
        "custody_replay_reconstruction_authority": "MASTER_RECORDS",
        "request_grants_authority": False,
        "sdk_executes_lifecycle": False,
        "authority_effect": "NONE_MANIFEST_RUNTIME_REQUEST_ONLY",
    }
    value["request_sha256"] = mod.sha256(value)
    return value


def closure(transition: str, digit: str, predecessor: str | None = None) -> dict:
    digest = digit * 64
    row = {
        "transition_id": transition,
        "state": "RECORDED",
        "reconstruction_status": "PASS",
        "required_evidence_validation_status": "PASS",
        "receipt_sha256": digest,
        "reconstructed_receipt_sha256": digest,
    }
    if predecessor is not None:
        row["predecessor_receipt_sha256"] = predecessor
    return row


def purpose_receipt(*, replay: bool) -> dict:
    transitions = [
        "WORKERCOORDINATOR_CLAIM_FENCE_BOUND",
        "TV_TVC_WARRANT_POLICY_VERIFIED",
        "STEGCORE_INTR_MATERIALIZATION_ADMITTED",
        "PURPOSE_BOUND_WORKER_MATERIALIZED",
        "PURPOSE_BOUND_WORKER_INVOCATION_STARTED",
        "PURPOSE_BOUND_WORKER_TASK_COMPLETED",
        "PURPOSE_BOUND_WORKER_RETIRED",
    ]
    rows = []
    prior = None
    for index, transition in enumerate(transitions, start=1):
        row = closure(transition, str(index), prior)
        rows.append(row)
        prior = row["receipt_sha256"]
    result = {
        "warrant_policy_master_records_transition": rows[1],
        "intr_admission_master_records_transition": rows[2],
        "purpose_bound_worker_result": {
            "canonical_master_records_transitions": rows[3:],
        },
        "governance": {"manifest_receipt_id": "MR-EXAMPLE"},
        "master_records_reconstruction": {
            "operation_transition_custody_status": "RECORDED",
        },
        "records_only": True,
        "worker_live_after_close": False,
        "continued_authority_after_retirement": False,
    }
    if replay:
        result["master_records_replay"] = {"status": "PASS"}
    return {
        "task_id": TASK_ID,
        "claim_fence_master_records_transition": rows[0],
        "result": result,
    }


class ManifestStateTransitionIngressTests(unittest.TestCase):
    def test_shared_listener_advertises_one_generic_sdk_profile(self):
        profile = shared.profile(False)
        self.assertIn(mod.PROFILE, profile["profiles"])
        self.assertEqual(profile["execution_authority"], "NONE")
        self.assertEqual(profile["credential_authority"], "TV/TVC")

    def test_request_hash_and_manifest_lineage_are_fail_closed(self):
        value = request()
        validated = mod.validate_request(value)
        self.assertEqual(validated["request_sha256"], value["request_sha256"])
        tampered = copy.deepcopy(value)
        tampered["canonical_manifest"]["payload"]["text"] = "changed"
        tampered_without_request_hash = dict(tampered)
        tampered_without_request_hash.pop("request_sha256")
        tampered["request_sha256"] = mod.sha256(tampered_without_request_hash)
        with self.assertRaisesRegex(ValueError, "canonical_manifest_sha256_recompute_mismatch"):
            mod.validate_request(tampered)

    def test_immutable_wire_and_projection_digests_are_independently_checked(self):
        value = request()
        original = copy.deepcopy(value["canonical_manifest"])
        original.pop("canonical_manifest_sha256")
        # The projection is a separately hash-bound SDK validation output.
        projection = dict(original)
        projection["ingress_mode"] = "external_manifest"
        value["canonical_manifest"] = original
        value["wire_manifest_sha256"] = mod.sha256(original)
        value["canonical_manifest_projection"] = projection
        value["canonical_manifest_sha256"] = mod.sha256(projection)
        value.pop("request_sha256")
        value["request_sha256"] = mod.sha256(value)
        self.assertEqual(mod.validate_request(value)["wire_manifest_sha256"], mod.sha256(original))
        tampered = copy.deepcopy(value)
        tampered["wire_manifest_sha256"] = "f" * 64
        tampered.pop("request_sha256")
        tampered["request_sha256"] = mod.sha256(tampered)
        with self.assertRaisesRegex(ValueError, "wire_manifest_sha256_mismatch"):
            mod.validate_request(tampered)
        tampered = copy.deepcopy(value)
        tampered["canonical_manifest_projection"]["source_output_id"] = "substituted"
        tampered["canonical_manifest_sha256"] = mod.sha256(tampered["canonical_manifest_projection"])
        tampered.pop("request_sha256")
        tampered["request_sha256"] = mod.sha256(tampered)
        with self.assertRaisesRegex(ValueError, "canonical_manifest_projection_source_mismatch"):
            mod.validate_request(tampered)

    def test_diagnostic_nonworker_attempt_exposes_exact_unrepaired_predicate(self):
        diagnostic = request("diagnostic")
        diagnostic["canonical_task_id"] = None
        diagnostic["requires_workercoordinator_claim_fence"] = False
        diagnostic["processing_capability"] = "ecosystem_diagnostic"
        diagnostic["route_id"] = "stegverse.route.ecosystem-diagnostic.v1"
        diagnostic["state_graph"]["canonical_task_id"] = None
        diagnostic["state_graph"]["processing_capability"] = diagnostic["processing_capability"]
        diagnostic["state_graph"]["route_id"] = diagnostic["route_id"]
        diagnostic.pop("request_sha256")
        diagnostic["request_sha256"] = mod.sha256(diagnostic)
        self.assertIsNone(mod.validate_request(diagnostic)["canonical_task_id"])
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "^canonical_task_id_required$"):
                mod.execute(Path(td), diagnostic)

    def test_distinct_reruns_are_immutable_and_latest_pointer_advances(self):
        first = request("one")
        second = request("two")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            latest1 = mod.persist_request(root, first)
            latest2 = mod.persist_request(root, second)
            self.assertEqual(latest1, latest2)
            self.assertEqual(json.loads(latest2.read_text())["request_sha256"], second["request_sha256"])
            immutable_root = root / mod.REQUEST_DIR / mod.IMMUTABLE_DIR / TASK_ID
            self.assertTrue((immutable_root / f"{first['request_sha256']}.json").is_file())
            self.assertTrue((immutable_root / f"{second['request_sha256']}.json").is_file())

    def test_return_assembly_refuses_to_invent_missing_replay(self):
        with self.assertRaisesRegex(ValueError, "MASTER_RECORDS_REPLAY_NOT_OBSERVED"):
            mod._assemble_purpose_result(request(), purpose_receipt(replay=False))

    def test_complete_return_preserves_no_continued_authority(self):
        result = mod._assemble_purpose_result(request(), purpose_receipt(replay=True))
        self.assertEqual(result["state"], "COMPLETE")
        self.assertTrue(result["terminal_state"]["records_only"])
        self.assertFalse(result["terminal_state"]["continued_authority"])
        self.assertFalse(result["terminal_state"]["worker_live_after_close"])
        self.assertEqual(len(result["transition_closures"]), 7)


if __name__ == "__main__":
    unittest.main()
