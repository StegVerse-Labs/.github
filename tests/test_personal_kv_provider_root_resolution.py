import importlib.util,json,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
resolver=load(Path("scripts/materialize_personal_kv_provider_root.py"),"resolver")

def test_existing_local_root_wins_without_provider_result():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)/"KnowledgeVault";root.mkdir();runtime=Path(d)/"runtime";runtime.mkdir()
        resolved,receipt=resolver.resolve_kv_root({"STEGVERSE_KV_ROOT":str(root)},runtime)
        assert resolved==root.resolve()
        assert receipt["state"]=="EXISTING_LOCAL_ROOT"
        assert receipt["provider_materialization_performed"] is False

def test_provider_resolution_fails_closed_without_tvc_result_file():
    with tempfile.TemporaryDirectory() as d:
        runtime=Path(d)/"runtime";runtime.mkdir()
        source=Path(d)/"source";(source/"runtime").mkdir(parents=True)
        binding=Path(d)/"binding.json";binding.write_text("{}")
        env={resolver.KV_SOURCE_ROOT_ENV:str(source),resolver.BINDING_PATH_ENV:str(binding),resolver.MATERIALIZED_ROOT_ENV:str(Path(d)/"materialized")}
        try:resolver.resolve_kv_root(env,runtime)
        except resolver.KVProviderMaterializationError as exc:assert "materialization_result_file_missing" in str(exc)
        else:raise AssertionError("missing TVC result must fail closed")

def test_retired_session_file_input_is_prohibited():
    with tempfile.TemporaryDirectory() as d:
        runtime=Path(d)/"runtime";runtime.mkdir()
        try:resolver.resolve_kv_root({resolver.RETIRED_SESSION_FILE_ENV:"/tmp/old-session"},runtime)
        except resolver.KVProviderMaterializationError as exc:assert "retired" in str(exc)
        else:raise AssertionError("retired session-file input must fail")

def test_no_raw_token_environment_contract():
    forbidden={"GOOGLE_ACCESS_TOKEN","GOOGLE_REFRESH_TOKEN","STEGVERSE_GOOGLE_DRIVE_TOKEN","STEGVERSE_TVC_PROVIDER_SESSION_FILE"}
    active={resolver.KV_SOURCE_ROOT_ENV,resolver.KV_ROOT_ENV,resolver.BINDING_PATH_ENV,resolver.MATERIALIZED_ROOT_ENV,resolver.RESULT_FILE_ENV}
    assert forbidden.isdisjoint(active)
    assert resolver.RESULT_FILE_ENV=="STEGVERSE_TVC_PROVIDER_MATERIALIZATION_RESULT_FILE"

def test_outer_tvc_result_must_be_secret_free_and_binding_matched():
    value={"schema":resolver.TVC_RESULT_SCHEMA,"provider":"GOOGLE_DRIVE","binding_id":"kvpb_"+"a"*24,"credential_authority":"TV/TVC","credential_material_exported":False,"provider_operation_authority_transferred":False,"runtime_activation_claimed":False,"broker_response":{}}
    assert resolver._validate_tvc_result(value,value["binding_id"])=={}
    value["credential_material_exported"]=True
    try:resolver._validate_tvc_result(value,value["binding_id"])
    except resolver.KVProviderMaterializationError as exc:assert "credential_export" in str(exc)
    else:raise AssertionError("credential export must fail")

if __name__=="__main__":
    test_existing_local_root_wins_without_provider_result()
    test_provider_resolution_fails_closed_without_tvc_result_file()
    test_retired_session_file_input_is_prohibited()
    test_no_raw_token_environment_contract()
    test_outer_tvc_result_must_be_secret_free_and_binding_matched()
    print("PERSONAL_KV_PROVIDER_ROOT_RESOLUTION_PASS")
