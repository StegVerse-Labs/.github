from __future__ import annotations
import importlib.util,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"workers/bootstrap_v1_release_gate_worker.py"
spec=importlib.util.spec_from_file_location("gate",PATH);m=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(m)
C=list(m.COMPONENTS)

def fixture():
    ids={c:"sha256:"+((str(i+1)*64)[:64]) for i,c in enumerate(C)}
    catalog={"schema":"stegverse.bootstrap.source-catalog/v1","catalog_version":"1.0.0","state":"FROZEN","source_identity_set_sha256":"set-123"}
    cb={"schema":"stegverse.bootstrap.release-candidate/v1","candidate_version":"1.0.0-rc.1","state":"FROZEN","source_catalog":{"sha256":"catalog","source_identity_set_sha256":"set-123"},"release_activated":False,"publication_performed":False,"execution_authority":"NONE"}
    c={**cb,"candidate_identity":"sha256:"+m.digest(cb)}
    packages=[{"component_id":x,"source_identity":ids[x]} for x in C]
    bb={"schema":"stegverse.bootstrap.bundle/v1","bundle_version":"1.0.0-rc.1","state":"BUILT","release_candidate":c,"source_catalog":catalog,"packages":packages,"component_order":C,"component_count":4,"github_platform_required":False,"specific_external_platform_required":False,"network_locator_required":False,"credential_required":False,"release_activated":False,"publication_performed":False,"execution_authority":"NONE"}
    b={**bb,"bundle_identity":"sha256:"+m.digest(bb)}
    ordered=[{"component_id":x,"source_identity":ids[x]} for x in C]
    p={"schema":"stegverse.bootstrap.materialization-proof/v1","state":"COMPLETE","transition_id":"BOOTSTRAP_V1_DISTRIBUTION_MATERIALIZATION_PROVEN","candidate_identity":c["candidate_identity"],"bundle_identity":b["bundle_identity"],"source_identity_set_sha256":"set-123","component_order":C,"component_identities":ordered,"node_id":"stegnode-web-test","device_continuity_id":"device-test","journal_tail_sha256":"a"*64,"device_evidence_sha256":"b"*64,"materialization_state":"MATERIALIZED_UNADMITTED","execution_authority":"NONE","release_activated":False,"publication_performed":False,"network_access_performed":False,"credential_used":False,"github_platform_required":False,"repository_writeback_performed":False,"authority_effect":"NONE_EVIDENCE_VALIDATION_ONLY"}
    return c,b,p,ordered

class ReleaseGateTests(unittest.TestCase):
    def test_valid_exact_chain_passes(self):
        c,b,p,ids=fixture();m.validate_candidate(c);self.assertEqual(m.validate_bundle(b,c),ids);m.validate_proof(p,c,b,ids)
    def test_proof_identity_drift_fails(self):
        c,b,p,ids=fixture();p["bundle_identity"]="sha256:"+"f"*64
        with self.assertRaisesRegex(RuntimeError,"candidate/bundle binding"):m.validate_proof(p,c,b,ids)
    def test_component_reorder_fails(self):
        c,b,p,ids=fixture();p["component_order"]=list(reversed(C))
        with self.assertRaisesRegex(RuntimeError,"component identity mismatch"):m.validate_proof(p,c,b,ids)
    def test_authority_escalation_fails(self):
        c,b,p,ids=fixture();p["execution_authority"]="GRANTED"
        with self.assertRaisesRegex(RuntimeError,"execution_authority mismatch"):m.validate_proof(p,c,b,ids)
    def test_network_or_credential_claim_fails(self):
        c,b,p,ids=fixture();p["credential_used"]=True
        with self.assertRaisesRegex(RuntimeError,"credential_used mismatch"):m.validate_proof(p,c,b,ids)
    def test_candidate_tamper_fails(self):
        c,b,p,ids=fixture();c["state"]="MUTATED"
        with self.assertRaises(m.Pending):m.validate_candidate(c)

if __name__=="__main__":unittest.main()
