from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workers import kv_connection_revalidation_worker as worker

class FakeStore:
    def __init__(self,assembly):
        self.registry={"schema":"stegverse.kv.connection-assembly-registry/v1","state":"ASSEMBLED_UNVERIFIED","authority_effect":"NONE","assemblies":[assembly]}
        self.health=[]
    def load_registry(self,kv): return self.registry
    def upsert_assembly(self,kv,assembly):
        self.registry={**self.registry,"state":"VERIFIED","assemblies":[assembly]}; return self.registry
    def persist_health_receipt(self,kv,receipt):
        self.health.append(receipt); return Path(kv)/"_System/Connections/Health"/"verified.json"

class FakeRevalidation:
    @staticmethod
    def admit_revalidation(assembly,conformance,readback,required_after=None):
        if required_after and conformance["observed_at"] < required_after:
            raise ValueError("stale")
        updated=json.loads(json.dumps(assembly)); updated["compatibility_state"]="VERIFIED"
        return updated,{
            "schema":"stegverse.kv.connection-health-receipt/v1",
            "assembly_id":assembly["assembly_id"],"provider":assembly["provider"],
            "observed_at":readback["observed_at"],"prior_state":assembly["compatibility_state"],
            "current_state":"VERIFIED","reason":"CONNECTION_AND_KV_READBACK_VERIFIED",
            "change_observation_ref":None,"revalidation_required":False,
            "connection_proof_ref":conformance["connection_proof_ref"],
            "readback_proof_ref":readback["readback_proof_ref"],
            "provider_operation_authorized":False,"credential_material_present":False,"authority_effect":"NONE"
        }

class KVConnectionRevalidationWorkerTests(unittest.TestCase):
    def assembly(self,state="REVALIDATION_REQUIRED"):
        return {
            "assembly_id":"kvcxn_1234567890abcdef12345678","provider":"coinbase",
            "compatibility_state":state,
            "monitoring":{"last_checked_at":"2026-08-28T16:00:00Z"}
        }
    def proof_files(self,root:Path):
        c=root/"conformance.json"; r=root/"readback.json"
        c.write_text(json.dumps({
            "schema":"stegverse.kv.connection-conformance-proof/v1",
            "assembly_id":"kvcxn_1234567890abcdef12345678","provider":"coinbase",
            "observed_at":"2026-08-28T17:00:00Z","connection_proof_ref":"proof:c"
        }))
        r.write_text(json.dumps({
            "schema":"stegverse.kv.connection-readback-proof/v1",
            "assembly_id":"kvcxn_1234567890abcdef12345678",
            "observed_at":"2026-08-28T17:01:00Z","readback_proof_ref":"proof:r"
        }))
        return c,r
    def env(self,root:Path,c:Path,r:Path):
        cvk=root/"cvk"; kv=root/"kv"; cvk.mkdir(); kv.mkdir()
        return {
            "STEGVERSE_CVK_ROOT":str(cvk),"STEGVERSE_KV_ROOT":str(kv),
            "STEGVERSE_KV_CONFORMANCE_PROOF":str(c),"STEGVERSE_KV_READBACK_PROOF":str(r)
        }

    def test_hosted_surface_rejected(self):
        x=worker.execute({"GITHUB_ACTIONS":"true"}); self.assertEqual(x["transition_id"],"HOSTED_SURFACE_REJECTED")

    def test_credential_environment_rejected(self):
        x=worker.execute({"COINBASE_API_KEY":"x"}); self.assertEqual(x["transition_id"],"FORBIDDEN_CREDENTIAL_ENV")

    def test_verified_persists_only_after_canonical_admission(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); c,r=self.proof_files(root); env=self.env(root,c,r)
            store=FakeStore(self.assembly())
            x=worker.execute(env,modules={"store":store,"revalidation":FakeRevalidation})
        self.assertEqual(x["state"],"COMPLETED")
        self.assertEqual(x["compatibility_state"],"VERIFIED")
        self.assertTrue(x["connection_verified"])
        self.assertFalse(x["provider_network_access_performed"])
        self.assertFalse(x["proof_generated_by_worker"])
        self.assertEqual(len(store.health),1)

    def test_proof_assembly_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); c,r=self.proof_files(root)
            rv=json.loads(r.read_text()); rv["assembly_id"]="kvcxn_aaaaaaaaaaaaaaaaaaaaaaaa"; r.write_text(json.dumps(rv))
            env=self.env(root,c,r)
            x=worker.execute(env,modules={"store":FakeStore(self.assembly()),"revalidation":FakeRevalidation})
        self.assertEqual(x["transition_id"],"REVALIDATION_PROOF_ASSEMBLY_MISMATCH")

    def test_already_verified_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); c,r=self.proof_files(root); env=self.env(root,c,r)
            x=worker.execute(env,modules={"store":FakeStore(self.assembly("VERIFIED")),"revalidation":FakeRevalidation})
        self.assertEqual(x["transition_id"],"CONNECTION_ALREADY_VERIFIED")

    def test_missing_time_floor_for_runtime_block_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); c,r=self.proof_files(root); env=self.env(root,c,r)
            assembly=self.assembly("BLOCKED_RUNTIME"); assembly["monitoring"]["last_checked_at"]=None
            x=worker.execute(env,modules={"store":FakeStore(assembly),"revalidation":FakeRevalidation})
        self.assertEqual(x["transition_id"],"REVALIDATION_TIME_FLOOR_REQUIRED")

if __name__=="__main__": unittest.main()
