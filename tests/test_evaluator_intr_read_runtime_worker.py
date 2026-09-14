from __future__ import annotations
import importlib.util, json, os, tempfile
from pathlib import Path
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("evaluator_intr_read_runtime_worker",ROOT/"workers/evaluator_intr_read_runtime_worker.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class EvaluatorInTrReadRuntimeWorkerTests(unittest.TestCase):
    def invocation(self):
        return {
            "schema":"stegverse.worker-invocation/v0.1",
            "task":{"task_id":mod.TASK_ID,"worker_id":mod.WORKER_ID,"claim_id":"c1","heartbeat_timing":{"fencing_token":44}},
            "handoff":{"authority":{"credential_authority":"TV/TVC","github_token_required":False,"non_tv_tvc_secret_or_token_allowed":False,"heartbeat_grants_execution_authority":False}}
        }
    def test_valid_invocation_requires_fence_and_preserves_authority(self):
        task=mod.validate_invocation(self.invocation())
        self.assertEqual(task["claim_id"],"c1")
    def test_missing_route_config_is_machine_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            prior=os.environ.get(mod.CONFIG_ENV)
            os.environ[mod.CONFIG_ENV]=str(Path(td)/"missing.json")
            try:
                with self.assertRaises(mod.RoutePending):
                    mod.load_config()
            finally:
                if prior is None: os.environ.pop(mod.CONFIG_ENV,None)
                else: os.environ[mod.CONFIG_ENV]=prior
    def test_public_route_requires_tls_material(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            for name in ("Site","StegOS","runtime"): (base/name).mkdir()
            cfg=base/"route.json"
            cfg.write_text(json.dumps({
                "site_root":str(base/"Site"),"stegos_root":str(base/"StegOS"),"runtime_root":str(base/"runtime"),
                "host":"0.0.0.0","port":8765,"allowed_origin":"https://stegverse.org","boundary_identity_ref":"node:1",
                "credential_authority":"TV/TVC","github_token_runtime_authority":"NONE"
            }))
            prior=os.environ.get(mod.CONFIG_ENV); os.environ[mod.CONFIG_ENV]=str(cfg)
            try:
                with self.assertRaises(mod.RoutePending):
                    mod.load_config()
            finally:
                if prior is None: os.environ.pop(mod.CONFIG_ENV,None)
                else: os.environ[mod.CONFIG_ENV]=prior

    def test_existing_round_trip_bundle_terminalizes_without_starting_receiver(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"; runtime.mkdir()
            receipt_root=runtime/"receipts/sovereign-network/evaluator-intr"; receipt_root.mkdir(parents=True)
            bundle=receipt_root/"observed.json"
            bundle.write_text(json.dumps({"state":"READ_REVIEW_ROUND_TRIP_FORWARDED"})+"\n",encoding="utf-8")
            config={"runtime_root":str(runtime)}
            result=mod.ensure_callable(config,base/"server.py")
            self.assertEqual(result["state"],"COMPLETE")
            self.assertEqual(result["transition_id"],"EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED")
            self.assertEqual(result["receipt_bundle_ref"],str(bundle))
            self.assertTrue(result["event_triggered"])
            self.assertFalse(result["persistent_receiver"])
            self.assertFalse(result["always_on_application_receiver_required"])

    def test_event_receiver_start_returns_callable_not_persistent(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"; runtime.mkdir()
            for name in ("Site","StegOS"): (base/name).mkdir()
            server=base/"server.py"; server.write_text("# server\n",encoding="utf-8")
            config={
                "runtime_root":str(runtime),"site_root":str(base/"Site"),"stegos_root":str(base/"StegOS"),
                "host":"127.0.0.1","port":8765,"allowed_origin":"https://stegverse.org",
                "boundary_identity_ref":"node:1","public_tls_terminated_by":"STEGVERSE_SHARED_SERVICE_GATEWAY"
            }
            class P:
                pid=4242
            with mock.patch.object(mod.subprocess,"Popen",return_value=P()) as popen, \
                 mock.patch.object(mod,"_pid_alive",return_value=True), \
                 mock.patch.object(mod,"_readiness",return_value={
                     "state":"READY","transport":"InTr","credential_authority":"TV/TVC","github_token_runtime_authority":"NONE"
                 }):
                result=mod.ensure_callable(config,server)
            self.assertEqual(result["state"],"CALLABLE")
            self.assertEqual(result["transition_id"],"EVALUATOR_INTR_EVENT_RECEIVER_CALLABLE")
            self.assertTrue(result["event_triggered"])
            self.assertEqual(result["max_requests"],1)
            self.assertFalse(result["persistent_receiver"])
            self.assertFalse(result["always_on_application_receiver_required"])
            self.assertFalse(result["round_trip_observed"])
            args=popen.call_args.args[0]
            self.assertIn("--max-requests",args)
            self.assertEqual(args[args.index("--max-requests")+1],"1")
            self.assertNotIn("0",args[args.index("--max-requests"):args.index("--max-requests")+2])

    def test_existing_live_event_receiver_is_reused_without_second_listener(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)
            runtime=base/"runtime"; runtime.mkdir()
            root=runtime/"receipts/sovereign-network/evaluator-intr"; root.mkdir(parents=True)
            latest=root/"event-receiver.latest.json"
            latest.write_text(json.dumps({
                "schema":"stegverse.evaluator-intr-event-callability/v1","state":"CALLABLE",
                "transition_id":"EVALUATOR_INTR_EVENT_RECEIVER_CALLABLE","pid":4242,
                "event_triggered":True,"persistent_receiver":False,
                "always_on_application_receiver_required":False
            })+"\n",encoding="utf-8")
            config={"runtime_root":str(runtime),"host":"127.0.0.1","port":8765}
            with mock.patch.object(mod,"_pid_alive",return_value=True), \
                 mock.patch.object(mod,"_readiness",return_value={"state":"READY"}), \
                 mock.patch.object(mod.subprocess,"Popen") as popen:
                result=mod.ensure_callable(config,base/"server.py")
            self.assertEqual(result["state"],"CALLABLE")
            popen.assert_not_called()

    def test_hosted_execution_fails_closed(self):
        inv=self.invocation()
        prior=os.environ.get("GITHUB_ACTIONS"); os.environ["GITHUB_ACTIONS"]="true"
        try:
            with self.assertRaises(RuntimeError):
                mod.execute(inv)
        finally:
            if prior is None: os.environ.pop("GITHUB_ACTIONS",None)
            else: os.environ["GITHUB_ACTIONS"]=prior

if __name__=="__main__": unittest.main()
