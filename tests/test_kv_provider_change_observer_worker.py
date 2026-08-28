from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workers import kv_provider_change_observer_worker as worker

class KVProviderChangeObserverTests(unittest.TestCase):
    def bindings(self,root:Path):
        targets=root/"targets.json"; state=root/"state"; state.mkdir()
        targets.write_text(json.dumps({
            "schema":"stegverse.kv.provider-monitor-targets/v1",
            "targets":[{
                "target_id":"coinbase-changelog","provider":"coinbase",
                "url":"https://docs.example.test/changelog","allowed_host":"docs.example.test",
                "source_type":"provider_changelog","change_class":"api_version",
                "severity":"MEDIUM","breaking_on_change":False,
                "affected_assumptions":["adapter_api_version"],"summary_on_change":"Synthetic change"
            }]
        }),encoding="utf-8")
        return {
            "STEGVERSE_KV_PROVIDER_MONITOR_TARGETS":str(targets),
            "STEGVERSE_KV_PROVIDER_MONITOR_STATE_ROOT":str(state)
        },state

    def test_hosted_surface_rejected(self):
        result=worker.execute({"GITHUB_ACTIONS":"true"})
        self.assertEqual(result["transition_id"],"HOSTED_SURFACE_REJECTED")

    def test_credential_environment_rejected(self):
        result=worker.execute({"GITHUB_TOKEN":"x"})
        self.assertEqual(result["transition_id"],"FORBIDDEN_CREDENTIAL_ENV")

    def test_http_target_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); env,state=self.bindings(root)
            p=Path(env["STEGVERSE_KV_PROVIDER_MONITOR_TARGETS"])
            value=json.loads(p.read_text()); value["targets"][0]["url"]="http://docs.example.test/changelog"; p.write_text(json.dumps(value))
            result=worker.execute(env,fetcher=lambda u,h:b"x")
        self.assertEqual(result["transition_id"],"TARGET_HTTPS_REQUIRED")

    def test_baseline_then_change_emits_observation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); env,state=self.bindings(root)
            fixed=lambda:"2026-08-28T16:00:00Z"
            first=worker.execute(env,fetcher=lambda u,h:b"v1",now=fixed)
            self.assertEqual(first["state"],"COMPLETED")
            self.assertEqual(first["emitted_change_count"],0)
            second=worker.execute(env,fetcher=lambda u,h:b"v2",now=lambda:"2026-08-28T17:00:00Z")
            self.assertEqual(second["emitted_change_count"],1)
            obs=list((state/"observations").glob("*.json"))
            self.assertEqual(len(obs),1)
            value=json.loads(obs[0].read_text())
            self.assertEqual(value["schema"],"stegverse.kv.source-change-observation/v1")
            self.assertEqual(value["provider"],"coinbase")
            self.assertEqual(value["authority_effect"],"NONE")
            self.assertFalse(second["provider_operation_authorized"])

    def test_unchanged_source_does_not_emit_change(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); env,state=self.bindings(root)
            worker.execute(env,fetcher=lambda u,h:b"same",now=lambda:"2026-08-28T16:00:00Z")
            result=worker.execute(env,fetcher=lambda u,h:b"same",now=lambda:"2026-08-28T17:00:00Z")
            self.assertEqual(result["emitted_change_count"],0)

if __name__=="__main__": unittest.main()
