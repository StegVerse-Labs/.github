"""Source-only checks for the existing admitted ephemeral diagnostic consumer.

ALL positive test callbacks are doubles: test success MUST NOT be interpreted
as actual Interlock/InTr, TV/TVC, sovereign organization or Master Records proof.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workers import sdk_manifest_diagnostic_admitted_consumer as mod


def request() -> dict:
    manifest = {
        "payload": {
            "goal_task_id": mod.GOAL,
            "cosv": mod.COSV,
        },
        "completion": {"publisher": {"required": True}},
    }
    return {
        "schema": "stegverse.sdk.manifest-state-transition-request/v1",
        "processing_capability": "ecosystem_diagnostic",
        "route_id": "stegverse.route.ecosystem-diagnostic.v1",
        "canonical_task_id": None,
        "requires_workercoordinator_claim_fence": False,
        "canonical_manifest": manifest,
        "wire_manifest_sha256": mod.sha256(manifest),
        "canonical_manifest_sha256": "9" * 64,
        "graph_id": "RTC-GOVERNED-PROCESSING-002:ECOSYSTEM_DIAGNOSTIC",
        "state_graph": {"request": {"diagnostic_request_id": "exp3-source-only-test"}},
        "request_sha256": "8" * 64,
    }


def setup(root: Path, source: dict, *, tamper: bool = False):
    ephemeral = root / "existing-ephemeral-runtime"
    ephemeral.mkdir()
    sdk = root / "installed-sdk"
    (sdk / "stegverse").mkdir(parents=True)
    (sdk / "stegverse/ecosystem_diagnostic_cli.py").write_text("# source-only test\n")
    (sdk / "stegverse/manifest_contract.py").write_text("# source-only test\n")
    binding_digest, ingress_digest = "b" * 64, "a" * 64
    ingress = {
        "transition_id": "STEGCORE_INTR_MATERIALIZATION_ADMITTED",
        "transition_outcome": "ALLOW",
        "prior_state_ref_or_hash": None,
        "transition_evidence": {
            "request_sha256": source["request_sha256"],
            "wire_manifest_sha256": source["wire_manifest_sha256"],
        },
    }
    binding = {
        "transition_id": mod.BINDING_TRANSITION,
        "transition_outcome": "OBSERVED",
        "transition_sequence": 2,
        "prior_state_ref_or_hash": "sha256:" + ingress_digest,
        "transition_evidence": {
            "runtime_binding": {
                "runtime_class": "CONTINUOUS" if tamper else "EVENT_EPHEMERAL",
                "lease_state": "LEASE_OPEN",
                "goal_task_id": mod.GOAL,
                "cosv": mod.COSV,
                "request_sha256": source["request_sha256"],
                "wire_manifest_sha256": source["wire_manifest_sha256"],
                "node_id": "SV-NODE-source-fixture",
                "interlock_id": "SV-IL-source-fixture",
                "lease_id": "lease-fixture",
                "runtime_id": "runtime-fixture",
                "runtime_root": str(ephemeral),
            },
        },
    }
    mock_receipts = {binding_digest: binding, ingress_digest: ingress}
    def reconstruct(digest: str):
        record = mock_receipts[digest]
        return {
            "state": "PASS",
            "required_evidence_validation_status": "PASS",
            "receipt_sha256": digest,
            "reconstructed_receipt_sha256": digest,
            "receipt": record,
        }
    locator = root / mod.ADMITTED_REL / (source["request_sha256"] + ".json")
    locator.parent.mkdir(parents=True)
    locator.write_text(json.dumps({
        "schema": "stegverse.sdk.admitted-ephemeral-receipt-locator/v1",
        "request_sha256": source["request_sha256"],
        "wire_manifest_sha256": source["wire_manifest_sha256"],
        "intr_admission_receipt_sha256": ingress_digest,
        "runtime_binding_receipt_sha256": binding_digest,
    }))
    return sdk, reconstruct


class AdmittedDiagnosticConsumerSourceTests(unittest.TestCase):
    def test_no_admitted_runtime_is_exact_predicate_not_a_worker_claim(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(mod.DiagnosticAdmissionError,
                                        "AUTHENTIC_EVENT_EPHEMERAL_BINDING_LOCATOR_REQUIRED"):
                mod.consume(Path(td), Path(td), request())
            self.assertFalse((Path(td) / "receipts/sdk-manifest-state-transition").exists())

    def test_reconstructed_wrong_runtime_class_rejected_before_processor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = request()
            sdk, reconstruct = setup(root, source, tamper=True)
            with patch.dict(os.environ, {"STEGVERSE_REPO_ROOTS_JSON": "{}",
                                          "STEGVERSE_SDK_ROOT": str(sdk)}):
                with self.assertRaisesRegex(mod.DiagnosticAdmissionError,
                                           "ADMITTED_NODE_INTERLOCK_LEASE_RUNTIME_CORRELATION_REQUIRED"):
                    mod.consume(root, root, source, reconstruct=reconstruct)

    def test_mocked_positive_composition_remains_simulation_not_authentic_allow(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = request()
            sdk, reconstruct = setup(root, source)
            exact_bytes = (json.dumps(source["canonical_manifest"], indent=2,
                                      sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
            fixture_sha = hashlib.sha256(exact_bytes).hexdigest()
            def fake_run(argv, **kwargs):
                self.assertEqual(argv[2], "stegverse.ecosystem_diagnostic_cli")
                self.assertEqual(kwargs["env"]["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"], "NONE")
                self.assertNotIn("GITHUB_TOKEN", kwargs["env"])
                output = Path(argv[argv.index("--output") + 1])
                output.write_text(json.dumps({
                    "schema": "stegverse.ecosystem-diagnostic-result.v1",
                    "processing_capability": "ecosystem_diagnostic",
                    "route_id": source["route_id"],
                    "authority_effect": "NONE_DIAGNOSTIC_ONLY",
                    "mutation_performed": False,
                    "diagnostic_request_id": "exp3-source-only-test",
                }))
                return type("SourceTestProcess", (), {"returncode": 0})()
            def fake_submit(record):
                self.assertEqual(record["transition_outcome"], "EXECUTED")
                self.assertEqual(record["transition_evidence"]["publisher_executed"], False)
                return {
                    "state": "RECORDED", "reconstruction_status": "PASS",
                    "required_evidence_validation_status": "PASS",
                    "receipt_sha256": "c" * 64,
                    "reconstructed_receipt_sha256": "c" * 64,
                    "organization_previous_receipt_sha256": "d" * 64,
                }
            with patch.dict(os.environ, {"STEGVERSE_REPO_ROOTS_JSON": "{}",
                                          "STEGVERSE_SDK_ROOT": str(sdk)}), \
                 patch.object(mod, "FROZEN_FILE_SHA256", fixture_sha):
                result = mod.consume(root, root, source, reconstruct=reconstruct,
                                     runner=fake_run, submit=fake_submit)
            self.assertEqual(result["state"], "SOURCE_SIMULATION_ONLY")
            self.assertEqual(result["disposition"], "SIMULATED")
            self.assertFalse(result["authentic_intr_disposition_observed"])
            self.assertFalse(result["organization_master_records_closure_observed"])


    def test_historical_lease_open_without_current_native_expiration_cannot_run(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(
                mod.DiagnosticAdmissionError,
                "CURRENT_EVENT_EPHEMERAL_LEASE_EXPIRY_REQUIRED",
            ):
                mod._verify_current_native_lease(
                    Path(__file__).resolve().parents[1],
                    Path(td),
                    {"lease_state": "LEASE_OPEN", "lease_id": "historic", "runtime_id": "old"},
                )

    def test_expired_or_invalid_native_lease_deadline_rejected_before_processor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for deadline, predicate in (
                ("2020-01-01T00:00:00Z", "CURRENT_EVENT_EPHEMERAL_LEASE_EXPIRED"),
                ("non-dateZ", "CURRENT_EVENT_EPHEMERAL_LEASE_EXPIRY_INVALID"),
            ):
                with self.subTest(deadline=deadline):
                    with self.assertRaisesRegex(mod.DiagnosticAdmissionError, predicate):
                        mod._verify_current_native_lease(
                            Path(__file__).resolve().parents[1],
                            root,
                            {"lease_expires_at": deadline, "lease_id": "old", "runtime_id": "historic"},
                        )

    def test_future_deadline_still_requires_native_lease_snapshot(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(
                mod.DiagnosticAdmissionError,
                "CURRENT_EVENT_EPHEMERAL_LEASE_SNAPSHOT_REQUIRED",
            ):
                mod._verify_current_native_lease(
                    Path(__file__).resolve().parents[1],
                    Path(td),
                    {"lease_expires_at": "2099-01-01T00:00:00Z",
                     "lease_state": "LEASE_OPEN", "lease_id": "historic"},
                )

    def test_existing_private_ledger_absent_is_not_a_runtime_deny(self):
        with tempfile.TemporaryDirectory() as td:
            source = request()
            with patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(Path(td) / "no-ledger")}):
                self.assertIsNone(mod._read_existing_authenticated_locator(
                    mod.Path(__file__).resolve().parents[1], Path(td), source))
            self.assertFalse((Path(td) / mod.ADMITTED_REL / (source["request_sha256"] + ".json")).exists())

    def test_original_ledger_and_exact_master_records_readback_only_with_source_test_double(self):
        import importlib
        import sys
        runtime_source = Path(__file__).resolve().parents[1] / "resident-runtime"
        if str(runtime_source) not in sys.path:
            sys.path.insert(0, str(runtime_source))
        org = importlib.import_module("aggregate_repo_transition")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = request()
            ledger = root / "original-org-ledger"
            ingress = {
                "schema": "stegverse.canonical-state-transition-receipt/v1",
                "transition_id": "SDK_MANIFEST_INTR_ADMITTED",
                "transition_outcome": "ALLOW",
                "prior_state_ref_or_hash": None,
                "transition_evidence": {
                    "request_sha256": source["request_sha256"],
                    "wire_manifest_sha256": source["wire_manifest_sha256"],
                },
                "required_evidence_manifest": [],
            }
            ingress_hash = org.sha(ingress)[7:]
            runtime_binding = {
                "schema": "stegverse.canonical-state-transition-receipt/v1",
                "transition_id": mod.BINDING_TRANSITION,
                "transition_outcome": "OBSERVED",
                "prior_state_ref_or_hash": "sha256:" + ingress_hash,
                "transition_evidence": {"runtime_binding": {
                    "request_sha256": source["request_sha256"],
                    "wire_manifest_sha256": source["wire_manifest_sha256"],
                    "runtime_class": "EVENT_EPHEMERAL",
                    "lease_state": "LEASE_OPEN",
                    "lease_id": "fixture-lease",
                }},
                "required_evidence_manifest": [],
            }
            binding_hash = org.sha(runtime_binding)[7:]
            records = {ingress_hash: ingress, binding_hash: runtime_binding}
            def fake_master_records_reconstruction(digest):
                value = records[digest]
                return {
                    "state": "PASS",
                    "required_evidence_validation_status": "PASS",
                    "receipt_sha256": digest,
                    "reconstructed_receipt_sha256": digest,
                    "receipt": value,
                }
            with patch.dict(os.environ, {"STEGVERSE_ORG_LEDGER_ROOT": str(ledger)}):
                org.aggregate_transition(ingress)
                org.aggregate_transition(runtime_binding)
                result = mod._read_existing_authenticated_locator(
                    Path(__file__).resolve().parents[1], root, source,
                    reconstruct=fake_master_records_reconstruction)
                self.assertEqual(result["intr_admission_receipt_sha256"], ingress_hash)
                self.assertEqual(result["runtime_binding_receipt_sha256"], binding_hash)
                self.assertTrue(result["source_simulation_only"])
                self.assertFalse((root / mod.ADMITTED_REL / (source["request_sha256"] + ".json")).exists())
                mod._require_current_organization_lease_status(
                    Path(__file__).resolve().parents[1],
                    binding_hash,
                    {"request_sha256": source["request_sha256"], "lease_id": "fixture-lease"},
                )
                revoked = {
                    "schema": "stegverse.canonical-state-transition-receipt/v1",
                    "transition_id": "EVENT_EPHEMERAL_LEASE_REVOKED",
                    "transition_outcome": "DENY",
                    "prior_state_ref_or_hash": "sha256:" + binding_hash,
                    "transition_evidence": {
                        "request_sha256": source["request_sha256"],
                        "lease_id": "fixture-lease",
                        "lease_state": "REVOKED",
                    },
                    "required_evidence_manifest": [],
                }
                org.aggregate_transition(revoked)
                with self.assertRaisesRegex(
                    mod.DiagnosticAdmissionError,
                    "CURRENT_EVENT_EPHEMERAL_LEASE_REVOKED_OR_ALREADY_CONSUMED",
                ):
                    mod._require_current_organization_lease_status(
                        Path(__file__).resolve().parents[1],
                        binding_hash,
                        {"request_sha256": source["request_sha256"], "lease_id": "fixture-lease"},
                    )
                # Tamper with the original private organization HEAD; the
                # existing exact-chain verifier must reject it before selection.
                head_path = ledger / "HEAD.json"
                head = json.loads(head_path.read_text())
                head["receipt_sha256"] = "sha256:" + "f" * 64
                head_path.write_text(json.dumps(head))
                with self.assertRaisesRegex(mod.DiagnosticAdmissionError, "ORGANIZATION_HEAD_EXACT_PREDECESSOR_READBACK_FAILED"):
                    mod._read_existing_authenticated_locator(
                        Path(__file__).resolve().parents[1], root, source,
                        reconstruct=fake_master_records_reconstruction)


if __name__ == "__main__":
    unittest.main()
