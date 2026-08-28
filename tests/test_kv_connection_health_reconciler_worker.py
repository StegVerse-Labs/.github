from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workers import kv_connection_health_reconciler_worker as worker

class FakeStore:
    def __init__(self,assembly):
        self.registry={"schema":"stegverse.kv.connection-assembly-registry/v1","state":"VERIFIED","authority_effect":"NONE","assemblies":[assembly]}
        self.health=[]; self.changes=[]
    def load_registry(self,kv): return self.registry
    def persist_source_change(self,kv,obs):
        self.changes.append(obs); return Path(kv)/"_System/Connections/Source_Changes"/f"{obs['observation_id']}.json"
    def upsert_assembly(self,kv,assembly):
        self.registry={**self.registry,"state":"ASSEMBLED_UNVERIFIED","assemblies":[assembly]}; return self.registry
    def persist_health_receipt(self,kv,receipt):
        self.health.append(receipt); return Path(kv)/"_System/Connections/Health"/"receipt.json"

class FakeMonitor:
    @staticmethod
    def evaluate_source_change(assembly,obs):
        updated=json.loads(json.dumps(assembly))
        updated["compatibility_state"]="REVALIDATION_REQUIRED"
        updated["monitoring"]["last_change_ref"]=obs["observation_id"]
        return updated,{
            "schema":"stegverse.kv.connection-health-receipt/v1",
            "assembly_id":updated["assembly_id"],"provider":updated["provider"],
            "observed_at":obs["observed_at"],"prior_state":"VERIFIED","current_state":"REVALIDATION_REQUIRED",
            "reason":"SOURCE_CHANGE_REVALIDATION_REQUIRED","change_observation_ref":obs["observation_id"],
            "revalidation_required":True,"connection_proof_ref":"proof:c","readback_proof_ref":"proof:r",
            "provider_operation_authorized":False,"credential_material_present":False,"authority_effect":"NONE"
        }

class KVConnectionHealthReconcilerTests(unittest.TestCase):
    def assembly(self):
        return {
            "schema":"stegverse.kv.connection-assembly/v1","assembly_id":"kvcxn_1234567890abcdef12345678",
            "provider":"coinbase","compatibility_state":"VERIFIED",
            "monitoring":{"last_change_ref":None}
        }
    def observation(self):
        return {
            "schema":"stegverse.kv.source-change-observation/v1",
            "observation_id":"kvchg_1234567890abcdef12345678",
            "provider":"coinbase","observed_at":"2026-08-28T16:00:00Z"
        }
    def env(self,root:Path,input_path:Path):
        cvk=root/"cvk"; kv=root/"kv"; cvk.mkdir(); kv.mkdir()
        return {"STEGVERSE_CVK_ROOT":str(cvk),"STEGVERSE_KV_ROOT":str(kv),"STEGVERSE_KV_SOURCE_CHANGE_INPUT":str(input_path)}

    def test_hosted_surface_rejected(self):
        r=worker.execute({"GITHUB_ACTIONS":"true"})
        self.assertEqual(r["transition_id"],"HOSTED_SURFACE_REJECTED")

    def test_credential_env_rejected(self):
        r=worker.execute({"GITHUB_TOKEN":"x"})
        self.assertEqual(r["transition_id"],"FORBIDDEN_CREDENTIAL_ENV")

    def test_observation_applies_and_never_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inp=root/"obs.json"; inp.write_text(json.dumps(self.observation()))
            store=FakeStore(self.assembly()); env=self.env(root,inp)
            r=worker.execute(env,modules={"store":store,"monitor":FakeMonitor})
        self.assertEqual(r["state"],"COMPLETED")
        self.assertEqual(r["assemblies_applied"],1)
        self.assertEqual(r["results"][0]["state"],"REVALIDATION_REQUIRED")
        self.assertFalse(r["connection_verified"])
        self.assertFalse(r["provider_operation_authorized"])
        self.assertEqual(len(store.health),1)

    def test_missing_provider_assembly_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inp=root/"obs.json"; inp.write_text(json.dumps(self.observation()))
            store=FakeStore({**self.assembly(),"provider":"other"}); env=self.env(root,inp)
            r=worker.execute(env,modules={"store":store,"monitor":FakeMonitor})
        self.assertEqual(r["transition_id"],"PROVIDER_ASSEMBLY_NOT_FOUND")

    def test_already_applied_observation_is_idempotently_skipped(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); inp=root/"obs.json"; inp.write_text(json.dumps(self.observation()))
            assembly=self.assembly(); assembly["monitoring"]["last_change_ref"]=self.observation()["observation_id"]
            store=FakeStore(assembly); env=self.env(root,inp)
            r=worker.execute(env,modules={"store":store,"monitor":FakeMonitor})
        self.assertEqual(r["assemblies_applied"],0)
        self.assertEqual(r["assemblies_skipped"],1)

if __name__=="__main__": unittest.main()
