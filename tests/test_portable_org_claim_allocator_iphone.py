from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/"control/portable-org-allocator/current-iphone-package.json"
MODULE=ROOT/"org_allocator/portable_allocator.js"
HANDOFF=ROOT/"docs/PORTABLE_ORG_CLAIM_ALLOCATOR_IPHONE_MIRROR_HANDOFF.md"

PRIORITY={"security":0,"release":1,"critical":2,"elevated":3,"normal":4}

def _surface(task):
    req=task["requirements"]["mandatory"][0]
    return set(req["scope"]["dependency_surfaces"])

def _paths(task):
    req=task["requirements"]["mandatory"][0]
    return set(req["scope"]["paths"])

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
        "task_0009_git_blob_sha":"eeb661ca59f305ce8a86c2f46adced37056baec8",
        "claims_git_blob_sha":"9e7eaf9cb1319dd570714a0c1806d7173a7ba7ff",
        "queue_git_blob_sha":"6cab961c8750495dab36d1a523980516b1ac3a5e",
    }
    assert pkg["claims_state"]["generation"]==2
    assert pkg["claims_state"]["claims"]==[]
    assert pkg["immediate_target_task_id"]=="TASK-2026-0009"
    assert pkg["immediate_target_dependency_surface"]=="site:hb31-ecosystem-chat-runtime-opportunity-successor"

def test_canonical_priority_and_successor_scope_are_nonconflicting():
    pkg=json.loads(PACKAGE.read_text(encoding="utf-8"))
    tasks=sorted(pkg["tasks"],key=lambda t:(PRIORITY[t["priority_class"]],t["requested_at"],t["task_id"]))
    assert [t["task_id"] for t in tasks]==["TASK-2026-0007","TASK-2026-0008","TASK-2026-0009"]
    assert _surface(tasks[0])=={"site:unified-conversational-capability-contract"}
    assert _surface(tasks[1])=={"site:stegos-de006-bound-inference-publication"}
    assert _surface(tasks[2])=={"site:hb31-ecosystem-chat-runtime-opportunity-successor"}
    assert _surface(tasks[2]).isdisjoint(_surface(tasks[0]))
    assert _surface(tasks[2]).isdisjoint(_surface(tasks[1]))
    assert _paths(tasks[2]).isdisjoint(_paths(tasks[0]))
    assert _paths(tasks[2]).isdisjoint(_paths(tasks[1]))
    assert tasks[2]["dependencies"]==[]
    assert tasks[2]["predecessor_provenance"]["allocator_fence"]==4
    assert tasks[2]["predecessor_provenance"]["reactivation_allowed"] is False

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
        'TASK-2026-0007|TASK-2026-0008|TASK-2026-0009',
        'site:hb31-ecosystem-chat-runtime-opportunity-successor',
    ]:
        assert marker in text
    assert "GITHUB_TOKEN" not in text
    assert "fetch(" not in text

def test_existing_g3_g4_state_can_allocate_distinct_task_0009_at_generation_5():
    node=shutil.which("node")
    if node is None:
        return
    script=r'''
const fs=require("fs");
const {webcrypto}=require("crypto");
if(!global.crypto){global.crypto=webcrypto;}
require(process.argv[1]);
const pkg=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const api=global.StegVersePortableOrgClaimAllocator;
api.validatePackage(pkg);
const state=api.initialState(pkg);
state.claims_state.generation=4;
state.task_statuses["TASK-2026-0007"]="active";
state.task_statuses["TASK-2026-0008"]="active";
delete state.task_statuses["TASK-2026-0009"];
function held(taskId){
  const t=pkg.tasks.find(x=>x.task_id===taskId);
  const c=JSON.parse(JSON.stringify(t.requirements.mandatory[0]));
  c.task_id=taskId;
  c.lease={fencing_token:taskId.endsWith("0007")?3:4};
  return c;
}
state.claims_state.claims=[held("TASK-2026-0007"),held("TASK-2026-0008")];
let committed=null;
const store={read:()=>Promise.resolve(state),atomicCompareAndSwap:(oldState,nextState)=>{committed=nextState;return Promise.resolve(true);}};
api.allocate(pkg,store,{now_ms:1788701400000}).then(result=>{
  if(result.receipt.selected!=="TASK-2026-0009") throw new Error("TASK-0009 not selected");
  if(result.receipt.claim_registry_generation!==5) throw new Error("generation not 5");
  if(result.claim_observation.fencing_tokens.join(",")!=="5") throw new Error("fence not 5");
  if(committed.task_statuses["TASK-2026-0007"]!=="active"||committed.task_statuses["TASK-2026-0008"]!=="active") throw new Error("prior task state reset");
  if(committed.task_statuses["TASK-2026-0009"]!=="active") throw new Error("successor not active");
  if(committed.claims_state.claims.length!==3) throw new Error("prior claims not retained");
  console.log("TASK_0009_G5_SUCCESSOR_ALLOCATION_PASS");
}).catch(err=>{console.error(err);process.exit(1);});
'''
    result=subprocess.run([node,"-e",script,str(MODULE),str(PACKAGE)],cwd=ROOT,text=True,capture_output=True,check=False)
    assert result.returncode==0,result.stdout+result.stderr
    assert "TASK_0009_G5_SUCCESSOR_ALLOCATION_PASS" in result.stdout

def test_bootstrap_deadlock_is_not_hidden():
    text=HANDOFF.read_text(encoding="utf-8")
    assert "Bootstrap circularity" in text
    assert "must not solve that by bypassing the claim gate" in text
