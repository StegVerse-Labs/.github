from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'control/resident-execution-request.d/consume-shared-docs-provider-content-integrity.py'
spec=importlib.util.spec_from_file_location('shared_docs_provider_content_integrity_consumer',TARGET)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_missing_request_is_non_authorizing_wait_state(tmp_path):
    result=mod.consume(ROOT,tmp_path,environ={})
    assert result['state']=='INPUT_NOT_MATERIALIZED'
    assert result['reason']=='RESIDENT_CONTENT_INTEGRITY_REQUEST_ABSENT'
    assert result['credential_authority']=='TV/TVC'
    assert result['provider_operation_authority_transferred'] is False
    assert result['provider_mutation_performed'] is False
    assert result['second_machine_required'] is False

def test_request_contract_is_exact_and_secret_free():
    request={
      'schema':'stegverse.resident-execution-request/v1','state':'REQUESTED','task_id':mod.TASK_ID,
      'mode':'TARGETED_INDEPENDENT_TASK_CONTROL','selector':mod.SELECTOR,'credential_authority':'TV/TVC',
      'github_token_required':False,'github_token_runtime_authority':'NONE','heartbeat_grants_execution_authority':False,
      'second_machine_required':False,'credential_material_allowed':False,'provider_mutation_allowed':False,
      'request_granted_authority':False,'authority_effect':'NONE_REQUEST_ONLY',
      'provider_request':{'schema':'stegverse.tvc.external-collaboration-google-drive-content-integrity-request/v1',
        'request_id':'shared-docs-ci-0123456789','binding_id':'wsprobe_abcdefghijklmnop','provider_file_id':'file123',
        'probe_reason':'Shared Docs immutable revision binding','content_profile':'google-drive.downloaded-bytes.v1',
        'read_only':True,'provider_mutation_allowed':False}}
    p=mod._validate(request)
    assert p['content_profile']==mod.CONTENT_PROFILE
