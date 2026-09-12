from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSUMER = ROOT / "control/resident-execution-request.d/consume-shared-docs-provider-content-integrity.py"
REQUEST = ROOT / "control/resident-execution-request.d/shared-docs-provider-content-integrity-001.json"


def load_consumer():
    spec = importlib.util.spec_from_file_location("shared_docs_provider_content_integrity_consumer", CONSUMER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_request_is_exact_non_authorizing_downloadable_profile():
    module = load_consumer()
    value = json.loads(REQUEST.read_text(encoding="utf-8"))
    provider = module._validate(value)
    assert value["task_id"] == "SHARED-DOCS-PROVIDER-FREEZE-INTEGRATION-001"
    assert value["selector"] == "shared_docs_provider_content_integrity"
    assert value["credential_authority"] == "TV/TVC"
    assert value["credential_material_allowed"] is False
    assert value["provider_mutation_allowed"] is False
    assert value["request_granted_authority"] is False
    assert provider["provider_file_id"] == "1uTDq29Q5gEmnqY18u8JCRPlUBGkCYqOE"
    assert provider["content_profile"] == "google-drive.downloaded-bytes.v1"
    assert provider["read_only"] is True
    assert provider["provider_mutation_allowed"] is False
    assert provider["binding_id"].startswith("wsprobe_")
