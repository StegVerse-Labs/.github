from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from workers import ara_graph_runtime_worker as worker


def invocation() -> dict:
    return {
        "schema": "stegverse.worker-invocation/v0.1",
        "heartbeat_epoch": 32,
        "task": {
            "task_id": worker.TASK_ID,
            "claim_id": "SHWP-ARA-GRAPH-RUNTIME-086-G32",
            "worker_id": "ara-graph-runtime-worker",
            "worker_instance_id": "ara-graph-runtime-worker-HB32-G32",
            "heartbeat_timing": {"fencing_token": 32},
        },
        "handoff": {
            "execution": {
                "required_capabilities": [worker.CAPABILITY],
                "allowed_paths": ["receipts/ara-graph-runtime/**"],
            },
        },
    }


class AraGraphRuntimeWorkerTests(unittest.TestCase):
    def test_hosted_runtime_blocks_before_tvc_discovery_or_execution(self) -> None:
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            receipt = base / "receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json"
            out = io.StringIO()
            with mock.patch.object(worker, "ROOT", base),                  mock.patch.object(worker, "HANDOFF_PATH", base / "handoff.json"),                  mock.patch.object(worker, "RECEIPT_PATH", receipt),                  mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))),                  mock.patch.object(worker.sys, "stdout", out),                  mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True),                  mock.patch.object(worker, "locate_tvc") as locate,                  mock.patch.object(worker.subprocess, "run") as run:
                self.assertEqual(worker.main(), 0)
            response = json.loads(out.getvalue())
            self.assertEqual(response["state"], "BLOCKED")
            stored = json.loads(receipt.read_text())
            self.assertEqual(stored["result"]["reason"], "HOSTED_RUNTIME_PROHIBITED")
            locate.assert_not_called()
            run.assert_not_called()

    def test_missing_current_local_tvc_remains_blocked_without_network_fetch(self) -> None:
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            receipt = base / "receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json"
            out = io.StringIO()
            with mock.patch.object(worker, "ROOT", base),                  mock.patch.object(worker, "RECEIPT_PATH", receipt),                  mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))),                  mock.patch.object(worker.sys, "stdout", out),                  mock.patch.dict(os.environ, {"HOME": str(base)}, clear=True),                  mock.patch.object(worker, "locate_tvc", return_value=(None, [{"path":"/local/TVC","required_ancestor_present":False}])),                  mock.patch.object(worker.subprocess, "run") as run:
                self.assertEqual(worker.main(), 0)
            response = json.loads(out.getvalue())
            self.assertEqual(response["state"], "BLOCKED")
            stored = json.loads(receipt.read_text())
            self.assertEqual(stored["result"]["reason"], "CURRENT_LOCAL_TVC_SOURCE_NOT_MATERIALIZED")
            self.assertFalse(stored["result"]["network_source_fetch_performed"])
            self.assertFalse(stored["result"]["source_mutation_performed"])
            run.assert_not_called()

    def test_preflight_block_never_invokes_execute_once(self) -> None:
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            tvc = base / "TVC"
            tvc.mkdir()
            receipt = base / "receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json"
            out = io.StringIO()
            blocked = SimpleNamespace(
                returncode=2,
                stdout=json.dumps({"status":"blocked","result":{"state":"BLOCKED","provider_operation_performed":False}}),
                stderr="",
            )
            with mock.patch.object(worker, "ROOT", base),                  mock.patch.object(worker, "RECEIPT_PATH", receipt),                  mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))),                  mock.patch.object(worker.sys, "stdout", out),                  mock.patch.dict(os.environ, {"PATH":"/usr/bin:/bin"}, clear=True),                  mock.patch.object(worker, "locate_tvc", return_value=(tvc, [])),                  mock.patch.object(worker, "_git_head", return_value="f"*40),                  mock.patch.object(worker.subprocess, "run", return_value=blocked) as run:
                self.assertEqual(worker.main(), 0)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(run.call_args.args[0][-1], "tvc.ara_graph.activation_preflight")
            response = json.loads(out.getvalue())
            self.assertEqual(response["state"], "BLOCKED")
            stored = json.loads(receipt.read_text())
            self.assertEqual(stored["result"]["reason"], "ARA_GRAPH_PREFLIGHT_BLOCKED")
            self.assertFalse(stored["result"]["provider_operation_performed"])

    def test_success_declares_authority_only_for_execute_once(self) -> None:
        inv = invocation()
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            tvc = base / "TVC"
            tvc.mkdir()
            receipt = base / "receipts/ara-graph-runtime/SHWP-ARA-GRAPH-RUNTIME-086.json"
            out = io.StringIO()
            request_hash = "a" * 64
            preflight = SimpleNamespace(
                returncode=0,
                stdout=json.dumps({
                    "status":"ok",
                    "result":{
                        "state":"READY_FOR_RESIDENT_INTAKE",
                        "request_hash":request_hash,
                        "resident_intake_invoked":False,
                        "provider_operation_performed":False,
                    },
                }),
                stderr="",
            )
            execute = SimpleNamespace(
                returncode=0,
                stdout=json.dumps({
                    "status":"ok",
                    "result":{
                        "state":"PROVIDER_OPERATION_RESULT_RECORDED",
                        "request_hash":request_hash,
                        "operation_class":"ARA_DEPLOYMENT_MAILBOX_FETCH",
                        "provider_result_path":"/var/lib/stegverse/tvc/ara-graph/outbox/result.json",
                        "preflight_ready":True,
                        "resident_intake_invoked":True,
                        "provider_operation_result_recorded":True,
                        "credential_material_exported":False,
                        "provider_access_material_exported":False,
                        "runtime_activation_claimed":False,
                        "ara_release_authority_effect":"NONE",
                    },
                }),
                stderr="",
            )
            env = {
                "PATH":"/usr/bin:/bin",
                "STEGVERSE_ARA_MAIL_SENDER":"sender@example.invalid",
                "STEGVERSE_ARA_MAIL_RECIPIENT":"recipient@example.invalid",
            }
            with mock.patch.object(worker, "ROOT", base),                  mock.patch.object(worker, "RECEIPT_PATH", receipt),                  mock.patch.object(worker.sys, "stdin", io.StringIO(json.dumps(inv))),                  mock.patch.object(worker.sys, "stdout", out),                  mock.patch.dict(os.environ, env, clear=True),                  mock.patch.object(worker, "locate_tvc", return_value=(tvc, [])),                  mock.patch.object(worker, "_git_head", return_value="f"*40),                  mock.patch.object(worker.subprocess, "run", side_effect=[preflight, execute]) as run:
                self.assertEqual(worker.main(), 0)

            self.assertEqual(run.call_count, 2)
            first = run.call_args_list[0]
            second = run.call_args_list[1]
            self.assertEqual(first.args[0][-1], "tvc.ara_graph.activation_preflight")
            self.assertEqual(second.args[0][-1], "tvc.ara_graph.execute_once")
            self.assertNotIn(worker.AUTHORITY_ENV, first.kwargs["env"])
            self.assertEqual(second.kwargs["env"][worker.AUTHORITY_ENV], worker.AUTHORITY_VALUE)
            self.assertNotIn("GITHUB_TOKEN", second.kwargs["env"])

            response = json.loads(out.getvalue())
            self.assertEqual(response["state"], "COMPLETED")
            stored = json.loads(receipt.read_text())
            self.assertEqual(stored["result"]["reason"], "ARA_GRAPH_PROVIDER_OPERATION_RECORDED")
            self.assertEqual(stored["result"]["preflight_request_hash"], request_hash)
            self.assertEqual(stored["result"]["operation_class"], "ARA_DEPLOYMENT_MAILBOX_FETCH")
            self.assertFalse(stored["result"]["credential_material_exported"])
            self.assertFalse(stored["result"]["provider_access_material_exported"])

    def test_source_has_no_network_fetch_or_secret_read_path(self) -> None:
        source = Path(worker.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "git clone", "git fetch", "git pull", "urllib", "urlopen(", "requests.get",
            "STEGVERSE_MAIL_CLIENT_SECRET", "access_token", "refresh_token",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("merge-base", source)
        self.assertIn("tvc.ara_graph.activation_preflight", source)
        self.assertIn("tvc.ara_graph.execute_once", source)


if __name__ == "__main__":
    unittest.main()
