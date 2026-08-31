from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_intr_worker",
    ROOT / "workers/bootstrap_v1_intr_bundle_delivery_worker.py",
)
worker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(worker)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class BootstrapV1InTrDeliveryWorkerTests(unittest.TestCase):
    def test_invocation_requires_fresh_fence(self) -> None:
        invocation = {
            "schema": "stegverse.worker-invocation/v0.1",
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "claim-1",
                "heartbeat_timing": {"fencing_token": 23},
            },
            "handoff": {
                "authority": {
                    "credential_authority": "TV/TVC",
                    "github_token_required": False,
                    "non_tv_tvc_secret_or_token_allowed": False,
                    "heartbeat_grants_execution_authority": False,
                }
            },
        }
        self.assertEqual(worker.validate_invocation(invocation)["claim_id"], "claim-1")
        invocation["task"]["heartbeat_timing"]["fencing_token"] = 22
        with self.assertRaisesRegex(RuntimeError, "fencing"):
            worker.validate_invocation(invocation)

    def test_observed_delivery_requires_receipt_chain(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            runtime = Path(td)
            config = {"runtime_root": str(runtime)}
            path = runtime / "receipts/sovereign-network/bootstrap-v1-intr/request.json"
            value = {
                "state": "DELIVERY_FORWARDED",
                "transition_id": "BOOTSTRAP_V1_INTR_BUNDLE_DELIVERY_OBSERVED",
                "transport_profile": "stegverse.universal-intr.adjacent-hop/v1",
                "universal_intr_policy_id": "STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001",
                "credential_used": False,
                "github_token_used": False,
                "execution_authority": "NONE",
                "bundle_identity": "sha256:" + "a" * 64,
                "request_ingress_receipt": {"receipt_hash": "sha256:" + "1" * 64},
                "response_egress_receipt": {"prior_receipt_hash": "sha256:" + "1" * 64},
            }
            write_json(path, value)
            observed = worker.observed_delivery(config)
            self.assertEqual(observed["path"], str(path))
            value["response_egress_receipt"]["prior_receipt_hash"] = "sha256:" + "2" * 64
            write_json(path, value)
            with self.assertRaisesRegex(RuntimeError, "chain drift"):
                worker.observed_delivery(config)


if __name__ == "__main__":
    unittest.main()
