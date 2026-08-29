from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
import os

from workers import cmc028_root_custody_worker as worker


def invocation() -> dict:
    return {
        "schema":"stegverse.worker-invocation/v0.1",
        "heartbeat_epoch":41,
        "task":{
            "task_id":worker.TASK_ID,
            "claim_id":"SHWP-CMC028-ROOT-CUSTODY-EVIDENCE-001-G41",
            "heartbeat_timing":{"fencing_token":41},
        },
        "handoff":{
            "execution":{
                "required_capabilities":[worker.CAPABILITY],
                "allowed_paths":["receipts/cmc028-root-custody/**"],
            }
        },
    }


class CMC028RootCustodyWorkerTests(unittest.TestCase):
    def test_hosted_runtime_blocks_before_source_or_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            out=io.StringIO()
            receipt=base/"receipts/cmc028-root-custody"/f"{worker.TASK_ID}.json"
            with mock.patch.object(worker,"ROOT",base),                  mock.patch.object(worker,"RECEIPT_PATH",receipt),                  mock.patch.object(worker.sys,"stdin",io.StringIO(json.dumps(invocation()))),                  mock.patch.object(worker.sys,"stdout",out),                  mock.patch.dict(os.environ,{"GITHUB_ACTIONS":"true"},clear=True),                  mock.patch.object(worker,"locate_tvc") as locate,                  mock.patch.object(worker.subprocess,"run") as run:
                self.assertEqual(worker.main(),0)
            locate.assert_not_called()
            run.assert_not_called()
            stored=json.loads(receipt.read_text())
            self.assertEqual(stored["state"],"BLOCKED")
            self.assertEqual(stored["result"]["reason"],"HOSTED_RUNTIME_PROHIBITED")
            self.assertFalse(stored["result"]["protected_material_read"])

    def test_missing_local_tvc_blocks_without_network_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            out=io.StringIO()
            receipt=base/"receipts/cmc028-root-custody"/f"{worker.TASK_ID}.json"
            with mock.patch.object(worker,"ROOT",base),                  mock.patch.object(worker,"RECEIPT_PATH",receipt),                  mock.patch.object(worker.sys,"stdin",io.StringIO(json.dumps(invocation()))),                  mock.patch.object(worker.sys,"stdout",out),                  mock.patch.dict(os.environ,{"HOME":str(base)},clear=True),                  mock.patch.object(worker,"locate_tvc",return_value=(None,[{"path":"/local/TVC","required_ancestor_present":False}])),                  mock.patch.object(worker.subprocess,"run") as run:
                self.assertEqual(worker.main(),0)
            run.assert_not_called()
            stored=json.loads(receipt.read_text())
            self.assertEqual(stored["result"]["reason"],"CURRENT_LOCAL_TVC_SOURCE_NOT_MATERIALIZED")
            self.assertFalse(stored["result"]["network_source_fetch_performed"])
            self.assertFalse(stored["result"]["source_mutation_performed"])

    def test_success_invokes_exact_dispatcher_and_exports_no_secret_env(self) -> None:
        result={
            "status":"ok",
            "result":{
                "state":"CUSTODY_RECOVERY_EVIDENCE_VERIFIED",
                "receipt_path":"/var/lib/stegverse/tvc/certificate-root-custody/latest.json",
                "key_id":"root-key-0001",
                "runtime_id":"resident-runtime-0001",
                "public_fingerprint":"sha256:"+"a"*64,
                "credential_authority":"TV/TVC",
                "protected_material_exported":False,
                "protected_material_read":False,
                "protected_material_hashed":False,
                "certificate_issuance_authority":False,
                "signing_authority_granted":False,
                "runtime_activation_claimed":False,
            },
        }
        proc=SimpleNamespace(returncode=0,stdout=json.dumps(result),stderr="")
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); tvc=base/"TVC"; tvc.mkdir()
            out=io.StringIO()
            receipt=base/"receipts/cmc028-root-custody"/f"{worker.TASK_ID}.json"
            env={"PATH":"/usr/bin:/bin","STEGVERSE_TVC_ROOT":str(tvc),"GITHUB_TOKEN":"forbidden","PRIVATE_KEY":"forbidden"}
            with mock.patch.object(worker,"ROOT",base),                  mock.patch.object(worker,"RECEIPT_PATH",receipt),                  mock.patch.object(worker.sys,"stdin",io.StringIO(json.dumps(invocation()))),                  mock.patch.object(worker.sys,"stdout",out),                  mock.patch.dict(os.environ,env,clear=True),                  mock.patch.object(worker,"locate_tvc",return_value=(tvc,[])),                  mock.patch.object(worker,"_git_head",return_value="f"*40),                  mock.patch.object(worker.subprocess,"run",return_value=proc) as run:
                self.assertEqual(worker.main(),0)
            args=run.call_args.args[0]
            self.assertEqual(args[-1],"tvc.certificate_root_custody.observe")
            child=run.call_args.kwargs["env"]
            self.assertNotIn("GITHUB_TOKEN",child)
            self.assertNotIn("PRIVATE_KEY",child)
            stored=json.loads(receipt.read_text())
            self.assertEqual(stored["state"],"COMPLETED")
            self.assertEqual(stored["result"]["reason"],"CMC028_CUSTODY_RECOVERY_EVIDENCE_RECORDED")
            self.assertFalse(stored["result"]["protected_material_read"])
            self.assertFalse(stored["result"]["protected_material_hashed"])
            self.assertFalse(stored["result"]["protected_material_exported"])

    def test_dispatcher_block_remains_blocked(self) -> None:
        proc=SimpleNamespace(
            returncode=2,
            stdout=json.dumps({"status":"blocked","result":{"state":"CMC028_RESIDENT_EVIDENCE_BLOCKED","reason":"runtime_locator_manifest_missing"}}),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); tvc=base/"TVC"; tvc.mkdir()
            out=io.StringIO()
            receipt=base/"receipts/cmc028-root-custody"/f"{worker.TASK_ID}.json"
            with mock.patch.object(worker,"ROOT",base),                  mock.patch.object(worker,"RECEIPT_PATH",receipt),                  mock.patch.object(worker.sys,"stdin",io.StringIO(json.dumps(invocation()))),                  mock.patch.object(worker.sys,"stdout",out),                  mock.patch.dict(os.environ,{"PATH":"/bin"},clear=True),                  mock.patch.object(worker,"locate_tvc",return_value=(tvc,[])),                  mock.patch.object(worker,"_git_head",return_value="f"*40),                  mock.patch.object(worker.subprocess,"run",return_value=proc):
                self.assertEqual(worker.main(),0)
            stored=json.loads(receipt.read_text())
            self.assertEqual(stored["state"],"BLOCKED")
            self.assertEqual(stored["result"]["reason"],"CMC028_RESIDENT_EVIDENCE_BLOCKED")
            self.assertFalse(stored["result"]["protected_material_exported"])

    def test_worker_source_has_no_source_fetch_or_key_content_read_path(self) -> None:
        source=Path(worker.__file__).read_text(encoding="utf-8")
        for forbidden in ("git clone","git fetch","git pull","urlopen(","requests.get","read_bytes(","open('/run/stegverse"):
            self.assertNotIn(forbidden,source)
        self.assertIn("tvc.certificate_root_custody.observe",source)
        self.assertIn("merge-base",source)


if __name__=="__main__":
    unittest.main()
