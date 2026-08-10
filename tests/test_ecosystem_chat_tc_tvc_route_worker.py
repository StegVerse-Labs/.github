from __future__ import annotations

import os
from pathlib import Path

from workers.ecosystem_chat_tc_tvc_route_worker import CURRENT, LEGACY, normalize, sovereign_child_env


def test_sovereign_route_wrapper_uses_minimal_environment(monkeypatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "forbidden")
    monkeypatch.setenv("GH_TOKEN", "forbidden")
    monkeypatch.setenv("ACTIONS_RUNTIME_TOKEN", "forbidden")
    monkeypatch.setenv("ZEROEX_API_KEY", "forbidden")
    monkeypatch.setenv("OPENAI_API_KEY", "forbidden")
    env = sovereign_child_env()
    assert set(env) == {"PATH", "PYTHONPATH", "LANG", "LC_ALL"}
    assert "GITHUB_TOKEN" not in env
    assert "GH_TOKEN" not in env
    assert "ACTIONS_RUNTIME_TOKEN" not in env
    assert "ZEROEX_API_KEY" not in env
    assert "OPENAI_API_KEY" not in env


def test_normalize_rewrites_only_legacy_credential_authority_value() -> None:
    value = {
        "credential_authority": LEGACY,
        "route_authority": "StegVerse-Labs/TVC",
        "historical_ref": "StegVerse-Labs/TV:policies/example.json",
        "nested": [{"credential_authority": LEGACY}],
    }
    result = normalize(value)
    assert result["credential_authority"] == CURRENT
    assert result["nested"][0]["credential_authority"] == CURRENT
    assert result["route_authority"] == "StegVerse-Labs/TVC"
    assert result["historical_ref"] == "StegVerse-Labs/TV:policies/example.json"
