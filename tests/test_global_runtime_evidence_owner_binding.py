import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_global_runtime_evidence_owner_binding.py"


def test_global_runtime_evidence_owner_binding():
    spec = importlib.util.spec_from_file_location("global_runtime_owner_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.validate() == []
