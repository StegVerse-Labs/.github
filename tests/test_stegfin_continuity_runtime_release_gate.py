from __future__ import annotations

import hashlib
from pathlib import Path
import tempfile
import unittest

from workers.stegfin_continuity_carrier_worker import (
    EXPECTED_PROVIDER_ROUTE,
    RUNTIME_READY_STATE,
    validate_exact_tvc_source,
    validate_runtime_release_receipt,
)


def evidence(status_code: int, detail: str | None = None) -> dict:
    return {
        "status_code": status_code,
        "detail": detail,
        "content_type": "application/json",
        "body_sha256": "0" * 64,
        "body_bytes_observed": 0,
    }


def ready_receipt() -> dict:
    return {
        "schema": "stegverse.tvc.runtime_boundary_observation.v2",
        "state": RUNTIME_READY_STATE,
        "credential_authority": "TV/TVC",
        "provider_operation_route": EXPECTED_PROVIDER_ROUTE,
        "consumer_credential_supplied": False,
        "github_token_required": False,
        "provider_secret_used": False,
        "provider_secret_exported": False,
        "non_tv_tvc_secret_or_token_used": False,
        "protected_values_observed": False,
        "provider_operation_attempted": False,
        "wallet_contacted": False,
        "signed": False,
        "broadcast": False,
        "probes": {
            "ingress_get": evidence(405, "method_not_allowed"),
            "ingress_empty_post": evidence(503, "tvc_capability_unavailable"),
            "provider_get": evidence(405, "Method Not Allowed"),
            "provider_invalid_post": evidence(403, "unexpected request schema"),
        },
    }


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


class StegFinContinuityRuntimeReleaseGateTests(unittest.TestCase):
    def test_valid_runtime_release_receipt_passes(self) -> None:
        self.assertEqual(validate_runtime_release_receipt(ready_receipt()), [])

    def test_endpoint_presence_without_ready_state_cannot_release_worker(self) -> None:
        receipt = ready_receipt()
        receipt["state"] = "BLOCKED_PROVIDER_OPERATION_ROUTE_NOT_BOUND"
        failures = validate_runtime_release_receipt(receipt)
        self.assertTrue(any("observer state" in failure for failure in failures))

    def test_wrong_provider_route_cannot_release_worker(self) -> None:
        receipt = ready_receipt()
        receipt["provider_operation_route"] = "https://example.invalid/v1/provider-operation"
        failures = validate_runtime_release_receipt(receipt)
        self.assertTrue(any("canonical TVC route" in failure for failure in failures))

    def test_secret_or_consumer_credential_drift_cannot_release_worker(self) -> None:
        receipt = ready_receipt()
        receipt["consumer_credential_supplied"] = True
        receipt["provider_secret_used"] = True
        receipt["provider_secret_exported"] = True
        receipt["non_tv_tvc_secret_or_token_used"] = True
        failures = validate_runtime_release_receipt(receipt)
        self.assertTrue(any("consumer_credential_supplied" in failure for failure in failures))
        self.assertTrue(any("provider_secret_used" in failure for failure in failures))
        self.assertTrue(any("provider_secret_exported" in failure for failure in failures))
        self.assertTrue(any("non_tv_tvc_secret_or_token_used" in failure for failure in failures))

    def test_invalid_provider_request_must_reach_canonical_schema_rejection(self) -> None:
        receipt = ready_receipt()
        receipt["probes"]["provider_invalid_post"] = evidence(503, "provider_operation_runtime_unavailable:FileNotFoundError")
        failures = validate_runtime_release_receipt(receipt)
        self.assertTrue(any("canonical schema rejection" in failure for failure in failures))

    def test_ingress_fail_closed_proof_is_required(self) -> None:
        receipt = ready_receipt()
        receipt["probes"]["ingress_empty_post"] = evidence(200)
        failures = validate_runtime_release_receipt(receipt)
        self.assertTrue(any("ingress empty-POST" in failure for failure in failures))

    def test_wallet_authority_drift_cannot_release_worker(self) -> None:
        receipt = ready_receipt()
        receipt["wallet_contacted"] = True
        receipt["signed"] = True
        receipt["broadcast"] = True
        failures = validate_runtime_release_receipt(receipt)
        self.assertTrue(any("wallet_contacted" in failure for failure in failures))
        self.assertTrue(any("signed" in failure for failure in failures))
        self.assertTrue(any("broadcast" in failure for failure in failures))

    def test_exact_tvc_source_gate_accepts_only_expected_blob_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = b"canonical\n"
            path = root / "app" / "main.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(raw)
            expected = {"app/main.py": git_blob_sha1(raw)}
            self.assertEqual(validate_exact_tvc_source(root, expected), [])

    def test_exact_tvc_source_gate_rejects_drift_and_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "app" / "main.py"
            path.parent.mkdir(parents=True)
            path.write_bytes(b"drifted\n")
            expected = {
                "app/main.py": git_blob_sha1(b"canonical\n"),
                "tvc_provider_operation_broker.py": git_blob_sha1(b"broker\n"),
            }
            failures = validate_exact_tvc_source(root, expected)
            self.assertTrue(any("source drift" in failure for failure in failures))
            self.assertTrue(any("missing validated TVC source" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
