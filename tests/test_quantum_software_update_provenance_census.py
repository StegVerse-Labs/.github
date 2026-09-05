from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "validate_quantum_software_update_provenance_census.py"


def _load():
    spec = importlib.util.spec_from_file_location("quantum_software_provenance_validator", MODULE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_census_validates_and_preserves_non_authority():
    result = _load().validate()
    assert result["state"] == "PASS"
    assert result["surface_count"] == 2
    assert result["authority_effect"] == "NONE_CENSUS_ONLY"


def test_hash_only_paths_are_not_upgraded_to_authenticated_or_pq():
    data = _load().json.loads(_load().CENSUS.read_text(encoding="utf-8"))
    for surface in data["surfaces"]:
        assert surface["authenticity_state"] == "HASH_MANIFEST_ONLY_AUTHENTICITY_UNPROVEN"
        assert surface["quantum_state"] == "QUANTUM_SAFETY_UNKNOWN"
    assert data["pqc_validated_surface_count"] == 0
