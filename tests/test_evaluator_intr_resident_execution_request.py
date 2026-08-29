from __future__ import annotations
import importlib.util, json, tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("consume_eval",ROOT/"scripts/consume_evaluator_intr_resident_execution_request.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class EvaluatorResidentRequestTests(unittest.TestCase):
    def request(self):
        return {
          "schema":"stegverse.resident-execution-request/v1","request_id":"r1","state":"REQUESTED",
          "task_id":mod.TARGET_TASK,"mode":mod.TARGET_MODE,"entrypoint":mod.TARGET_ENTRYPOINT,
          "credential_authority":"TV/TVC","credential_requirement":"NONE_FOR_PUBLIC_READ",
          "github_token_required":False,"github_token_runtime_authority":"NONE",
          "heartbeat_grants_execution_authority":False,"second_machine_required":False,
          "network_source_fetch_allowed":False,"request_granted_authority":False,"authority_effect":"NONE_REQUEST_ONLY"
        }

    def setup_runtime(self, base:Path):
        source=base/"source"; runtime=base/"runtime"; source.mkdir(); runtime.mkdir()
        p=runtime/mod.REQUEST_REL; p.parent.mkdir(parents=True); p.write_text(json.dumps(self.request())+"\n")
        (runtime/"scripts").mkdir(exist_ok=True)
        (runtime/mod.MATERIALIZER).write_text("# materializer\n")
        (runtime/mod.TARGET_ENTRYPOINT).write_text("# entrypoint\n")
        return source,runtime

    def test_predicate_pending_is_not_terminally_consumed(self):
        with tempfile.TemporaryDirectory() as td:
            source,runtime=self.setup_runtime(Path(td))
            calls=[]
            def runner(command,**kwargs):
                calls.append(command)
                if Path(command[1]).name=="materialize_evaluator_intr_route_config.py":
                    return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"PREDICATE_PENDING","reason":"local Site source root unavailable"})+"\n",stderr="")
                raise AssertionError("target execution must not run while predicate pending")
            receipt=mod.consume(source,runtime,runner=runner,env={"PATH":"/bin","HOME":td})
            self.assertEqual(receipt["state"],"PREDICATE_PENDING")
            self.assertFalse(receipt["runtime_execution_attempted"])
            self.assertFalse(receipt["terminal_round_trip_observed"])
            self.assertFalse(mod.terminally_consumed(runtime,self.request(),mod.stable_hash(self.request())))

    def test_terminal_round_trip_is_consumed_once(self):
        with tempfile.TemporaryDirectory() as td:
            source,runtime=self.setup_runtime(Path(td))
            def runner(command,**kwargs):
                if Path(command[1]).name=="materialize_evaluator_intr_route_config.py":
                    return SimpleNamespace(returncode=0,stdout=json.dumps({"state":"MATERIALIZED","path":"/tmp/config"})+"\n",stderr="")
                result={"transition_id":"EVALUATOR_INTR_READ_ROUND_TRIP_OBSERVED"}
                return SimpleNamespace(returncode=0,stdout=json.dumps(result)+"\n",stderr="")
            receipt=mod.consume(source,runtime,runner=runner,env={"PATH":"/bin","HOME":td})
            self.assertEqual(receipt["state"],"COMPLETED")
            self.assertTrue(receipt["terminal_round_trip_observed"])
            second=mod.consume(source,runtime,runner=lambda *a,**k: (_ for _ in ()).throw(AssertionError("must not rerun")),env={"PATH":"/bin","HOME":td})
            self.assertEqual(second["state"],"ALREADY_CONSUMED")

    def test_request_rejects_authority_drift(self):
        bad=self.request(); bad["github_token_required"]=True
        with self.assertRaises(RuntimeError): mod.validate_request(bad)

if __name__=="__main__": unittest.main()
