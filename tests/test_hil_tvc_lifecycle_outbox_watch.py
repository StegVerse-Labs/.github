from __future__ import annotations
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts import watch_hil_tvc_lifecycle_outbox as mod

class Clock:
    def __init__(self): self.t=0.0
    def now(self): return self.t
    def sleep(self,v): self.t+=v

class WatchTests(unittest.TestCase):
    def test_admission_terminates_watch(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td); p=runtime/mod.CONSUMER_REL; p.parent.mkdir(parents=True); p.write_text("#x\n")
            calls={"n":0}
            def runner(cmd,**kwargs):
                calls["n"]+=1
                state="NO_EVENT" if calls["n"]==1 else "ADMITTED_TO_TVC_HIL_LIFECYCLE"
                return subprocess.CompletedProcess(cmd,0,json.dumps({"state":state})+"\n","")
            clock=Clock()
            result=mod.watch(runtime,window_seconds=10,poll_seconds=1,runner=runner,env={},monotonic=clock.now,sleeper=clock.sleep)
            self.assertEqual(result["state"],"TVC_LIFECYCLE_ADMITTED")
            self.assertEqual(result["attempts"],2)
            self.assertTrue((runtime/mod.WATCH_RECEIPT_REL).is_file())

    def test_no_event_expires_without_authority_claim(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td); p=runtime/mod.CONSUMER_REL; p.parent.mkdir(parents=True); p.write_text("#x\n")
            def runner(cmd,**kwargs): return subprocess.CompletedProcess(cmd,0,json.dumps({"state":"NO_EVENT"})+"\n","")
            clock=Clock()
            result=mod.watch(runtime,window_seconds=2,poll_seconds=1,runner=runner,env={},monotonic=clock.now,sleeper=clock.sleep)
            self.assertEqual(result["state"],"LEASE_WINDOW_EXPIRED_NO_TVC_ADMISSION")
            self.assertEqual(result["authority_effect"],"NONE_EVENT_WATCH_ONLY")

    def test_consumer_fail_closed_stops_immediately(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td); p=runtime/mod.CONSUMER_REL; p.parent.mkdir(parents=True); p.write_text("#x\n")
            def runner(cmd,**kwargs): return subprocess.CompletedProcess(cmd,1,json.dumps({"state":"FAIL_CLOSED"})+"\n","")
            clock=Clock()
            result=mod.watch(runtime,window_seconds=10,poll_seconds=1,runner=runner,env={},monotonic=clock.now,sleeper=clock.sleep)
            self.assertEqual(result["state"],"FAIL_CLOSED")
            self.assertEqual(result["attempts"],1)

if __name__=="__main__": unittest.main()
