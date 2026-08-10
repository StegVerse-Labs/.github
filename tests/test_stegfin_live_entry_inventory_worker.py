from __future__ import annotations

from pathlib import Path

from workers.stegfin_live_entry_inventory_worker import child_env, verified_inventory_envelope


def envelope() -> dict:
    return {
        "inventory": {
            "schema": "stegwallet.base_asset_lounge_snapshot.v1",
            "chain_id": "0x2105",
            "inventory_state_hash": "sha256:inventory",
            "boundary_state_hash": "sha256:boundary",
            "assets": [
                {"symbol": "ETH"},
                {"symbol": "USDC"},
                {"symbol": "WETH"},
            ],
        },
        "observation_receipt": {
            "schema": "stegwallet.live_inventory_observation_receipt.v1",
            "state": "INVENTORY_N_OBSERVED",
            "complete_current_asset_inventory": True,
            "provider_capability_required": False,
            "github_token_required": False,
            "github_runtime_required": False,
            "wallet_contacted": False,
            "signed": False,
            "broadcast": False,
            "trade_authority_granted": False,
            "authority_effect": "NONE_OBSERVATION_ONLY",
            "inventory_state_hash": "sha256:inventory",
            "boundary_state_hash": "sha256:boundary",
        },
    }


def test_inventory_envelope_requires_complete_non_authorizing_observation() -> None:
    value = envelope()
    assert verified_inventory_envelope(value) is True
    value["observation_receipt"]["trade_authority_granted"] = True
    assert verified_inventory_envelope(value) is False


def test_inventory_envelope_rejects_state_hash_drift() -> None:
    value = envelope()
    value["observation_receipt"]["inventory_state_hash"] = "sha256:other"
    assert verified_inventory_envelope(value) is False


def test_child_environment_contains_no_github_provider_or_wallet_credentials(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "forbidden")
    monkeypatch.setenv("GH_TOKEN", "forbidden")
    monkeypatch.setenv("ZEROEX_API_KEY", "forbidden")
    monkeypatch.setenv("WALLET_PRIVATE_KEY", "forbidden")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "forbidden")
    env = child_env(tmp_path)
    assert set(env) == {"PATH", "PYTHONPATH", "LANG", "LC_ALL"}
    assert env["PYTHONPATH"] == str(tmp_path)
    assert "GITHUB_TOKEN" not in env
    assert "GH_TOKEN" not in env
    assert "ZEROEX_API_KEY" not in env
    assert "WALLET_PRIVATE_KEY" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env
