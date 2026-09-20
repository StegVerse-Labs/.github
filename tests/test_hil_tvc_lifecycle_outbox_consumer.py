from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts import consume_hil_tvc_lifecycle_outbox as mod

class HILTVCConsumerTests(unittest.TestCase):
    def test_no_worker_receipt_is_no_event(self):
        with tempfile.TemporaryDirectory() as td:
            result=mod.consume(Path(td),env={})
            self.assertEqual(result["state"],"NO_EVENT")

    def test_consumes_exact_queue_and_receiver_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=root/"runtime"; runtime.mkdir()
            durable=root/"hil"; durable.mkdir()
            wp=runtime/mod.WORKER_RECEIPT_REL; wp.parent.mkdir(parents=True)
            wp.write_text(json.dumps({"receiver_ready":True,"durable_state_root":str(durable)}))
            receiver_dir=durable/"receiver-receipts"; receiver_dir.mkdir()
            rr=receiver_dir/"S1.json"; rr.write_text(json.dumps({"schema_version":"HIL-RECEIVER-RECEIPT-v2","submission_id":"S1"}))
            outbox=durable/"intr-outbox/tvc-hil-lifecycle"; outbox.mkdir(parents=True)
            q=outbox/"S1.json"; q.write_text(json.dumps({
                "schema":"stegverse.hil.tvc_interlock_queue/v1","state":"READY_FOR_INTERLOCK_ADMISSION",
                "submission_id":"S1","queue_hash":"sha256:"+"a"*64,"receiver_receipt_ref":str(rr)
            }))
            tvc=root/"TVC"; (tvc/"tools").mkdir(parents=True)
            (tvc/"tools/hil_intr_lifecycle_intake.py").write_text("# test\n")
            for rel in mod.TVC_PROTECTED_PATHS:
                p=tvc/rel; p.parent.mkdir(parents=True,exist_ok=True); p.touch(exist_ok=True)
            def runner(cmd,**kwargs):
                if cmd[0]=="git":
                    if "merge-base" in cmd: return subprocess.CompletedProcess(cmd,0,"","")
                    return subprocess.CompletedProcess(cmd,0,"","")
                payload={"state":"ADMITTED_TO_TVC_HIL_LIFECYCLE","credential_authority":"TV/TVC","authority_transfer":False,
                         "private_review_completed":False,"publication_authorized":False,"admission_hash":"sha256:admit",
                         "tvc_interlock_receipt":{"receipt_hash":"sha256:hop"},"next_required_transition":"TVC_HIL_PRIVATE_REVIEW_INTERLOCK"}
                return subprocess.CompletedProcess(cmd,0,json.dumps(payload)+"\n","")
            result=mod.consume(runtime,runner=runner,env={"STEGVERSE_TVC_ROOT":str(tvc)})
            self.assertEqual(result["state"],"ADMITTED_TO_TVC_HIL_LIFECYCLE")
            self.assertEqual(result["results"][0]["tvc_interlock_receipt_hash"],"sha256:hop")
            self.assertFalse(result["private_review_completed"])
            self.assertTrue((runtime/mod.CONSUMPTION_REL).is_file())


    def test_consumes_admitted_tvc_materialization_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=root/"runtime"; runtime.mkdir()
            tvc=root/"TVC"; (tvc/"tools").mkdir(parents=True)
            (tvc/"tools/hil_intr_lifecycle_intake.py").write_text("# test\n")
            for rel in mod.TVC_PROTECTED_PATHS:
                p=tvc/rel; p.parent.mkdir(parents=True,exist_ok=True); p.touch(exist_ok=True)
            queue={
                "schema":"stegverse.hil.tvc_interlock_queue/v1","state":"READY_FOR_INTERLOCK_ADMISSION",
                "submission_id":"S1","payload_hash":"sha256:"+"2"*64,"prior_receipt_hash":"sha256:"+"3"*64,
                "transport_intent":{"operation_id":"OP:TVC"},"response_artifact_ref":"response.pdf","provenance_artifact_ref":"provenance.json",
                "transport_protocol":"InTr","interlock_required":True,"authority_transfer":False,
                "tvc_admission_completed":False,"blind_consequence_retry_allowed":False,
            }
            queue["queue_hash"]="sha256:"+"4"*64
            receiver={
                "schema_version":"HIL-RECEIVER-RECEIPT-v2","submission_id":"S1","intr_tvc_queue_hash":queue["queue_hash"],
                "intr_receipt_chain":{"next_interlock_intent":queue["transport_intent"]},
            }
            bundle={
                "schema":"stegverse.hil.tvc-lifecycle-materialization-bundle/v1",
                "queue":queue,"receiver_receipt":receiver,
                "response_bytes_base64":base64.b64encode(b"%PDF-1.7\nX\n%%EOF\n").decode(),
                "provenance_manifest":{"schema_version":"HIL-RESPONSE-PROVENANCE-v1.1"},
                "credential_authority":"TV/TVC","authority_effect":"NONE_TRANSPORT_ONLY",
            }
            payload=base64.b64encode(json.dumps(bundle,separators=(",",":"),sort_keys=True).encode()).decode()
            request={
                "materialization_id":"INTR-MAT-"+"e"*24,
                "request_hash":"sha256:"+"1"*64,
                "destination":mod.TVC_DESTINATION,
                "downstream_owner_ref":mod.TVC_OWNER,
                "payload_ref":mod.BUNDLE_PREFIX+payload,
            }
            reqdir=runtime/mod.MATERIALIZATION_REQUEST_DIR_REL; reqdir.mkdir(parents=True)
            (reqdir/(request["materialization_id"]+".json")).write_text(json.dumps(request))
            recdir=runtime/mod.MATERIALIZATION_INGRESS_DIR_REL; recdir.mkdir(parents=True)
            (recdir/(request["materialization_id"]+".json")).write_text(json.dumps({
                "state":"INGRESS_ADMITTED","materialization_id":request["materialization_id"],"request_hash":request["request_hash"]
            }))
            seen={}
            def runner(cmd,**kwargs):
                if cmd[0]=="git":
                    return subprocess.CompletedProcess(cmd,0,"","")
                seen["cmd"]=cmd
                payload={"state":"ADMITTED_TO_TVC_HIL_LIFECYCLE","admission_hash":"sha256:admit",
                         "tvc_interlock_receipt":{"receipt_hash":"sha256:hop"},"next_required_transition":"TVC_HIL_PRIVATE_REVIEW_INTERLOCK"}
                return subprocess.CompletedProcess(cmd,0,json.dumps(payload)+"\n","")
            result=mod.consume(runtime,runner=runner,env={"STEGVERSE_TVC_ROOT":str(tvc)})
            self.assertEqual(result["state"],"ADMITTED_TO_TVC_HIL_LIFECYCLE")
            self.assertEqual(result["materialization_event_count"],1)
            self.assertIn("--artifact-root",seen["cmd"])
            materialized=runtime/mod.MATERIALIZED_BUNDLE_DIR_REL/request["materialization_id"]
            self.assertTrue((materialized/"response.pdf").is_file())
            self.assertTrue((materialized/"provenance.json").is_file())

    def test_discovers_verified_portable_tvc_bundle_without_git_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            control=Path(td)/"resident-control-plane"
            tvc=control/"vendor/TVC"
            entries=[]
            for rel in mod.TVC_PROTECTED_PATHS:
                path=tvc/rel
                path.parent.mkdir(parents=True,exist_ok=True)
                data=(rel+"\n").encode()
                path.write_bytes(data)
                entries.append({
                    "path":"vendor/TVC/"+rel,
                    "sha256":hashlib.sha256(data).hexdigest(),
                    "size":len(data),
                })
            manifest={
                "schema":"stegverse.sovereign-control-plane-bundle/v1",
                "network_fetch_required":False,
                "credential_authority":"TV/TVC",
                "github_token_runtime_authority":"NONE",
                "bundle_grants_authority":False,
                "files":entries,
                "vendor_source_proofs":{
                    "TVC":{
                        "schema":"stegverse.portable-source-proof/v1",
                        "state":"VERIFIED_LOCAL_GIT_SOURCE",
                        "repository":"StegVerse-Labs/TVC",
                        "materialized_subpath":"vendor/TVC",
                        "source_floor":mod.TVC_SOURCE_FLOOR,
                        "source_floor_present":True,
                        "protected_paths":list(mod.TVC_PROTECTED_PATHS),
                        "protected_paths_unchanged_since_floor":True,
                        "network_fetch_performed":False,
                    }
                },
            }
            manifest_path=control/".stegverse-source-manifest.json"
            manifest_path.write_text(json.dumps(manifest)+"\n")

            def runner(cmd,**kwargs):
                return subprocess.CompletedProcess(cmd,128,"","not a git repository")

            root,mode=mod.discover_tvc_root({
                "STEGVERSE_TVC_ROOT":str(tvc),
                "STEGVERSE_RESIDENT_SOURCE_MANIFEST":str(manifest_path),
            },runner=runner)

            self.assertEqual(root,tvc.resolve())
            self.assertEqual(mode,"VERIFIED_PORTABLE_BUNDLE_PROOF")

    def test_receiver_receipt_must_stay_inside_durable_root(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); runtime=root/"runtime"; runtime.mkdir(); durable=root/"hil"; durable.mkdir()
            wp=runtime/mod.WORKER_RECEIPT_REL; wp.parent.mkdir(parents=True)
            wp.write_text(json.dumps({"receiver_ready":True,"durable_state_root":str(durable)}))
            outside=root/"outside.json"; outside.write_text("{}")
            outbox=durable/"intr-outbox/tvc-hil-lifecycle"; outbox.mkdir(parents=True)
            (outbox/"S1.json").write_text(json.dumps({"schema":"stegverse.hil.tvc_interlock_queue/v1","state":"READY_FOR_INTERLOCK_ADMISSION","submission_id":"S1","receiver_receipt_ref":str(outside)}))
            tvc=root/"TVC"; (tvc/"tools").mkdir(parents=True)
            (tvc/"tools/hil_intr_lifecycle_intake.py").write_text("# test\n")
            for rel in mod.TVC_PROTECTED_PATHS:
                p=tvc/rel; p.parent.mkdir(parents=True,exist_ok=True); p.touch(exist_ok=True)
            def runner(cmd,**kwargs): return subprocess.CompletedProcess(cmd,0,"","")
            result=mod.consume(runtime,runner=runner,env={"STEGVERSE_TVC_ROOT":str(tvc)})
            self.assertEqual(result["state"],"FAIL_CLOSED")
            self.assertEqual(result["failures"][0]["reason"],"receiver_receipt_ref_invalid")

if __name__=="__main__": unittest.main()
