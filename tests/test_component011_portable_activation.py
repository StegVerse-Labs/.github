from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("component011_portable", ROOT / "scripts/refresh_and_dispatch_resident_requests.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Component011PortableActivationTests(unittest.TestCase):
    def test_exact_goal_selector_only(self):
        self.assertIn(mod.DEFENSIVE_CONSUMER, mod.ALLOWED_TARGET_CONSUMERS)
        good = {
            mod.REUSABLE_TASK_ID_ENV: mod.REUSABLE_CANONICAL_WORK_TASK_ID,
            mod.REUSABLE_TASK_PARAMETERS_ENV: json.dumps({
                "source_root": "/tmp/source", "runtime_root": "/tmp/runtime",
                "only_consumer": mod.DEFENSIVE_CONSUMER,
                "goal_task_id": mod.DEFENSIVE_GOAL,
            }),
        }
        self.assertEqual(mod.reusable_canonical_work_parameters(good)["goal_task_id"], mod.DEFENSIVE_GOAL)
        for wrong in (mod.DEFENSIVE_GOAL + "-OTHER", "HYGIENE-CAUSAL-ROOTS-001"):
            invalid = dict(good)
            parsed = json.loads(good[mod.REUSABLE_TASK_PARAMETERS_ENV])
            parsed["goal_task_id"] = wrong
            invalid[mod.REUSABLE_TASK_PARAMETERS_ENV] = json.dumps(parsed)
            with self.assertRaisesRegex(RuntimeError, "exact component-011"):
                mod.reusable_canonical_work_parameters(invalid)

    def test_existing_canonical_work_path_preserved(self):
        source = (ROOT / "scripts/refresh_and_dispatch_resident_requests.py").read_text()
        self.assertIn("normalized[\"only_consumer\"] != \"canonical_work_coordination\"", source)
        self.assertIn("goal task context requires canonical_work_coordination", source)
        self.assertIn('"STEGVERSE_TVC_ROOT"', source)

    def test_dispatch_visit_does_not_promote_missing_or_nonterminal_evidence(self):
        for complete in (False, True):
            with self.subTest(complete=complete), tempfile.TemporaryDirectory() as td:
                source, runtime = Path(td)/"source", Path(td)/"runtime"
                source.mkdir(); runtime.mkdir()
                dispatcher = runtime / mod.DISPATCHER_REL
                dispatcher.parent.mkdir(parents=True); dispatcher.write_text("# existing dispatcher\n")
                invocation = []
                payload = {
                    "schema": "stegverse.ungoverned-ai-defensive-envelope-request-consumption/v1",
                    "state": "COMPLETED" if complete else "ATTEMPT_RECORDED",
                    "task_id": mod.DEFENSIVE_GOAL,
                    "terminal": complete, "runtime_execution_attempted": True,
                    "bridge_contract_valid": True,
                }
                def runner(command, **kwargs):
                    invocation.append(command)
                    if complete:
                        consumed = runtime / mod.DEFENSIVE_CONSUMPTION_REL
                        consumed.parent.mkdir(parents=True, exist_ok=True)
                        consumed.write_text(json.dumps(payload))
                        bound = runtime / mod.DEFENSIVE_BOUNDARY_REL
                        bound.parent.mkdir(parents=True, exist_ok=True)
                        bound.write_text(json.dumps({
                            "schema":"stegverse.ungoverned-ai-defensive-envelope-resident-boundary/v1",
                            "task_id":mod.DEFENSIVE_GOAL,
                            "external_provider_observed":False,
                            "goal_runtime_completion_claimed":False,
                            "claim":{"claim_id":"sample-G1","fencing_token":1},
                            "probe":{"admitted_interaction":{
                                "decision":"ALLOW","consumed":True,"result_observed":42,
                                "filesystem_capability_exposed":False,
                                "network_capability_exposed":False,
                                "temporary_state_destroyed":True,
                            },"denied_interactions":[{"decision":"DENY","consumed":False,"consequence_reachable":False}]},
                            "governed_egress_disposition":"EVIDENCE_ONLY_NO_CONSEQUENTIAL_EGRESS_REQUESTED",
                        }))
                    result = {
                        "state":"DISPATCH_COMPLETE", "selection_scope":"EXACT_SELECTOR",
                        "selected_consumers":[mod.DEFENSIVE_CONSUMER], "consumer_count":1,
                        "current_goal_task_id":None,"goal_context_forwarded_to":None,
                        "outcomes":[{
                            "consumer":mod.DEFENSIVE_CONSUMER,"attempted":True,
                            "returncode":0,"result":payload,
                        }],
                    }
                    destination = runtime / mod.DISPATCH_RECEIPT_REL
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_text(json.dumps(result))
                    return SimpleNamespace(returncode=0, stdout="", stderr="")
                with mock.patch.object(mod,"refresh",return_value={
                    "network_fetch_performed":False,"credential_read_or_acquired":False,
                    "mutable_runtime_state_preserved":True,
                }):
                    result=mod.refresh_and_dispatch(source,runtime,
                        target_consumer=mod.DEFENSIVE_CONSUMER,
                        goal_task_id=mod.DEFENSIVE_GOAL,
                        runner=runner, env={"PATH":"/bin","HOME":td})
                self.assertEqual(len(invocation),1)
                self.assertEqual(invocation[0][invocation[0].index("--only-consumer")+1],mod.DEFENSIVE_CONSUMER)
                self.assertNotIn("--goal-task-id",invocation[0])
                self.assertEqual(result["exact_target_consumption_evidence_observed"],complete)
                self.assertEqual(result["state"],"REFRESH_AND_DISPATCH_COMPLETE" if complete else "REFRESH_COMPLETE_DISPATCH_INCOMPLETE")
                self.assertFalse(result["bridge_grants_execution_authority"])


if __name__ == "__main__":
    unittest.main()
