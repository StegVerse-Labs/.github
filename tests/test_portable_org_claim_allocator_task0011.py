from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "org_allocator" / "portable_allocator.js"
PACKAGE = ROOT / "control" / "portable-org-allocator" / "current-iphone-package-task0011.json"
TASK = ROOT / "tasks" / "TASK-2026-0011.json"


def test_task0011_package_is_exact_delta_successor():
    pkg = json.loads(PACKAGE.read_text(encoding="utf-8"))
    task = json.loads(TASK.read_text(encoding="utf-8"))
    assert pkg["retained_state_required"] is True
    assert pkg["immediate_target_task_id"] == "TASK-2026-0011"
    assert pkg["tasks"] == [task]
    assert pkg["source_binding"]["task_0011_git_blob_sha"] == "a9f90414e59e308d66faf7ff2d5c31173b1687ca"
    scope = task["requirements"]["mandatory"][0]["scope"]
    assert scope["dependency_surfaces"] == ["site:current-iphone-kv-testflight-static-bootstrap"]
    assert "stegos-bootstrap/kv-bound-ephemeral-projection-context.js" in scope["paths"]
    assert "stegos-bootstrap/kv-projection-file-loader.js" in scope["paths"]
    assert "stegos-bootstrap/current-iphone-testflight.html" not in scope["paths"]
    assert task["predecessor_provenance"]["reactivation_or_scope_widening_allowed"] is False


def test_retained_g6_state_allocates_delta_successor_at_generation_7():
    node = shutil.which("node")
    if node is None:
        return
    script = r'''
const fs=require("fs");
const {webcrypto}=require("crypto");
if(!global.crypto){global.crypto=webcrypto;}
require(process.argv[1]);
const pkg=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const api=global.StegVersePortableOrgClaimAllocator;
api.validatePackage(pkg);
const state=api.initialState(pkg);
state.claims_state.generation=6;
state.queue_state.generation=4;
state.task_statuses={"TASK-2026-0007":"active","TASK-2026-0008":"active","TASK-2026-0009":"active","TASK-2026-0010":"active"};
state.claims_state.claims=[{
  repository:{host:"github.com",owner:"StegVerse-Labs",name:"Site",full_name:"StegVerse-Labs/Site",default_branch:"main"},
  mode:"scoped_exclusive",
  preemptible:true,
  scope:{
    paths:["stegos-bootstrap/current-iphone-testflight.html","stegos-bootstrap/current-iphone-testflight-bootstrap.js"],
    contracts:["stegverse.current-iphone-ipa-signing-executor/v1"],
    release_surfaces:["site:current-iphone-testflight-static-bootstrap"],
    capabilities:["current-iphone-testflight-static-bootstrap-projection"],
    workflows:[],
    dependency_surfaces:["site:current-iphone-testflight-static-bootstrap"]
  },
  task_id:"TASK-2026-0010",
  lease:{fencing_token:6}
}];
let committed=null;
const store={read:()=>Promise.resolve(state),atomicCompareAndSwap:(oldState,nextState)=>{committed=nextState;return Promise.resolve(true);}};
api.allocate(pkg,store,{now_ms:1789092000000}).then(result=>{
  if(result.receipt.selected!=="TASK-2026-0011") throw new Error("TASK-0011 not selected");
  if(result.receipt.claim_registry_generation!==7) throw new Error("generation not 7");
  if(result.claim_observation.fencing_tokens.join(",")!=="7") throw new Error("fence not 7");
  if(committed.claims_state.claims.length!==2) throw new Error("G6 claim not retained");
  if(committed.task_statuses["TASK-2026-0011"]!=="active") throw new Error("successor not active");
  console.log("TASK_0011_G7_DELTA_SUCCESSOR_PASS");
}).catch(err=>{console.error(err);process.exit(1);});
'''
    result = subprocess.run(
        [node, "-e", script, str(MODULE), str(PACKAGE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TASK_0011_G7_DELTA_SUCCESSOR_PASS" in result.stdout


def test_task0011_scope_conflicts_with_same_dependency_surface():
    node = shutil.which("node")
    if node is None:
        return
    script = r'''
const fs=require("fs");
const {webcrypto}=require("crypto");
if(!global.crypto){global.crypto=webcrypto;}
require(process.argv[1]);
const pkg=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const api=global.StegVersePortableOrgClaimAllocator;
const state=api.initialState(pkg);
state.claims_state.generation=6;
state.task_statuses={};
state.claims_state.claims=[{
  repository:{host:"github.com",owner:"StegVerse-Labs",name:"Site",full_name:"StegVerse-Labs/Site",default_branch:"main"},
  mode:"scoped_exclusive",preemptible:true,
  scope:{paths:["other"],contracts:[],release_surfaces:[],capabilities:[],workflows:[],dependency_surfaces:["site:current-iphone-kv-testflight-static-bootstrap"]},
  task_id:"HELD",lease:{fencing_token:6}
}];
let committed=null;
const store={read:()=>Promise.resolve(state),atomicCompareAndSwap:(oldState,nextState)=>{committed=nextState;return Promise.resolve(true);}};
api.allocate(pkg,store,{now_ms:1789092000000}).then(result=>{
  if(result.receipt.selected!==null) throw new Error("conflicting successor selected");
  if(result.receipt.claim_registry_generation!==6) throw new Error("generation changed on conflict");
  console.log("TASK_0011_CONFLICT_FAIL_CLOSED_PASS");
}).catch(err=>{console.error(err);process.exit(1);});
'''
    result = subprocess.run(
        [node, "-e", script, str(MODULE), str(PACKAGE)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "TASK_0011_CONFLICT_FAIL_CLOSED_PASS" in result.stdout
