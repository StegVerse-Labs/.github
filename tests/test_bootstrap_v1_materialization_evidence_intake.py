from __future__ import annotations
import importlib.util,json,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"workers/bootstrap_v1_materialization_evidence_intake_worker.py"
spec=importlib.util.spec_from_file_location("intake",PATH);m=importlib.util.module_from_spec(spec);assert spec and spec.loader;spec.loader.exec_module(m)

C=list(m.COMPONENTS)

def candidate():
    body={"schema":"stegverse.bootstrap.release-candidate/v1","candidate_version":"1.0.0-rc.1","state":"FROZEN","source_catalog":{"sha256":"placeholder","source_identity_set_sha256":"placeholder"},"release_activated":False,"publication_performed":False,"execution_authority":"NONE"}
    return {**body,"candidate_identity":"sha256:"+m.digest(body)}

def make_bundle():
    ids={c:"sha256:"+(str(i+1)*64)[:64] for i,c in enumerate(C)}
    catalog={"schema":"stegverse.bootstrap.source-catalog/v1","catalog_version":"1.0.0","state":"FROZEN","source_identity_scheme":"sha256-content-manifest","component_count":4,"components":[{"component_id":c,"source_identity":ids[c]} for c in C],"source_identity_set_sha256":"set-123","github_platform_required":False,"specific_external_platform_required":False,"network_locator_required":False}
    c=candidate();c["source_catalog"]={"sha256":m.digest(catalog),"source_identity_set_sha256":catalog["source_identity_set_sha256"]};c["candidate_identity"]="sha256:"+m.digest(m.candidate_body(c))
    packages=[{"schema":"stegverse.source-package/v1","package_version":"1.0.0","component_id":x,"source_identity":ids[x]} for x in C]
    body={"schema":"stegverse.bootstrap.bundle/v1","bundle_version":"1.0.0-rc.1","state":"BUILT","release_candidate":c,"source_catalog":catalog,"packages":packages,"component_order":C,"component_count":4,"source_identity_scheme":"sha256-content-manifest","github_platform_required":False,"specific_external_platform_required":False,"network_locator_required":False,"transport_implementation_required":False,"credential_required":False,"bundle_integrity_confers_execution_authority":False,"release_activated":False,"publication_performed":False,"execution_authority":"NONE","authority_effect":"NONE_BUNDLE_BUILD_ONLY"}
    return c,{**body,"bundle_identity":"sha256:"+m.digest(body)},ids

def entry(receipt,seq,prev):
    rh=m.digest(receipt);body={"schema":"stegos.web_bootstrap_journal_entry.v1","sequence":seq,"previous_entry_sha256":prev,"receipt":receipt,"receipt_sha256":rh};return {**body,"entry_sha256":m.digest(body)}

def evidence(c,b,ids):
    node="stegnode-web-test";device="device-test";rows=[];prev=None
    genesis={"schema":"stegos.web_device_node_binding_receipt.v1","node_id":node,"device_continuity_id":device,"authority_effect":"NONE"};e=entry(genesis,1,prev);rows.append(e);prev=e["entry_sha256"]
    package_entries=[]
    for component in C:
        r={"schema":"stegos.web_source_package_materialization_receipt.v1","node_id":node,"device_continuity_id":device,"component_id":component,"source_identity":ids[component],"source_bundle_sha256":ids[component][7:],"file_count":1,"local_custody":"INDEXEDDB_STEGOS_SOURCE_PACKAGES_V1","materialization_state":"MATERIALIZED","admission_state":"UNADMITTED","execution_authority":"NONE","credential_material_observed":False,"github_platform_required":False,"specific_external_platform_required":False,"new_node_identity_minted":False,"authority_effect":"NONE_SOURCE_MATERIALIZATION_ONLY"};e=entry(r,len(rows)+1,prev);rows.append(e);package_entries.append(e);prev=e["entry_sha256"]
    expected=[{"component_id":x,"source_identity":ids[x]} for x in C]
    r={"schema":"stegos.web_bootstrap_bundle_materialization_receipt.v1","node_id":node,"device_continuity_id":device,"bundle_identity":b["bundle_identity"],"candidate_identity":c["candidate_identity"],"source_identity_set_sha256":b["source_catalog"]["source_identity_set_sha256"],"component_order":C,"component_identities":expected,"component_count":4,"all_components_materialized":True,"bundle_state":"MATERIALIZED_UNADMITTED","admission_state":"UNADMITTED","execution_authority":"NONE","release_activated":False,"publication_performed":False,"github_platform_required":False,"specific_external_platform_required":False,"new_node_identity_minted":False,"authority_effect":"NONE_BUNDLE_MATERIALIZATION_ONLY"};agg=entry(r,len(rows)+1,prev);rows.append(agg)
    rep=m.replay(rows)
    return {"schema":"stegverse.device-node-bootstrap-bundle-evidence/v1","state":"MATERIALIZED_UNADMITTED","node_id":node,"device_continuity_id":device,"continuity_source":"LIVE_EXISTING_WEB_BOOTSTRAP","bundle_identity":b["bundle_identity"],"candidate_identity":c["candidate_identity"],"source_identity_set_sha256":b["source_catalog"]["source_identity_set_sha256"],"component_count":4,"component_order":C,"component_identities":expected,"package_materialization_entries":package_entries,"bundle_materialization_entry":agg,"journal_replay":{"schema":"stegos.web_journal_replay_report.v1",**rep,"authority_effect":"NONE"},"continued_receipts":rows,"all_components_materialized":True,"admission_state":"UNADMITTED","credential_material_observed":False,"github_platform_required":False,"specific_external_platform_required":False,"new_node_identity_minted":False,"release_activated":False,"publication_performed":False,"execution_authority":"NONE","authority_effect":"NONE"}

class TestIntake(unittest.TestCase):
    def test_valid_evidence(self):
        c,b,ids=make_bundle();m.validate_candidate(c);self.assertEqual(m.validate_bundle(b,c),ids);obs=m.validate_evidence(evidence(c,b,ids),c,b,ids);self.assertEqual(obs["journal_entries"],6)
    def test_bundle_tamper_rejected(self):
        c,b,ids=make_bundle();e=evidence(c,b,ids);e["bundle_identity"]="sha256:"+"f"*64
        with self.assertRaisesRegex(RuntimeError,"bundle/candidate binding"):m.validate_evidence(e,c,b,ids)
    def test_journal_hash_tamper_rejected(self):
        c,b,ids=make_bundle();e=evidence(c,b,ids);e["continued_receipts"][2]["receipt_sha256"]="0"*64
        with self.assertRaisesRegex(RuntimeError,"journal receipt hash mismatch"):m.validate_evidence(e,c,b,ids)
    def test_component_reorder_rejected(self):
        c,b,ids=make_bundle();e=evidence(c,b,ids);e["component_order"]=list(reversed(C))
        with self.assertRaisesRegex(RuntimeError,"component order/count"):m.validate_evidence(e,c,b,ids)
    def test_authority_escalation_rejected(self):
        c,b,ids=make_bundle();e=evidence(c,b,ids);e["execution_authority"]="GRANTED"
        with self.assertRaisesRegex(RuntimeError,"execution_authority mismatch"):m.validate_evidence(e,c,b,ids)
    def test_bundle_identity_recomputed(self):
        c,b,ids=make_bundle();b["component_count"]=5
        with self.assertRaisesRegex(RuntimeError,"bundle identity mismatch"):m.validate_bundle(b,c)

if __name__=="__main__":unittest.main()
