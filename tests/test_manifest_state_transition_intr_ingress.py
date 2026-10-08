from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
    """Real producer: the transition appends to the tmp Organization ledger root."""
    from workers.canonical_state_transition_custody import build_state_receipt, submit_state_receipt

    result = submit_state_receipt(build_state_receipt(
        transition_id=transition,
        transition_sequence=int(digit),
        subject_or_correlation_id=TASK_ID,
        transition_outcome="OBSERVED",
        prior_state_ref_or_hash=None if predecessor is None else "sha256:" + predecessor,
        resulting_state_ref_or_hash=None,
        governance_decision_ref_where_applicable=None,
        transition_evidence={"transition": transition},
    ))
    organization = result["organization_receipt"]
    # Master Records reconstruction is not requested and never gates the closure.
    row = {
        "transition_id": transition,
        "state": result["state"],
        "reconstruction_status": result["reconstruction_status"],
        "required_evidence_validation_status": result["required_evidence_validation_status"],
        "receipt_sha256": result["receipt_sha256"],
        "organization_receipt_sha256": organization["receipt_sha256"],
        "organization_source_transition_sha256": organization["source_transition_sha256"],
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
    def setUp(self):
        # Ledger roots are supplied, never derived from the host.
        ledger = tempfile.TemporaryDirectory()
        self.addCleanup(ledger.cleanup)
        env = patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": ledger.name})
        env.start()
        self.addCleanup(env.stop)

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

    def test_tvc_binding_is_derived_only_from_validated_manifest_lineage(self):
        value = request("tvc-binding")
        caller = {
            "schema": "stegverse.vault.non_exportable_operation_request.v1",
            "sdk_manifest_binding": {
                "request_sha256": "f" * 64,
                "canonical_manifest_sha256": "f" * 64,
                "processing_capability": "caller-selected",
                "route_id": "caller-selected",
            },
            "lease_receipt": {
                "decision": "ALLOW_CAPABILITY_LEASE",
                "sdk_manifest_binding": {
                    "request_sha256": "e" * 64,
                    "canonical_manifest_sha256": "e" * 64,
                    "processing_capability": "lease-selected",
                    "route_id": "lease-selected",
                },
            },
        }
        bound = mod.bind_tvc_provider_request(value, caller)
        expected = {
            "request_sha256": value["request_sha256"],
            "canonical_manifest_sha256": value["canonical_manifest_sha256"],
            "processing_capability": value["processing_capability"],
            "route_id": value["route_id"],
        }
        self.assertEqual(bound["sdk_manifest_binding"], expected)
        self.assertEqual(bound["lease_receipt"]["sdk_manifest_binding"], expected)

    def test_tvc_binding_rejects_unvalidated_manifest_request(self):
        value = request("tvc-tampered")
        value["processing_capability"] = "caller-selected"
        with self.assertRaises(ValueError):
            mod.bind_tvc_provider_request(value, {"lease_receipt": {"decision": "ALLOW_CAPABILITY_LEASE"}})

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
            first = mod.execute(Path(td), diagnostic)
            second = mod.execute(Path(td), diagnostic)
            self.assertEqual(first, second)
            self.assertEqual(first["disposition"], "DENY")
            self.assertEqual(first["reason_code"], "ORIGINAL_WIRE_DIGEST_MISMATCH")
            self.assertEqual(first["failed_predicate"], "ORIGINAL_WIRE_DIGEST_MISMATCH")
            self.assertFalse(first["terminal"])
            self.assertFalse(first["automatic_retry_permitted"])
            self.assertFalse(first["authentic_intr_disposition_observed"])
            self.assertFalse(first["organization_master_records_organization_record_observed"])
            self.assertEqual(first["request_sha256"], diagnostic["request_sha256"])
            self.assertTrue(Path(first["source_disposition_ref"]).is_file())
            self.assertEqual(json.loads(Path(first["source_disposition_ref"]).read_text())["disposition"], "DENY")
            self.assertFalse((Path(td) / "receipts/sovereign-host/sdk-tt-purpose-bound-worker-runtime-proof.latest.json").exists())

    def test_missing_embedded_hash_is_retained_deny_then_corrected_envelope_advances(self):
        original = request("exp3-hash-deny")
        # The original frozen wire manifest has no derived embedded digest.
        frozen = copy.deepcopy(original["canonical_manifest"])
        frozen.pop("canonical_manifest_sha256")
        rejected = copy.deepcopy(original)
        rejected["canonical_manifest"] = frozen
        rejected["canonical_manifest_sha256"] = mod.sha256(frozen)
        rejected.pop("request_sha256")
        rejected["request_sha256"] = mod.sha256(rejected)
        before = copy.deepcopy(frozen)

        def validated_transport(_headers, _body):
            return {"origin": "TVC_RELAY_EGRESS"}

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            denied = mod.admit(
                runtime_root=root,
                body=mod.canonical(rejected),
                headers={},
                transport_validator=validated_transport,
            )
            self.assertEqual(denied["state"], "DENY")
            self.assertEqual(denied["reason_code"], "canonical_manifest_sha256_binding_mismatch")
            self.assertEqual(denied["failed_predicate"], denied["reason_code"])
            self.assertEqual(denied["transition_id"], "SDK_MANIFEST_BINDING")
            self.assertFalse(denied["terminal"])
            self.assertFalse(denied["authentic_intr_admission_observed"])
            self.assertTrue(denied["transport_validated"])
            self.assertEqual(denied["original_wire_manifest_sha256"], mod.sha256(before))
            self.assertEqual(denied["original_request_sha256"], mod.sha256(rejected))
            self.assertEqual(json.loads(Path(denied["source_disposition_ref"]).read_text())["state"], "DENY")
            self.assertEqual(frozen, before)

            # A corrected builder envelope separately commits both wire and
            # normalized projection. Its next verdict is not the hash DENY.
            corrected = copy.deepcopy(rejected)
            projection = dict(frozen)
            projection["ingress_mode"] = "external_manifest"
            corrected["wire_manifest_sha256"] = mod.sha256(frozen)
            corrected["canonical_manifest_projection"] = projection
            corrected["canonical_manifest_sha256"] = mod.sha256(projection)
            corrected.pop("request_sha256")
            corrected["request_sha256"] = mod.sha256(corrected)
            self.assertEqual(
                mod.validate_request(corrected)["wire_manifest_sha256"],
                mod.sha256(before),
            )
            self.assertEqual(frozen, before)
            # The subsequent attempt's actual execution disposition requires
            # an admitted existing runtime; this source test cannot mint it.

    def test_unrelated_invalid_credential_contract_is_not_builder_deny(self):
        invalid = request("invalid-authority")
        invalid["credential_authority"] = "GITHUB"
        invalid.pop("request_sha256")
        invalid["request_sha256"] = mod.sha256(invalid)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "credential_authority_mismatch"):
                mod.admit(
                    runtime_root=Path(td),
                    body=mod.canonical(invalid),
                    headers={},
                    transport_validator=lambda _h, _b: {"origin": "TVC_RELAY_EGRESS"},
                )

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

    def test_return_assembly_refuses_master_records_pass_without_organization_receipt(self):
        receipt = purpose_receipt(replay=True)
        forged = dict(receipt["claim_fence_master_records_transition"], reconstruction_status="PASS",
                      required_evidence_validation_status="PASS")
        forged.pop("organization_receipt_sha256")
        forged.pop("organization_source_transition_sha256")
        receipt["claim_fence_master_records_transition"] = forged
        with self.assertRaisesRegex(ValueError, "organization_receipt_refused:FAIL_CLOSED:ORGANIZATION_RECEIPT_SHA256_ABSENT"):
            mod._assemble_purpose_result(request(), receipt)

    def test_complete_return_preserves_no_continued_authority(self):
        result = mod._assemble_purpose_result(request(), purpose_receipt(replay=True))
        self.assertEqual(result["state"], "COMPLETE")
        self.assertTrue(result["terminal_state"]["records_only"])
        self.assertFalse(result["terminal_state"]["continued_authority"])
        self.assertFalse(result["terminal_state"]["worker_live_after_close"])
        self.assertEqual(len(result["transition_closures"]), 7)


if __name__ == "__main__":
    unittest.main()
