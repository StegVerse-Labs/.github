from __future__ import annotations
import json
import tempfile
from pathlib import Path
import unittest
from unittest import mock

from scripts import dispatch_resident_execution_requests as dispatch
from scripts import refresh_and_dispatch_resident_requests as refresh_dispatch
from scripts import consume_sv_dn1_publication_resident_request as consumer
from scripts import run_sv_dn1_publication_continuation as continuation


class SvDn1PublicationResidentContinuationTests(unittest.TestCase):
    def test_exact_selector_is_registered_and_isolated(self):
        selected=dispatch.select_consumers(("sv_dn1_publication",))
        self.assertEqual(selected,(("sv_dn1_publication","scripts/consume_sv_dn1_publication_resident_request.py"),))
        self.assertIn("sv_dn1_publication", refresh_dispatch.ALLOWED_TARGET_CONSUMERS)

    def test_nonsecret_locators_forward_without_credentials(self):
        env=refresh_dispatch.clean_exec_env({
            "PATH":"/usr/bin",
            "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT":"/tmp/persist",
            "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION":"/tmp/admission.json",
        })
        self.assertEqual(env["STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT"],"/tmp/persist")
        self.assertEqual(env["STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION"],"/tmp/admission.json")
        self.assertNotIn("GITHUB_TOKEN",env)
        self.assertNotIn("TVC_EPHEMERAL_GITHUB_TOKEN",env)

    def test_continuation_does_not_forward_generic_bound_state_root(self):
        env=continuation.clean_exec_env({
            "PATH":"/usr/bin",
            "STEGVERSE_BOUND_STATE_ROOT":"/tmp/shared",
            "STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT":"/tmp/persist",
            "STEGVERSE_TVC_SV_DN1_REPOSITORY_PERSISTENCE_ADMISSION":"/tmp/admission.json",
        })
        self.assertNotIn("STEGVERSE_BOUND_STATE_ROOT",env)
        self.assertEqual(env["STEGVERSE_SV_DN1_REPOSITORY_PERSISTENCE_STATE_ROOT"],"/tmp/persist")

    def test_publication_request_retries_until_terminal_completion(self):
        with tempfile.TemporaryDirectory() as td:
            runtime=Path(td)
            (runtime/consumer.REQUEST_REL).parent.mkdir(parents=True)
            request={
                "schema":"stegverse.resident-execution-request/v1",
                "request_id":"RESIDENT-EXEC-SV-DN1-PUBLICATION-001",
                "state":"REQUESTED",
                "task_id":consumer.TARGET_TASK,
                "mode":consumer.TARGET_MODE,
                "entrypoint":consumer.TARGET_ENTRYPOINT,
                "fresh_fence_minimum_exclusive":22,
                "credential_authority":"TV/TVC",
                "github_token_required":False,
                "github_token_runtime_authority":"NONE",
                "heartbeat_grants_execution_authority":False,
                "second_machine_required":False,
                "network_source_fetch_allowed":False,
                "request_granted_authority":False,
                "authority_effect":"NONE_REQUEST_ONLY",
            }
            (runtime/consumer.REQUEST_REL).write_text(json.dumps(request))
            rh=consumer.stable_hash(request)
            (runtime/consumer.CONSUMPTION_REL).parent.mkdir(parents=True,exist_ok=True)
            (runtime/consumer.CONSUMPTION_REL).write_text(json.dumps({
                "request_id":request["request_id"],
                "request_sha256":rh,
                "execution_result":{"state":"HANDOFF_READY","transition_id":"SV_DN1_PUBLICATION_STEP_NOT_TERMINAL"},
            }))
            self.assertFalse(consumer.previously_consumed(runtime,request,rh))
            (runtime/consumer.CONSUMPTION_REL).write_text(json.dumps({
                "request_id":request["request_id"],
                "request_sha256":rh,
                "execution_result":{"state":"COMPLETE","transition_id":"SV_DN1_PUBLICATION_CONTINUATION_COMPLETE"},
            }))
            self.assertTrue(consumer.previously_consumed(runtime,request,rh))

    def test_hosted_and_tvc_credential_env_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError,"hosted"):
            continuation.clean_exec_env({"GITHUB_ACTIONS":"true"})
        with self.assertRaisesRegex(RuntimeError,"credential-bearing"):
            continuation.clean_exec_env({"TVC_EPHEMERAL_GITHUB_TOKEN":"secret"})


if __name__=="__main__":
    unittest.main()
