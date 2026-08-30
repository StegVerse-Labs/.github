from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sv002_public_observation_runtime_worker",
    ROOT / "workers/sv002_public_observation_runtime_worker.py",
)
mod = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(mod)


def hop(receipt_id: str, *, transition: str, from_role: str, to_role: str, prior: str | None):
    body = {
        "schema": "stegverse.intr.hop_receipt/v1",
        "receipt_id": receipt_id,
        "packet_id": "INTR-" + "a" * 24,
        "hop_index": 1,
        "direction": "FORWARD",
        "from_role": from_role,
        "to_role": to_role,
        "operation_hash": "sha256:" + "b" * 64,
        "payload_hash": "sha256:" + "c" * 64,
        "prior_receipt_hash": prior,
        "boundary_identity_ref": "SV-NODE-" + "d" * 24,
        "boundary_verification": "VERIFIED",
        "transition_state": transition,
        "secret_plaintext_present": False,
        "authority_transfer": False,
        "recorded_at": "2026-08-30T04:00:00Z",
    }
    return {**body, "receipt_hash": mod._sha256_uri(body)}


def bundle():
    ingress = hop(
        "SV002-OBS-IN-" + "1" * 24,
        transition="RECEIVED",
        from_role="DEVICE_SYSTEM",
        to_role="STEGOS_ECOSYSTEM",
        prior=None,
    )
    egress = hop(
        "SV002-OBS-OUT-" + "2" * 24,
        transition="FORWARDED",
        from_role="STEGOS_ECOSYSTEM",
        to_role="DEVICE_SYSTEM",
        prior=ingress["receipt_hash"],
    )
    return {
        "schema": "stegverse.sv002-public-observation-runtime-receipt-bundle/v1",
        "state": "SV002_PUBLIC_OBSERVATION_ROUND_TRIP_FORWARDED",
        "observer_binding": {
            "node_id": "SV-NODE-" + "e" * 24,
            "interlock_id": "SV-IL-" + "f" * 24,
            "registration_receipt_sha256": "1" * 64,
        },
        "request_sha256": "2" * 64,
        "ingress_receipt": ingress,
        "egress_receipt": egress,
        "observer_direct_relation_to_stegverse_002": False,
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "recorded_at": "2026-08-30T04:00:00Z",
    }


class SV002PublicObservationRuntimeWorkerIntegrityTests(unittest.TestCase):
    def test_valid_round_trip_bundle_is_terminal_evidence(self):
        value = bundle()
        mod.validate_round_bundle(value)

    def test_tampered_ingress_hash_is_rejected(self):
        value = bundle()
        value["ingress_receipt"]["payload_hash"] = "sha256:" + "9" * 64
        with self.assertRaisesRegex(RuntimeError, "ingress receipt integrity"):
            mod.validate_round_bundle(value)

    def test_broken_egress_lineage_is_rejected(self):
        value = bundle()
        value["egress_receipt"]["prior_receipt_hash"] = "sha256:" + "8" * 64
        body = dict(value["egress_receipt"])
        body.pop("receipt_hash")
        value["egress_receipt"]["receipt_hash"] = mod._sha256_uri(body)
        with self.assertRaisesRegex(RuntimeError, "does not bind ingress"):
            mod.validate_round_bundle(value)

    def test_authority_or_direct_relation_smuggling_is_rejected(self):
        value = bundle()
        value["observer_direct_relation_to_stegverse_002"] = True
        with self.assertRaisesRegex(RuntimeError, "observer_direct_relation"):
            mod.validate_round_bundle(value)

        value = bundle()
        value["credential_authority"] = "OTHER"
        with self.assertRaisesRegex(RuntimeError, "credential_authority"):
            mod.validate_round_bundle(value)

    def test_terminal_looking_corrupt_file_cannot_terminalize_worker(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            root = runtime / "receipts/sovereign-network/sv002-public-observation"
            root.mkdir(parents=True)
            path = root / ("SV002-OBS-IN-" + "1" * 24 + ".json")
            value = bundle()
            value["ingress_receipt"]["receipt_hash"] = "sha256:" + "0" * 64
            path.write_text(json.dumps(value), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "ingress receipt integrity"):
                mod.existing_round({"runtime_root": str(runtime)})

    def test_valid_persisted_bundle_is_returned(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            root = runtime / "receipts/sovereign-network/sv002-public-observation"
            root.mkdir(parents=True)
            path = root / ("SV002-OBS-IN-" + "1" * 24 + ".json")
            path.write_text(json.dumps(bundle()), encoding="utf-8")
            self.assertEqual(mod.existing_round({"runtime_root": str(runtime)}), str(path))


if __name__ == "__main__":
    unittest.main()
