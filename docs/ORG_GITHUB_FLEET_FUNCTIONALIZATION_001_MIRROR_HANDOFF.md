# Organization GitHub Fleet Functionalization Mirror Handoff

Status: ACTIVE / CHECKED_OUT
Repository: `StegVerse-Labs/.github`
Goal Task ID: `ORG-GITHUB-FLEET-FUNCTIONALIZATION-001`
COSV profile: `task.v1`
COSV vector: `20010000100000`
Parent evidence task: `ORG-GITHUB-REPOSITORY-STATUS-SUMMARY-001`
Parent census: `reports/ORG_GITHUB_REPOSITORY_STATUS_SUMMARY_001.md`

## Goal

Convert the 22 repositories represented by the census's 15 `FULFILLING_INTENDED_ROLE` plus 7 `VALIDATED_OR_IMPLEMENTED_PARTIAL` repositories into a dependency-stable functional set without promoting source/CI evidence into runtime/provider/public proof.

Primary partial targets remain `.github`, `GP10`, `StegMusic`, `StegTalk`, `TVC`, `StegBrain`, and `stegfin-governance`. The 15 already role-functional repositories remain a regression set and are not reopened without evidence of regression.

## Preserved completed / evidence-isolated state

- GP10 repository-native runtime proof remains COMPLETE/PASS at tested commit `06a2f17ec7864562e1d947d95b93b33b261dec73`, run `35266625877`, job `105355312939`, receipt `GP10-RUNTIME-5204306871AADC95`.
- StegTalk AURI-001..006 remain COMPLETE; AURI-007 has no remaining repository-controlled machine repair and remains isolated at external `deployment.authorization_evidence.pending`.
- TVC -> StegMusic exact request remains staged for `StegVerse-Labs/StegMusic@12c335df716040a2f98333e0b2355ef118502d01` and has not been promoted to resident consumption/materialization/PASS.
- HB31 remains valid historical FULL COSV evidence only; it is not treated as the current protocol reference or execution authority.

## Shared .github/TVC/runtime dependency inspection — 2026-09-17 continuation

Four concrete repository-native defects have now been repaired without claiming resident execution.

### 1. COSV WorkerCoordinator policy-binding skew

The canonical COSV handoff authorizes:

```text
cosv-heartbeat-state-packet-v2-independent-task-control
```

while `control/worker-registry.d/cosv-live-packet-automation-006.json` previously carried `cosv-live-packet-v2-independent-task-control`.

Repair:

```text
commit: 391ea3860f98792f0a9e3d27795badf8462ec110
file: control/worker-registry.d/cosv-live-packet-automation-006.json
```

Regression assertion:

```text
commit: bc59a7c1e53c204dd8804722a3e64785a05c63fc
file: tests/test_task_load_independent_admission.py
```

No post-anchor COSV packet or StegBrain gradient is claimed from this source correction.

### 2. TVC exact resident-request cleanup defect

`scripts/authorize_and_activate_private_source_read.py` accepted a custom `--resident-request-path` but successful completion deleted the hard-coded default request instead of the exact path used by the invocation. A non-default request could therefore survive terminal service completion and be observed again.

Repair:

```text
source commit: 6c7ae0711c2c889ac6b08aa6c903d72b88f72381
test commit: 207bb046ef98b60f04a2998b6ab95120bb7a6c9c
```

The helper now removes the exact `resident_request_path` on exception, service failure, and successful completion. This does not prove service installation, credential presence, request consumption, materialization, or StegMusic PASS.

### 3. Preclaim fragment-policy reconciliation seam

Inspection of the actual fragment-loading semantics found a second-order defect behind the COSV policy repair. `_apply_registry_fragments` is intentionally append-only: once a task ID is present in mutable resident `control/worker-registry.json`, refreshing a corrected static fragment cannot overwrite it. Therefore a resident that had previously admitted the stale COSV fragment could preserve the old `authorized_policy_version` indefinitely even after local source refresh.

The repair is deliberately narrower than general fragment overwrite. The canonical admitted WorkerCoordinator now permits only an **unclaimed `HANDOFF_READY` preclaim policy reconciliation** when all of these are true:

```text
state == HANDOFF_READY
claim_id / worker_id / worker_instance_id absent
heartbeat_timing absent
assignment_timer absent
lease absent
existing handoff_ref == fragment handoff_ref
fragment authorized_policy_version == canonical handoff authority.policy_version
```

Only `authorized_policy_version` is reconciled. Claim, fence, worker assignment, timing, lease, credential, execution and transition authority remain untouched. Live/bound tasks remain protected by the existing policy-rebind path.

Repair:

```text
source commit: 491947e94a4463d7fed07c84372e261bd492d03f
file: heartbeat_runtime/admitted_worker_runtime.py
```

Regression coverage:

```text
commit: dbf35f095e770203fb274ab27f1984a397544b7e
file: tests/test_preclaim_fragment_policy_reconciliation.py
```

The tests cover successful unclaimed reconciliation, refusal to alter claimed/timed tasks, and fail-closed fragment/handoff policy mismatch.

### 4. Exact-selector dispatch false-complete semantics

The resident request dispatcher intentionally reports `DISPATCH_COMPLETE` for a broad all-consumer pass even when one request fails, because failure of one independent request must not starve later consumers. That behavior is correct for the broad dispatcher.

However, the exact-selector path used by portable targeted execution inherited the same aggregate state. With exactly one selected target, a consumer could return `FAIL_CLOSED`, appear in `request_failures`, and still yield `DISPATCH_COMPLETE`. A targeted bridge could therefore treat a failed target visit as a completed dispatch.

The dispatcher now distinguishes these cases:

```text
ALL_REGISTERED + one request failure -> DISPATCH_COMPLETE, later requests still visited
EXACT_SELECTOR + selected target request failure -> DISPATCH_INCOMPLETE
```

Repair:

```text
source commit: 24ad1e4f290980f7aaa7a7c24e18db6ce504b3c8
file: scripts/dispatch_resident_execution_requests.py
```

Regression coverage:

```text
commit: 069014cab0e88b84dac0ca8f045b9b1c4a3a5ce4
file: tests/test_resident_request_dispatcher.py
```

The broad non-starvation contract remains unchanged while exact-target execution now fails closed on its own request failure.

## TVC -> StegMusic current state

```text
request: StegVerse-Labs/TVC/requests/private-source-read/TVC-STEGMUSIC-VALIDATION-001.json
consumer_task: TVC-STEGMUSIC-VALIDATION-001
reference_mode: IMMUTABLE_COMMIT
exact_sha: 12c335df716040a2f98333e0b2355ef118502d01
materialization_id: stegmusic-main-validation-12c335df
ttl_seconds: 600
state: RESIDENT_ADMISSION_REQUEST_STAGED
```

Still not directly observed:

```text
sole-host service/watcher installation
TVC_PRIVATE_SOURCE_READ_TOKEN presence under TV/TVC custody
scoped grant activation
request consumption
exact resident materialization
authorized_exact_sha == observed_exact_sha
StegMusic deterministic PASS/BLOCK receipt
```

No alternate credential, GitHub Actions activation, duplicate runtime, or synthetic PASS is permitted.

## COSV -> StegBrain current state

Existing canonical chain remains:

```text
.github COSV-LIVE-PACKET-AUTOMATION-006
-> protocol-derived post-anchor packet
-> changed DELTA only if canonical state differs
-> non-empty gradient_inputs for changed records
-> existing StegBrain live-gradient consumer
```

Direct state after repair:

```text
heartbeat core: ACTIVE_PROTOCOL_VERIFIED
HB31: historical FULL packet preserved
COSV producer source: COMPLETE_RELEASED
COSV task: HANDOFF_READY / independently task-control claimable
COSV static worker policy binding: RECONCILED TO CANONICAL HANDOFF
stale unclaimed resident policy after refresh: MACHINE-REPAIRABLE BY BOUNDED PRECLAIM RECONCILIATION
GitHub Actions activation: prohibited
first post-anchor packet: NOT OBSERVED
first changed post-anchor DELTA: NOT OBSERVED
StegBrain live-gradient consumer source: COMPLETE_RELEASED
deterministic replay: PASS
first live gradient receipt: NOT OBSERVED
```

The materializer derives the current heartbeat reference from `heartbeat_runtime.independent_oscillator.current_reference`; persisted carrier/worker files remain historical evidence surfaces. These source repairs do not themselves establish an admitted resident execution opportunity.

## Current target-specific posture

- `.github`: heartbeat protocol core verified; COSV policy skew and stale-preclaim policy-refresh seam repaired; exact-selector dispatch now fails closed; first authentic post-anchor packet remains unobserved.
- `TVC`: private-source source/control implementation exists; exact custom-request cleanup defect repaired; authentic resident service/credential/request consumption remains unobserved.
- `StegMusic`: exact-current request remains staged; resident materialization and deterministic PASS remain unobserved.
- `StegBrain`: live-gradient consumer source complete and deterministic replay PASS; first changed post-anchor DELTA/live gradient remain unobserved.
- `GP10`: repository-native runtime proof COMPLETE/PASS; remaining transitions are authentic-evidence or human-authority gated.
- `StegTalk`: repository and adjacent automation COMPLETE; no machine-remediable work remains before external `deployment.authorization_evidence.pending` condition.
- `stegfin-governance`: pre-sign `WALLET_HANDOFF_READY` directly evidenced; USER_ONLY signing/broadcast remains outside machine functionalization.

## Remediation order from here

1. Continue source-only inspection of source-refresh, exact resident ingress, task-pointer, fencing, request-consumption and receipt-retention semantics for further concrete defects.
2. Preserve staged `TVC-STEGMUSIC-VALIDATION-001` until authentic TVC resident service/credential evidence appears; then consume only through the existing TVC path.
3. Preserve `COSV-LIVE-PACKET-AUTOMATION-006` until an authentic admitted local execution surface appears. Local source refresh may reconcile only the narrow unclaimed policy seam above; actual claim/fence/execution still requires the canonical runtime.
4. If the first post-anchor COSV packet is a verified changed DELTA with non-empty `gradient_inputs`, consume it only through the existing StegBrain live-gradient consumer and retain packet/gradient receipts.
5. Preserve GP10 runtime-proof completion, StegTalk's external-only AURI-007 boundary, and StegFin USER_ONLY signing/broadcast.
6. Promote resident/runtime/provider/public predicates only from authentic receipts.

## README impact

These repairs close internal control-plane, request-cleanup and exact-target result-semantics defects. They do not change `.github` or TVC public interfaces, authority boundaries, credential ownership, or user-facing behavior. Existing README descriptions remain materially correct; canonical handoffs carry the internal functional changes.

## Completion predicates

- all 15 previously role-functional repositories remain role-functional after dependency regression review;
- each of the 7 partial repositories reaches its established functional role with direct evidence, or its remaining non-machine authority/evidence condition is isolated after machine-remediable dependencies are complete;
- dependency defects get canonical owners/tasks instead of remaining prose;
- README/handoff state remains current where function materially changes;
- no runtime/provider/public-E2E claim is made without direct evidence.

## Current state

`ACTIVE / CHECKED_OUT`.

This continuation repaired two additional shared-runtime defects: stale preclaim fragment policy could previously survive source refresh indefinitely, and exact-target resident dispatch could falsely report completion after its selected consumer failed. Both are now fail-closed without weakening the existing live-claim/fence authority boundary. No resident/runtime predicates were promoted.
