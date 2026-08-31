from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

dispatcher = load('resident_dispatcher_manifest_test', 'scripts/dispatch_resident_execution_requests.py')
refresh_dispatch = load('refresh_dispatch_manifest_test', 'scripts/refresh_and_dispatch_resident_requests.py')


def test_verified_source_manifest_survives_both_dispatch_boundaries():
    values = {
        'PATH': '/bin',
        'HOME': '/tmp',
        'STEGVERSE_RESIDENT_SOURCE_MANIFEST': '/state/resident-control-plane/.stegverse-source-manifest.json',
        'STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT': '/state/resident-control-plane/vendor/master-records-orchestration',
        'STEGVERSE_MASTER_RECORDS_ROOT': '/state/resident-control-plane/vendor/master-records-orchestration',
    }
    first = refresh_dispatch.clean_exec_env(values)
    second = dispatcher.clean_exec_env(first)
    assert second['STEGVERSE_RESIDENT_SOURCE_MANIFEST'] == values['STEGVERSE_RESIDENT_SOURCE_MANIFEST']
    assert second['STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT'] == values['STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT']
    assert second['STEGVERSE_MASTER_RECORDS_ROOT'] == values['STEGVERSE_MASTER_RECORDS_ROOT']
    assert second['STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY'] == 'NONE'
    assert second['STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY'] == 'TV/TVC'


def test_sv002_adapter_allows_only_nonsecret_source_locators_for_reconstruction():
    fragment = json.loads((ROOT / 'control/process-worker-adapters.d/sv002-self-characterization-001.json').read_text())
    allowed = set(fragment['adapters'][0]['env_allowlist'])
    assert 'STEGVERSE_RESIDENT_SOURCE_MANIFEST' in allowed
    assert 'STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT' in allowed
    assert 'STEGVERSE_MASTER_RECORDS_ROOT' in allowed
    assert 'GITHUB_TOKEN' not in allowed
    assert 'GH_TOKEN' not in allowed
