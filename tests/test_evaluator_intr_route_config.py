from __future__ import annotations
import json, tempfile
from pathlib import Path
import unittest
from unittest import mock
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("materialize_eval",ROOT/"scripts/materialize_evaluator_intr_route_config.py")
assert SPEC and SPEC.loader
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class EvaluatorRouteConfigTests(unittest.TestCase):
    def test_materializes_loopback_nonsecret_config(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); site=base/"Site"; stegos=base/"StegOS"; runtime=base/"runtime"
            for p in (site,stegos,runtime): p.mkdir()
            node=base/"node.json"; node.write_text(json.dumps({"declared":True,"credential_authority":"TV/TVC","node_id":"node-1"}))
            out=base/"config.json"
            env={"STEGVERSE_SITE_ROOT":str(site),"STEGVERSE_STEGOS_ROOT":str(stegos),"STEGVERSE_HEARTBEAT_ROOT":str(runtime),"STEGVERSE_EVALUATOR_INTR_PORT":"8765"}
            with mock.patch.object(mod,"NODE_MARKERS",(node,)):
                result=mod.materialize(env,out)
            cfg=result["config"]
            self.assertEqual(cfg["host"],"127.0.0.1")
            self.assertEqual(cfg["public_tls_terminated_by"],"STEGVERSE_SHARED_SERVICE_GATEWAY")
            self.assertEqual(cfg["credential_authority"],"TV/TVC")
            self.assertFalse(cfg["second_machine_required"])
            self.assertNotIn("tls_key",cfg)
            self.assertTrue(out.is_file())

    def test_missing_site_root_is_retryable(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(mod.PredicatePending):
                mod.materialize({"STEGVERSE_HEARTBEAT_ROOT":td},Path(td)/"c.json")

if __name__=="__main__": unittest.main()
