from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "org_allocator" / "portable_allocator.js"
PACKAGE = ROOT / "control" / "portable-org-allocator" / "current-iphone-package-task0012.json"
TASK = ROOT / "tasks" / "TASK-2026-0012.json"


def run_node(script: str):
    node = shutil.which("node")
    if node is None:
        return None
    return subprocess.run(
        [node, "-e", script, str(MODULE), str(PACKAGE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_task0012_package_is_exact_non_widening_carrier_successor():
    pkg = json.loads(PACKAGE.read_text(encoding="utf-8"))
    task = json.loads(TASK.read_text(encoding="utf-8"))
    assert pkg["retained_state_required"] is True
    assert pkg["portable_authority_epoch"] == "ORG-ALLOCATOR-PORTABLE-IPHONE-20260902"
    assert pkg["immediate_target_task_id"] == "TASK-2026-0012"
    assert pkg["tasks"] == [task]
    assert pkg["source_binding"]["task_0012_git_blob_sha"] == "9c521a97803f3ed353c86640bb77d135952b3310"
    assert task["supersedes"] == "TASK-2026-0011"
    assert task["predecessor_provenance"]["allocator_generation"] == 7
    assert task["predecessor_provenance"]["allocator_fence"] == 7
    assert task["predecessor_provenance"]["reactivation_or_scope_widening_allowed"] is False
    assert task["dependencies"] == []
    successor = task["source_successor"]
    assert successor["source_floor_commit"] == "67dc40e8b78ed8566d598a2aa87b52536a534878"
    assert successor["actual_source_commit"] is None
    assert successor["actual_source_commit_must_equal_or_descend_from_floor"] is True
    assert task["evidence_constraints"]["old_task0011_unsigned_ipa_source_commit"] == "32115e32d701e783af2c2659a900e4bc90460fd2"
    assert task["evidence_constraints"]["old_package_may_satisfy_packet_tunnel_runtime"] is False
    assert task["evidence_constraints"]["metadata_only_refresh_allowed"] is False


def test_retained_g7_claim_blocks_task0012_without_generation_advance():
    script = r'''
const fs=require("fs");
const {webcrypto}=require("crypto");
if(!global.crypto){global.crypto=webcrypto;}
require(process.argv[1]);
const pkg=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const api=global.StegVersePortableOrgClaimAllocator;
api.validatePackage(pkg);
const state=api.initialState(pkg);
state.claims_state.generation=7;
state.queue_state.generation=5;
state.task_statuses={"TASK-2026-0011":"active","TASK-2026-0012":"queued"};
state.claims_state.claims=[{
  repository:{host:"github.com",owner:"StegVerse-Labs",name:"Site",full_name:"StegVerse-Labs/Site",default_branch:"main"},
  mode:"scoped_exclusive",preemptible:true,
  scope:{
    paths:["stegos-bootstrap/current-iphone-kv-testflight.html","stegos-bootstrap/current-iphone-kv-testflight-bootstrap.js"],
    contracts:["stegos.kv-bound-ephemeral-projection-context/v1"],
    release_surfaces:["site:current-iphone-kv-testflight-static-bootstrap"],
    capabilities:["current-iphone-kv-testflight-entry","kv-bound-ephemeral-projection-gate"],
    workflows:[],
    dependency_surfaces:["site:current-iphone-kv-testflight-static-bootstrap"]
  },
  task_id:"TASK-2026-0011",
  lease:{fencing_token:7}
}];
let committed=null;
const store={read:()=>Promise.resolve(state),atomicCompareAndSwap:(oldState,nextState)=>{committed=nextState;return Promise.resolve(true);}};
api.allocate(pkg,store,{now_ms:1789343000000}).then(result=>{
  if(result.receipt.selected!==null) throw new Error("TASK-0012 selected while G7/F7 predecessor claim remained active");
  if(result.receipt.claim_registry_generation!==7) throw new Error("generation advanced on conflict");
  if(committed.claims_state.claims.length!==1) throw new Error("active G7 claim changed");
  console.log("TASK_0012_G7_CONFLICT_FAIL_CLOSED_PASS");
}).catch(err=>{console.error(err);process.exit(1);});
'''
    result = run_node(script)
    if result is None:
        return
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TASK_0012_G7_CONFLICT_FAIL_CLOSED_PASS" in result.stdout


def test_released_g7_lineage_allocates_task0012_at_generation_8_fence_8():
    script = r'''
const fs=require("fs");
const {webcrypto}=require("crypto");
if(!global.crypto){global.crypto=webcrypto;}
require(process.argv[1]);
const pkg=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const api=global.StegVersePortableOrgClaimAllocator;
api.validatePackage(pkg);
const state=api.initialState(pkg);
state.claims_state.generation=7;
state.queue_state.generation=5;
state.task_statuses={"TASK-2026-0011":"completed","TASK-2026-0012":"queued"};
state.claims_state.claims=[];
let committed=null;
const store={read:()=>Promise.resolve(state),atomicCompareAndSwap:(oldState,nextState)=>{committed=nextState;return Promise.resolve(true);}};
api.allocate(pkg,store,{now_ms:1789343000000}).then(result=>{
  if(result.receipt.selected!=="TASK-2026-0012") throw new Error("TASK-0012 not selected after G7 claim release");
  if(result.receipt.claim_registry_generation!==8) throw new Error("generation not 8");
  if(!result.claim_observation||result.claim_observation.fencing_tokens.join(",")!=="8") throw new Error("fence not 8");
  if(committed.task_statuses["TASK-2026-0012"]!=="active") throw new Error("TASK-0012 not activated in retained state");
  if(committed.claims_state.claims.length!==1) throw new Error("unexpected claim count");
  console.log("TASK_0012_G8_SUCCESSOR_PASS");
}).catch(err=>{console.error(err);process.exit(1);});
'''
    result = run_node(script)
    if result is None:
        return
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TASK_0012_G8_SUCCESSOR_PASS" in result.stdout
