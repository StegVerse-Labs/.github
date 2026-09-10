from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "control/portable-org-allocator/current-iphone-package.json"
MODULE = ROOT / "org_allocator/portable_allocator.js"


class PortableOrgAllocatorCollisionTests(unittest.TestCase):
    def test_task_0010_scope_is_disjoint_from_live_g5_task_0009_claim(self) -> None:
        pkg = json.loads(PACKAGE.read_text(encoding="utf-8"))
        by_id = {task["task_id"]: task for task in pkg["tasks"]}
        t9 = by_id["TASK-2026-0009"]["requirements"]["mandatory"][0]["scope"]
        t10 = by_id["TASK-2026-0010"]["requirements"]["mandatory"][0]["scope"]
        self.assertTrue(set(t9["paths"]).isdisjoint(set(t10["paths"])))
        self.assertTrue(set(t9["contracts"]).isdisjoint(set(t10["contracts"])))
        self.assertTrue(set(t9["release_surfaces"]).isdisjoint(set(t10["release_surfaces"])))
        self.assertTrue(set(t9["capabilities"]).isdisjoint(set(t10["capabilities"])))
        self.assertTrue(set(t9["dependency_surfaces"]).isdisjoint(set(t10["dependency_surfaces"])))
        self.assertNotIn("README.md", t10["paths"])

    def test_authentic_g5_shape_selects_task_0010_at_generation_6(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node unavailable")
        script = r'''
const fs=require("fs");
const {webcrypto}=require("crypto");
if(!global.crypto){global.crypto=webcrypto;}
require(process.argv[1]);
const pkg=JSON.parse(fs.readFileSync(process.argv[2],"utf8"));
const api=global.StegVersePortableOrgClaimAllocator;
api.validatePackage(pkg);
const state=api.initialState(pkg);
state.claims_state.generation=5;
state.task_statuses["TASK-2026-0007"]="active";
state.task_statuses["TASK-2026-0008"]="active";
state.task_statuses["TASK-2026-0009"]="active";
state.task_statuses["TASK-2026-0010"]="queued";
function held(taskId,fence){
  const t=pkg.tasks.find(x=>x.task_id===taskId);
  const c=JSON.parse(JSON.stringify(t.requirements.mandatory[0]));
  c.task_id=taskId;
  c.lease={fencing_token:fence};
  return c;
}
state.claims_state.claims=[held("TASK-2026-0007",3),held("TASK-2026-0008",4),held("TASK-2026-0009",5)];
let committed=null;
const store={read:()=>Promise.resolve(state),atomicCompareAndSwap:(oldState,nextState)=>{committed=nextState;return Promise.resolve(true);}};
api.allocate(pkg,store,{now_ms:1789005000000}).then(result=>{
  if(result.receipt.selected!=="TASK-2026-0010") throw new Error("TASK-0010 not selected");
  if(result.receipt.claim_registry_generation!==6) throw new Error("generation not 6");
  if(!result.claim_observation||result.claim_observation.fencing_tokens.join(",")!=="6") throw new Error("fence not 6");
  if(committed.claims_state.claims.length!==4) throw new Error("retained claims changed unexpectedly");
  console.log("AUTHENTIC_G5_SHAPE_TO_TASK_0010_G6_PASS");
}).catch(err=>{console.error(err);process.exit(1);});
'''
        result = subprocess.run(
            [node, "-e", script, str(MODULE), str(PACKAGE)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("AUTHENTIC_G5_SHAPE_TO_TASK_0010_G6_PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
