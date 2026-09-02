import importlib.util, json, os, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

resolver=load(Path("scripts/materialize_personal_kv_provider_root.py"),"resolver")

def test_existing_local_root_wins_without_provider_session():
    with tempfile.TemporaryDirectory() as d:
        root=Path(d)/"KnowledgeVault";root.mkdir()
        runtime=Path(d)/"runtime";runtime.mkdir()
        resolved,receipt=resolver.resolve_kv_root({"STEGVERSE_KV_ROOT":str(root)},runtime)
        assert resolved==root.resolve()
        assert receipt["state"]=="EXISTING_LOCAL_ROOT"
        assert receipt["provider_materialization_performed"] is False
        assert receipt["credential_material_persisted"] is False
        assert receipt["authority_effect"]=="NONE"

def test_provider_resolution_fails_closed_without_tvc_session_file():
    with tempfile.TemporaryDirectory() as d:
        runtime=Path(d)/"runtime";runtime.mkdir()
        source=Path(d)/"source";(source/"runtime").mkdir(parents=True)
        binding=Path(d)/"binding.json";binding.write_text("{}")
        materialized=Path(d)/"materialized"
        env={
            "STEGVERSE_KV_SOURCE_ROOT":str(source),
            "STEGVERSE_KV_PROVIDER_BINDING_PATH":str(binding),
            "STEGVERSE_KV_PROVIDER_MATERIALIZED_ROOT":str(materialized),
        }
        try:
            resolver.resolve_kv_root(env,runtime)
            assert False
        except resolver.KVProviderMaterializationError as exc:
            assert "tvc_provider_session_file_missing" in str(exc)

def test_provider_resolution_does_not_accept_token_value_environment():
    forbidden={"GOOGLE_ACCESS_TOKEN","GOOGLE_REFRESH_TOKEN","STEGVERSE_GOOGLE_DRIVE_TOKEN"}
    assert forbidden.isdisjoint({
        resolver.KV_SOURCE_ROOT_ENV,
        resolver.KV_ROOT_ENV,
        resolver.BINDING_PATH_ENV,
        resolver.MATERIALIZED_ROOT_ENV,
        resolver.SESSION_FILE_ENV,
    })

def test_session_reference_class_is_tvc_owned():
    assert resolver.SESSION_FILE_ENV=="STEGVERSE_TVC_PROVIDER_SESSION_FILE"


if __name__=="__main__":
    test_existing_local_root_wins_without_provider_session()
    test_provider_resolution_fails_closed_without_tvc_session_file()
    test_provider_resolution_does_not_accept_token_value_environment()
    test_session_reference_class_is_tvc_owned()
    print("PERSONAL_KV_PROVIDER_ROOT_RESOLUTION_PASS")
