from __future__ import annotations

import json
from pathlib import Path
import subprocess

from scripts.install_sovereign_heartbeat_service import materialize_service
from scripts.run_worker_runtime import poll_resident_rendezvous


def test_native_worker_service_receives_non_secret_rendezvous_config(tmp_path, monkeypatch):
    config_home = tmp_path / "config"
    env = {
        "XDG_CONFIG_HOME": str(config_home),
        "STEGVERSE_RESIDENT_RENDEZVOUS_URL": "https://stegverse.org",
        "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF": "node:primary",
    }
    result = materialize_service(
        tmp_path / "runtime",
        system="linux",
        env=env,
    )
    worker = Path(result["worker_registration_path"]).read_text(encoding="utf-8")
    carrier = Path(result["carrier_registration_path"]).read_text(encoding="utf-8")
    assert "STEGVERSE_RESIDENT_RENDEZVOUS_URL=https://stegverse.org" in worker
    assert "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF=node:primary" in worker
    assert "STEGVERSE_RESIDENT_RENDEZVOUS_URL" not in carrier
    assert result["resident_rendezvous_configured"] is True
    assert result["resident_rendezvous_grants_execution_authority"] is False


def test_native_worker_service_derives_node_ref_from_canonical_declaration(tmp_path):
    marker = tmp_path / "node.json"
    marker.write_text(
        json.dumps({
            "schema": "stegverse.sovereign-node-declaration/v0.4",
            "declared": True,
            "node_id": "SV-NODE-" + "a" * 24,
            "credential_authority": "TV/TVC",
            "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
        }),
        encoding="utf-8",
    )
    result = materialize_service(
        tmp_path / "runtime",
        system="linux",
        env={
            "XDG_CONFIG_HOME": str(tmp_path / "config"),
            "STEGVERSE_RESIDENT_RENDEZVOUS_URL": "https://stegverse.org",
            "STEGVERSE_SOVEREIGN_NODE_MARKER": str(marker),
        },
    )
    worker = Path(result["worker_registration_path"]).read_text(encoding="utf-8")
    assert "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF=SV-NODE-" + "a" * 24 in worker
    assert result["resident_rendezvous_node_ref"] == "SV-NODE-" + "a" * 24
    assert result["resident_rendezvous_configured"] is True


def test_native_worker_service_rejects_noncanonical_derived_node_ref(tmp_path):
    marker = tmp_path / "node.json"
    marker.write_text(
        json.dumps({
            "schema": "stegverse.sovereign-node-declaration/v0.4",
            "declared": True,
            "node_id": "node:primary",
            "credential_authority": "TV/TVC",
            "authority_effect": "RUNTIME_ELIGIBILITY_ONLY_NO_CREDENTIAL_OR_ROUTE_AUTHORITY",
        }),
        encoding="utf-8",
    )
    try:
        materialize_service(
            tmp_path / "runtime",
            system="linux",
            env={
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "STEGVERSE_RESIDENT_RENDEZVOUS_URL": "https://stegverse.org",
                "STEGVERSE_SOVEREIGN_NODE_MARKER": str(marker),
            },
        )
    except RuntimeError as exc:
        assert "node ref required" in str(exc)
    else:
        raise AssertionError("noncanonical derived node ref should fail closed")


def test_rendezvous_config_requires_https(tmp_path):
    try:
        materialize_service(
            tmp_path / "runtime",
            system="linux",
            env={
                "XDG_CONFIG_HOME": str(tmp_path / "config"),
                "STEGVERSE_RESIDENT_RENDEZVOUS_URL": "http://example.test",
                "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF": "node:primary",
            },
        )
    except RuntimeError as exc:
        assert "must use https" in str(exc)
    else:
        raise AssertionError("non-HTTPS rendezvous URL should fail closed")


def test_worker_runtime_poll_invokes_only_rendezvous_consumer(tmp_path):
    root = tmp_path
    script = root / "scripts" / "consume_resident_rendezvous.py"
    script.parent.mkdir(parents=True)
    script.write_text("# placeholder\n", encoding="utf-8")

    receipt_path = root / "receipts" / "sovereign-host" / "resident-rendezvous-consumption.latest.json"
    receipt_path.parent.mkdir(parents=True)

    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        receipt_path.write_text(
            json.dumps({
                "schema": "stegverse.resident-rendezvous.local-consumption/v1",
                "state": "NO_REQUEST",
                "runtime_execution_attempted": False,
                "gateway_execution_authority": "NONE",
                "credential_authority": "TV/TVC",
                "authority_effect": "NONE",
            }),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, "", "")

    result = poll_resident_rendezvous(
        root,
        runner=runner,
        env={
            "PATH": "/usr/bin",
            "STEGVERSE_RESIDENT_RENDEZVOUS_URL": "https://stegverse.org",
            "STEGVERSE_RESIDENT_RENDEZVOUS_NODE_REF": "node:primary",
        },
    )
    assert result["state"] == "NO_REQUEST"
    assert result["gateway_execution_authority"] == "NONE"
    assert result["worker_coordinator_remains_execution_admission_authority"] is True
    assert len(calls) == 1
    assert str(script) in calls[0]


def test_worker_runtime_poll_is_noop_when_not_configured(tmp_path):
    assert poll_resident_rendezvous(tmp_path, env={"PATH": "/usr/bin"}) is None
