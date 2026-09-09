# Global Runtime Evidence Convergence Matrix

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Umbrella issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / ALL_18_LANES_HB32_RUNTIME_NODE_PROFILED / STEGCLAW_P4_RESIDENT_EXECUTION_PATH_BOUND / AUTHENTIC_RUNTIME_PREDICATES_STILL_EVIDENCE_BOUND`

## Finding

The StegBrowser milestone established the reusable runtime-state pattern:

```text
retained StegOS node identity + continuity
+ HB32 synchronization / freshness observation
+ exact task / subject binding
+ bounded or ephemeral execution session
-> task-specific execution path
-> exact receipt / custody / reconstruction
```

The node survives bounded execution-session teardown. Session-local cookies, credentials, provider sessions, navigation state, and temporary execution state do not. The 18 runtime lanes now have explicit runtime-node profiles, but profile presence alone is not execution evidence.

Canonical source:

```text
control/runtime-node-profiles.json
control/runtime-profile-sources.json
scripts/build_runtime_profile_map.py
scripts/run_global_runtime_node_profile_convergence.py
control/runtime-observability-consumers/stegbrowser-ephemeral-runtime-binding-001.json
```

## Shared convergence stages

1. `SOURCE_AND_REQUEST_READY`
2. `RETAINED_STEGOS_NODE_PROFILE_BOUND`
3. `AUTHENTIC_RESIDENT_PROCESS_OBSERVED`
4. `AUTHENTIC_REQUEST_CONSUMPTION`
5. `WORKERCOORDINATOR_CLAIM_FENCE`
6. `INTERLOCK_INTR_ADMISSION`
7. `CREDENTIAL_OR_PROVIDER_CUSTODY` when applicable
8. `COMPONENT_EXECUTION`
9. `EXACT_RECEIPT_EXPORT_OR_RETENTION`
10. `MASTER_RECORDS_CUSTODY_RECONSTRUCTION`
11. `DOWNSTREAM_PROPAGATION_VERIFICATION`

## Current lane comparison

| Lane | Runtime-node profile / existing route | First unresolved or next evidence stage |
| --- | --- | --- |
| CryptoBot / `CRYPTO-LIVE-AUTO-001` | Canonical Work ingress profile | Authentic exact CryptoBot request consumption |
| HIL / `SHWP-HIL-SOVEREIGN-RECEIVER-001` | `hil` resident selector + browser evidence lineage | ESRL `LEASE_OPEN` and downstream receiver/custody proof |
| Hugging Face / SV-DN1 | `sv_dn1` + publication selectors | Exact SDK first-round resident analysis |
| SDK / Ecosystem Chat | `ecosystem_chat` selector | Exact parent SDK execution / inference evidence |
| VACC / `VACP-SOVEREIGN-PROVIDER-REALIGNMENT-023` | LLM-adapter external-runtime profile + existing VA/Master Records bridges | Exact current model/TVC route/reconstruction execution, or verified live VACC process reuse |
| DEVICE_KV / MyKV | `stegos_kv_intr_chain` selector | Subject-bound resident execution plus exact KV evidence |
| StegVerse-001 | `stegverse001_bounded_autonomy` selector | Current-device continuation predicates not already terminal |
| SV002 | `sv002_public_observation` selector | Authentic materialization consumption and observation chain |
| StegClaw P4 | `workers/stegclaw_p4_profiled_resident_execution.py` -> existing `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` / COSV `50000000101000` | Authentic resident wrapper visit; then later StegClaw admission/execution/replay predicates |
| Endpoint Fanout | Existing `stegos_kv_intr_chain` downstream of DEVICE_KV | Authentic DEVICE_KV parent then exact fanout result |
| GADI | Existing preflight-gated wrapper | Real preflight + claim/fence + InTr + controlled execution evidence |
| Governed Multilane Manifold | Existing manifold selector | Per-child claim/fence and formalism receipts |
| GLM 5.3 Sovereign | `glm53_sovereign_lane` selector | Subject-bound GLM execution |
| SV-011 Phase 5 | Source-materialization + phase-5 selectors | Subject-bound phase-5 execution |
| Canonical Runtime Profile Map | Runtime-profile lifecycle selectors | Authentic CanonicalWork ingress / resident map lifecycle |
| Native Email | `native_email_action_monitor` selector | Provider/runtime mailbox consumption and downstream action evidence |
| StegBrowser | `STEGBROWSER_RESIDENT` + Canonical Work ingress | Authentic current-iPhone node/process continuity and browser invocation |
| DE-006 | Exact-parent-rebind profile | `EXACT_DE006_BOUND_PARENT_ADMISSION_OR_REEXECUTION_OF_AUTHENTIC_DEVICE_LOCAL_EVIDENCE` |

## StegClaw P4 runtime repair

The prior profile only observed the external StegClaw state. Fresh inspection of the named shared executor found a concrete queue defect: `workers/organization_local_resident_boundary_executor.py` left successfully consumed ingress packets in the live sorted ingress directory. An old completed packet could therefore remain first forever and starve later work.

The repair now moves an exactly verified consumed ingress packet to `spool/organization-local-boundary/consumed/` after its receipt and egress reconstruct. Receipt, egress, and exact original ingress bytes are retained; a different-byte archive collision fails closed.

StegClaw P4 now uses a real resident-materialized worker bridge:

```text
workers/stegclaw_p4_profiled_resident_execution.py
```

The bridge stages an exact packet bound to `DATA-CONTINUATION-STEGCLAW-P4`, then invokes the already-registered `ORGANIZATION-LOCAL-RESIDENT-BOUNDARY-EXECUTOR-001` through `refresh_and_execute_resident_task.py` with COSV `50000000101000`. Only an exact organization-local receipt whose claim/fence and packet hashes reconstruct may produce:

```text
receipts/sovereign-host/stegclaw-p4-resident-execution.latest.json
state = STEGCLAW_P4_RESIDENT_EXECUTION_OBSERVED
```

That receipt satisfies the named-executor/path-attribution portion of P4 only. It does not infer StegClaw terminal activation, later request admission/consumption, application execution, or replay/reconstruction.

The bridge lives under `workers/`, which both sovereign source-refresh implementations already materialize wholesale. This removes the one-off script allowlist seam that existed in the first draft of the repair.

## Remaining formerly-unwired lanes

### VACC

The profile distinguishes a verified live VACC process, missing LLM-adapter materialization, incomplete runtime surfaces, and parent model/TVC-route/reconstruction pending. The next repair should turn the current profile-only classification into an exact executable wrapper reusing the already-existing LLM-adapter and Master Records bridges.

### DE-006

The exact-parent-rebind profile checks the canonical evidence bindings and preserves the already-authentic device-local inference only as candidate evidence until exact DE-006 parent admission/re-execution exists. The next repair should execute that exact parent path rather than merely report readiness.

## StegBrowser lifecycle reference

```text
retained
  node_ref
  genesis_hash
  state_generation
  state_commitment

ephemeral
  browser context
  cookies
  provider session
  credential material
  navigation history
  temporary page state
```

Merged source/build evidence satisfies implementation predicates only; authentic current-iPhone same-node continuity remains a physical runtime predicate.

## Remaining runtime problem classes

1. resident not materially present/current;
2. exact request not consumed;
3. claim/fence or InTr stage missing;
4. provider/model/runtime dependency not materially present/current;
5. component execution receipt absent;
6. exact parent/custody/reconstruction incomplete;
7. physical current-device observation absent;
8. downstream propagation incomplete.

## Execution order

1. Merge the StegClaw P4 profiled resident-execution repair after exact-head validation.
2. Refresh the authentic resident from already-local canonical source.
3. Enter through `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` and run profiled convergence.
4. Require task-local StegClaw execution evidence instead of observation-only classification.
5. Implement the same executable-profile pattern for VACC and DE-006.
6. Continue every other lane from its actual first missing subject-bound predicate.
7. Reconstruct exact receipts through Master Records and re-run convergence.

## README impact

`README.md` was reviewed. Existing documentation already covers the single resident runtime, exact subject-bound evidence, HB observation semantics, reusable ephemeral constructs, and autonomous continuation. This repair specializes those existing semantics and introduces no new user-facing interface. No README text mutation is required.
