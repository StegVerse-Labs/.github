from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"control/portable-org-allocator/current-iphone-package.json"
MODULE=ROOT/"org_allocator/portable_allocator.js"
HANDOFF=ROOT/"docs/PORTABLE_ORG_CLAIM_ALLOCATOR_IPHONE_MIRROR_HANDOFF.md"

PRIORITY={"security":0,"release":1,"critical":2,"elevated":3,"normal":4}

def _surface(task):
    req=task["requirements"]["mandatory"][0]
    return set(req["scope"]["dependency_surfaces"])

def test_portable_allocator_package_is_exact_current_floor():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert pkg["schema"]=="stegverse.org-allocator-portable-package/v1"
    assert pkg["canonical_authority_owner"]=="StegVerse-Labs/.github organization allocator"
    assert pkg["execution_surface"]=="CURRENT_USER_IPHONE"
    assert pkg["credential_authority"]=="TV/TVC"
    assert pkg["github_token_runtime_authority"]=="NONE"
    assert pkg["heartbeat_grants_claim_authority"] is False
    assert pkg["request_grants_claim_authority"] is False
    assert pkg["stegos_grants_claim_authority"] is False
    assert pkg["requires_other_machine"] is False
    assert pkg["second_user_operated_device_required"] is False
    assert pkg["always_on_external_host_required"] is False
    assert pkg["source_binding"]=={
        "allocator_git_blob_sha":"7c0105c8529b682c24a94b39ba31a8ca574c3717",
        "task_0007_git_blob_sha":"8d3cada7cd3b545620f8dd3cdc6e31e799f82339",
        "task_0008_git_blob_sha":"f534167633c867bbee6b397ae345b10ed502aa2b",
        "claims_git_blob_sha":"9e7eaf9cb1319dd570714a0c1806d7173a7ba7ff",
        "queue_git_blob_sha":"6cab961c8750495dab36d1a523980516b1ac3a5e",
    }
    assert pkg["claims_state"]["generation"]==2
    assert pkg["claims_state"]["claims"]==[]

def test_completed_0007_is_retained_as_history_but_not_fresh_device_candidate():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    by_id={t["task_id"]:t for t in pkg["tasks"]}
    assert by_id["TASK-2026-0007"]["status"]=="completed"
    assert by_id["TASK-2026-0007"]["completed_at"]=="2026-08-22T12:23:32Z"
    assert by_id["TASK-2026-0007"]["completion_evidence"]["merge_commit"]=="cdf68fe70294d43b59607c2991478c2cc4b53546"
    assert by_id["TASK-2026-0007"]["completion_evidence"]["portable_allocator_runtime_history"]["current_iphone_claim_generation"]==3
    assert by_id["TASK-2026-0008"]["status"]=="queued"
    queued=[t for t in pkg["tasks"] if t["status"]=="queued"]
    assert [t["task_id"] for t in queued]==["TASK-2026-0008"]
    assert _surface(by_id["TASK-2026-0007"])=={"site:unified-conversational-capability-contract"}
    assert _surface(by_id["TASK-2026-0008"])=={"site:stegos-de006-bound-inference-publication"}
    assert _surface(by_id["TASK-2026-0007"]).isdisjoint(_surface(by_id["TASK-2026-0008"]))
    assert pkg["catalog_reconciliation"]["task_0007"]["fresh_device_eligible"] is False
    assert pkg["catalog_reconciliation"]["task_0008"]["fresh_device_eligible"] is True

def test_portable_module_preserves_native_allocator_semantics_and_authority():
    text=MODULE.read_text(encoding="utf-8")
    for marker in [
        'var PRIORITY={security:0,release:1,critical:2,elevated:3,normal:4}',
        'dependencySurfaces(request),dependencySurfaces(active)',
        'request.repository.full_name!==active.repository.full_name',
        'request.mode==="repository_exclusive"||active.mode==="repository_exclusive"',
        'generation+=1',
        'fencing_token:generation',
        'selected.task_id',
        'task7.completed_at',
        'portable allocator TASK-0007 completion evidence mismatch',
        'atomicCompareAndSwap',
        'CLAIM_AUTHORITY_ONLY_WHEN_SELECTED_BY_CANONICAL_ALLOCATOR',
        'NONE_OBSERVATION_ONLY',
        'canonical_authority_owner:"StegVerse-Labs/.github organization allocator"',
        'execution_surface:"CURRENT_USER_IPHONE"',
        'requires_other_machine:false',
    ]:
        assert marker in text
    assert "GITHUB_TOKEN" not in text
    assert "fetch(" not in text

def test_bootstrap_deadlock_is_not_hidden():
    text=HANDOFF.read_text(encoding="utf-8")
    assert "Bootstrap circularity" in text
    assert "must not solve that by bypassing the claim gate" in text
