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
        "task_0007_git_blob_sha":"a5fd4662b2a370e8a86099c943b8d1ec18b93e19",
        "task_0008_git_blob_sha":"f534167633c867bbee6b397ae345b10ed502aa2b",
        "claims_git_blob_sha":"9e7eaf9cb1319dd570714a0c1806d7173a7ba7ff",
        "queue_git_blob_sha":"6cab961c8750495dab36d1a523980516b1ac3a5e",
    }
    assert pkg["claims_state"]["generation"]==2
    assert pkg["claims_state"]["claims"]==[]

def test_canonical_priority_selects_0007_before_0008_then_0008_remains_nonconflicting():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    tasks=sorted(pkg["tasks"],key=lambda t:(PRIORITY[t["priority_class"]],t["requested_at"],t["task_id"]))
    assert [t["task_id"] for t in tasks]==["TASK-2026-0007","TASK-2026-0008"]
    assert _surface(tasks[0])=={"site:unified-conversational-capability-contract"}
    assert _surface(tasks[1])=={"site:stegos-de006-bound-inference-publication"}
    assert _surface(tasks[0]).isdisjoint(_surface(tasks[1]))
    # Therefore after TASK-0007 is active, TASK-0008 is still dependency-surface admissible.
    assert tasks[1]["dependencies"]==[]

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
