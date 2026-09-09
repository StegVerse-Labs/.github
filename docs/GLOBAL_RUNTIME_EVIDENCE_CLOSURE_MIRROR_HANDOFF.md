# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / ALL_18_RUNTIME_LANES_HB32_NODE_PROFILED / PROFILE_CONVERGENCE_MERGED / RESIDENT_SOURCE_REFRESH_PROPAGATION_IN_PROGRESS / AUTHENTIC_PROFILE_CONVERGENCE_EXECUTION_NEXT`

## Purpose

Converge all StegVerse ecosystem capabilities that are source-implemented or integration-ready but still require authentic runtime execution/evidence, custody/reconstruction, runtime-bound validation, or downstream propagation proof. Preserve each child Goal Task ID and resume it from the first genuinely unresolved subject-bound predicate.

## Retained-node convergence model

The first StegBrowser ephemeral StegOS node implementation established the reusable state model:

```text
retained StegOS node identity + continuity
+ HB32 synchronization / freshness observation
+ exact task / subject binding
+ bounded or ephemeral execution session
-> task-specific execution path
-> exact receipts
-> Master Records reconstruction
```

Retained node state survives bounded session teardown. Session-local cookies, credentials, provider sessions, navigation state, and temporary execution state do not. HB remains observation/timing/freshness/correlation only and grants no execution, admission, claim/fence, credential, routing, transition, custody, publication, or completion authority.

Canonical StegBrowser evidence:

```text
StegVerse-Labs/StegBrowser@0de903391f30cb8af50a3f9a8d95cfcd1ea9edf3
StegVerse-Labs/StegOS@cfe1e0b27f085d084c6290d346b6c2ff6be50fcb
docs/milestones/STEGBROWSER_FIRST_EPHEMERAL_STEGOS_NODE_2026-09-09.md
```

## Merged global profile convergence

`.github` PR #1288 merged at:

```text
c22f0f347bb91e77b81d78e6e5e9b9ce7eea7409
```

Exact PR head `a0930793d78481b4a1c9ddac38c0a944f22621b9` passed:

```text
organization control plane: 34369862142 SUCCESS
deterministic repository suite: 34369861959 SUCCESS
heartbeat validation: 34369862200 SUCCESS
```

Merged source now includes:

```text
control/runtime-node-profiles.json
control/runtime-profile-sources.json
control/runtime-observability-consumers/stegbrowser-ephemeral-runtime-binding-001.json
scripts/build_runtime_profile_map.py
scripts/run_global_runtime_evidence_convergence.py
scripts/run_global_runtime_node_profile_convergence.py
scripts/install_and_run_canonical_work_event_bootstrap.py
tests/test_global_runtime_node_profile_convergence.py
```

`control/runtime-node-profiles.json` defines exactly 18 task-bound `HB32 / RETAINED_STEGOS_NODE / EPHEMERAL_OR_BOUNDED_RUNTIME_LEASE` profiles. The canonical Runtime Profile Map builder projects all 18 as `PRODUCT_RUNTIME` profiles over the existing resident substrate.

The profiled convergence runner wraps the existing global convergence visitor and resident dispatcher. It does not create a second heartbeat, scheduler, dispatcher, WorkerCoordinator, credential path, or transition plane.

The three prior generic-unwired lanes now resolve through explicit profile classes:

```text
VACC       -> EXTERNAL_RUNTIME_PROFILE_BRIDGE
StegClaw   -> OBSERVABILITY_BOUND_EXTERNAL_RUNTIME
DE-006     -> EXACT_PARENT_REBIND_PROFILE
```

Profile binding is not runtime proof. It removes the false `NO_REGISTERED_SELECTOR / UNWIRED_CHILD_RUNTIME` abstraction and exposes the real missing runtime predicate.

## Resident source-refresh propagation defect found after #1288

Post-merge inspection found that the canonical sovereign source-refresh allowlists did not yet carry the newly merged runtime-node profile registry, profiled convergence runner, base convergence runner, Runtime Profile Map builder, partial-solution projection, or full runtime-observability consumer directory into a refreshed resident root.

That is a real execution-path propagation defect: a resident refreshed from canonical source could continue running older source even while repository validation was green.

The active repair updates both:

```text
scripts/refresh_sovereign_worker_runtime_source.py
scripts/refresh_sovereign_worker_runtime_source_base.py
```

so resident refresh carries:

```text
scripts/build_runtime_profile_map.py
scripts/run_global_runtime_evidence_convergence.py
scripts/run_global_runtime_node_profile_convergence.py
control/runtime-node-profiles.json
control/runtime-profile-sources.json
control/runtime-partial-solution-projections/GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001.json
control/runtime-observability-consumers/
```

Focused regression:

```text
tests/test_runtime_node_profile_resident_source_refresh.py
```

The test requires both refresh implementations to carry the full profile-convergence source set and executes an actual local source refresh into a temporary runtime root, verifying the new wrapper/profile/consumer files are present while mutable runtime state remains preserved and no network/credential/GitHub-token operation occurs.

## Runtime profile policy

```text
hb_protocol = HB32
node_state_class = RETAINED_STEGOS_NODE
execution_session_class = EPHEMERAL_OR_BOUNDED_RUNTIME_LEASE
node_identity_survives_session_teardown = true
session_credentials_survive_teardown = false
session_cookies_survive_teardown = false
hb_is_observability_only = true
hb_grants_execution_authority = false
profile_match_grants_execution_authority = false
worker_claim_authority = WORKERCOORDINATOR
credential_authority = TV/TVC
transition_admission = INTERLOCK_INTR
runtime_reality_custody = MASTER_RECORDS
exact_subject_binding_required = true
source_presence_proves_runtime = false
```

## Current lane routing

- CryptoBot -> Canonical Work ingress profile.
- HIL -> `hil` selector profile.
- Hugging Face / SV-DN1 -> `sv_dn1` + publication profiles.
- SDK / Ecosystem Chat -> `ecosystem_chat` profile.
- VACC -> existing LLM-adapter external-runtime surfaces + VA/Master Records bridges.
- DEVICE_KV / MyKV -> `stegos_kv_intr_chain` profile.
- Endpoint Fanout -> same exact chain after DEVICE_KV parent.
- StegVerse-001 -> `stegverse001_bounded_autonomy` profile.
- SV002 -> `sv002_public_observation` profile.
- StegClaw -> canonical HB observability-bound external runtime profile.
- GADI -> existing preflight-gated runtime wrapper profile.
- Governed Multilane Manifold -> existing manifold selector profile.
- GLM 5.3 Sovereign -> existing GLM selector profile.
- SV-011 Phase 5 -> source-materialization + phase-5 profiles.
- Runtime Profile Map -> existing lifecycle selector profile.
- Native Email -> native-email selector profile.
- StegBrowser -> `STEGBROWSER_RESIDENT` retained-node profile + Canonical Work ingress.
- DE-006 -> exact-parent-rebind profile.

## Remaining runtime problem classes

After profile and source-refresh convergence, remaining failures are actual runtime/evidence stages rather than missing generic wiring:

1. retained node/process not materially present/current;
2. exact request not consumed;
3. WorkerCoordinator claim/fence not observed;
4. Interlock/InTr stage not observed;
5. required model/provider/external runtime not materially present/current;
6. component execution receipt absent;
7. exact parent rebinding/custody/reconstruction incomplete;
8. physical current-device observation absent;
9. downstream propagation incomplete.

The resident should preserve the same task/node identity and continue from the first missing stage rather than constructing a replacement runtime.

## README review

`README.md` remains accurate for this repair. It already documents HB as non-authorizing observation/timing/freshness, exact subject-bound runtime presence, the single existing resident dispatcher/WorkerCoordinator model, reusable ephemeral constructs with durable identity, and autonomous machine continuation. The repair changes source propagation for those already-documented semantics and introduces no new user-facing interface. No README mutation is required.

## Next execution

After the source-refresh propagation repair validates and merges:

1. refresh the authentic sovereign resident from the already-local canonical source;
2. enter through the existing `STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001` CanonicalWork event;
3. run the existing base convergence visitor and the profiled wrapper;
4. require `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` with 18 members and zero generic-unwired classifications;
5. continue each child from the exact first unresolved predicate in that receipt;
6. retain exact child execution evidence and reconstruct through Master Records.

Source/CI/refresh still does not substitute for authentic resident execution.

## Manual work

None currently required.
