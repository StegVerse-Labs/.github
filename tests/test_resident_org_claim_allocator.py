from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


allocator = load_module("resident_org_allocator_test", "scripts/allocate_claims.py")
consumer = load_module("resident_org_allocator_consumer_test", "scripts/consume_org_claim_allocator_request.py")


def request() -> dict:
    return json.loads(
        (ROOT / "control/resident-execution-request.d/org-claim-allocator-001.json").read_text(encoding="utf-8")
    )


def test_request_is_repeatable_intent_not_claim_authority():
    value = request()
    assert value["task_id"] == "SHWP-ORG-CLAIM-ALLOCATOR-001"
    assert value["mode"] == "CANONICAL_ORGANIZATION_CLAIM_ALLOCATION"
    assert value["repeat_on_resident_dispatch"] is True
    assert value["request_grants_claim_authority"] is False
    assert value["allocator_remains_claim_authority"] is True
    assert value["heartbeat_grants_execution_authority"] is False
    assert value["github_token_required"] is False
    assert value["network_source_fetch_allowed"] is False
    assert value["second_machine_required"] is False
    assert value["authority_effect"] == "NONE_REQUEST_ONLY"


def test_allocator_lock_blocks_live_concurrent_owner_without_granting_authority():
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "allocator.lock"
        first = allocator.acquire_allocator_lock(path)
        try:
            assert first["acquired"] is True
            second = allocator.acquire_allocator_lock(path)
            assert second["acquired"] is False
            assert second["state"] == "ALLOCATOR_BUSY"
            assert second["owner_pid"] == os.getpid()
            assert second["authority_effect"] == "NONE_SERIALIZATION_ONLY"
        finally:
            allocator.release_allocator_lock(path)
        assert not path.exists()


def test_resident_consumer_invokes_existing_allocator_and_retains_authority_boundary():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        runtime = base / "runtime"
        source = base / "source"
        request_path = runtime / consumer.REQUEST_REL
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request()), encoding="utf-8")
        allocator_path = runtime / consumer.ALLOCATOR_REL
        allocator_path.parent.mkdir(parents=True, exist_ok=True)
        allocator_path.write_text("# canonical allocator\n", encoding="utf-8")
        calls = []

        def runner(command, **kwargs):
            calls.append((command, kwargs))
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps({
                    "selected": "TASK-2026-0008",
                    "queued": ["TASK-2026-0008"],
                    "blocked_missing_dependency_declaration": [],
                    "state": "ALLOCATION_COMPLETE",
                    "authority_effect": "CLAIM_AUTHORITY_ONLY_WHEN_SELECTED_BY_CANONICAL_ALLOCATOR",
                }) + "\n",
                stderr="",
            )

        result = consumer.consume(source, runtime, runner=runner, env={"PATH": "/bin", "HOME": td})
        assert result["state"] == "ATTEMPT_RECORDED"
        assert result["selected_task_id"] == "TASK-2026-0008"
        assert result["claim_grant_occurred"] is True
        assert result["request_granted_claim_authority"] is False
        assert result["allocator_remains_claim_authority"] is True
        assert result["heartbeat_grants_execution_authority"] is False
        assert result["github_token_required"] is False
        assert result["network_source_fetch_performed"] is False
        assert result["second_machine_required"] is False
        assert len(calls) == 1


def test_resident_consumer_rejects_hosted_environment_before_allocator_invocation():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        runtime = base / "runtime"
        request_path = runtime / consumer.REQUEST_REL
        request_path.parent.mkdir(parents=True, exist_ok=True)
        request_path.write_text(json.dumps(request()), encoding="utf-8")
        allocator_path = runtime / consumer.ALLOCATOR_REL
        allocator_path.parent.mkdir(parents=True, exist_ok=True)
        allocator_path.write_text("# canonical allocator\n", encoding="utf-8")
        calls = []
        try:
            consumer.consume(
                base / "source",
                runtime,
                runner=lambda *a, **k: calls.append((a, k)),
                env={"PATH": "/bin", "GITHUB_ACTIONS": "true"},
            )
        except RuntimeError as exc:
            assert "hosted environment" in str(exc)
        else:
            raise AssertionError("hosted environment must fail closed")
        assert calls == []


def test_resident_dispatch_and_materialization_wiring_present():
    dispatcher = (ROOT / "scripts/dispatch_resident_execution_requests.py").read_text(encoding="utf-8")
    bootstrap = (ROOT / "scripts/bootstrap_sovereign_runtime.py").read_text(encoding="utf-8")
    installer = (ROOT / "scripts/install_sovereign_heartbeat_service.py").read_text(encoding="utf-8")
    refresh = (ROOT / "scripts/refresh_sovereign_worker_runtime_source.py").read_text(encoding="utf-8")
    assert '("org_claim_allocator", "scripts/consume_org_claim_allocator_request.py")' in dispatcher
    for source in (bootstrap, installer, refresh):
        assert "consume_org_claim_allocator_request.py" in source
        assert "org-claim-allocator-001.json" in source
