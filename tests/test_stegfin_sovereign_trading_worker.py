from __future__ import annotations
import json
from pathlib import Path

from workers.stegfin_sovereign_trading_worker import env

ROOT=Path(__file__).resolve().parents[1]


def test_worker_child_environment_strips_github_provider_wallet_and_cloud_credentials(monkeypatch,tmp_path:Path)->None:
    for name in ("GITHUB_TOKEN","GH_TOKEN","ZEROEX_API_KEY","WALLET_PRIVATE_KEY","AWS_SECRET_ACCESS_KEY","CLOUDFLARE_API_TOKEN"):
        monkeypatch.setenv(name,"forbidden")
    child=env(tmp_path)
    assert set(child)=={"PATH","PYTHONPATH","LANG","LC_ALL"}
    assert child["PYTHONPATH"]==str(tmp_path)
    for name in ("GITHUB_TOKEN","GH_TOKEN","ZEROEX_API_KEY","WALLET_PRIVATE_KEY","AWS_SECRET_ACCESS_KEY","CLOUDFLARE_API_TOKEN"):
        assert name not in child


def test_registry_fragment_uniquely_binds_internal_activation_worker()->None:
    fragment=json.loads((ROOT/"control/worker-registry.d/stegfin-sovereign-trading-001.json").read_text())
    task=fragment["tasks"][0]; worker=fragment["workers"][0]
    capability="stegfin_sovereign_internal_trading_activation"
    assert task["task_id"]=="SHWP-STEGFIN-SOVEREIGN-TRADING-001"
    assert worker["worker_id"]=="stegfin-sovereign-trading-worker"
    assert capability in worker["capabilities"]
    assert fragment["github_token_required"] is False
    assert fragment["wallet_signing_authority"] is False
    assert fragment["transaction_broadcast_authority"] is False


def test_handoff_has_zero_external_financial_authority()->None:
    handoff=json.loads((ROOT/"handoffs/SHWP-STEGFIN-SOVEREIGN-TRADING-001.json").read_text())
    caps=set(handoff["execution"]["required_capabilities"])
    assert "stegfin_sovereign_internal_trading_activation" in caps
    assert handoff["execution"]["external_cost_ceiling_usd"]==0
    ceiling=set(handoff["goal"]["authority_ceiling"])
    assert "no_wallet_signing" in ceiling
    assert "no_transaction_broadcast" in ceiling
    assert "no_external_custody" in ceiling
    assert "no_scale_up" in ceiling
    assert handoff["authority"]["heartbeat_grants_execution_authority"] is False
