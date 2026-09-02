import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("hb_presence",ROOT/"scripts/project_hb_runtime_presence.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class TestHBRuntimePresence(unittest.TestCase):
    def write(self,root,rel,value):
        path=root/rel; path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(value)+"\n",encoding="utf-8")

    def test_persistent_supervision_and_distinct_consumption(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            now=1_800_000_000.0
            self.write(root,"control/sovereign-node.json",{"node_id":"SV-NODE-abc"})
            self.write(root,"receipts/sovereign-host/activation.latest.json",{
                "active":True,"native_process_supervision_only":True,
                "carrier_active":True,"worker_active":True,"registration_kind":"systemd-user-separated"
            })
            self.write(root,"control/heartbeat-carrier-runtime-state.json",{
                "epoch":40,"generation":40,"reference_frame":"heartbeat_epoch:40",
                "oscillator":{"sampled_unix_ns":int((now-1)*1_000_000_000)}
            })
            self.write(root,"control/worker-runtime-state.json",{
                "runtime_tick":9,"last_cycle_at":"2027-01-15T07:59:59+00:00","observation_mode":"TASK_CAPABLE"
            })
            self.write(root,"control/worker-control-plane-coordination.json",{"worker_coordination":{"state":"ACTIVE"}})
            self.write(root,"control/resident-execution-request.d/x.json",{"request_id":"R1","task_id":"T1","state":"REQUESTED"})
            self.write(root,"receipts/sovereign-host/x-request-consumption.latest.json",{
                "request_id":"R1","task_id":"T1","state":"COMPLETED","runtime_execution_attempted":True,
                "execution_result":{"authorized_execution":True,"transition_id":"DONE"},
                "master_records_reconstruction":{"state":"PASS"}
            })
            out=mod.project(root,task_id="T1",max_age_seconds=120,now=now)
            self.assertTrue(out["resident"]["supervision_observed"])
            self.assertTrue(out["distinct_runtime_predicates"]["governed_request_consumed"])
            self.assertEqual(out["governed_request"]["execution_transition_observed"],"DONE")
            self.assertTrue(out["retained_evidence"]["reconstruction_observed"])
            self.assertFalse(out["authority"]["heartbeat_grants_execution_authority"])

    def test_bootstrap_files_do_not_equal_live_resident(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            self.write(root,"control/heartbeat-carrier-runtime-state.json",{"epoch":40,"generation":40,"last_cycle_at":"2026-01-01T00:00:00Z"})
            self.write(root,"control/worker-runtime-state.json",{"runtime_tick":1,"last_cycle_at":"2026-01-01T00:00:00Z"})
            out=mod.project(root,now=1_800_000_000.0)
            self.assertFalse(out["resident"]["supervision_observed"])
            self.assertFalse(out["distinct_runtime_predicates"]["resident_process_alive_supervised"])
            self.assertFalse(out["distinct_runtime_predicates"]["governed_request_consumed"])

if __name__=="__main__":
    unittest.main()
