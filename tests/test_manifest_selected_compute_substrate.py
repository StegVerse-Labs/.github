import importlib.util, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_manifest_selected_compute_contract():
 p=json.loads((ROOT/"control/canonical-work-runtime-profile.json").read_text())
 assert p["environment_classes"]==["MANIFEST_SELECTED_EPHEMERAL"]
 s=p["compute_substrate"]; assert s["authority_effect"]=="NONE_COMPUTE_ONLY"; assert s["persistent_resident_host_required"] is False; assert s["systemd_required"] is False
def test_dispatcher_strips_hosted_identity():
 spec=importlib.util.spec_from_file_location("d",ROOT/"scripts/dispatch_resident_execution_requests.py");m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 e=m.clean_exec_env({"PATH":"/bin","GITHUB_ACTIONS":"true","GITHUB_TOKEN":"x"})
 assert "GITHUB_ACTIONS" not in e and "GITHUB_TOKEN" not in e
 assert e["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"]=="NONE"
