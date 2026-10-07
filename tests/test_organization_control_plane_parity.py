import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p): return json.loads((ROOT/p).read_text())
def test_labs_owns_sole_org_boundary():
 b=load("org-runtime/interlock-intr.json")
 assert b["organization"]=="StegVerse-Labs"
 assert b["owner_repository"]=="StegVerse-Labs/.github"
 assert b["communication_policy"]=="ALL_ORGANIZATION_INGRESS_EGRESS_GENERATED_AT_ORG_DOT_GITHUB_BOUNDARY"
def test_manifest_ingress_is_repo_owned_not_http_or_environment():
 b=load("org-runtime/interlock-intr.json")
 x=b["ingress"]["capability_endpoint_bindings"][0]["receiving_operation"]
 assert x["owner_repository"]=="StegVerse-Labs/.github"
 assert x["operation_id"]=="ORGANIZATION_SDK_MANIFEST_INGRESS"
 assert x["operation"]=="resident-runtime/organization_manifest_ingress.py"
 assert x["address_form"]=="REPOSITORY_OWNED_OPERATION_NOT_HOST_OR_URL"
 assert x["host_required"] is False and x["environment_url_required"] is False
 assert "method" not in x and "path" not in x
def test_egress_is_repo_owned_and_non_authorizing():
 b=load("org-runtime/interlock-intr.json")
 x=b["egress"]["emitting_operation"]
 assert x["owner_repository"]=="StegVerse-Labs/.github"
 assert x["operation_id"]=="ORGANIZATION_INTER_ORG_EGRESS"
 assert x["grants_routing_authority"] is False
 assert x["grants_admission_authority"] is False
 assert x["grants_execution_authority"] is False
def test_manifest_service_is_boundary_local():
 s=load("org-boundary/registry/services.json")["services"]
 x=next(v for v in s if v["service_id"]=="stegverse-labs.sdk-manifest-ingress")
 assert x["repository"]=="StegVerse-Labs/.github"
 assert x["boundary_role"]=="BOUNDARY_LOCAL_CAPABILITY_INGRESS"
def test_stegcore_is_internal_decision_authority_not_org_ingress():
 s=load("org-boundary/registry/services.json")["services"]
 g=next(v for v in s if v["service_id"]=="stegverse-labs.governance")
 assert g["repository"]=="StegVerse-Labs/.github"
 assert g["boundary_role"]=="INTERNAL_ENDPOINT"
 assert g["decision_authority"].startswith("StegVerse-Labs/StegCore:")
 assert not any(v.get("repository")=="StegVerse-Labs/StegCore" and v.get("boundary_role","").startswith("BOUNDARY_LOCAL") for v in s)
