from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workers import tvc_coinbase_intr_resident_activation_worker as worker


class TVCIntrActivationWorkerTests(unittest.TestCase):
    def test_hosted_surface_rejected(self):
        result=worker.execute({"GITHUB_ACTIONS":"true"})
        self.assertEqual(result["transition_id"],"HOSTED_SURFACE_REJECTED")
        self.assertFalse(result["provider_operation_authorized"])

    def test_non_root_surface_rejected(self):
        with patch.object(worker.os,"geteuid",return_value=1000):
            result=worker.execute({})
        self.assertEqual(result["transition_id"],"TVC_RESIDENT_ROOT_AUTHORITY_REQUIRED")

    def test_missing_stack_requires_both_nonsecret_storage_bindings(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for rel in (
                "scripts/activate_coinbase_intr_resident.py",
                "scripts/observe_coinbase_intr_resident_readiness.py",
                "scripts/observe_coinbase_service_gateway_route.py",
                "scripts/project_coinbase_owner_ingress_site_config.py",
                "scripts/execute_service_gateway_webpki_http01_029.py",
            ):
                p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("# test\n",encoding="utf-8")
            env={"STEGVERSE_TVC_ROOT":str(root)}
            with patch.object(worker.os,"geteuid",return_value=0), patch.object(worker,"_run",return_value=(2,{"state":"BLOCKED_RECIPIENT_KEY_NOT_PROVISIONED","reason":"resident SKAP recipient private key missing"},"")):
                result=worker.execute(env)
        self.assertEqual(result["transition_id"],"RESIDENT_STORAGE_BINDINGS_REQUIRED")

    def test_service_gateway_storage_alias_satisfies_gateway_binding(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            gateway=root/"gateway"; custody=root/"custody"; gateway.mkdir(); custody.mkdir()
            for rel in (
                "scripts/activate_coinbase_intr_resident.py",
                "scripts/observe_coinbase_intr_resident_readiness.py",
                "scripts/observe_coinbase_service_gateway_route.py",
                "scripts/project_coinbase_owner_ingress_site_config.py",
                "scripts/execute_service_gateway_webpki_http01_029.py",
            ):
                p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("# test\n",encoding="utf-8")
            calls=[]
            def fake_run(args,cwd,**kwargs):
                calls.append(args)
                joined=" ".join(str(x) for x in args)
                if "observe_coinbase_intr_resident_readiness.py" in joined:
                    return 2,{"state":"BLOCKED_RECIPIENT_KEY_NOT_PROVISIONED","reason":"resident SKAP recipient private key missing"},""
                if "activate_coinbase_intr_resident.py" in joined:
                    self.assertIn(str(gateway),joined)
                    self.assertIn(str(custody),joined)
                    return 0,{"provider_operation_started":False,"credential_values_provisioned":False},""
                raise AssertionError(joined)
            env={"STEGVERSE_TVC_ROOT":str(root),"STEGVERSE_SERVICE_GATEWAY_STORAGE_ROOT":str(gateway),"STEGVERSE_KV_CUSTODY_ROOT":str(custody)}
            with patch.object(worker.os,"geteuid",return_value=0), patch.object(worker,"_run",side_effect=fake_run):
                result=worker.execute(env)
        self.assertNotEqual(result["transition_id"],"RESIDENT_STORAGE_BINDINGS_REQUIRED")
        self.assertTrue(any("activate_coinbase_intr_resident.py" in " ".join(str(x) for x in call) for call in calls))

    def test_route_only_block_reuses_key_stack_and_projects_without_activation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for rel in (
                "scripts/activate_coinbase_intr_resident.py",
                "scripts/observe_coinbase_intr_resident_readiness.py",
                "scripts/observe_coinbase_service_gateway_route.py",
                "scripts/project_coinbase_owner_ingress_site_config.py",
                "scripts/execute_service_gateway_webpki_http01_029.py",
            ):
                p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("# test\n",encoding="utf-8")
            route=root/"route.json"; activation=root/"activation.json"; liveness=root/"liveness.json"; projection=root/"projection.json"
            calls=[]
            readiness_calls=0
            def fake_run(args,cwd,**kwargs):
                nonlocal readiness_calls
                calls.append(args)
                joined=" ".join(str(x) for x in args)
                if "observe_coinbase_intr_resident_readiness.py" in joined:
                    readiness_calls += 1
                    if readiness_calls == 1:
                        return 2,{"state":"BLOCKED_RESIDENT_BINDING_INVALID","reason":"current production public InTr route observation missing"},""
                    return 0,{"state":"READY_FOR_OWNER_INGRESS","ready_for_owner_ingress":True,"recipient_key_id":"k","runtime_instance_id":"r","public_intr_route_observation_digest":"sha256:"+"a"*64},""
                if "observe_coinbase_service_gateway_route.py" in joined:
                    route.write_text(json.dumps({"state":"OBSERVED"}),encoding="utf-8")
                    return 0,{"state":"OBSERVED"},""
                if "project_coinbase_owner_ingress_site_config.py" in joined:
                    projection.write_text(json.dumps({"ready_for_owner_ingress":True,"provider_operation_authorized":False,"provider_operation_started":False}),encoding="utf-8")
                    return 0,None,""
                raise AssertionError(joined)
            env={"STEGVERSE_TVC_ROOT":str(root),"STEGVERSE_COINBASE_PUBLIC_NODE_URL":"https://node.example/api/stegverse-node"}
            tls=root/"tls-adoption.json"; tls.write_text("{}\\n",encoding="utf-8")
            with patch.object(worker.os,"geteuid",return_value=0), patch.object(worker,"ROUTE_OBS",route), patch.object(worker,"ACTIVATION",activation), patch.object(worker,"LIVENESS",liveness), patch.object(worker,"SITE_PROJECTION",projection), patch.object(worker,"TLS_ADOPTION",tls), patch.object(worker,"_run",side_effect=fake_run):
                result=worker.execute(env)
        self.assertEqual(result["state"],"COMPLETED",result)
        self.assertFalse(result["activation_performed"])
        self.assertTrue(result["route_observation_performed"])
        self.assertFalse(any("activate_coinbase_intr_resident.py" in " ".join(call) for call in calls))
        self.assertFalse(result["site_repository_mutated"])

    def test_missing_tls_invokes_cmc029_then_waits_for_gateway_reconciliation(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for rel in (
                "scripts/activate_coinbase_intr_resident.py",
                "scripts/observe_coinbase_intr_resident_readiness.py",
                "scripts/observe_coinbase_service_gateway_route.py",
                "scripts/project_coinbase_owner_ingress_site_config.py",
                "scripts/execute_service_gateway_webpki_http01_029.py",
            ):
                p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text("# test\\n",encoding="utf-8")
            tls=root/"tls-adoption.json"
            calls=[]
            def fake_run(args,cwd,**kwargs):
                calls.append(args)
                joined=" ".join(str(x) for x in args)
                if "observe_coinbase_intr_resident_readiness.py" in joined:
                    return 2,{"state":"BLOCKED_RESIDENT_BINDING_INVALID","reason":"current production public InTr route observation missing"},""
                if "execute_service_gateway_webpki_http01_029.py" in joined:
                    tls.write_text("{}\\n",encoding="utf-8")
                    return 0,{
                        "state":"ISSUED_AND_ADOPTED_FOR_STEGDEPLOY_TLS",
                        "private_key_exported":False,
                        "private_key_bytes_recorded":False,
                        "account_key_bytes_recorded":False,
                        "provider_operation_authority":"NONE",
                        "tls_adoption_receipt_sha256":"sha256:"+"b"*64,
                    },""
                raise AssertionError(joined)
            env={
                "STEGVERSE_TVC_ROOT":str(root),
                "STEGVERSE_SERVICE_GATEWAY_HOSTNAME":"gateway.stegverse.org",
                "STEGVERSE_ACME_DIRECTORY_URL":"https://ca.example/directory",
                "STEGVERSE_ACME_CONTACT":"mailto:ops@stegverse.org",
                "STEGVERSE_COINBASE_PUBLIC_NODE_URL":"https://gateway.stegverse.org/api/stegverse-node",
            }
            with patch.object(worker.os,"geteuid",return_value=0), patch.object(worker,"TLS_ADOPTION",tls), patch.object(worker,"_run",side_effect=fake_run):
                result=worker.execute(env)
        self.assertEqual(result["transition_id"],"SERVICE_GATEWAY_TLS_ADOPTED_WAITING_FOR_GATEWAY_RECONCILIATION")
        self.assertTrue(result["tls_issuance_performed"])
        self.assertTrue(any("execute_service_gateway_webpki_http01_029.py" in " ".join(str(x) for x in call) for call in calls))
        self.assertFalse(any("observe_coinbase_service_gateway_route.py" in " ".join(str(x) for x in call) for call in calls))
        self.assertFalse(result["provider_operation_authorized"])


if __name__=="__main__":
    unittest.main()
