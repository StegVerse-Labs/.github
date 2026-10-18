## 14. r8: G-8 eligibility sweep and H46 (Labs#3211)

> **r10:** dispositions below that said "owner applies / owner decides / owner-only" are superseded by the §16 A/B/C/D table (Rigel 04:08Z: no owner items; questions decided from invariants first). Codes such as `REGISTRY_SURFACE_OWNER_ONLY` are kept as the r7/r8 record.

**Grant.** G-8 (Rigel, 2026-10-18 02:59Z, until 2026-11-16, relayed by the orchestrator; not yet in INDEX at 03:00Z): lane bots may push their own branches and open DRAFT PRs in their Goal's repos. Merges, pushes to main, registry generation bumps, settings changes and ledger dispatch remain forbidden. The Site claim hold and the registry-surface holds still apply.

**Eligibility test.** An item is eligible only if no active session-work claim holds its paths, it touches no registry surface (canonical records and rows, schema, task-vectors, claims and worker registry, cosv index), and the repo's own claim rules don't require a new claim fragment or cosv-index edit.

**Repo rules read:**
- **Site** (`SITE_MIRROR_HANDOFF.md`, SITE-259-PREWORK-CLAIM-ENFORCEMENT; `scripts/check_session_work_claims.py`): every mutable Site PR lane must resolve to exactly one active pre-work claim. Site#1458 failed CI without one (Labs `docs/ECOSYSTEM_ECONOMIC_WHITEPAPER_GATED_ROADMAP_MIRROR_HANDOFF.md:15`). Site#1605 added a claim fragment and changed `data/cosv/task-vector-index.json`.
- **Labs:** no CI-enforced session-claim check. Registry surfaces change only by manifest transition (r10: Labs#3232, §16).
- **StegOps-Orchestrator** (`CONTRIBUTING.md`; `ops/task-registry.json`): the CRM task is the repo's native task registry entry. Future work is "under a separately claimed continuation".

**Result: no eligible item, so no PR was opened.** Six-field FAIL_CLOSED per item:
| Item | failure_code | failed_predicate | required_evidence_or_repair | retry_entrypoint | owning_existing_goal | next_attempt |
|---|---|---|---|---|---|---|
| D13 | SITE_PATH_HELD_BY_ACTIVE_CLAIM | ONE_ACTIVE_OWNER_PER_DEPENDENCY_SURFACE | the holder of SITE-WORKSPACE-INTEROPERABILITY-20260831 carries it, r10: A, org claim allocator, Labs#3231 (§16) | patches/D13-r6-rebased-on-site-b6ebfee0.diff | STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 | on that grant |
| WU5 | same | same | same | patches/WU5-storage-persist-tests.diff | same | same |
| WU1 | SITE_PREWORK_CLAIM_REQUIRED (+ D1) | EVERY_MUTABLE_SITE_PR_RESOLVES_TO_ONE_ACTIVE_CLAIM | Site claim for workspace.js, workspace-kv-bridge.js and workspace-node-binding.js (all held) plus the D1 claim | wu1-wu5-readiness.md WU1 | same | on that grant and D1 |
| WU2 | same (+ RECOVERY_RESULT_DELIVERY_PATH_UNOBSERVED) | same | Site claim (workspace.js held) plus InTr naming the recovery route | wu2-wu3-plan.md | same | on the grant and the route |
| WU3 | SITE_PREWORK_CLAIM_REQUIRED (+ REBIND_RECEIPT_CLASS_UNDEFINED) | same | a Site claim fragment and cosv-index edit (not Lane D's to make); after WU2 | wu2-wu3-plan.md | same | after WU2 |
| WU4 | REGISTRY_SURFACE_OWNER_ONLY | SECOND_PLATFORM_TASK_NOT_REGISTERED | B: Labs#3232 registration transition (r10 §16) | patches/WU4-restated-registry-entry.json | same | r10 §16 |
| D4 | REGISTRY_SURFACE_OWNER_ONLY | LANE_MAY_EDIT_CANONICAL_TASK_RECORD_SCHEMA | B: Labs#3232 registration transition (r10 §16) | patches/D4-canonical-task-record-schema.diff | same | r10 §16 |
| D14 | REGISTRY_SURFACE_OWNER_ONLY | REGISTRY_ROW_AND_RECORD_EDIT | B: Labs#3232 registration transition (r10 §16) | patches/D14-*.json-patch.json | same | r10 §16 |
| CRM row | REGISTRY_SURFACE_OWNER_ONLY | REGISTRY_GENERATION_BUMP_FORBIDDEN | B: Labs#3232 registration transition (r10 §16) | patches/STEGOPS-CRM-registry-row.json-patch.json | STEGOPS-CAMPAIGN-CRM-PROJECTION-001 | r10 §16 |
| F-CRM-1 | REGISTRY_SURFACE_OWNER_ONLY | NATIVE_TASK_REGISTRY_EDIT | the StegOps owner, or a claimed continuation, adds the evidence class to ops/task-registry.json claim_state and the handoff | §13.1 | STEGOPS-CAMPAIGN-CRM-PROJECTION-001 | r10 §16 |
| H31b governance mint step | DUPLICATES_OPEN_SURFACE (DENY) | NEVER_DUPLICATE_GOVERNANCE_OR_CLAIM_AUTHORITY | use the #3211 allocator path with the H46 repair | Labs#3211 | STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 | n/a |
| Fence-floor repair | CLAIM_SURFACE_ON_ANOTHER_LANES_OPEN_BRANCH | LANE_MAY_PUSH_TO_FOREIGN_PR_BRANCH | the #3211 author applies patches/H46-fence-floor-repair.diff | Labs#3211 new head | SHWP-ORG-CLAIM-ALLOCATOR-001 | when the author pushes |
| Site stale claim SITE-EVALUATOR-REVIEW-INTR-CONNECTOR-634 | CLAIM_FILE_EDIT | LANE_MAY_TERMINALIZE_FOREIGN_CLAIM | holder or owner | Site data/session-work-claims.d | STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 | r10 §16 |
| Labs WorkSpace handoff doc refresh | HANDOFF_OWNED_BY_ANOTHER_SESSION | LANE_MAY_EDIT_FOREIGN_CANONICAL_HANDOFF | session 01CoqHFr… or the owner (Labs convention: a session-work claim fragment per handoff edit, e.g. workspace-handoff-current-20261017) | docs/STEGVERSE_WORKSPACE_ANY_DEVICE_KV_SURFACE_MIRROR_HANDOFF.md | STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 | on request |

### 14.1 H46: Labs#3211 assessment (read-only)
**Facts (read about 03:00Z):**
- State: draft, open. Head `6bbce8c2` (2 commits), base `3da74c74`.
- Author: the StegVerse account through Claude Code session `013aXjQ22ZG7VKiewGKyCd4T`; the body says "Part of #3183 (SDK#484 lane)".
- Created 2026-10-17T14:15:55Z; last update 16:24:39Z. 0 reviews, 0 comments.
- Mergeability: GitHub MERGEABLE/CLEAN. A local merge onto main `bfcf0318` is clean (6 files, +689/−10).
- CI on the head: consolidated-source-validators pass (run 39049281083), ratchet pass, validate pass (run 39049281213); transition skipped. Nothing has run against current main.
- Local run on main plus #3211: `test_resident_org_claim_allocator`, `test_org_claim_custody`, `test_organization_ledger_explicit_root_guard` and `test_organization_ledger_same_store_readback` pass 99/99. Global invariants PASS. Ratchet PASS (99/99).

**Against the standard:**
| Check | Result | Evidence |
|---|---|---|
| Manifest-directed transitions with an org-ledger receipt | ALLOW | a push of `control/resident-execution-request.d/org-claim-allocator-*.json` → existing consumer and allocator → typed `ORGANIZATION_WORKER_CLAIM_GRANTED/_REFUSED/_FAIL_CLOSED`, appended to `refs/stegverse/organization-ledger` (fast-forward plus compare-and-swap push) and read back from a fresh bare fetch |
| No external machine or polling | ALLOW | event-ephemeral runtime under `RUNNER_TEMP`, checkout token only, `concurrency: organization-ledger` |
| No clock- or wall-time-derived epochs or fences | ALLOW for fences (`fence = max(chain_max, floor)+1`) | Finding H46-F1: `scripts/allocate_claims.py:280` uses `datetime.now` for the lease `expires_at` and `heartbeat_due_at`. That is pre-existing and not in #3211's diff, but it runs in the hosted path. The org receipt's `observed_at` is wall-clock but declared non-ordering (`aggregate_repo_transition.py:11,680`) |
| Six fields on every non-ALLOW | FAIL_CLOSED | `non_allow()` evidence and result carry `failed_predicate`, `required_evidence_or_repair` and `retry_entrypoint` (null on DENY), but no `failure_code`, `owning_existing_goal` or `next_attempt`. `_ledger_refusal()` is the same. The 4 inline workflow refusals lack `owning_existing_goal` and `next_attempt` |
| Fence floor | FAIL_CLOSED (structural) | `materialize_org_control_inputs()` initializes the ephemeral runtime `claims-active.json` from the committed copy (gen 2, 0 claims, updated 2026-08-06) on every run. The guard requires runtime gen == issued = max(chain grant fences, TASK-2026-0012 `allocator_fence` 7). So every request on the first run gives `FENCE_GENERATION_BEHIND_ISSUED_FENCES`, as the PR predicts. A hand-committed gen 7 would go stale after the first grant (chain 8), and every later run would fail the same way |

**Which counter is authoritative (from source):**
- **Allocator domain:** the issued fence = max(org-chain grant fences, provenance floor 7, `tasks/TASK-2026-0012.json#predecessor_provenance`, allocator_task TASK-2026-0011). **Authoritative floor: 7.** `control/claims-active.json` gen 2 is a stale projection.
- `control/worker-registry.json` gen 22 (SHWP fences 6, 13, 15, 17, 18) is the **WorkerCoordinator domain**. The canonical registry's `authoritative_roles.execution_claim_and_fence` names it, and `scripts/project_worker_claim_into_canonical_task.py` ("the WorkerCoordinator registry is the sole source for claim/fence ownership") reads only it.
- So an allocator grant from #3211 doesn't project into `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`. D1 also needs a grant-to-worker-registry projection, which r10 classifies B, built by Lane D (§16). Lane D's earlier floor-22 proposal applied to the worker-registry domain; for the #3211 path the floor is 7.
- Org-ledger grant count: UNKNOWN_NOT_AUTHENTICALLY_OBSERVED (not re-read in r8; the r5 count was 0).

**Disposition: FAIL_CLOSED. Live, not stale; recommend keeping it open.**
- failure_code: `STANDARD_CONFORMANCE_INCOMPLETE`
- failed_predicate: `EVERY_NON_ALLOW_CARRIES_SIX_FIELDS`, `EVENT_EPHEMERAL_FENCE_FLOOR_RECONCILES_WITH_ISSUED_FENCES`
- required_evidence_or_repair: apply `patches/H46-fence-floor-repair.diff` to `claude/org-claim-allocator-event-ephemeral`, then CI on a head based on current main
- retry_entrypoint: Labs#3211 checks on the new head
- owning_existing_goal: `SHWP-ORG-CLAIM-ALLOCATOR-001` (Labs#3183, SDK#484 lane), consumed by #167 D1
- next_attempt: when the #3211 author pushes. Admission stays with the merge-admission transition (TVC#519 + governance ALLOW).
- Execution locus: AUTHORIZED_EXTERNAL reads, plus a local sandbox merge and tests.

**Recommendation:**
1. The #3211 author applies the repair diff and rebases onto main.
2. The PR becomes admission-input-ready and is admitted by the merge-admission transition (TVC#519 + governance ALLOW). After admission, the first real run should give ALLOW at fence 8 for the queued TASK-2026-0014 request, with the rematerialization basis in its receipt.
3. r10 B (Lane D builds): the allocator-grant → canonical claim_ref projection before D1 can use this path.
4. H46-F1 (wall-clock lease): r10 JOINT DISCOVERY QUEUE JDQ-1 (§16).

Closing is not recommended.

### 14.2 Repair diff `patches/H46-fence-floor-repair.diff`
- 263 lines, sha256 `2913290826412d46b8c4d00618d0f02fd678114c896b65388ff3a1d0b4c2ddb5`.
- Base: #3211 head `6bbce8c2` (consumer blob `d51c94d5`). It also applies on main `bfcf0318` plus #3211.
- **What it does:**
  1. `rematerialize_runtime_claim_generation()` runs only in event-ephemeral mode, only when this run initialized the runtime registry from source, and only when that registry holds no claims. It runs after the replay check and before the allocator plan. It raises the **ephemeral runtime** generation to the verified issued fence `max(chain_max, floor)`.
  2. The basis (`ORGANIZATION_CHAIN_MAX_FENCE_AND_PROVENANCE_FLOOR`, chain max, floor fence and sha, org head, source generation) goes into the grant's repository receipt evidence as `runtime_claims_generation_rematerialized`. The transition and its receipt carry the change; nothing is a hand edit of counters.
  3. It never lowers the generation, never reissues a fence (next = issued+1), never writes the committed `control/claims-active.json`, and restores the runtime bytes when the selected task replays a prior grant.
  4. Every consumer non-ALLOW (`non_allow` evidence and result, `_ledger_refusal`) carries `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint` (also on DENY), `owning_existing_goal` and `next_attempt`. The 4 workflow refusals gain `owning_existing_goal` and `next_attempt`. The text avoids the words a test forbids ("poll").
- **Tests (6 new):**
  - the committed registry is behind the floor;
  - a fresh hosted run grants fence 8 with the basis (2 → 7, chain 0, floor 7) in the receipt and the source file unchanged, and a second fresh event replays fence 8 with the same org receipt;
  - a source registry that holds claims is not rematerialized and stays FAIL_CLOSED;
  - every event-ephemeral non-ALLOW carries the six fields;
  - a preserved runtime registry behind the fences still gives FAIL_CLOSED `FENCE_GENERATION_BEHIND_ISSUED_FENCES`;
  - the workflow refusals carry the six fields.
- **Results:** 105/105 on #3211 head and 105/105 on main plus #3211; `python -m unittest tests.test_org_claim_custody tests.test_resident_org_claim_allocator` OK; global invariants PASS; ratchet PASS.
- **Who applies:** the #3211 author (Claude Code session `013aXjQ22…`, SDK#484 lane). Lane D does not push to a foreign PR branch. Admission is by the merge-admission transition (TVC#519 + governance ALLOW) only. It is not a G-8 PR, because it sits on another lane's open branch and the fence state is a claims surface.

```diff
diff --git a/.github/workflows/organization-claim-allocator-transition.yml b/.github/workflows/organization-claim-allocator-transition.yml
index ed1ef261..92dc799a 100644
--- a/.github/workflows/organization-claim-allocator-transition.yml
+++ b/.github/workflows/organization-claim-allocator-transition.yml
@@ -103,7 +103,7 @@ jobs:
             git fetch --no-tags origin "+$LEDGER_REF:$LEDGER_REF"
             echo "ledger tip before append: $(git rev-parse "$LEDGER_REF")"
           else
-            echo '{"disposition":"FAIL_CLOSED","failure_code":"ORGANIZATION_LEDGER_REF_ABSENT","failed_predicate":"DESIGNATED_REF_ALREADY_PUBLISHED","required_evidence_or_repair":"refs/stegverse/organization-ledger already exists; this writer appends to it and does not open a replacement","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","consequence_committed":false,"authority_effect":"NONE_REFUSAL_ONLY"}'
+            echo '{"disposition":"FAIL_CLOSED","failure_code":"ORGANIZATION_LEDGER_REF_ABSENT","failed_predicate":"DESIGNATED_REF_ALREADY_PUBLISHED","required_evidence_or_repair":"refs/stegverse/organization-ledger already exists; this writer appends to it and does not open a replacement","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","owning_existing_goal":"SHWP-ORG-CLAIM-ALLOCATOR-001","next_attempt":"on the next request event after the repair is recorded","consequence_committed":false,"authority_effect":"NONE_REFUSAL_ONLY"}'
             exit 1
           fi
           git rev-parse "$LEDGER_REF" > "$RUNNER_TEMP/ledger-before"
@@ -163,7 +163,7 @@ jobs:
           before=$(cat "$RUNNER_TEMP/ledger-before")
           after=$(git rev-parse "$LEDGER_REF")
           if ! git merge-base --is-ancestor "$before" "$after"; then
-            echo '{"disposition":"FAIL_CLOSED","failure_code":"ORGANIZATION_LEDGER_HISTORY_REWRITTEN","failed_predicate":"APPEND_FAST_FORWARDS_THE_EXISTING_REF","required_evidence_or_repair":"the local ref is not a descendant of the fetched tip; nothing is pushed","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","consequence_committed":false,"authority_effect":"NONE_REFUSAL_ONLY"}'
+            echo '{"disposition":"FAIL_CLOSED","failure_code":"ORGANIZATION_LEDGER_HISTORY_REWRITTEN","failed_predicate":"APPEND_FAST_FORWARDS_THE_EXISTING_REF","required_evidence_or_repair":"the local ref is not a descendant of the fetched tip; nothing is pushed","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","owning_existing_goal":"SHWP-ORG-CLAIM-ALLOCATOR-001","next_attempt":"on the next request event after the repair is recorded","consequence_committed":false,"authority_effect":"NONE_REFUSAL_ONLY"}'
             exit 1
           fi
           echo "ledger tip after append: $after (ancestor $before)"
@@ -176,7 +176,7 @@ jobs:
             exit 0
           fi
           if ! git push origin "$LEDGER_REF:$LEDGER_REF"; then
-            echo '{"disposition":"FAIL_CLOSED","failure_code":"ORGANIZATION_LEDGER_PUBLISH_RACE","failed_predicate":"PUBLISHED_REF_FAST_FORWARDS","required_evidence_or_repair":"another append moved the ref first; this run published nothing","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","consequence_committed":false,"authority_effect":"NONE_REFUSAL_ONLY"}'
+            echo '{"disposition":"FAIL_CLOSED","failure_code":"ORGANIZATION_LEDGER_PUBLISH_RACE","failed_predicate":"PUBLISHED_REF_FAST_FORWARDS","required_evidence_or_repair":"another append moved the ref first; this run published nothing","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","owning_existing_goal":"SHWP-ORG-CLAIM-ALLOCATOR-001","next_attempt":"on the next request event after the repair is recorded","consequence_committed":false,"authority_effect":"NONE_REFUSAL_ONLY"}'
             exit 1
           fi
 
@@ -187,7 +187,7 @@ jobs:
           git init -q --bare "$fresh"
           auth_header=$(git config --local --get http.https://github.com/.extraheader || true)
           if [ -z "$auth_header" ]; then
-            echo '{"disposition":"FAIL_CLOSED","failure_code":"LEDGER_READBACK_CREDENTIAL_UNAVAILABLE","failed_predicate":"FRESH_FETCH_HAS_CHECKOUT_CREDENTIAL","required_evidence_or_repair":"checkout credentials unavailable for an independent ref fetch","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","consequence_committed":false,"authority_effect":"NONE_READBACK_ONLY"}'
+            echo '{"disposition":"FAIL_CLOSED","failure_code":"LEDGER_READBACK_CREDENTIAL_UNAVAILABLE","failed_predicate":"FRESH_FETCH_HAS_CHECKOUT_CREDENTIAL","required_evidence_or_repair":"checkout credentials unavailable for an independent ref fetch","retry_entrypoint":".github/workflows/organization-claim-allocator-transition.yml","owning_existing_goal":"SHWP-ORG-CLAIM-ALLOCATOR-001","next_attempt":"on the next request event after the repair is recorded","consequence_committed":false,"authority_effect":"NONE_READBACK_ONLY"}'
             exit 1
           fi
           git --git-dir="$fresh" -c http.https://github.com/.extraheader="$auth_header" \
diff --git a/scripts/consume_org_claim_allocator_request.py b/scripts/consume_org_claim_allocator_request.py
index d51c94d5..117df896 100644
--- a/scripts/consume_org_claim_allocator_request.py
+++ b/scripts/consume_org_claim_allocator_request.py
@@ -438,6 +438,7 @@ def ledger_custody(source: Path, repo_ledger_root: Any, org_ledger_root: Path |
         "organization_root": organization_root,
         "organization_store": organization_store,
         "shared_ref": shared_ref,
+        "event_ephemeral": bool(event_ephemeral),
     }
 
 
@@ -607,6 +608,43 @@ def provenance_floor(source: Path) -> dict[str, Any]:
     }
 
 
+FENCE_FLOOR_REMATERIALIZATION_BASIS = "ORGANIZATION_CHAIN_MAX_FENCE_AND_PROVENANCE_FLOOR"
+
+
+def rematerialize_runtime_claim_generation(runtime: Path, issued: int, *, chain_max: int,
+                                           floor: Mapping[str, Any], head: str | None,
+                                           initialized_from_source: bool, event_ephemeral: bool) -> dict[str, Any] | None:
+    """Raise a stale, empty ephemeral runtime claim registry to the verified issued fence.
+
+    Only in the event-ephemeral materialization, and only when this run initialized
+    the runtime registry from the committed source copy (no runtime state is
+    preserved) and that copy holds no claims. The generation is derived from the
+    verified Organization chain (`chain_max`) and the immutable provenance floor,
+    never from a clock and never lowered; the next fence is still issued + 1, so no
+    fence is reissued. The committed control/claims-active.json is not touched: the
+    basis is recorded in the transition's own receipt evidence. Anything else stays
+    FAIL_CLOSED FENCE_GENERATION_BEHIND_ISSUED_FENCES.
+    """
+    path = runtime / "control/claims-active.json"
+    state = load_json(path)
+    generation = state.get("generation", 0)
+    if (not event_ephemeral or not initialized_from_source or state.get("claims")
+            or not isinstance(generation, int) or isinstance(generation, bool) or generation >= issued):
+        return None
+    state["generation"] = issued
+    state["generation_basis"] = {
+        "basis": FENCE_FLOOR_REMATERIALIZATION_BASIS,
+        "chain_max_fence": chain_max,
+        "provenance_floor_fence": floor["fence"],
+        "provenance_floor_sha256": floor["provenance_record_sha256"],
+        "organization_head_sha256": head,
+        "source_generation": generation,
+    }
+    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
+    return dict(state["generation_basis"], rematerialized_generation=issued,
+                authority_effect="NONE_EPHEMERAL_RUNTIME_PROJECTION_ONLY")
+
+
 def task_cosv(source: Path, task: Mapping[str, Any]) -> str | None:
     ref = task.get("canonical_task_record")
     if ref is None:
@@ -985,10 +1023,13 @@ def _ledger_refusal(request: Mapping[str, Any] | None, detail: str, *,
         "request_id": (request or {}).get("request_id"),
         "task_id": TASK_ID,
         "disposition": "FAIL_CLOSED",
+        "failure_code": predicate,
         "failed_predicate": predicate,
         "detail": detail,
         "required_evidence_or_repair": repair,
         "retry_entrypoint": RETRY_ENTRYPOINT,
+        "owning_existing_goal": (request or {}).get("task_id") or TASK_ID,
+        "next_attempt": "on the next request event after the repair is recorded",
         "runtime_execution_attempted": False,
         "fence_issued": False,
         "consequence_committed": False,
@@ -1056,13 +1097,16 @@ def consume_request(source: Path, runtime: Path, request_rel: Path, *, custody:
             "request_id": request.get("request_id"),
             "request_sha256": request_hash,
             "target_task_id": target,
+            "failure_code": predicate,
             "failed_predicate": predicate,
             "detail": detail,
             "organization_head_sha256": head,
             "fencing_token": None,
             "fence_issued": False,
             "required_evidence_or_repair": repair,
-            "retry_entrypoint": RETRY_ENTRYPOINT if transition_class == FAIL_CLOSED else None,
+            "retry_entrypoint": EVENT_EPHEMERAL_ENTRYPOINT if custody.get("event_ephemeral") else RETRY_ENTRYPOINT,
+            "owning_existing_goal": request.get("task_id") or TASK_ID,
+            "next_attempt": "on the next request event after the repair is recorded",
             "consequence_committed": False,
         }
         if readback_refusal is not None:
@@ -1093,10 +1137,13 @@ def consume_request(source: Path, runtime: Path, request_rel: Path, *, custody:
             "transition_id": transition_id,
             "disposition": DISPOSITION[transition_class],
             "claim_task_id": claim_task,
+            "failure_code": predicate,
             "failed_predicate": predicate,
             "detail": detail,
             "required_evidence_or_repair": repair,
             "retry_entrypoint": evidence["retry_entrypoint"],
+            "owning_existing_goal": evidence["owning_existing_goal"],
+            "next_attempt": evidence["next_attempt"],
             "fencing_token": None,
             "fence_issued": False,
             "selected_task_id": None,
@@ -1208,6 +1255,15 @@ def consume_request(source: Path, runtime: Path, request_rel: Path, *, custody:
                 prior = prior_grant(grants, target) if target else None
                 if prior is not None:
                     return allow(target, prior, None, replayed=True)
+                # Only a run that may mint rematerializes; a replay reprojects the retained grant.
+                claims_rel = runtime / "control/claims-active.json"
+                runtime_claims_before = claims_rel.read_bytes()
+                verified_chain_max = max([row["boundary_evidence"]["fencing_token"] for row in grants], default=0)
+                rematerialized = rematerialize_runtime_claim_generation(
+                    runtime, max(verified_chain_max, floor["fence"]), chain_max=verified_chain_max,
+                    floor=floor, head=head,
+                    initialized_from_source="control/claims-active.json" in control_inputs.get("initialized_control_files", []),
+                    event_ephemeral=bool(custody.get("event_ephemeral")))
                 plan = run_allocator(runner, runtime, safe_env, "--plan", *(("--task", target) if target else ()))
                 selected = plan.get("selected")
                 if not isinstance(selected, str) or not selected:
@@ -1218,6 +1274,8 @@ def consume_request(source: Path, runtime: Path, request_rel: Path, *, custody:
                 claim_task = selected
                 prior = prior_grant(grants, selected)
                 if prior is not None:
+                    if rematerialized is not None:
+                        claims_rel.write_bytes(runtime_claims_before)
                     return allow(selected, prior, None, replayed=True)
                 chain_max = max([row["boundary_evidence"]["fencing_token"] for row in grants], default=0)
                 runtime_generation = plan.get("claim_registry_generation")
@@ -1252,6 +1310,7 @@ def consume_request(source: Path, runtime: Path, request_rel: Path, *, custody:
                     "provenance_floor": floor,
                     "provenance_floor_sha256": floor["provenance_record_sha256"],
                     "runtime_claims_generation_observed": runtime_generation,
+                    "runtime_claims_generation_rematerialized": rematerialized,
                     "request_id": request.get("request_id"),
                     "request_sha256": request_hash,
                     "target_task_id": target,
diff --git a/tests/test_resident_org_claim_allocator.py b/tests/test_resident_org_claim_allocator.py
index 63de757f..c58ecdb7 100644
--- a/tests/test_resident_org_claim_allocator.py
+++ b/tests/test_resident_org_claim_allocator.py
@@ -567,6 +567,83 @@ class EventEphemeralClaimMaterializationTests(unittest.TestCase):
         self.assertFalse(consumer.event_ephemeral_materialization(self.env.source, other, None))
         self.assert_refused_before_anything(repo_ledger_root=other)
 
+    # H46 fence-floor repair (Lane D, STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 D1).
+    def fresh_runtime(self, name: str, *, source_claims: list | None = None):
+        """A runtime with no preserved claim registry, as the hosted workflow materializes it."""
+        env = custody_tests.Env(self.base / name, generation=None, seed=False,
+                                org_ledger=self.base / "unused-org-root")
+        if source_claims is not None:
+            path = env.source / "control/claims-active.json"
+            state = json.loads(path.read_text(encoding="utf-8"))
+            state["claims"] = source_claims
+            path.write_text(json.dumps(state), encoding="utf-8")
+        return env
+
+    def consume_hosted(self, env):
+        return consumer.consume(env.source, env.runtime, repo_ledger_root=locator(self.node), runner=self.runner,
+                                env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), **HOSTED})
+
+    def test_committed_claims_registry_is_behind_the_issued_fences(self):
+        committed = json.loads((ROOT / "control/claims-active.json").read_text(encoding="utf-8"))
+        floor = consumer.provenance_floor(ROOT)
+        self.assertLess(committed["generation"], floor["fence"])
+        self.assertEqual(committed.get("claims") or [], [])
+
+    def test_event_ephemeral_rematerializes_a_stale_empty_source_registry_from_the_chain(self):
+        env = self.fresh_runtime("fresh")
+        source_bytes = (env.source / "control/claims-active.json").read_bytes()
+        result = self.consume_hosted(env)
+        self.assertEqual(result["transition_class"], consumer.GRANTED, result)
+        self.assertEqual(result["fencing_token"], 8)
+        self.assertEqual(result["organization_readback"], "VERIFIED")
+        custody = consumer.ledger_custody(env.source, locator(self.node), None, event_ephemeral=True)
+        keys = custody["emitter"].ledger_store
+        receipt = custody["repository_store"].get(keys.receipt_key(result["repository_receipt_sha256"]))
+        evidence = receipt["evidence"]
+        basis = evidence["runtime_claims_generation_rematerialized"]
+        self.assertEqual(basis["basis"], consumer.FENCE_FLOOR_REMATERIALIZATION_BASIS)
+        self.assertEqual((basis["source_generation"], basis["rematerialized_generation"]), (2, 7))
+        self.assertEqual((basis["chain_max_fence"], basis["provenance_floor_fence"]), (0, 7))
+        self.assertEqual(evidence["runtime_claims_generation_observed"], 7)
+        # The committed source registry is never edited; only the ephemeral runtime projection moved.
+        self.assertEqual((env.source / "control/claims-active.json").read_bytes(), source_bytes)
+        # A later event derives the generation from the chain again: no fence is reissued.
+        again = self.consume_hosted(self.fresh_runtime("fresh-again"))
+        self.assertEqual(again["fencing_token"], 8)
+        self.assertEqual(again["organization_receipt_sha256"], result["organization_receipt_sha256"])
+
+    def test_source_registry_holding_claims_is_not_rematerialized(self):
+        held = {"task_id": "TASK-2026-0007", "lease": {"fencing_token": 2}}
+        env = self.fresh_runtime("held", source_claims=[held])
+        result = self.consume_hosted(env)
+        self.assertEqual(result["transition_class"], consumer.FAIL_CLOSED, result)
+        self.assertNotIn("generation_basis", env.claims())
+        self.assertEqual(env.claims()["generation"], 2)
+
+    def test_every_event_ephemeral_non_allow_carries_the_six_fields(self):
+        result = self.consume_hosted(self.fresh_runtime("held6", source_claims=[{"task_id": "TASK-2026-0007"}]))
+        for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
+                      "owning_existing_goal", "next_attempt"):
+            self.assertTrue(result.get(field), field)
+        self.assertEqual(result["retry_entrypoint"], consumer.EVENT_EPHEMERAL_ENTRYPOINT)
+
+    def test_preserved_runtime_registry_behind_the_fences_still_fails_closed(self):
+        env = custody_tests.Env(self.base / "preserved", generation=2, seed=False,
+                                org_ledger=self.base / "unused-org-root")
+        result = self.consume_hosted(env)
+        self.assertEqual(result["transition_class"], consumer.FAIL_CLOSED, result)
+        self.assertEqual(result["failed_predicate"], "FENCE_GENERATION_BEHIND_ISSUED_FENCES")
+
+    def test_workflow_refusals_carry_the_six_fields(self):
+        text = (ROOT / ".github/workflows/organization-claim-allocator-transition.yml").read_text(encoding="utf-8")
+        refusals = [json.loads(line.strip()[len("echo '"):-1]) for line in text.splitlines()
+                    if line.strip().startswith("echo '{\"disposition\":\"FAIL_CLOSED\"")]
+        self.assertEqual(len(refusals), 4)
+        for refusal in refusals:
+            for field in ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
+                          "owning_existing_goal", "next_attempt"):
+                self.assertIn(field, refusal)
+
     def test_event_ephemeral_requires_the_repository_chain_on_the_declared_store(self):
         elsewhere = bare_repository(self.base / "elsewhere.git")
         with self.assertRaises(consumer.OrganizationLedgerNotAdmitted) as raised:
```

### 14.3 Posted text, #167 6245048854
**Lane D r8: G-8 sweep (no eligible draft PR) and the H46 read-only assessment of Labs#3211. Interim evidence.**

This adds to 6240783580 and 6240796246.
- **Pins (read about 03:05Z):** Labs `.github` `bfcf0318` (registry gen 319), Site `4073b7cf`, org `0f9481af`, StegOps-Orchestrator `34f61545`.
- **Execution locus:** AUTHORIZED_EXTERNAL. Reads used the owner's account, and tests ran in the Lane D sandbox. Nothing was pushed, opened, claimed, merged or dispatched.

### G-8 sweep: nothing is eligible, so no PR was opened
| Item | Disposition | failure_code / failed_predicate | Repair, retry and next_attempt |
|---|---|---|---|
| D13, WU5 (Site) | FAIL_CLOSED | `SITE_PATH_HELD_BY_ACTIVE_CLAIM` / `ONE_ACTIVE_OWNER_PER_DEPENDENCY_SURFACE` (`SITE-WORKSPACE-INTEROPERABILITY-20260831`) | The holder carries them, r10: A, org claim allocator, Labs#3231 (§16). Patches are in `patches/`. Next attempt is on that grant |
| WU1, WU2, WU3 (Site) | FAIL_CLOSED | `SITE_PREWORK_CLAIM_REQUIRED` / `EVERY_MUTABLE_SITE_PR_RESOLVES_TO_ONE_ACTIVE_CLAIM` (SITE-259; Site#1458 failed CI without a claim). WU1/WU2 touch claimed `workspace.js`, bridge and node-binding, and every one of them needs a claim fragment and a `data/cosv/task-vector-index.json` edit. All also carry D1 | A Site claim from the owner or the holder. Next attempt is on that grant |
| WU4 | FAIL_CLOSED | `REGISTRY_SURFACE_OWNER_ONLY` / `SECOND_PLATFORM_TASK_NOT_REGISTERED` | B: Labs#3232 registration transition (r10 §16) |
| D4, D14, CRM row | FAIL_CLOSED | `REGISTRY_SURFACE_OWNER_ONLY` | B: Labs#3232 registration transition (r10 §16). Drafts are in the lane file §10/§13 |
| H31b mint step in Labs governance | DENY | `DUPLICATES_OPEN_SURFACE` / `NEVER_DUPLICATE_GOVERNANCE_OR_CLAIM_AUTHORITY` (#3211 is the allocator path) | Superseded by the H46 repair below |
| Fence-floor repair | FAIL_CLOSED (diff only) | `CLAIM_SURFACE_ON_ANOTHER_LANES_OPEN_BRANCH` / `LANE_MAY_PUSH_TO_FOREIGN_PR_BRANCH` | The #3211 author applies it (below) |
| F-CRM-1 (StegOps) | FAIL_CLOSED | `REGISTRY_SURFACE_OWNER_ONLY` / `NATIVE_TASK_REGISTRY_EDIT`. The fix is `ops/task-registry.json` `claim_state`, and the repo says further work needs "a separately claimed continuation" | The StegOps owner or a claimed continuation |
| Site stale claim `…INTR-CONNECTOR-634` | FAIL_CLOSED | claim-file edit | Holder or owner |
Owning goal for all of these: `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`; for the CRM rows, `STEGOPS-CAMPAIGN-CRM-PROJECTION-001`.

### H46: Labs#3211 (`6bbce8c2`, branch `claude/org-claim-allocator-event-ephemeral`)
**Facts.**
- Draft. Author: the StegVerse account through Claude Code session `013aXjQ22…`; the body says "Part of #3183 (SDK#484 lane)".
- Last activity 2026-10-17T16:24:39Z. 0 reviews, 0 comments.
- GitHub reports MERGEABLE/CLEAN. It merges cleanly onto main `bfcf0318`, and on that merge its 4 test files pass 99/99.
- CI on the head (base `3da74c74`): consolidated, ratchet and validate pass; transition skipped. CI has not run against current main.

**Against the standard:**
| Check | Result |
|---|---|
| Manifest-directed, with an org receipt | ALLOW. A push of `org-claim-allocator-*.json` runs the existing consumer and allocator. The run appends to `refs/stegverse/organization-ledger` fast-forward only, then reads back from a fresh fetch |
| No external machine or polling | ALLOW. The run is event-ephemeral and uses only the checkout token |
| Clock-free fences and epochs | ALLOW for fences (`max(chain_max, floor)+1`). **Finding:** the allocator lease uses wall time (`allocate_claims.py:280` `datetime.now` → `expires_at`, `heartbeat_due_at`). This is pre-existing and outside #3211's diff. `observed_at` is non-ordering by declaration |
| Six fields on every non-ALLOW | **FAIL_CLOSED.** Consumer non-ALLOW evidence and results have no `owning_existing_goal` or `next_attempt`, and DENY has `retry_entrypoint: null`. The 4 inline workflow refusals also lack `owning_existing_goal` and `next_attempt` |
| Fence floor | **FAIL_CLOSED, structural.** The hosted runtime is rebuilt every run from the committed `claims-active.json` (gen 2). The guard needs runtime gen == issued, which is max(chain, floor 7). So the first run fails, as #3211 predicts. Even a committed gen 7 would go stale after the first grant (chain 8), and every later run would fail again |

**Which counter is authoritative, from source.** The allocator's issued fence is `max(org-chain grant fences, TASK-2026-0012 allocator_fence = 7)`, so **7 is the floor** for this domain. `claims-active` gen 2 is a stale projection. `control/worker-registry.json` (gen 22, SHWP fences 6–18) is a **separate WorkerCoordinator domain**. This answers the floor question in 6240783580: 7, not 22. Also, `scripts/project_worker_claim_into_canonical_task.py` reads only the worker registry, so an allocator grant from #3211 does not yet project into the WorkSpace canonical record. D1 also needs that bridge.

**Disposition: FAIL_CLOSED. The PR is live, not stale. Do not close it.**
- failure_code: `STANDARD_CONFORMANCE_INCOMPLETE`
- failed_predicate: `EVERY_NON_ALLOW_CARRIES_SIX_FIELDS`, `EVENT_EPHEMERAL_FENCE_FLOOR_RECONCILES_WITH_ISSUED_FENCES`
- required_evidence_or_repair: apply `patches/H46-fence-floor-repair.diff` (lane file §14) to the #3211 branch, then re-run CI on a head based on current main
- retry_entrypoint: Labs#3211 checks on the new head
- owning_existing_goal: `SHWP-ORG-CLAIM-ALLOCATOR-001` (#3183, SDK#484 lane), consumed by #167 D1
- next_attempt: when the #3211 author pushes. Admission stays with the merge-admission transition (TVC#519 + governance ALLOW)

**Repair diff** (263 lines; sha256 `29132908…`; applies to #3211 head and to main plus #3211):
- In event-ephemeral mode only, and only when the runtime registry was initialized from source this run and holds no claims, the runtime generation is raised to the verified issued fence (chain max, provenance floor). The basis is recorded in the grant receipt evidence (`runtime_claims_generation_rematerialized`).
- It never lowers the generation, never reissues a fence, and never writes the committed `claims-active.json`. A replay still reprojects the retained grant.
- It adds the six fields to every consumer non-ALLOW and to the 4 workflow refusals.
- 6 new tests. The 4 files pass 105/105 on #3211 and on main plus #3211; the unittest invocation is OK; global invariants PASS; ratchet PASS.
- Owner of the repair: the #3211 author (Claude Code session `013aXjQ22…`, SDK#484 lane). Lane D will not push to that branch. Admission: the merge-admission transition (TVC#519 + governance ALLOW).

Lane file: Drive `1EmaRyhHeR5afyrMWIaz3Qt8xhz4hSjal` §14. Nothing here is admission-input-ready until every job at the exact head ran and passed; admission is by the merge-admission transition (TVC#519 + governance ALLOW) only.


### 14.4 Posted text, Labs#3183 6245050387
**Lane D r8 cross-post (G-7).** The full text is on StegVerse-org/.github#167 [6245048854](https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245048854).

- **H46, Labs#3211 (SDK#484 lane, draft `6bbce8c2`):** live, not stale. It merges cleanly on main `bfcf0318`, its 99 tests pass there, and CI is green on the head. Do not close it.
  - Under the standard it is **FAIL_CLOSED `STANDARD_CONFORMANCE_INCOMPLETE`**, for two reasons.
  - Non-ALLOW results lack `owning_existing_goal` and `next_attempt`.
  - The fence floor is structural. The hosted runtime rebuilds from committed `claims-active.json` gen 2, but the issued fence is 7 (TASK-2026-0012). Even a committed fix would go stale after the first grant.
- **Repair:** Lane D's diff `patches/H46-fence-floor-repair.diff` (Lane D file §14) raises the ephemeral runtime generation to the verified issued fence, derived from the chain plus the floor. The basis is recorded in the grant receipt, and the committed file is never edited. It also adds the six fields everywhere. 105/105 tests pass.
  - **Ask:** the #3211 author (Claude Code session `013aXjQ22…`) applies it to `claude/org-claim-allocator-event-ephemeral`. Admission is by the merge-admission transition (TVC#519 + governance ALLOW) only.
- **Floor answer from source:** 7 for the allocator domain. `worker-registry` gen 22 is a separate WorkerCoordinator domain, and canonical projection reads only that registry, so the WorkSpace D1 claim needs a bridge too.
- **G-8 sweep:** no eligible Lane D draft PR. Every Site item needs a Site pre-work claim (held or absent). Registry items: r10 B, Labs#3232 (§16). F-CRM-1 is StegOps' native task registry. All are recorded as six-field FAIL_CLOSED on #167.


---
## 15. r9: admission path suspended, and the stale-head correction

**Verdict preserved as recorded.**
- **ChatGPT, #167 [6245083581](https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245083581), 03:14:28Z:** STOP_FAIL_CLOSED for admission; runtime UNKNOWN_NOT_AUTHENTICALLY_OBSERVED. The goal is PROPOSED/UNCLAIMED, COSV `10500000110000`, canonical record blob `106a2c21`, handoff blob `2d34a61a`. It also says "Labs #3211 draft allocator has no authenticated claim/fence issuance".
- **Site#1607 audit 6245082370, 03:14:18Z:** failed predicate `TASK_CHECKED_OUT_UNDER_AUTHENTIC_WORKERCOORDINATOR_CLAIM_AND_FENCE`. Required repair:
  - authenticate the full Organization issued-fence chain and its projection;
  - retain the existing Site claim, or record an authenticated release;
  - integrate D13/WU5 into the authorized existing workstream;
  - rerun the exact-head checks;
  - establish the actual production deployed SHA and gate enforcement;
  - obtain a manifest-bound Organization/Master Records readback.

**Suspension.** Lane D makes no admission or claim attempt and drafts no request for this goal until an authenticated readback supersedes the verdict. This covers D1 (§12, §14).

**Readback around 04:05Z** (gh API on the owner's account):
| Head | Check runs |
|---|---|
| `7ea0f94d7c2fa90e0f89e21d52193df9b268a4a3` (cited; pushed 2026-10-17 19:07Z) | **failure:** Site Handoff Orchestrator 39061063189, Ecosystem Heartbeat Orchestration 39061063150, Site Bootstrap Validate 39061063195. **success:** Workspace KV Binding Validation 39061063196 and 39061059577, Site Bootstrap Validate 39061059591, Workers Builds: site |
| **`924d92edf0f379af54bdf7702895e2966bc7fed1`** (current; commits `88d0239d` and `924d92ed` pushed 03:15:01Z and 03:15:11Z, **after** the verdict) | **6/6 success:** Site Handoff Orchestrator 39092966666, Ecosystem Heartbeat 39092966667, Site Bootstrap Validate 39092966652 and push run 39092963016, Workspace KV Binding 39092966558, Workers Builds: site (external integration) |

- PR state: draft, MERGEABLE/CLEAN, branch `chatgpt/1509-six-field-ui-fallback-20261017`, updated 03:16:15Z.
- The legacy combined commit-status API reads `pending` with no status contexts on either head. Only check runs exist.
- The orchestrator's figures match: head `924d92ed`, 6/6 green, and `7ea0f94d` is stale.
- Commit `88d0239d` is titled "Rebind existing Workspace lane claim to PR 1607". The Site claim holder (ChatGPT) is acting on SITE-WORKSPACE-INTEROPERABILITY-20260831, which bears on the D13/WU5 holds.

**The correction implies no authority, admission, claim or runtime fact, and does not reverse the verdict.**

Disposition: FAIL_CLOSED (suspended).
- failure_code: `ADMISSION_STOP_FAIL_CLOSED_BY_INDEPENDENT_AUDIT`
- failed_predicate: `TASK_CHECKED_OUT_UNDER_AUTHENTIC_WORKERCOORDINATOR_CLAIM_AND_FENCE`
- required_evidence_or_repair: as in Site#1607 6245082370
- retry_entrypoint: a fresh independent audit on #167
- owning_existing_goal: `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`
- next_attempt: when that audit supersedes the verdict

Execution locus: AUTHORIZED_EXTERNAL, read-only.

### 15.1 Posted text, #167 [6245466806](https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245466806)
**Lane D r9: admission path SUSPENDED for `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`, plus a stale-head readback correction (G-1).**

**Suspension.** Lane D suspends its admission path for this goal task and keeps the verdict's evidence as recorded. The verdict is ChatGPT's 6245083581 (03:14:28Z), with its Site audit at Site#1607 6245082370 (03:14:18Z):
- disposition **STOP_FAIL_CLOSED** for admission; runtime UNKNOWN_NOT_AUTHENTICALLY_OBSERVED;
- the goal is PROPOSED/UNCLAIMED, COSV `10500000110000`, canonical record blob `106a2c21`, handoff blob `2d34a61a`, and WorkerCoordinator `claim_ref`/`fence_ref` are null;
- failed predicate `TASK_CHECKED_OUT_UNDER_AUTHENTIC_WORKERCOORDINATOR_CLAIM_AND_FENCE`;
- Labs#3211 issues no authenticated claim or fence.

Lane D makes no admission or claim attempt and drafts no request until a later authenticated readback supersedes the verdict. This covers the D1 path in 6240783580 and 6245048854.

**Stale-head correction (readback around 04:05Z):**
- The verdict cites Site#1607 head `7ea0f94d`. On that head:
  - three runs failed: Site Handoff Orchestrator 39061063189, Ecosystem Heartbeat Orchestration 39061063150, and Site Bootstrap Validate 39061063195;
  - Workspace KV Binding Validation passed (39061063196).
- `7ea0f94d` is now **stale**. Site#1607 (still a draft, MERGEABLE/CLEAN) is at **`924d92ed`**, after two commits pushed at 03:15Z, after the verdict.
- On `924d92ed`, **6 of 6 checks pass**:
  - Handoff Orchestrator 39092966666;
  - Heartbeat 39092966667;
  - Bootstrap Validate ×2 (39092966652 and push run 39092963016);
  - KV Binding 39092966558;
  - the external "Workers Builds: site" check.

**This correction implies no authority, admission, claim or runtime fact, and does not reverse the verdict.** Green source CI is not runtime proof, and the failed predicate still stands.

Disposition: **FAIL_CLOSED, suspended.**
- failure_code: `ADMISSION_STOP_FAIL_CLOSED_BY_INDEPENDENT_AUDIT`
- failed_predicate: `TASK_CHECKED_OUT_UNDER_AUTHENTIC_WORKERCOORDINATOR_CLAIM_AND_FENCE`
- required_evidence_or_repair: the repairs listed in Site#1607 6245082370
- retry_entrypoint: a fresh independent audit on #167
- owning_existing_goal: `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`
- next_attempt: when that audit supersedes the verdict

Execution locus: AUTHORIZED_EXTERNAL, read-only GitHub readback. Nothing was pushed, claimed or dispatched.


---
## 16. r10: no-owner-items reclassification, claim request and registration transition

**Inputs:**
- Rigel 04:08Z: no owner items; classes A/B/C; build B under G-8.
- Rigel 04:09Z: decide from invariants first and cite the rule; only undecidable items go to the JOINT DISCOVERY QUEUE (INVARIANT CHECKED / QUESTION / FEEDBACK OUTPUT).
- Coordination #167 [6245553028](https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245553028), which adds class D (decided by invariant) and moves D13/WU5 to A via the org claim allocator.
- Registry check: Labs registry gen 319 has `human_actions: []`.

**16.1 Cited invariant (readback, Labs `bfcf0318`).** `TASK_REGISTRY_CANONICAL_INVARIANTS.md` blob `1f9669a9`, §"Worker-claim field invariant", L42-55:
- L44: "A chat/session may be the current coordination holder or source-mutation actor, but `CURRENT_SESSION`, a model identity, repository identity, transport identity, or handoff reference must never be encoded as execution claim/fence authority."
- L55: session ownership "does not become WorkerCoordinator authority merely because a session is actively editing source."
- Also `data/task-registry-ai-ingress-policy.json` L63: `SELF_DECLARED_CHATGPT_SESSION_NEVER_CREATES_AUTHENTIC_CHECKIN_LEDGER_EVENT`.

So the ChatGPT session hold SITE-WORKSPACE-INTEROPERABILITY-20260831 (Site `data/session-work-claims.d/site-workspace-interoperability-20260831.json`, `session_worker_id: chatgpt:…`) is projection only.

**16.2 Claim request: [Labs#3231](https://github.com/StegVerse-Labs/.github/pull/3231)** (draft, branch `laned/org-claim-allocator-workspace-kv-site`, head `9671ee7a`).
- **Repository located by readback:** the allocator lives in Labs .github (`scripts/consume_org_claim_allocator_request.py` blob `8c225efd`, `scripts/allocate_claims.py`), not in org.
- **Files:**
  - `control/resident-execution-request.d/org-claim-allocator-workspace-kv-site-001.json`: `stegverse.resident-execution-request/v1`, the shape of `org-claim-allocator-sdk-structural-validator-001.json`. `target_task_id` TASK-2026-0015; `source_catalog_floor.scope_sha256` = `0b23fc0e48cd85a450d2315fdab3218031f128e89bc72ac5291a4abba9824075`.
  - `tasks/TASK-2026-0015.json`: `stegverse.org-task/v0.2`, status queued.
    - The ID is the next sequential one; no open Labs PR touches it (all 11 checked).
    - `canonical_task_record` points at the WorkSpace record, so the COSV `10500000110000` is read, not restated.
    - Scope: Site `assets/workspace.js`, `tests/workspace-kv-six-field-dispositions.test.cjs` and `tests/workspace-storage-persistence.test.cjs`; workflows `.github/workflows/workspace-kv-binding-validation.yml`; dependency surface `site:workspace-device-kv`, reused from the Site claim's `dependency_surface_keys`.
  - Registration lines in `REQUEST_RELS` (consumer) and `REQUIRED_SOURCE_FILES` (`scripts/bootstrap_sovereign_runtime.py`), as the SDK requests did.
  - `tests/test_org_claim_custody.py`: the pinned queue tail is extended to TASK-2026-0015.
  - A new test, `tests/test_org_claim_allocator_workspace_kv_site_request.py`.
- **Not a registry data edit.** No records, rows, task-vectors, claims-active, worker registry or COSV index are touched. Labs has no CI-enforced per-PR session claim, so no claim is needed for the request itself.
- **Validation:**
  - `validate_request` and `validate_source_catalog_floor` (SOURCE_CATALOG_FLOOR_SATISFIED) pass; new tests 4/4.
  - `test_org_claim_custody` 56/56; `test_resident_org_claim_allocator` 12/12; `test_cross_repository_dependency_claims` and `test_bootstrap_sovereign_runtime` pass.
  - Scratch allocator `--task TASK-2026-0015`: selected, `ALLOCATION_COMPLETE`, no conflict, generation 2→3.
- **CI at opening:** validate ×3 and consolidated-source-validators pass; ratchet pending.
- **Expected first receipt:** `ORGANIZATION_WORKER_CLAIM_FAIL_CLOSED` / `FENCE_GENERATION_BEHIND_ISSUED_FENCES`, because the generation (2) is below the floor (7). On main the consumer is resident-only (`clean_env` refuses hosted runners).
- **#3211 relation:** hosted, event-ephemeral consumption needs #3211 plus the H46 repair. Both edit the same consumer file; #3231's change is a 1-line tuple entry.
- **D13/WU5 stay on Lane D branches:** patches `D13-r6-rebased-on-site-b6ebfee0.diff` and `WU5-storage-persist-tests.diff`. No Site PR until a GRANTED receipt is observed (WBF L82).
- **Answer to the Claude KV/WorkSpace comment [6245570470](https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245570470)** ("B, not A": fixed tuple and `TASK-` format). Both points are cleared the way the existing requests were (tuple line + `tasks/TASK-*` projection), so the item stays A.

**16.3 (B) build: [Labs#3232](https://github.com/StegVerse-Labs/.github/pull/3232)** (draft, branch `laned/canonical-task-registration-transition`, head `abdc51f2`).
- **Files:**
  - `contracts/canonical-task-registration-transition.v1.json`: the manifest entry.
  - `schemas/canonical-task-registration-request.schema.json` and `schemas/canonical-task-registration-transition-receipt.schema.json`.
  - `scripts/canonical_task_registration_transition.py` (plan/apply/verify).
  - `.github/workflows/canonical-task-registration-transition.yml`: `contents: read`, registered REVIEW_REQUIRED in `control/workflow-surface-registry.json`.
  - `control/canonical-task-registration-requests/README.md`, a fixture, and `tests/test_canonical_task_registration_transition.py`.
- **What it derives:** from one manifest, it derives the record, the row (row == record), the generation (tip + 1), `control/task-vectors/<id>.json` (COSV = `cosv.encode_task(exact_metrics)`) and `control/task-vector-index.d/<id>.json`. Verify requires the PR head to hold exactly those bytes.
- **Tests:** 16/16. A scratch end-to-end verify returned ALLOW (319→320, diff +59/−1). A hand edit returned FAIL_CLOSED REGISTRATION_BYTES_DIVERGE.
- **CI at opening:** verify and consolidated pass; ratchet pending.
- **Unblocks:** D14, the CRM row (gen 320, COSV derived, so UNASSIGNED_PENDING_OWNER is retired) and WU4. It does not cover D4 (schema), which is JDQ-2.

**16.4 Comment posted.** #167 [6245617675](https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245617675) carries the full A/B/C/D table and the JDQ entries, copied below. Cross-post: Labs#3183 [6245618755](https://github.com/StegVerse-Labs/.github/issues/3183#issuecomment-6245618755) (CRM licensing SEPARATE, CRM row via #3232, F-CRM-1 decided).

**Lane D r10: no-owner-items reclassification, decided from invariants. Two G-8 draft PRs. Adds to Coordination 6245553028; answers 6245570470.**

Refs, Labs main `bfcf0318`:
- **TRCI:** `TASK_REGISTRY_CANONICAL_INVARIANTS.md` blob `1f9669a9`, §"Worker-claim field invariant" L42-55.
- **TCP:** `data/task-coordination-policy.json`.
- **GI:** `data/task-registry-global-invariants.json`.
- **WBF:** `docs/WORKER_BLOCKER_FALLBACK_INVARIANT.md`.
- **ORRD:** org `docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md` §Conformance.
- **CONS:** `scripts/consume_org_claim_allocator_request.py` blob `8c225efd`.

Classes: **A** = an existing transition, whose receipt is the observation; **B** = build; **C** = joint discovery; **D** = decided by invariant.

**Readback of the cited rule.** TRCI L44: "`CURRENT_SESSION`, a model identity … must never be encoded as execution claim/fence authority". L55: session ownership "does not become WorkerCoordinator authority merely because a session is actively editing source". So the Site hold SITE-WORKSPACE-INTEROPERABILITY-20260831 (`chatgpt:` session) is projection only.

**On 6245570470 (allocator path "B, not A").** Both blockers are real at `bfcf0318`, but the existing requests show how they are cleared: one tuple line in `REQUEST_RELS`/`REQUIRED_SOURCE_FILES` plus a `tasks/TASK-*.json` projection. `org-claim-allocator-sdk-structural-validator-001` + `TASK-2026-0014` were added that way. So this is A with a one-line registration, not a new capability. Filed as **Labs#3231 (draft)**:
- `control/resident-execution-request.d/org-claim-allocator-workspace-kv-site-001.json`
- `tasks/TASK-2026-0015.json`: the next sequential ID; no open PR uses it. COSV is read from the existing record (`10500000110000`).
- Scope: Site `assets/workspace.js`, 2 test files, workflow `workspace-kv-binding-validation.yml`, surface `site:workspace-device-kv` (reused from the Site claim).
- Validation:
  - local: `validate_request` + `validate_source_catalog_floor` pass; tests 4/4; `test_org_claim_custody` 56/56 (pinned queue tail extended).
  - scratch allocator `--task TASK-2026-0015` selects it with no conflict, at generation 3.
  - CI: validate ×3 and consolidated pass; ratchet pending.
- The #3211 overlap is a 1-line tuple entry in the same file, an easy rebase.
- **Expected first receipt is not GRANTED.**
  - On main the consumer is resident-only (`clean_env` refuses hosted).
  - The generation (2) is behind the fence floor (7), so the receipt will be `FENCE_GENERATION_BEHIND_ISSUED_FENCES`.
  - Hosted consumption needs #3211 plus the H46 repair. D13/WU5 stay on a Lane D branch, with no Site PR until GRANTED (WBF L82).

**A/B/C/D table** (each non-ALLOW: fc = failure_code / fp = failed_predicate / rep = required repair / re = retry_entrypoint / goal = owning_existing_goal (KV = STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001) / next = next_attempt):

| Item | Class | Decided by | Disposition and six fields |
|---|---|---|---|
| D1 claim/fence | **A** (CONS → `stegverse.organization-transition-receipt/v1`, ORGANIZATION_WORKER_CLAIM_*) | TRCI L44; TCP `WORKERCOORDINATOR_OWNS_EXECUTION_CLAIM_AND_FENCE`; `tasks/*.json` `authority.workercoordinator_authority_owner` = Labs WorkerCoordinator | FAIL_CLOSED. fc WORKERCOORDINATOR_CLAIM_NOT_GRANTED / fp TASK_CHECKED_OUT_UNDER_AUTHENTIC_WORKERCOORDINATOR_CLAIM_AND_FENCE / rep #3231 merged + GRANTED receipt (hosted: #3211 + H46) / re CONS::consume / goal KV / next on receipt |
| 22-vs-7 floor | **D** | CONS header: candidate = max(chain_max, provenance floor) + 1; `PROVENANCE_FLOOR_REL` = `tasks/TASK-2026-0012.json` | Allocator domain floor = **7**. `worker-registry.json` gen 22 is the separate SHWP domain. No question remains. |
| Allocator grant → canonical `claim_ref` projection | **B** (Lane D builds next) | TRCI L44 + `tasks/*` authority says the allocator is WorkerCoordinator. `scripts/project_worker_claim_into_canonical_task.py` reads only `worker-registry.json` | FAIL_CLOSED. fc CLAIM_PROJECTION_SOURCE_INCOMPLETE / fp ALLOCATOR_GRANT_PROJECTS_INTO_CANONICAL_TASK / rep projector also reads verified allocator grant receipts / re that script / goal KV / next next G-8 build |
| D2 admission | **A** (CanonicalWork ingress, `stegverse.canonical-work-intr-materialization-ingress/v1` → `apply_admitted_canonical_work_projection.py`), **suspended** | ChatGPT 6245083581 STOP_FAIL_CLOSED; TCP `new_session_entry`/`workercoordinator_claim_fence_still_required` | FAIL_CLOSED. fc ADMISSION_STOP_FAIL_CLOSED_BY_INDEPENDENT_AUDIT / fp TASK_CHECKED_OUT_UNDER_AUTHENTIC_WORKERCOORDINATOR_CLAIM_AND_FENCE / rep D1 receipt + Site#1607 6245082370 repairs / re fresh audit on #167 / goal KV / next on audit |
| D13, WU5 | **A** (#3231 → CONS) | TRCI L44 (hold is projection only); WBF L82 | FAIL_CLOSED until GRANTED. fc WORKERCOORDINATOR_CLAIM_NOT_GRANTED / fp SITE_WORKSPACE_PATHS_CLAIMED_BY_WORKERCOORDINATOR / rep GRANTED receipt for TASK-2026-0015 / re CONS::consume / goal KV / next on receipt |
| Site claim hold | **D** | TRCI L44, L55; `data/task-registry-ai-ingress-policy.json` `SELF_DECLARED_CHATGPT_SESSION_NEVER_CREATES_AUTHENTIC_CHECKIN_LEDGER_EVENT` | Projection only, not a fence. The allocator decides. A ChatGPT release record is welcome but not a predicate. |
| WU1-WU3 | **A** (same allocator path, second scope: `workspace-node-binding.js`, `workspace-kv-bridge.js`) | TRCI L44; WU1 exemption register entry (Labs#3209) | FAIL_CLOSED. fc WORKERCOORDINATOR_CLAIM_NOT_GRANTED / fp SITE_WORKSPACE_PATHS_CLAIMED_BY_WORKERCOORDINATOR / rep second request after the TASK-2026-0015 receipt (ordering avoids self-conflict on `workspace.js`) / re CONS / goal KV / next on receipt |
| D14 record/row; WU4 entry | **B, built: Labs#3232** → then A | TCP `adjacent_task_derivation_contract`, `session_mutation_generation_fence`; `docs/TASK_REGISTRATION_GUIDE.md` step 3 had no transition | FAIL_CLOSED. fc REGISTRATION_TRANSITION_NOT_MERGED / fp CANONICAL_TASK_REGISTRATION_BY_MANIFEST / rep #3232 merged, then a manifest under `control/canonical-task-registration-requests/` / re `scripts/canonical_task_registration_transition.py verify` / goal KV / next on merge |
| CRM row gen 320 + COSV | **B, built: #3232** → then A | COSV = `scripts/cosv.py encode_task(exact_metrics)`; economic-roadmap handoff L19 (no manual vector). The transition derives it, so UNASSIGNED_PENDING_OWNER is retired | FAIL_CLOSED. fc REGISTRATION_TRANSITION_NOT_MERGED / fp as above / rep #3232 merged + CRM manifest / re as above / goal STEGOPS-CAMPAIGN-CRM-PROJECTION-001 / next on merge |
| CRM licensing (Q-D-ENT-1) | **D** | Labs#3183 body L2 ("StegOps CRM as a **separately entitled** commercial product"), L41 (entitlement enforced separately; "a paid tier cannot manufacture ALLOW"); SDK-COST-DERIVED-TIER-PRICING-001 issues no TV/TVC entitlement | **Separate.** No bundle entitlement exists, so bundling is FAIL_CLOSED by default. Pricing and terms stay in #3183 workstream D. |
| F-CRM-1 (native COMPLETE) | **D** | GI `legacy_unqualified_completion_authority: NONE_NON_AUTHORITATIVE_PROVENANCE_ONLY`, `…may_satisfy_terminal_predicate: false` | Native COMPLETE is provenance only. The canonical row registers `completion.claimed: false` (via #3232). No StegOps edit needed. |
| D4 schema fields | **C** | conflict, see JDQ-2 | FAIL_CLOSED. fc INVARIANT_CONFLICT_UNRESOLVED / fp CANONICAL_RECORD_SCHEMA_ADMITS_COSV_BINDING / rep JDQ-2 output / re #167 / goal STEGVERSE-CANONICAL-WORK-COORDINATION-001 / next on the JDQ answer |
| H46 repair for #3211 | **D** (relay only) | TCP `pull_request_precreation_gate` `same_branch_repair_required: true`, `deny_when PREDECESSOR_PR_OPEN` | Must land on the #3211 branch. Its author applies `patches/H46-fence-floor-repair.diff` (lane file §14.2). Lane D opens no competing PR. |
| H46-F1 wall-clock leases | **C** | see JDQ-1 | FAIL_CLOSED. fc INVARIANT_ABSENT / fp CLAIM_LEASE_TIME_BASE_DECLARED / rep JDQ-1 output / re #167 / goal SHWP-ORG-CLAIM-ALLOCATOR-001 / next on the JDQ answer |

**JOINT DISCOVERY QUEUE** (Claude, ChatGPT):
- **JDQ-1: lease time base.**
  - INVARIANT CHECKED: GI has no lease rule. `.stegverse/transition-ledger/emit.py` says the heartbeat/kernel owns *epoch* derivation, but `allocate_claims.py:280` lease expiry is wall-clock and is not an epoch or fence.
  - QUESTION: must claim leases derive from the kernel heartbeat epoch, or is wall-time lease expiry admissible?
  - FEEDBACK OUTPUT: a GI `claim_lease_time_base` invariant, or an `org-kernel` lease derivation that the allocator calls.
- **JDQ-2: COSV binding vs record schema.**
  - INVARIANT CHECKED: TCP `adjacent_task_derivation_contract.new_task_must_receive` includes COSV_TASK_VECTOR_PROJECTION, and rows carry `cosv_task_vector`/`source_state_vector_ref`. But `schemas/canonical-task-record.schema.json` has `additionalProperties: false` without them; only 5 of 212 records pass.
  - QUESTION: amend the schema to admit the binding fields, or move the binding out of the record?
  - FEEDBACK OUTPUT: a schema amendment through a manifest transition (the next B after #3232), or a declared rule in TRCI.

**PRs (draft; not admission-input-ready until every job at the exact head ran and passed):**
- Labs#3231 (claim request).
- Labs#3232 (registration transition: plan/apply/verify, receipt schema, 16/16 tests; CI verify and consolidated pass, ratchet pending).

**#3211:** head `6bbce8c2`, draft, CLEAN, CI green (transition skipped), no activity since 2026-10-17 16:24Z.

Lane file r10 §16. Execution locus: AUTHORIZED_EXTERNAL. Source PRs only; no merge, dispatch, ledger append or registry data edit.


**16.5 #3211 tracking.** Head `6bbce8c28d44119eab4be5a4a38b7d364b689f70`, draft, MERGEABLE/CLEAN. Checks: consolidated-source-validators, ratchet and validate pass; transition skipped. Last update 2026-10-17 16:24Z. The H46 repair has not been applied yet.

**16.6 Not done this round.** The allocator-grant → canonical `claim_ref` projector (B, Lane D builds it next), the WU1–WU3 second claim request (after the TASK-2026-0015 receipt), and the CRM and D14 registration manifests (after #3232 merges).


## 17. r11: allocator-grant → worker-registry projection (H10), fence-domain reconciliation

**17.1 Build (class B, G-8 draft).** StegVerse-Labs/.github#3235 (https://github.com/StegVerse-Labs/.github/pull/3235).
- Branch `laned/worker-claim-grant-projection-transition`, head `5052569970dc05f3932ad640f9ea296b555d038a`, base Labs main `bfcf0318`. **Not admission-input-ready until every job at the exact head ran and passed; admission is by the merge-admission transition only.**
- Locus: AUTHORIZED_EXTERNAL. Authority effect: NONE_PROJECTION_ONLY.
- Files (8 changed, +805):
  - `scripts/worker_claim_grant_projection_transition.py` (plan/apply/verify)
  - `contracts/worker-claim-grant-projection-transition.v1.json`
  - `schemas/worker-claim-grant-projection-request.schema.json`
  - `schemas/worker-claim-grant-projection-transition-receipt.schema.json`
  - `control/worker-claim-grant-projection-requests/README.md` (no manifest; there is no grant yet)
  - `.github/workflows/worker-claim-grant-projection-transition.yml` (contents: read)
  - `control/workflow-surface-registry.json` (REVIEW_REQUIRED entry)
  - `tests/test_worker_claim_grant_projection_transition.py` (21 tests, stdlib unittest)
- No registry data file is edited.

**17.2 Behaviour.**
1. **Request.** `stegverse.worker-claim-grant-projection-request/v1` carries:
   - `allocator_task_id` (TASK-…);
   - `canonical_task_id`, which must equal the allocator task's `canonical_task_record`;
   - `observed_worker_registry_generation`;
   - `organization_receipt_sha256` and the receipt object, inline as bytes.
2. **Receipt checks.** The receipt must:
   - recompute (canonical JSON sha);
   - be an `ORGANIZATION_WORKER_CLAIM_GRANTED` ALLOW for the task, with `source_transition_id` = `ORGANIZATION-WORKER-CLAIM-GRANTED-{task}-G{fence}`;
   - have a fence above the floor (7, read through the consumer's own `provenance_floor`);
   - carry `hb_reference.derived_from_clock == false`;
   - sit on the verified Organization chain (HEAD → genesis, the same predicates as CONS `_verify_store_chain`);
   - not be superseded by a later grant for the task.
3. **Worker-registry checks.**
   - A row already carrying this receipt → ALLOW, replayed, no byte change. This is checked before the generation check, so replay is idempotent at any later generation.
   - The observed generation must equal the tip.
   - The task must not already hold a claim.
   - The fence must not already be projected from another receipt.
4. **Successor.** generation = `max(gen+1, fence+1)`. One row is added or filled:
   - claim_id = the grant transition id;
   - `assignment_timer` = {fencing_token: fence, fence_domain: ORGANIZATION_CLAIM_ALLOCATOR, grant_receipt_sha256, allocator_task_id, claim_scope_sha256, organization_head_sha256, start_epoch: receipt hb epoch};
   - state CLAIM_GRANTED_PROJECTED; worker/instance null; executor_binding UNBOUND.

   `updated_at` is not touched. The output format matches the file (indent 2, key order preserved).
5. **Downstream.** The existing `scripts/project_worker_claim_into_canonical_task.py` carries the row into the canonical record. It still requires coordination_state ≠ PROPOSED, and the KV Goal is PROPOSED, so admission stays STOP_FAIL_CLOSED.
6. **Refusals.** 15 FAIL_CLOSED codes, each with the six fields and `consequence_committed: false`. The receipt asserts `workercoordinator_domain_fence_minted`, `allocator_fence_reissued`, `generation_lowered`, `clock_read` and `organization_ledger_appended` are all false.

**17.3 Fence-domain reconciliation (decided from invariants).**
- **R1 target = WorkerCoordinator:** canonical registry `authoritative_roles.execution_claim_and_fence` = "control/worker-registry.json / WorkerCoordinator"; TCP `WORKERCOORDINATOR_OWNS_EXECUTION_CLAIM_AND_FENCE`; `tasks/*.json authority.workercoordinator_authority_owner`.
- **R2 no mint:** TCP `TASK_REGISTRY_DOES_NOT_MINT_EXECUTION_AUTHORITY`; TRCI blob 1f9669a9, Worker-claim field invariant L42-55 (L44: a session or model identity is never claim/fence authority); projector docstring.
- **R3 generation exclusive of the fence:** `heartbeat_runtime/worker_runtime_legacy.py` L493-498 `minimum_fencing_token_exclusive`; TCP `session_mutation_generation_fence`.
- **R4 no reissue:** CONS `verify_fence_history`; WBF collision constraint.
- **R5 epoch, not clock:** `org-kernel/kernel.py hb_reference` (OSCILLATOR_ONLY; the epoch comes from the carrier); `aggregate_repo_transition.py` `observed_at` is non-ordering.
- **R6 evidence as bytes:** org ORRD §Conformance; GI `completion_language_requires_evidence_class`.

**17.4 JOINT DISCOVERY entries for the orchestrator to queue** (Lane D does not write INDEX):
- **Lane D JDQ-3 → proposed Q-D-3 (C, Claude/ChatGPT): fence-domain unification.**
  - INVARIANT CHECKED: R1–R4 sources above.
  - QUESTION: should the Organization claim-allocator fence (floor 7, chain) and the WorkerCoordinator generation (worker-registry gen 22) become one counter, or stay namespaced under the exclusive-generation rule? The invariants fix the target, no-mint and never-lower, but not whether one domain subsumes the other.
  - FEEDBACK OUTPUT: a TCP invariant entry (FENCE_DOMAINS_NAMESPACED_GENERATION_EXCLUSIVE or UNIFIED_FENCE_COUNTER) and a #3235 contract update.
  - DEFAULT: namespaced.
- **Lane D JDQ-4 → proposed Q-D-4 (C, Claude, the #3211 author; same class as H34): carrier epoch on the hosted allocator path.**
  - INVARIANT CHECKED: `kernel.hb_reference` docstring; `aggregate_repo_transition.py` L1082 (`kernel.hb_reference()` when hb_epoch is None); ORRD.
  - QUESTION: which carrier supplies `hb_epoch` for a grant on the event-ephemeral path? Until one does, should a clock-derived, non-ordering reference be accepted?
  - FEEDBACK OUTPUT: CONS passes the named carrier epoch via `record_transition` → `aggregate_transition(hb_epoch=…)` on #3211's branch, or a policy entry admits derived non-ordering epochs; #3235 R5 is updated to match.
  - DEFAULT: refuse (GRANT_EPOCH_NOT_CARRIER_SUPPLIED).

**17.5 Six-field note on the finding.** CONS never passes `hb_epoch`, so every grant emitted today is clock-derived and #3235 refuses it.
- failure_code / failed_predicate: GRANT_EPOCH_NOT_CARRIER_SUPPLIED
- required_evidence_or_repair: the allocator passes the carrier epoch
- retry_entrypoint: #3235 verify workflow
- owning_existing_goal: STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001
- next_attempt: after #3211's branch carries the epoch

Class D→C: `pull_request_precreation_gate.same_branch_repair_required` puts it on #3211's branch together with H46. Lane D does not push there.

**17.6 Observations.**
- **Organization ledger:** `refs/stegverse/organization-ledger` `a5bb54d8`, read only, gives 7 receipts that verify rooted and continuous, with 0 GRANTED.
- **#3231** `9671ee7a` and **#3232** `abdc51f`: all checks success, ratchet included; there are no lane-caused failures, so nothing was fixed.
- **#3235 CI:** consolidated-source-validators success, verify success, ratchet success (all green).
- **Parallel branches:** none for this build (the `claude/3183-*` and `claude/workspace-*` heads all predate the 04:26Z ruling).
- **#3211:** `6bbce8c2`, unchanged.
- **Site#1607:** head `924d92ed` per ChatGPT 6245673014 and the 04:32Z delta 6245688836. Admission is still refused.

**17.7 Posted.** #167 checkpoint 6245736551 (https://github.com/StegVerse-org/.github/issues/167#issuecomment-6245736551).

**17.8 Not done.**
- The CONS hb_epoch repair (JDQ-4; lands on #3211's branch).
- The first projection manifest (waits for a GRANTED receipt).
- The WU1–WU3 second claim request (after the TASK-2026-0015 receipt).
- The CRM and D14 registration manifests (after #3232 merges).

## 18. r12: Site#1607 provider deploy, the production-promotion authorization transition (B), and the claim-hold disposition

Source: orchestrator relay from New Bot, 05:14Z, which cites #167 comments 6245688836 and 6245673014. I verified both comments by reading them from the GitHub API.

**18.1 Verification of the relay.**
- **6245688836** was posted at 04:33Z as StegVerse through the chatgpt-codex-connector app. It is the "KV/WorkSpace coordination delta 04:32Z" and says:
  - Site#1607 head is `924d92ed…`, DRAFT/UNMERGED, with four workflows SUCCESS.
  - The Cloudflare bot comment 6237313898 reports a production deploy at the same SHA, build `1790bb75-3340-4bd3-929d-f188b9f23405`.
  - The verdict is CORRECTION_REQUIRED, with predicate `PRODUCTION_PROMOTION_AUTHORIZED_BY_MANIFEST_AND_SOVEREIGN_RECEIPT`, and admission is STOP_FAIL_CLOSED.
  - Labs#3211 at `6bbce8c2` is pending. Claude reports `CODE_PUSH_NOT_GRANTED` and that the original author session is inactive.
  - Q-D-1 and Q-D-2 are open.
  - It asks Grok to reconcile the indexed and unindexed files. That is INDEX work, so it goes to the orchestrator.
- **6245673014** was posted at 04:31Z the same way and is ChatGPT's Q-G1/Q-R-f coordination. It says:
  - No competing Site branch or claim mutation is authorized.
  - Disposition: `SITE_PATH_HELD_BY_ACTIVE_CLAIM` / `ONE_ACTIVE_OWNER_PER_DEPENDENCY_SURFACE`.
  - Repair: the existing holder integrates D13/WU5, or a manifest-authorized allocator grants a fragment or release, with an exact-head readback and a sovereign readback.
  - "No LLM may record a claim release merely because INDEX asks for it."
- **Cloudflare comment** Site 6237313898, from `cloudflare-workers-and-pages[bot]`, was created 10-17 17:10Z and edited in place, last at 10-18 03:16Z. It says "Deployment successful", service `site`, commit `924d92ed`, and its log link points to `…/workers/services/view/site/production/builds/1790bb75…`.
- **Discrepancy (precision):**
  - The bot does not name a route. "Production" appears only in the dashboard environment path.
  - The PR is a draft on a non-main branch (`chatgpt/1509-six-field-ui-fallback-20261017`).
  - So whether the production route serves `924d92ed` is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED. The build might be only a version upload.
  - The FAIL_CLOSED holds either way, because no authorization is observed.
- **Site#1607 head:** `924d92ed`, re-read at 05:15Z. Draft. Updated 04:33Z.
- **Labs#3211 head:** `6bbce8c2`, re-read at 05:15Z. Draft, mergeable clean, last updated 10-17 16:24Z.
- **Labs main:** `bfcf0318`. `control/claims-active.json` is at gen 2 with `claims: []`.

**18.2 Six-field FAIL_CLOSED: the Site#1607 provider deploy.**
- **Disposition:** FAIL_CLOSED.
- **Execution locus:** Cloudflare Workers Builds, service `site`. This is an external provider, triggered by a push to the #1607 branch. Lane D only observed it, read-only, through the GitHub API.
- **Deploy observed:** yes, `924d92ed`, build `1790bb75`, as reported by the provider.
- **Authorization:** UNKNOWN_NOT_AUTHENTICALLY_OBSERVED. There is no manifest, no InTr admission and no org-ledger receipt.
- **Production route serving:** UNKNOWN_NOT_AUTHENTICALLY_OBSERVED.

The six fields:
- **failure_code:** `PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT`
- **failed_predicate:** `PRODUCTION_PROMOTION_AUTHORIZED_BY_MANIFEST_AND_SOVEREIGN_RECEIPT` (as named in 6245688836)
- **required_evidence_or_repair:**
  - A manifest-bound `SITE_PRODUCTION_PROMOTION_*` receipt (`stegverse.organization-transition-receipt/v1`) on the Labs org ledger. It binds the SHA, the build, and the declared environment and route, and comes with a fresh-fetch readback.
  - Until then, CI and the provider deploy count only as evidence.
- **retry_entrypoint:** SPPA (18.3) in retro-classification mode over build `1790bb75`.
- **owning_existing_goal:** `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001` (#167). No new Goal Task ID.
- **next_attempt:** the first SPPA run. Expected result: FAIL_CLOSED `PROMOTION_SOURCE_NOT_ON_PROMOTION_REF`, because #1607 is unmerged.

Rules cited:
- ORRD (`docs/ORGANIZATION_ROLE_RUNTIME_REALITY_DEPLOYMENT.md`):
  - L19 scope rule `EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT`
  - L21: InTr is the transition authority; GitHub is non-authorizing.
  - Standard 1: every action is a manifest-bound transition.
  - Standard 5: six fields on any non-ALLOW result.
  - §Validation: "Source validation and merge grant no runtime authority."
- Labs `docs/SV_DN1_PUBLIC_PROMOTION_TASK_MIRROR_HANDOFF.md`:
  - L43: deployment is a separate lifecycle state.
  - L141: Actions "cannot become publication-decision or runtime authority".

Admission stays **STOP_FAIL_CLOSED** as an audit label. There is no rollback; a rollback would be its own transition.

**18.3 (B) Lane D build item: SPPA, the Site production-promotion authorization transition.**
- **Gap:**
  - The registry has no deploy-authorization transition.
  - The SV-DN1 promotion stops at `PROMOTION_READY_FOR_REPOSITORY_MUTATION`.
  - The Site `promote_stegwallet_siwe_runtime.py` and `check_stegwallet_siwe_promotion_gate.py` scripts are specific to their product, not to Site Workers deploys.
  - So this is class B, a missing capability that Lane D builds. It is ecosystem-first: it reuses the org-ledger CAS/readback pattern from #3211 and the existing receipt schema.
- **Location (planned G-8 draft):**
  - Repo: StegVerse-Labs/.github, branch `laned/site-production-promotion-authorization`.
  - `scripts/authorize_site_production_promotion.py`
  - Schema `stegverse.site-production-promotion-manifest/v1`
  - Tests.
  - Not built yet.
- **Inputs:**
  - repo `StegVerse-Labs/Site`
  - the exact 40-hex SHA and the promotion ref
  - the manifest: SHA, environment, route, and the `wrangler.jsonc` sha256 (service `site`, main `src/worker.js`, assets `.`, D1 `HIL_REGISTRY`)
  - the allocator claim/fence on dependency surface `site:production-deploy`
  - the InTr admission reference
  - TV/TVC credential reference (GitHub token runtime authority NONE)
  - provider build identity: service, build id, environment
  - CI check-run ids on the exact SHA
  - the predecessor org-ledger tip
- **Predicates:**
  - P1 `PROMOTION_SOURCE_ON_PROMOTION_REF`: the SHA is reachable from main or the declared ref.
  - P2 `PROMOTION_MANIFEST_BINDS_SHA`
  - P3 `PROMOTION_CLAIM_AND_FENCE_ISSUED`: the fence is at or above the issued floor, the allocator domain is used, and a session claim is never accepted (TRCI L44/L55).
  - P4 `EXACT_SHA_CHECKS_SUCCESS`: evidence only.
  - P5 `INTR_ADMISSION_PRESENT`
  - P6 `CREDENTIAL_AUTHORITY_TVC`
  - P7 `PROVIDER_BUILD_MATCHES_MANIFEST`
  - P8 `FRESH_FETCH_READBACK_VERIFIED`
- **Receipt:**
  - `stegverse.organization-transition-receipt/v1`, transition `SITE_PRODUCTION_PROMOTION_{AUTHORIZED,REFUSED,FAIL_CLOSED}`.
  - Appended to `refs/stegverse/organization-ledger` by compare-and-swap under concurrency group `organization-ledger`.
  - Binds the SHA, the build id, the manifest sha256, the claim/fence and the predecessor receipt sha. It has six fields on any non-ALLOW result.
  - A retro-classification mode records provider deploys that have no receipt, as `PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT`.
- **Refusal codes:**
  - `PROMOTION_SOURCE_NOT_ON_PROMOTION_REF`
  - `PROMOTION_MANIFEST_MISSING`
  - `PROMOTION_MANIFEST_SHA_MISMATCH`
  - `PROMOTION_CLAIM_OR_FENCE_MISSING`
  - `FENCE_GENERATION_BEHIND_ISSUED_FENCES` (existing)
  - `PROMOTION_INTR_ADMISSION_MISSING`
  - `PROMOTION_CREDENTIAL_AUTHORITY_NOT_TVC`
  - `PROVIDER_DEPLOY_IDENTITY_MISMATCH`
  - `PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT`
  - `PROMOTION_READBACK_NOT_VERIFIED`
- **Out of Lane D grants:**
  - Changing Cloudflare build settings, for example gating non-production branch builds. G-8 does not allow settings changes.
  - This goes to JDQ as **Q-D-5**:
    - INVARIANT CHECKED: ORRD L21 and standard 1; SV-DN1 L141.
    - QUESTION: is provider-side promotion enforced in the provider build configuration, or only in SPPA retro-classification?
    - FEEDBACK OUTPUT: a policy entry plus the Site owner's configuration change through its own manifest.
    - DEFAULT: SPPA gates, and every provider build without a receipt is classified unauthorized.

**18.4 SITE_PATH_HELD_BY_ACTIVE_CLAIM disposition.**
- **No competing branch.** I listed the Site branches (122, two pages). None is a `laned/*` or Grok branch, and Lane D opens none.
  - The open Site PRs are #1607 (`chatgpt/1509-six-field-ui-fallback-20261017`, `924d92ed`) and #1606.
- **How D13/WU5 proceed:**
  - **Route (a):** the current holder carries them on its own branch. Site `88d0239d` "Rebind existing Workspace lane claim to PR 1607", so the hold is now on #1607's branch; earlier it was `claude/1509-gate-dispositions-and-b6` at `36ab2637`. The patches in `patches/` stay available to the holder.
  - **Route (b):** an allocator fragment or release receipt.
- **#3231 assessment (`9671ee7a`, not closed): no conflict.**
  - It is `NONE_REQUEST_ONLY`, with `request_grants_claim_authority=false` and `allocator_remains_claim_authority=true`. It is route (b) itself: it asks WorkerCoordinator to decide and records no release.
  - The branch `laned/d13-wu5-workspace-kv` in TASK-2026-0015 `workspace` is conditional. It is created only after a GRANTED receipt and readback.
- **Expected outcome:**
  1. **Now:** no receipt, because main has no hosted consumer until #3211 merges. The request is durably queued (ORRD standard 3).
  2. **#3211 without H46:** `ORGANIZATION_WORKER_CLAIM_FAIL_CLOSED` / `FENCE_GENERATION_BEHIND_ISSUED_FENCES`, because claims-active is at gen 2 and the floor is 7.
  3. **After H46:** the allocator domain holds no Site claim (`claims: []`), so GRANTED is expected with fence ≥ 8. #3235 still refuses projection with `GRANT_EPOCH_NOT_CARRIER_SUPPLIED` until the carrier supplies hb_epoch.
  4. **On REFUSED:** route (a).
- **Annotated:** Labs#3231 comment 6246018591.

**18.5 Open items (unchanged class).**
- **Labs#3211 `6bbce8c2`:** class C. Claude applies the H46 fix and the hb_epoch pass-through on the same branch. 6245688836 says Claude reports CODE_PUSH_NOT_GRANTED, so the repair goes through an authorized same-branch write. Lane D does not push there.
- **Q-D-1 (lease time base) and Q-D-2 (COSV binding vs record schema):** open in the JDQ.
- **Q-D-3, Q-D-4 (§17) and Q-D-5 (above):** proposed.

**18.6 Posted.**
- #167 checkpoint 6246017441: https://github.com/StegVerse-org/.github/issues/167#issuecomment-6246017441
- Labs#3231 note 6246018591: https://github.com/StegVerse-Labs/.github/pull/3231#issuecomment-6246018591

**18.7 Not done.**
- SPPA is not built yet. It is the next G-8 draft.
- No merge, claim, release, settings change, registry edit or ledger dispatch was made.
- Delivery to the orchestrator is handed to the parent session, because the executor had no agent-messaging tool.


## 19. r12: H46 + carrier hb_epoch, superseding G-8 draft Labs#3241 (2026-10-18)
Basis: orchestrator ruling 05:15Z, Q-C7/Q-R-g RULED ALLOW option (b). Claude push to #3211 FAIL_CLOSED CODE_PUSH_NOT_GRANTED (author session_013aXjQ2 inactive). Invariant: a lane holding the patch may adopt a PR whose author session is inactive, as a superseding G-8 draft.
- PR: StegVerse-Labs/.github#3241 DRAFT, branch laned/h46-fence-floor-repair-hb-epoch, head 6ac4c05743ed15c8f1377e9b65d3f36e036c12b6, base main bfcf0318 (unchanged).
- Commits:
  - 42a6084, 79ae5d0 = #3211 ebe4c75c, 6bbce8c2, cherry-picked with -x, Claude authorship and trailers kept.
  - 171f2d5 = patches/H46-fence-floor-repair.diff unchanged (sha256 29132908…; consumer blob 117df896).
  - 6ac4c05 = carrier hb_epoch pass-through. consume(hb_epoch=)/--hb-epoch → consume_request → record_transition → emit.append(hb_epoch=) and aggregate_transition/_aggregate_transition_locked(hb_epoch=). Grant without an epoch: FAIL_CLOSED GRANT_EPOCH_NOT_CARRIER_SUPPLIED before any fence is computed; rematerialized ephemeral registry restored. Invalid epoch: FAIL_CLOSED GRANT_EPOCH_INVALID before any read or append. Non-ALLOW receipts without an epoch stay derived_from_clock:true and grant nothing.
- Tests:
  - unittest custody + resident allocator: 89/89 (77 → 83 H46 → 89 hb_epoch; 6 new for hb_epoch).
  - pytest over 8 claim/allocator files: 113 passed, 1 failed (iphone::test_bootstrap_deadlock_is_not_hidden, pre-existing on main).
  - unittest over 14 claim/allocator files: 111 OK.
  - Global invariants PASS; ratchet exit 0.
  - New tests fail on the H46-only consumer.
- CI at push: consolidated-source-validators, ratchet, validate pending; transition skipping.
- Comments: #167 c6246065413; Labs#3211 c6246065503. #3211 stays OPEN until #3241 merges; nothing pushed to its branch.
- Six-field (B) CARRIER_HB_EPOCH_FORWARDER:
  - failure_code/failed_predicate: GRANT_EPOCH_NOT_CARRIER_SUPPLIED
  - required_evidence_or_repair: a carrier forwards the heartbeat epoch to the consumer. Neither the hosted workflow nor scripts/dispatch_resident_execution_requests.py does today; same pattern as the H34 kernel run_endpoint_adapter forwarding.
  - retry_entrypoint: .github/workflows/organization-claim-allocator-transition.yml / consume --hb-epoch
  - owning_existing_goal: SHWP-ORG-CLAIM-ALLOCATOR-001 (D1, STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001)
  - next_attempt: on the next request event after a carrier supplies the epoch
  - consequence: the first hosted grant is a recorded FAIL_CLOSED, not ALLOW at fence 8. Q-D-4 default refuse holds.
- Transition: ALLOW (G-8 draft + coordination comments), execution locus AUTHORIZED_EXTERNAL (GitHub, own branch). No merge, no push to main or a foreign branch, no registry generation bump, no settings, no ledger dispatch. Admission is by the merge-admission transition (TVC#519 + governance ALLOW) only.
- Next: Lane D builds the carrier-epoch forwarder (B); track #3241 CI; after merge, #3231's receipt and #3235 projection; Q-D-1/Q-D-2 still open.


## 20. r12b/r12c: carrier hb_epoch forwarder (Labs#3243) and SPPA (Labs#3244) (2026-10-18)

**20.1 CARRIER_HB_EPOCH_FORWARDER (B): Labs#3243, DRAFT.**
- Branch `laned/carrier-hb-epoch-forwarder`, head `af6c9dc6834ad6d07a3b7c779651b920a56c0431`. Base: `laned/h46-fence-floor-repair-hb-epoch` (stacked on #3241).
- **Epoch source, from the invariants:** the carrier frame's `heartbeat_reference.epoch`.
  - Checked by the kernel shared rule `supplied_epoch_failure` (`SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`; org-kernel/kernel.py `run_endpoint_adapter` / `carrier_epoch`; H34b; TVC#517 P1).
  - Not a source: the runtime heartbeat snapshot. It is clock-sampled (`independent_oscillator.sample_state`) and `snapshot_is_observation_only`, and the COSV handoff says it is not heartbeat authority.
- **Built:**
  - `scripts/dispatch_resident_execution_requests.py` gains `--hb-epoch` (raw text, shared rule). It forwards the epoch only to `CARRIER_EPOCH_CONSUMERS = {org_claim_allocator}`.
  - With no epoch, nothing is forwarded or derived. An invalid epoch is a six-field FAIL_CLOSED `HB_EPOCH_INVALID` and that consumer is not run.
  - The consumer's `--hb-epoch` applies the same rule to the raw text.
  - The hosted workflow is unchanged.
- **Tests:** unittest 101/101. pytest over the claim, allocator and dispatch files: 233 passed, 6 failed; the same 6 fail on #3241 head and on main. Invariants PASS, ratchet exit 0.
- **CI at the one check:** most checks pending, validate-deepseek-resident and one validate passing. #3241 is now green (consolidated, ratchet and validate pass; transition skipping).
- **Comments:** #167 6246117684; #3241 6246117802.
- **Six-field FAIL_CLOSED still open:**
  - failure_code / failed_predicate: `GRANT_EPOCH_NOT_CARRIER_SUPPLIED` / `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
  - required_evidence_or_repair: a kernel carrier frame delivers the request. Neither the hosted event nor the resident bootstrap has one.
  - retry_entrypoint: dispatcher `--hb-epoch` / allocator workflow
  - owning_existing_goal: SHWP-ORG-CLAIM-ALLOCATOR-001
  - next_attempt: after the Q-D-6 answer
- **JDQ Q-D-6 (refines Q-D-4):**
  - INVARIANT CHECKED: kernel `run_endpoint_adapter` / `carrier_epoch` / `supplied_epoch_failure`; independent_oscillator; COSV handoff; kernel header.
  - QUESTION: does a carrier frame reach the request through (a) a CARRIER_SUPPLIED endpoint row, (b) the request committed with its publishing frame (sha-bound), or (c) neither, so grants stay refused?
  - FEEDBACK OUTPUT: the chosen path; Lane D wires it. Default: refuse.

**20.2 SPPA (B), the Site production-promotion authorization transition: Labs#3244, DRAFT.**
- Branch `laned/site-production-promotion-authorization`, head `1bd7a43022bed7041d85ac53d4cab0411039cc53`, base main `bfcf0318` (current).
- **Files:**
  - `scripts/authorize_site_production_promotion.py`
  - `schemas/site-production-promotion-manifest.schema.json` (`stegverse.site-production-promotion-manifest/v1`)
  - `tests/fixtures/site-production-promotion/site-1607-build-1790bb75-retro.request.json`
  - `tests/test_site_production_promotion_authorization.py` (12 tests)
- **Pattern:**
  - The receipts are recorded through the existing emitters (emit.py, then aggregate_repo_transition) as `stegverse.organization-transition-receipt/v1`. `boundary_evidence.operation` is `SITE_PRODUCTION_PROMOTION_{AUTHORIZED,REFUSED,FAIL_CLOSED}`, the same way allocator grants are recorded.
  - Each receipt is read back through the existing verifier (`verified_organization_receipt`).
  - Every non-ALLOW carries the six fields.
- **Predicates:**
  - P1: compare `<ref>...<sha>` is identical or behind.
  - P2: complete manifest, sha256 recomputes, binds sha/ref/repo/wrangler sha256.
  - P3: allocator grant on the verified chain, scope covers `site:production-deploy`, fence above the TASK-2026-0012 floor (7), not superseded; a session claim is never claim authority (TRCI).
  - P4: evidence only.
  - P5: InTr reference binds the sha. Authenticity: UNKNOWN_NOT_AUTHENTICALLY_OBSERVED.
  - P6: TV/TVC, GitHub token authority NONE.
  - P7: provider service, environment, commit and build match.
  - P8: readback.
- **Dispositions:**
  - PROMOTE: present-but-contradicting evidence is DENY (SOURCE_NOT_ON_REF, MANIFEST_SHA_MISMATCH, CREDENTIAL_NOT_TVC, IDENTITY_MISMATCH). Absent or unverifiable evidence is FAIL_CLOSED.
  - AUTHORIZED also needs the carrier-supplied epoch, otherwise FAIL_CLOSED HB_EPOCH_NOT_SUPPLIED or HB_EPOCH_INVALID. `promotion_may_proceed` is true only after the receipt reads back.
  - RETRO_CLASSIFY is always FAIL_CLOSED with classification PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT. An existing AUTHORIZED receipt for the same sha and build gives AUTHORIZED_RECEIPT_PRESENT, and nothing is appended.
- **Retro-classification of Site#1607, build `1790bb75-3340-4bd3-929d-f188b9f23405` @ `924d92ed`:**
  - Observed read-only: compare main...924d92ed is **diverged** (7 ahead, 31 behind; main `2790025d`, merge base `0916d020`). 6 check runs on the sha are all success (Workers Builds: site 117573570266). Provider comment 6237313898. wrangler.jsonc sha256 `6c85bee3…`. Production route serving: UNKNOWN_NOT_AUTHENTICALLY_OBSERVED.
  - **Result: FAIL_CLOSED `PROMOTION_SOURCE_NOT_ON_PROMOTION_REF`**, classification `PROVIDER_DEPLOY_WITHOUT_AUTHORIZATION_RECEIPT`.
  - Also failed: P2 MISSING, P3 MISSING, P5 MISSING, P6 NOT_TVC and P7 IDENTITY_MISMATCH. P6 and P7 fail because the evidence is absent; §18.3 defines no separate "missing" code for them.
  - The receipt was appended to a temporary ledger in a test only; the real ledger was not touched.
- **Tests:** 12/12. pytest with the custody and resident allocator suites: 80 passed. Invariants PASS, ratchet exit 0.
- **CI at the one check:** consolidated-source-validators and ratchet pending.
- **Comment:** #167 6246172926.
- **Transition:** ALLOW (G-8 draft and coordination comment). Execution locus: AUTHORIZED_EXTERNAL (own branch).
- **Not done:** no Cloudflare wiring, no provider settings, no workflow, no ledger dispatch, no merge. Provider-side enforcement stays JDQ Q-D-5 (default: SPPA gates).
- **Next:**
  - SPPA invocation by manifest-dispatched transition, once Q-D-5 is answered.
  - Track CI on #3241, #3243 and #3244.
  - Q-D-1, Q-D-2 and Q-D-6 are open.

## 21. r12d: SPPA manifest-dispatched real-ledger run (Labs#3245) (2026-10-18)

**21.1 Draft PR: StegVerse-Labs/.github#3245.**
- Branch `laned/sppa-manifest-dispatched-run`, head `4f042db87229c95c038ba1f5ca5065b727679ad2`.
- Base: `laned/site-production-promotion-authorization` @ `1bd7a430` (stacked on #3244).
- It was built against the fail-closed defaults under the Orchestrator 05:40Z instruction and does not wait on Q-D-1/2/5/6.

**21.2 Pattern: the resident request manifest, the same shape as the org-claim-allocator path.**
- `scripts/consume_site_production_promotion_request.py`:
  - Consumes `stegverse.resident-execution-request/v1`, mode `SITE_PRODUCTION_PROMOTION_AUTHORIZATION`, task `STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001`.
  - Reads the fixed path `control/resident-execution-request.d/site-production-promotion-001.json`. The request carries the SPPA request inline with `promotion_request_sha256`.
  - Every request-only flag is pinned false: GitHub token, network fetch, second machine, heartbeat authority, promotion authority, provider settings, and deployment.
  - It calls `authorize()` from #3244. That appends the repository and organization receipts and reads them back through `organization_readback`.
  - Its output is a write-once consumption record plus a `.latest` projection, in `receipts/sovereign-host/site-production-promotion-consumptions/`. Replay is idempotent.
- `schemas/site-production-promotion-resident-request.schema.json`.
- Dispatcher `CONSUMERS` gains `site_production_promotion`. `STEGVERSE_{REPO,ORG}_LEDGER_ROOT` are forwarded the same way as for `org_claim_allocator`.
- Materialization: the consumer and SPPA scripts are added to the install, bootstrap and refresh lists, which avoids CONSUMER_NOT_MATERIALIZED.
- **Six-field refusals before evaluation:**
  - `LEDGER_LOCATION_REQUIRED_FROM_MATERIALIZER`
  - `HOSTED_ENVIRONMENT_NOT_ADMITTED` (via the allocator's `clean_env`)
  - `SITE_PRODUCTION_PROMOTION_REQUEST_INVALID` (covers a hash mismatch)

**21.3 Not done:**
- No request file was added, so the repository commits nothing that would cause a real run.
- No workflow was changed or triggered, and the ledger was not dispatched.
- No Cloudflare or provider settings were touched, and nothing was merged.

**21.4 Expected first run: FAIL_CLOSED.**
- Once a request is committed in a separate commit, which needs its own approval, the first real-ledger run is expected FAIL_CLOSED. That holds until #3241 and #3243 merge and a carrier frame reaches the request (Q-D-6 default refuse).
- A PROMOTE request gets `HB_EPOCH_NOT_SUPPLIED`. The epoch is never synthesized from the clock, and the oscillator snapshot is not a source.
- A retro request fails closed on its first failed predicate. The hosted path is refused.
- Six fields of the expected first refusal:
  - failure_code / failed_predicate: `HB_EPOCH_NOT_SUPPLIED` / `SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH`
  - required_evidence_or_repair: a carrier frame delivers the epoch to the request (Q-D-6)
  - retry_entrypoint: `scripts/consume_site_production_promotion_request.py --hb-epoch` via the resident dispatcher
  - owning_existing_goal: STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001
  - next_attempt: after #3241 and #3243 merge and Q-D-6 is answered

**21.5 Tests (local):**
- New `tests/test_site_production_promotion_dispatched_run.py`: 9/9. SPPA: 12/12.
- 107 related test files (dispatcher, materializer, claim, SPPA): 683 passed / 20 failed, against 674 / 20 at the #3244 head. The failing set is identical (pre-existing).
- Invariants: `TASK_REGISTRY_GLOBAL_VERIFIER_NODE_SUBSTRATE_INVARIANTS_PASS`.
- The local ratchet reports one NEW_FAILURE, `test_sdk_evaluator_governance_posture_resident::test_exact_manifest_calls_sdk_entrypoint_and_retains_binding`. The same failure appears at the #3244 head without this change, and the test passes in isolation, so it is a local environment artifact.

**21.6 CI, one read each at exact heads (heads unchanged):**
- #3241 `6ac4c057`: consolidated pass, ratchet pass, validate pass, transition skipping.
- #3243 `af6c9dc6`: consolidated pass, ratchet pass, all validate checks pass, validate-deepseek-resident pass, transition skipping.
- #3244 `1bd7a430`: consolidated pass, ratchet pass.
- #3245 `4f042db8`: ratchet, consolidated and one validate pending (UNKNOWN_NOT_AUTHENTICALLY_OBSERVED). validate-deepseek-resident and the other validate checks pass.

**21.7 Comment:** #167 6246259390.

**21.8 Transition:** ALLOW (G-8 draft and coordination comment). Execution locus: AUTHORIZED_EXTERNAL (own branch).

**21.9 Follow-ups:**
1. After #3243 merges, add `site_production_promotion` to `CARRIER_EPOCH_CONSUMERS` and consume `--hb-epoch`. Expect a textual conflict in the dispatcher.
2. A commit that adds a real request must also add its path to the bootstrap and refresh `REQUIRED_SOURCE_FILES` lists in the same commit.
3. Q-D-1, Q-D-2, Q-D-5 and Q-D-6 remain open.

## 22. r12e: #3244 merged, branches updated from main a9a2b9b0, #3245 retargeted (2026-10-18)

**22.1 Main.**
- Labs#3244 (SPPA) was merged by the Orchestrator at 11:50:55Z from `1bd7a430`.
- Labs main is `a9a2b9b058fc2049f43d3fd45ad6c614b161254e`, verified by fetch and the API. It follows #3242 `3b04a7e9` (ICV distribution pins).
- Registry is still gen 319; Lane D did not bump it.

**22.2 Branch updates.** Main was merged into each branch as a merge commit, with no rebase and no force-push. Every push was checked as a fast-forward (old head is an ancestor of the new head).

| PR | Branch | Old head | New head | How updated |
|---|---|---|---|---|
| #3241 | `laned/h46-fence-floor-repair-hb-epoch` | `6ac4c057` | `bfb745831e335330fde93ae4a757b102724e0aef` | merged main; base main |
| #3243 | `laned/carrier-hb-epoch-forwarder` | `af6c9dc6` | `114053afac49350ba89db89b29f4a57138eb7785` | merged the updated #3241 branch; base stays the #3241 branch |
| #3245 | `laned/sppa-manifest-dispatched-run` | `4f042db8` | `e9c31b65f1e121a350d968aee026deaa95eea6ec` | merged main; base retargeted from the merged #3244 branch to main |

- #3245's diff is now the run transition only, 7 files:
  - consumer, request schema, dispatcher, install/bootstrap/refresh lists, tests
- The #3245 PR body was updated for the retarget.

**22.3 Conflicts: none.**
- #3242 only added new files under `distribution/icv/`, plus `docs/ICV_DISTRIBUTION_PINS_MIRROR_HANDOFF.md`, `scripts/icv_distribution_offline_install.py` and `tests/test_icv_distribution_offline_install.py`. None of them overlap the Lane D files.
- The `receipts/sovereign-host/resident-request-dispatch.latest.json` change in #3241 dates from the #3211 cherry-pick (79ae5d0) and was unchanged by the merge.

**22.4 Local verification at the new heads.**
- unittest:
  - #3241: claim custody, resident allocator and SPPA, 101/101 (89 + 12 SPPA from main).
  - #3243: those suites plus the forwarder, 107/107.
  - #3245: dispatched run plus SPPA, 21/21.
- pytest over 123 related test files (dispatcher, materializer, claim, allocator, custody, hb_epoch, SPPA). Each head fails the same 20 tests that fail on main (pre-existing).

| Head | Passed | Failed |
|---|---|---|
| main | 957 | 20 |
| #3241 | 978 | 20 |
| #3243 | 984 | 20 |
| #3245 | 966 | 20 |

- Invariants: `TASK_REGISTRY_GLOBAL_VERIFIER_NODE_SUBSTRATE_INVARIANTS_PASS` on all three heads.
- Local ratchet is identical to main on all three heads. The only flag is the same local NEW_FAILURE `test_sdk_evaluator_governance_posture_resident::test_exact_manifest_calls_sdk_entrypoint_and_retains_binding`, which main shows too and which passes in isolation.

**22.5 CI, one read each at the new heads (~3 min after push).**
- #3241 `bfb74583`: 2 pass (validate, consolidated). 1 pending (ratchet) and 1 skipped (transition), both UNKNOWN_NOT_AUTHENTICALLY_OBSERVED.
- #3243 `114053af`: 6 pass (consolidated, validate ×4, validate-deepseek-resident). 1 pending (ratchet) and 1 skipped (transition), both UNKNOWN.
- #3245 `e9c31b65`: 9 pass (validate ×5, consolidated, validate-deepseek-resident, validate-resident-carrier ×2). 1 pending (ratchet), UNKNOWN.
- Main `a9a2b9b0`: check runs ratchet success and consolidated-source-validators success. The combined commit status is "pending" with 0 statuses, so there are no status contexts and it is not a failure signal.

**22.6 Comment:** StegVerse-org/.github#167 6249680106. It is the checkpoint: #3244 merged, new heads, CI counts, #3245 is the (B) real-ledger SPPA run item (already built), Q-D-5 default SPPA gates. It also carries the correction for misposted Labs#167 6246259390.
- The misposted comment was NOT deleted, because deleting needs the user's approval.

**22.7 Transition:** ALLOW (G-8: own-branch merge-commit updates, a fast-forward push, a draft base retarget, a coordination comment).
- No merge to main, no foreign branch, no registry bump, no settings change, no ledger dispatch.
- No request committed and no workflow triggered.

**22.8 Open items:**
- Q-D-1, Q-D-2 and Q-D-6 remain open. Q-D-5 defaults to SPPA gates.
- After #3243 merges: add `site_production_promotion` to `CARRIER_EPOCH_CONSUMERS`.
- The first real SPPA run is expected FAIL_CLOSED `HB_EPOCH_NOT_SUPPLIED` until #3241/#3243 merge and Q-D-6 is answered.

## 23. r12f: `transition` job skipped on PRs, and the PR-safe fix (Labs#3251, #3241, #3243) (2026-10-18)

**23.1 Request.** Coordination (3d7a33fe) flagged that `transition` is SKIPPED on #3241, #3243, #3230, #3213 and #3207, and a skipped check is not an admission input. New Bot's 12:09Z INDEX rule: a PR is admission-input-ready only when every job at the exact head ran and passed. #3241 and its followers (#3232, #3235, #3236, #3243) are held on this.

**23.2 Cause.** The skip comes from a job-level `if:` that excludes pull_request:
- `.github/workflows/organization-ledger-transition.yml` (on main; affects #3230, #3213, #3207): `transition` has `if: github.event_name == 'workflow_dispatch'`.
- `.github/workflows/organization-claim-allocator-transition.yml` (exists only on #3241's branch, from #3211; affects #3241, #3243): `transition` has `if: github.event_name == 'push' || github.event_name == 'workflow_dispatch'`.

The path filters are not the cause. A PR that touches none of the listed paths doesn't trigger the workflow, so it gets no check rather than a skipped one. That is why #3243 shows no Organization Ledger Transition check: its diff against the #3241 branch touches none of that workflow's paths.

**23.3 What the job does (critical).**
- Both `transition` jobs hold `contents: write`.
  - The allocator job binds the contract and fetches the ref, then runs the consumer and allocator against `$GITHUB_WORKSPACE/.git` and appends typed claim dispositions. It checks the fast-forward, runs `git push origin $LEDGER_REF:$LEDGER_REF`, and reads back with the checkout extraheader credential.
  - The ledger job appends the intr-destination self-closure with a dispatch-supplied `hb_epoch` and `communication_id`, then pushes the ref and reads back.
- Running either as-is on a PR would publish to the real Organization ledger, which is a ledger dispatch and never grantable. So neither was made to run as-is.

**23.4 Fix: same job, a PR-safe variant, no new dependencies.**
- The job-level `if:` is removed, so `transition` always runs. Every publishing step is gated `if: github.event_name != 'pull_request'` and is otherwise unchanged.
- On pull_request:
  - Checkout uses `persist-credentials: false`. A guard refuses (six fields) if any `http.*.extraheader` is set.
  - The same contract assertions run.
  - The published ref is copied anonymously (`credential.helper=`, `GIT_TERMINAL_PROMPT=0`; the repo is public) into a temporary bare ledger under `$RUNNER_TEMP`.
  - **Allocator:** the same consumer and allocator run against the temporary ledger with no hb_epoch. Any of the typed classes GRANTED, REFUSED or FAIL_CLOSED passes. The fast-forward check and readback (`--readback-result`) run on the temporary ledger.
  - **Ledger:** `organization_ledger_readback.py` verifies the temporary copy; it must return ALLOW with `readback_writes=false`. No append is attempted: the self-closure needs dispatch inputs, and no epoch is synthesized.
  - Both require the published ref unchanged, or a descendant if another writer appended meanwhile. There is no push, no secret, and no token reference.
- Concurrency: `group: organization-ledger${{ pull_request && '-pr-dry-run-<n>' || '' }}`. PR runs can't displace a pending ORGANIZATION_LEDGER_LOCK writer, and the writer group is unchanged.
- Tests: new `tests/test_transition_job_runs_on_pull_request.py`, stdlib only, 8 tests (the allocator test is skipped on main). The six-field refusal pin in `test_resident_org_claim_allocator` is raised from 4 to 6 on #3241.
- Residual: `contents: write` is job-level and can't be event-conditional, so a same-repo PR run is still issued a write-scoped `GITHUB_TOKEN`. No PR step persists, references or uses it. Follow-up: split the writer into its own workflow, which needs a workflow-surface-registry entry.

**23.5 Commits and heads.** All pushes were fast-forward, with merge commits and no force.

| Item | Branch | Commit or head | Notes |
|---|---|---|---|
| Standalone G-8 draft StegVerse-Labs/.github#3251 | `laned/transition-job-runs-on-pr`, from main `a9a2b9b0` | `0721e170eed3dabce4144bd5cdef6b5eb1bd176a` | generic `organization-ledger-transition.yml` fix plus tests |
| #3241 | `laned/h46-fence-floor-repair-hb-epoch` | `bfb74583` → `e5ba67b26403bef2207638161fcc9cc28e7d8036` | merge of `0721e170`, then the allocator fix `e5ba67b2` |
| #3243 | `laned/carrier-hb-epoch-forwarder` | `114053af` → `9bbb3eae573d0f57f56a513c7dae797734b68868` | merged the #3241 branch |

- Other PRs (#3230, #3213, #3207; not ours, not pushed): they get the fix by merging main after #3251 or #3241 lands, or by cherry-picking `0721e170eed3dabce4144bd5cdef6b5eb1bd176a`.

**23.6 Local verification.**
- Simulated the PR steps (pull_request environment, no credential) against the real published ledger: both variants pass, and the published tip stayed `a5bb54d8`.
- unittest: #3241 141/141; #3243 147/147.
- pytest over 123 related files: each head has the same 20 failures as main.

| Head | Passed | Failed |
|---|---|---|
| #3241 | 986 | 20 |
| #3243 | 992 | 20 |

- Ratchet `observed=99 baseline=99 new=0` on #3251, #3241 and #3243. Invariants PASS.

**23.7 CI, one read each, about 4 minutes after push.**
- #3241 `e5ba67b2`: **6 pass / 0 fail / 0 pending / 0 skipped**. Organization Ledger Transition validate and transition; Organization Claim Allocator Transition validate and transition; ratchet; consolidated-source-validators.
- #3243 `9bbb3eae`: **7 pass / 0 fail / 1 pending (ratchet, UNKNOWN) / 0 skipped**. Allocator validate and transition; Cross-Task Coordination validate; KV AI Memory validate; Resident Runtime/Interlock validate; validate-deepseek-resident; consolidated-source-validators.
- #3251 `0721e170`: **3 pass / 0 fail / 1 pending (ratchet, UNKNOWN) / 0 skipped**. Ledger validate and transition; consolidated-source-validators.
- CI logs confirm `PULL_REQUEST_DRY_RUN` and `PULL_REQUEST_VERIFY` ran. The published ledger tip after the runs is `a5bb54d81893b392a3ce28182986fc39857807e1` (unchanged).

**23.8 Six fields: the publishing half legitimately can't run on a PR.**
- failure_code: `LEDGER_PUBLICATION_NOT_ADMITTED_ON_PULL_REQUEST`
- failed_predicate: `PULL_REQUEST_RUN_DOES_NOT_DISPATCH_THE_ORGANIZATION_LEDGER`
- required_evidence_or_repair: none needed for admission-input readiness. The replacement check is the same `transition` job's PR-safe dry run or verify, which runs and reports pass/fail. Publication stays on push/workflow_dispatch.
- retry_entrypoint: `.github/workflows/organization-claim-allocator-transition.yml` / `.github/workflows/organization-ledger-transition.yml` (pull_request)
- owning_existing_goal: SHWP-ORG-CLAIM-ALLOCATOR-001 (allocator); STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001 (Lane D)
- next_attempt: on each pull_request event

**23.9 Comments:** StegVerse-org/.github#167 6249916096 (repo double-checked); StegVerse-Labs/.github#3241 6249916252.

**23.10 Transition:** ALLOW (G-8: own branches, fast-forward pushes, a new draft PR, coordination comments).
- No merge, nothing pushed to main, no foreign branch, no registry bump, no settings change, no ledger dispatch.
- The real ledger is untouched.

## 24. r12g: writer-only workflow split, so PR runs hold no write-scoped token (Labs#3255, Labs#3258) (2026-10-18)

**24.1 Request.** Orchestrator 12:31Z: a new (B) item under SHWP-ORG-CLAIM-ALLOCATOR-001.
- Keep the PR-facing `transition` job (`contents: read`, dry run or verify only).
- Move every publishing step into a writer-only workflow, triggered only by push to main or workflow_dispatch, with `contents: write`.
- Register the new files in `control/workflow-surface-registry.json`, following #3248's entry format.
- Add tests: PR-triggered jobs have no write permission, and writer workflows never trigger on pull_request.
- Build it as a G-8 draft stacked on Lane C's #3248 (`74ba229c`) and do not push to #3248's branch.

Main had moved to `978b8880` (#3246). #3248 is based on that.

**24.2 Labs#3255: the ledger split.** DRAFT, branch `laned/ledger-writer-workflow-split`, head `75fc4dddffe57e3ad05d87e55a1d6ddffcdec4a0`, base `grok/lane-c-workflow-surface-registration` @ `74ba229c`.
- It merged #3251's `0721e170` (merge commit `cfe868e`), then split the workflow:
  - **`organization-ledger-transition.yml`** is PR-facing:
    - `pull_request` only (path-filtered, now including the writer file and the split test);
    - workflow and every job `contents: read`, and every checkout `persist-credentials: false`;
    - concurrency `organization-ledger-pr-dry-run-<n>`;
    - `validate` is unchanged. `transition` has no job-level `if` and runs the PR-safe verify (anonymous temporary ledger copy, readback, published ref unchanged). No append, no push, no synthesized epoch.
  - **New `organization-ledger-transition-writer.yml`** is writer-only:
    - `workflow_dispatch` only (the original had no push trigger), never pull_request;
    - workflow `contents: read`, job `publish` `contents: write`;
    - `group: organization-ledger` (ORGANIZATION_LEDGER_LOCK);
    - the publishing steps are moved unchanged, and their retry entrypoints name the writer.
  - **Registry:** the writer is registered `KEEP_STANDALONE_EXCEPTION`. Owner: #3248's owner for the file plus "SHWP-ORG-CLAIM-ALLOCATOR-001 (writer split, Lane D)". The reason on #3248's PR-facing entry is updated to describe the split.
  - **Tests (stdlib only):** `tests/test_transition_job_runs_on_pull_request.py` (10) checks:
    - **across the repository, no pull_request/pull_request_target-triggered workflow declares a write permission;**
    - the PR-facing file is pull_request-only, `contents: read`, with no push, credential or token reference, and `transition` is never skipped;
    - **writers never trigger on pull_request** and hold write only at job scope under the shared lock;
    - the split files are registered.

    `test_organization_ledger_transition_writer` now pins the writer file.
- **Correction during the build:** the first pushed commit `b7978fd2` carried only the new writer file, because an index slip left the rest unstaged. `75fc4ddd` adds the rest. Both are fast-forward, no force. The PR head was re-verified from a clean checkout.
- **Local results:**
  - tests 42/42 (1 allocator test skipped);
  - related pytest 966 passed / 20 failed, the same 20 as main;
  - ratchet 99/99, new 0; invariants PASS; hygiene `PASS_REGISTERED_SURFACES` 21/21;
  - a simulated PR `transition` job against the real published ledger passed, and the tip was unchanged at `a5bb54d8`.
- **CI, one read:** **4 pass / 0 fail / 0 pending / 0 skipped**. Organization Ledger Transition validate and transition; ratchet; consolidated-source-validators. The writer never runs on a PR, so it shows no skipped check.

**24.3 Labs#3258: the allocator split.** DRAFT, branch `laned/allocator-writer-workflow-split`, head `361f35bfb31b6fd72f420cec3eb106962f275e9f`, base `laned/h46-fence-floor-repair-hb-epoch` @ `e5ba67b2` (#3241).
- **Placement decision: stacked on #3241.** `organization-claim-allocator-transition.yml` exists only on #3241's branch (from #3211), so the split can't sit on #3248 or #3255. It is a separate draft rather than a commit on #3241, so #3241's verified head (every job ran and passed) is not churned. It can be folded into #3241 by merging the branch.
- **#3241 depends on it.** Once #3255 is on main, #3241 cannot be admission-input-ready without this split: #3255's repository-wide no-write test fails a pull_request-triggered workflow that holds `contents: write`.
- **Build:**
  - It merged #3255's branch (bringing #3248 and main `978b8880`). There was a registry conflict at the end of the surfaces list; I kept both sides, with #3248's three entries and the ledger writer, then the allocator entry.
  - Split:
    - **PR-facing `organization-claim-allocator-transition.yml`:** pull_request only, `contents: read`, per-PR group. `transition` is the PR-safe dry run: the same consumer and allocator against an anonymous temporary ledger, no `hb_epoch`, fast-forward check and readback on the copy, published ref unchanged.
    - **New writer-only `organization-claim-allocator-transition-writer.yml`:** push to main on `control/resident-execution-request.d/org-claim-allocator-*.json` plus workflow_dispatch; job `publish` `contents: write`; shared lock.
  - Entrypoint references: the consumer's `EVENT_EPHEMERAL_ENTRYPOINT`, the writer's refusals and the handoff doc's trigger line now name the writer.
  - Registry: the writer is registered, and the allocator entry reason is updated.
  - Tests: the allocator pins read the writer, and the six-field refusal count spans both files (4 + 2).
- **Local results:**
  - unittest 143/143;
  - related pytest 988 passed / 20 failed, the same 20 as main;
  - ratchet 99/99, new 0; invariants PASS; hygiene 23/23;
  - both simulated PR `transition` jobs pass, and the published ledger is unchanged.
- **CI, one read:** **5 pass / 0 fail / 1 pending (ratchet, UNKNOWN) / 0 skipped**. Allocator validate and transition; ledger validate and transition; consolidated-source-validators.

**24.4 Observations, not acted on.**
- `gadi-resident-execution-preflight-validation.yml` and `test-suite-ratchet.yml` are pull_request-triggered and declare no top-level `permissions`. Their token scope is therefore the repository default. Neither declares a write permission, so the repository-wide test passes.
- `completion_evidence.live_workflow_count` in the registry (16) was already stale and was not changed.
- Every session pushes as the GitHub account StegVerse, so commit author metadata can't prove BRANCH_WRITER_IS_BRANCH_OWNER. Each PR body carries the session's own declaration.

**24.5 PR-body edits under the binding rule** (12:35Z / 12:47Z). Merge wording was relabelled to admission terms, and `Authoring session` (Lane D "KV and WorkSpace" Grok bot, agent b699e0c0-3b4e-4a24-945f-6f521c282268, pushing as StegVerse) plus `Branch writers` lines were added:

| PR | Merge wording relabelled | Branch writers |
|---|---|---|
| #3231 | "Do not merge without Rigel." | Lane D only (`9671ee7a`) |
| #3232 | "Do not merge without Rigel." | Lane D only (`abdc51f2`) |
| #3235 | "Do not merge without Rigel." | Lane D only (`50525699`) |
| #3241 | "Do not merge without Rigel." | the only pusher is Lane D; openly carries Claude's #3211 commits `42a60846` and `79ae5d05`, cherry-picked with `-x`; the rest are Lane D's; whether that satisfies BRANCH_WRITER_IS_BRANCH_OWNER is an input for admission |
| #3243 | "Do not merge without Rigel." | Lane D only |
| #3245 | "Do not merge." | **fails BRANCH_WRITER_IS_BRANCH_OWNER** (foreign stopgap commits `dd317bd3`, `8e08e467`, `88a2067a`); a superseding `laned/` draft will be opened once #3253 is on main (not opened now) |
| #3251 | "Do not merge." | Lane D only |
| #3253 | "Do not merge without Rigel's authorization." | Lane D only (`c9703e3e`) |
| #3255, #3258 | created with the declarations; "applies until admission" wording aligned | Lane D, with merged-in base commits declared |

A re-read of all 10 bodies shows the session and writers lines present and 0 matches for Rigel / merge-ready / merge order.

**24.6 Comment:** StegVerse-org/.github#167 6250060467 (org verified).

**24.7 Transition:** ALLOW (G-8: own branches, fast-forward pushes, draft PRs, own PR-body edits, coordination comment).
- No push to #3248's branch or to #3245/#3253's branches, no merge, no main, no registry-generation bump, no settings change, no ledger dispatch.

**24.8 For later (not acted on).** Once #3248 is on main, #3241 and then #3243 merge main, and each is reported only when every job at the exact head ran and passed. With #3255 on main as well, #3241 also needs #3258 folded in.

## 25. r12g: SPPA fail-open correction (Labs#3253) (2026-10-18)

**25.1 PR.** Labs#3253 DRAFT, branch `laned/sppa-fail-open-correction`, head `c9703e3e`, base main `978b8880`. CI 2/2.

**25.2 Correction.**
- `decide()` returns AUTHORIZED only if P1–P7 all PASS at the required authenticity. UNKNOWN, missing or unauthenticated evidence gives at most FAIL_CLOSED. Caller-supplied evidence may refuse but never authorize.
- Issuers:
  - boundary: `org-runtime/interlock-intr.json` `owner_repository` (P1, P4, P5, P7);
  - TVC: `control/formalism-tvc-repository-transport.json` `tvc_broker.repository` (P6).
- `AUTHENTICATING_CUSTODY_BASES` is empty (Q74-01), so AUTHORIZED is unreachable on main.
- P4 is reconciled with `scripts/evaluate_pr_precreation_gate.py` and the INDEX exact-head rule.

**25.3 Verification.**
- Tests 12 → 22.
- Suites: 182 passed / 1 failed (main: 172 passed / 1 failed).
- Ratchet 99/99, new 0. Invariants PASS.

**25.4 #3245.**
- #3245 merged the correction, giving head `6d974c92`. That supersedes another session's stopgap commits `dd317bd`, `8e08e46` and `88a2067`.
- 34/34 local. CI: 9 pass, ratchet pending (UNKNOWN).
- #3245 fails BRANCH_WRITER_IS_BRANCH_OWNER (§24.5). A superseding `laned/` draft will be opened once #3253 is on main.

**25.5 Six fields.**
- failure_code: `SPPA_CALLER_EVIDENCE_YIELDS_AUTHORIZED`
- failed_predicate: `decide()`
- required_evidence_or_repair: Labs#3253
- retry_entrypoint: `scripts/authorize_site_production_promotion.py`
- owning_existing_goal: STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001
- next_attempt: re-run #3245 after #3253 merges

**25.6 New (B) items.**
- Producers for SITE_SOURCE_REACHABILITY_OBSERVED, SITE_EXACT_HEAD_CHECKS_OBSERVED, SITE_PRODUCTION_PROMOTION_INTR_ADMITTED, TVC_CREDENTIAL_ISSUED and SITE_PROVIDER_BUILD_OBSERVED.
- A custody basis declaration.

**25.7 Comments:** org#167 c6249948909; #3245 c6249951611.

**25.8 Boundary:** this session did not touch the #3253 and #3245 branches. They are maintained by the concurrent SPPA job. This session edited only their PR bodies under the binding rule.

## 26. r13: C4 drafted body amendments for merge-authority wording (2026-10-18)

Class B item C4, assigned by the orchestrator. The coordination comment is on StegVerse-org/.github#160 (issuecomment-6250171232). I edited no issue body. These drafts go through the KV standards path for body edits.

Binding source: INDEX "MERGE AUTHORITY" (Rigel 12:35Z): "Rigel merges no PRs and is never asked to." "PRs merge ONLY through the ecosystem's merge-admission transition: TVC#519 MERGE_ADMITTED_PULL_REQUEST plus a governance-decision ALLOW, observed through ledger receipts." Rigel 12:39Z: "The ecosystem should be able to merge its own PRs."

### 26.1 StegVerse-Labs/.github#3183 body, line 50
- OLD: `- Owner approves merges; CI and exact expected-head protection required. Do not open duplicate PRs or leave stale failing PRs unaddressed.`
- NEW: `- PRs merge only through the merge-admission transition (TVC#519 MERGE_ADMITTED_PULL_REQUEST + governance-decision ALLOW, observed via ledger receipt). Inputs: admission-input-ready (every job at the exact head ran and passed, no skips) and admission order. Preconditions include PR_AUTHOR_SESSION_DECLARED and BRANCH_WRITER_IS_BRANCH_OWNER. Exact expected-head protection required. Do not open duplicate PRs or leave stale failing PRs unaddressed.`

### 26.2 StegVerse-org/.github#160 body, invariant 2 (last sentence)
- OLD: `Preserve exact-head checks, expected-head protection, and existing owner-required merge authorization.`
- NEW: `Preserve exact-head checks and expected-head protection; merge authorization is the merge-admission transition (TVC#519 MERGE_ADMITTED_PULL_REQUEST + governance-decision ALLOW, ledger-receipted), never an owner action or a request to the owner.`

### 26.3 StegVerse-org/.github#120 F1
Ruling (orchestrator, by invariant): Rigel's 04:08Z no-owner-items rule covers every item. So F1 becomes a manifest-directed Sandbox activation transition (class A), and its missing capability is built under StegVerse-org/.github#163.
- OLD (a): `Obtain specific owner authorization for activation and manifest scope.`
- NEW (a): `Activation and manifest scope are decided by the manifest-directed Sandbox activation transition (class A; ALLOW/DENY/FAIL_CLOSED with receipt). The missing activation capability is built under StegVerse-org/.github#163.`
- OLD (b): `Preserve exact-head protected merges for any independently authorized source repair.`
- NEW (b): `Any independently authorized source repair merges only through the merge-admission transition (TVC#519 + governance ALLOW) with exact-head protection.`
- OLD (c): `If authorization remains absent, report OWNER_AUTHORIZATION_PENDING as a decision prerequisite, not as a fabricated runtime disposition.`
- NEW (c): `Until the activation capability exists (StegVerse-org/.github#163), report the Sandbox activation transition's FAIL_CLOSED with all six fields, not a fabricated runtime disposition. OWNER_AUTHORIZATION_PENDING is retired.`

### 26.4 NWI-S0 migration fixtures: not built
The INDEX NWI-S0 entry says SV_ISSUE and SV_CHANGE become record types inside STEGVERSE-CANONICAL-WORK-COORDINATION-001, with the schema change going through repo-standards together with org#150. On StegVerse-Labs/.github main, `git grep SV_ISSUE|SV_CHANGE|work_items` returned no matches. No schema for these record types is published (schemas/ has only canonical-task-record and the worker-* schemas), and StegVerse-org/repo-standards returned 404 to this session. Disposition FAIL_CLOSED:
- reason: S0_RECORD_FORMAT_NOT_PUBLISHED
- observed: no SV_ISSUE/SV_CHANGE schema on Labs main or in any open PR found by the search
- required: published S0 record schema (repo-standards + org#150)
- authority: INDEX NWI-S0 (12:53Z)
- repair: build laned/s0-lane-d-migration-fixtures once the schema lands
- evidence: this section; org#160 comment 6250171232
