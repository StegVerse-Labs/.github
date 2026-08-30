from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from workers import sv_dn1_public_promotion_worker as worker


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n", encoding="utf-8")


class SvDn1PublicPromotionWorkerTests(unittest.TestCase):
    def invocation(self) -> dict:
        return {
            "schema": "stegverse.worker-invocation/v0.1",
            "task": {
                "task_id": worker.TASK_ID,
                "worker_id": worker.WORKER_ID,
                "claim_id": "claim-public",
                "heartbeat_timing": {"fencing_token": 31},
            },
        }

    def test_sdk_receipt_must_be_authentic_analyzed_and_unpublished(self) -> None:
        good = {
            "schema": "stegverse.sv-dn1.sdk-first-round-worker-receipt/v1",
            "state": "COMPLETE",
            "transition_id": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
            "first_round_analysis": "ANALYZED",
            "dashboard_generated": True,
            "dashboard_publicly_hosted": False,
            "repository_writeback_performed": False,
            "credential_used": False,
            "github_token_used": False,
            "authority_effect": "NONE",
        }
        worker.validate_sdk(good)
        bad = dict(good)
        bad["dashboard_publicly_hosted"] = True
        with self.assertRaises(worker.Pending):
            worker.validate_sdk(bad)

    def test_execute_preserves_exact_finalized_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            sdk = base / "sdk"
            demo = base / "demo"
            bound = base / "bound"
            finalized = sdk / "round"
            public = demo / "public/sv-dn1"
            finalized.mkdir(parents=True)
            (demo / "scripts").mkdir(parents=True)
            (demo / "docs").mkdir(parents=True)
            (demo / "docs/SV_DN1_AUTHENTIC_PUBLIC_PROMOTION_MIRROR_HANDOFF.md").write_text("handoff\n")
            write_json(sdk / "receipts/latest.json", {
                "schema": "stegverse.sv-dn1.sdk-first-round-worker-receipt/v1",
                "state": "COMPLETE",
                "transition_id": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
                "first_round_analysis": "ANALYZED",
                "dashboard_generated": True,
                "dashboard_publicly_hosted": False,
                "repository_writeback_performed": False,
                "credential_used": False,
                "github_token_used": False,
                "authority_effect": "NONE",
            })
            for name in worker.PROMOTED:
                (finalized / name).write_bytes((name + "\n").encode())
            promoter = demo / "scripts/promote_sv_dn1_public_result.py"
            promoter.write_text(
                "import argparse,json,pathlib,shutil\n"
                "a=argparse.ArgumentParser();a.add_argument('--finalized-dir');a.add_argument('--public-dir');a.add_argument('--receipt');x=a.parse_args();s=pathlib.Path(x.finalized_dir);d=pathlib.Path(x.public_dir);d.mkdir(parents=True,exist_ok=True);names=('first-round-analysis.json','production-pipeline-observation.json','result-receipt.json','report.md','index.html');import hashlib\n"
                "h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();[shutil.copyfile(s/n,d/n) for n in names];src={n:h(s/n) for n in names};dst={n:h(d/n) for n in names};r={'schema':'stegverse.sv-dn1.public-promotion-receipt/v1','state':'PROMOTION_READY_FOR_REPOSITORY_MUTATION','exchange_id':'ex','manifest_receipt_id':'mr','publication_state':'PUBLIC_OBSERVED','observation_class':'LIVE','source_artifact_sha256':src,'destination_artifact_sha256':dst,'exact_bytes_preserved':True,'semantic_rewrite_performed':False,'network_fetch_performed':False,'credential_used':False,'repository_writeback_performed':False,'deployment_performed':False,'authority_effect':'NONE_STATIC_PROJECTION_ONLY'};p=pathlib.Path(x.receipt);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r));print(json.dumps(r))\n"
            )
            with mock.patch.dict("os.environ", {
                worker.SDK_STATE_ENV: str(sdk),
                worker.DEMO_ROOT_ENV: str(demo),
                worker.BOUND_ENV: str(bound),
                "PATH": "/usr/bin",
            }, clear=True):
                receipt = worker.execute(self.invocation())
            self.assertEqual(receipt["transition_id"], "SV_DN1_PUBLIC_PROMOTION_READY")
            self.assertEqual(receipt["source_artifact_sha256"], receipt["destination_artifact_sha256"])
            self.assertFalse(receipt["repository_writeback_performed"])
            self.assertFalse(receipt["deployment_performed"])
            for name in worker.PROMOTED:
                self.assertEqual((finalized / name).read_bytes(), (public / name).read_bytes())

    def test_hosted_and_credential_environments_are_rejected(self) -> None:
        with mock.patch.dict("os.environ", {"GITHUB_ACTIONS": "true"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "hosted environment"):
                worker.execute(self.invocation())
        with mock.patch.dict("os.environ", {"GITHUB_TOKEN": "secret"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "credential-bearing"):
                worker.execute(self.invocation())


if __name__ == "__main__":
    unittest.main()
