from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("component011_scheduler", ROOT / "scripts/run_reusable_task_scheduler.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Component011CanonicalCOSVGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / ".github"
        self.runtime = self.root / "runtime"
        self.tvc = self.root / "TVC"
        self.source.mkdir(); self.runtime.mkdir(); self.tvc.mkdir()
        trigger = self.source / "scripts/trigger_reusable_task.py"
        trigger.parent.mkdir(); trigger.write_text("# existing trigger\n")
        self.task = "ECOSYSTEM-INGRESS-AI-BOUNDARIES-001"
        self.row = {
            "reusable_task_id": "RT-CANONICAL-WORK-PORTABLE-DISPATCH-001",
            "tracking_task_id": self.task,
            "cosv_task_vector": None,
            "cosv_binding_policy": "CANONICAL_INDEX_EXACT_EMITTED_ONLY",
            "repository": "StegVerse-Labs/.github",
            "enabled": True,
            "invocation_key": self.task,
            "retry_interval_minutes": 15,
            "max_attempts_per_slot": 4,
            "parameters": {"only_consumer":"ungoverned_ai_defensive_envelope","goal_task_id":self.task}
        }
        self.roots = {"StegVerse-Labs/.github":self.source, "StegVerse-Labs/TVC":self.tvc}
        self.now = datetime(2026,9,22,14,tzinfo=timezone.utc)

    def test_missing_cosv_is_bounded_without_invocation(self):
        with mock.patch.object(mod.subprocess,"run") as run:
            result=mod.execute_child(self.row,self.roots,self.runtime,self.now)
        run.assert_not_called()
        self.assertEqual(result["boundary"],"CANONICAL_COSV_NOT_EMITTED")
        self.assertFalse(result["slot_satisfied"])

    def test_exact_emitted_index_record_and_task_required(self):
        vector="10100000100000"  # fixture only; not asserted as the Goal's canonical vector
        vec_ref=f"control/task-vectors/{self.task}.json"
        index={"tasks":[{
            "task_id":self.task,"vector":vector,"vector_state":"EMITTED",
            "repository":"StegVerse-Labs/.github","source_state_vector_ref":vec_ref,
            "authority_effect":"NONE"
        }]}
        record={"task_id":self.task,"cosv_task_vector":vector,"source_state_vector_ref":vec_ref}
        vector_record={
            "identity":f"StegVerse-Labs/.github:task:{self.task}",
            "vector":vector,"vector_state":"EMITTED","authority_effect":"NONE"
        }
        for path,obj in [
            (self.source/"control/task-vector-index.json",index),
            (self.source/f"data/canonical-task-records/{self.task}.json",record),
            (self.source/vec_ref,vector_record),
        ]:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(obj))
        call=[]
        def runner(command,**kwargs):
            call.append((command,kwargs))
            p=self.runtime/"receipts/reusable-task"/(mod.slot_id(self.row["reusable_task_id"],self.now,self.task)+".latest.json")
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps({"state":"AUTOMATABLE_STEPS_EXHAUSTED"}))
            return mock.Mock(returncode=0)
        with mock.patch.object(mod.subprocess,"run",side_effect=runner):
            result=mod.execute_child(self.row,self.roots,self.runtime,self.now)
        self.assertEqual(result["state"],"COMPLETE")
        cmd,opts=call[0]
        self.assertEqual(cmd[cmd.index("--cosv-task-vector")+1],vector)
        self.assertEqual(cmd[cmd.index("--task-id")+1],self.task)
        self.assertEqual(opts["env"]["STEGVERSE_TVC_ROOT"],str(self.tvc))
        record["cosv_task_vector"]="99999999999999"
        (self.source/f"data/canonical-task-records/{self.task}.json").write_text(json.dumps(record))
        with mock.patch.object(mod.subprocess,"run") as blocked:
            # Fresh hour avoids treating the fixture's previous receipt as a current slot.
            result=mod.execute_child(self.row,self.roots,self.runtime,self.now.replace(hour=15))
        blocked.assert_not_called()
        self.assertEqual(result["boundary"],"CANONICAL_COSV_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
