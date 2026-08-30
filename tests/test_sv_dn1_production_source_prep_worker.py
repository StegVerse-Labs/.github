import base64, json, tempfile, unittest
from pathlib import Path
from unittest import mock
from workers import sv_dn1_production_source_prep_worker as worker

class SovereignSourcePackageTests(unittest.TestCase):
    def make_package(self, component, files):
        rows=[]; payload=[]
        for path,data in sorted(files.items()):
            rows.append({"path":path,"sha256":worker.sha256_bytes(data),"size":len(data)})
            payload.append({"path":path,"sha256":worker.sha256_bytes(data),"size":len(data),"content_base64":base64.b64encode(data).decode()})
        digest=worker.sha256_bytes(worker.canonical_bytes(rows))
        return {"schema":worker.PACKAGE_SCHEMA,"package_version":worker.PACKAGE_VERSION,
                "component_id":component,"source_identity":"sha256:"+digest,
                "credential_material_included":False,
                "manifest":{"file_count":len(rows),"source_bundle_sha256":digest,"files":rows},
                "files":payload,"provenance":{"legacy_coordinate":worker.COMPONENTS[component]["legacy_coordinate"]},
                "authority_effect":"NONE_SOURCE_TRANSPORT_ONLY"}

    def test_worker_has_no_network_source_acquisition(self):
        src=Path(worker.__file__).read_text()
        for forbidden in ("urllib","urlopen(","github.com/","codeload.github.com","MATERIALIZE_SOURCE_ARCHIVE","TVC-GITHUB-REPOSITORY-OPERATION-BROKER"):
            self.assertNotIn(forbidden,src)
        self.assertIn("github_platform_required",src)
        self.assertIn("sha256-content-manifest",src)

    def test_package_validates_and_materializes_without_network(self):
        component="Data-Continuation/core-lite"; rel="core_lite/transaction_route.py"; data=b"route\n"
        with tempfile.TemporaryDirectory() as td:
            base=Path(td)/"source"; store=Path(td)/"packages"
            package=self.make_package(component,{rel:data})
            with mock.patch.dict(worker.COMPONENTS[component],{"anchors":{rel:worker.git_blob_sha1(data)}},clear=False):
                pp=worker.package_path(store,component); pp.parent.mkdir(parents=True); pp.write_text(json.dumps(package))
                row=worker.ensure_component(base,store,component)
            self.assertEqual(row["state"],"PACKAGE_MATERIALIZED_VERIFIED")
            self.assertTrue((worker.repo_root(base,component)/rel).is_file())
            self.assertFalse(row["network_fetch_performed"])
            self.assertTrue(row["source_identity"].startswith("sha256:"))

    def test_missing_package_requests_transport_neutral_source(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(worker.SourcePackagePending):
                worker.ensure_component(Path(td)/"source",Path(td)/"packages","StegVerse-Labs/StegCore")

    def test_local_root_can_be_canonicalized_without_git_or_network(self):
        component="master-records/orchestration"; rel="services/manifest_receipt_custody.py"; data=b"custody\n"
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); root=worker.repo_root(base,component); (root/Path(rel).parent).mkdir(parents=True); (root/rel).write_bytes(data)
            with mock.patch.dict(worker.COMPONENTS[component],{"anchors":{rel:worker.git_blob_sha1(data)}},clear=False):
                row=worker.observe_local_component(base,component)
            self.assertEqual(row["state"],"LOCAL_PRESENT_VERIFIED")
            self.assertTrue(row["source_identity"].startswith("sha256:"))

    def test_handoff_forbids_platform_dependency(self):
        root=Path(__file__).resolve().parents[1]
        h=json.loads((root/"handoffs/SV-DN1-PRODUCTION-SOURCE-PREP-001.json").read_text())
        self.assertFalse(h["execution"]["public_network_access"]["enabled"])
        self.assertFalse(h["authority"]["github_platform_required"])
        self.assertEqual(h["execution"]["source_identity_scheme"],"sha256-content-manifest")

if __name__=="__main__": unittest.main()
