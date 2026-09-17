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

Two concrete repository-native defects were found and repaired without claiming resident execution.

### 1. COSV WorkerCoordinator policy-binding skew

The canonical COSV handoff authorizes policy version:

```text
cosv-heartbeat-state-packet-v2-independent-task-control
```

but `control/worker-registry.d/cosv-live-packet-automation-006.json` still carried:

```text
cosv-live-packet-v2-independent-task-control
```

This was a stale control-plane binding: WorkerCoordinator policy-rebind logic records and reconciles the task's `authorized_policy_version` against the handoff's observed policy version, so leaving the fragment divergent could force unnecessary rebind/block semantics at the authentic execution surface.

Repair:

```text
commit: 391ea3860f98792f0a9e3d27795badf8462ec110
file: control/worker-registry.d/cosv-live-packet-automation-006.json
new authorized_policy_version: cosv-heartbeat-state-packet-v2-independent-task-control
```

Regression guard:

```text
commit: bc59a7c1e53c204dd8804722a3e64785a05c63fc
file: tests/test_task_load_independent_admission.py
assertion: fragment authorized_policy_version == handoff authority.policy_version
```

A focused isolated execution of the policy-binding assertion passed. No post-anchor COSV packet was emitted by this source repair, and no live StegBrain gradient is claimed.

### 2. TVC exact resident-request cleanup defect

`scripts/authorize_and_activate_private_source_read.py` accepted a custom `--resident-request-path` but, after successful service completion, unlinked the hard-coded default `REQUEST_PATH`. A non-default request could therefore remain after successful activation and be observed again by its watcher.

Repair:

```text
source commit: 6c7ae0711c2c889ac6b08aa6c903d72b88f72381
test commit: 207bb046ef98b60f04a2998b6ab95120bb7a6c9c
source: StegVerse-Labs/TVC/scripts/authorize_and_activate_private_source_read.py
test: StegVerse-Labs/TVC/tests/test_authorize_and_activate_private_source_read.py
```

The activation helper now removes exactly `resident_request_path` on exception, service failure, and successful service completion; cleanup is idempotent. Focused isolated cleanup regression tests passed. The TVC StegMusic handoff was reconciled at commit `fccef9068f4ace6cacae19cfc257943d1eaa063a`.

This repair does not prove systemd service installation, credential presence, scoped grant activation, staged StegMusic request consumption, exact materialization, or deterministic validation PASS.

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
COSV worker policy binding: RECONCILED TO CANONICAL HANDOFF
GitHub Actions activation: prohibited
first post-anchor packet: NOT OBSERVED
first changed post-anchor DELTA: NOT OBSERVED
StegBrain live-gradient consumer source: COMPLETE_RELEASED
deterministic replay: PASS
first live gradient receipt: NOT OBSERVED
```

The materializer derives the current heartbeat reference from `heartbeat_runtime.independent_oscillator.current_reference` and treats persisted carrier/worker files as historical evidence surfaces; source repair does not itself establish an admitted resident execution opportunity.

## Current target-specific posture

- `.github`: heartbeat protocol core verified; COSV worker control-plane policy skew repaired; first authentic post-anchor packet still unobserved.
- `TVC`: private-source source/control implementation exists; exact custom request cleanup defect repaired; authentic resident service/credential/request consumption remains unobserved.
- `StegMusic`: exact-current request remains staged; resident materialization and deterministic PASS remain unobserved.
- `StegBrain`: live-gradient consumer source complete and deterministic replay PASS; first changed post-anchor DELTA/live gradient remain unobserved.
- `GP10`: repository-native runtime proof COMPLETE/PASS; remaining transitions are authentic-evidence or human-authority gated.
- `StegTalk`: repository and adjacent automation COMPLETE; no machine-remediable work remains before external `deployment.authorization_evidence.pending` condition.
- `stegfin-governance`: pre-sign `WALLET_HANDOFF_READY` directly evidenced; USER_ONLY signing/broadcast remains outside machine functionalization.

## Remediation order from here

1. Continue source-only inspection of the shared WorkerCoordinator/resident request path for stale policy, pointer, request-ingress, or receipt-retention defects that can be proven without live execution.
2. Preserve staged `TVC-STEGMUSIC-VALIDATION-001` until authentic TVC resident service/credential evidence appears; then consume only through the existing TVC path.
3. Preserve `COSV-LIVE-PACKET-AUTOMATION-006` until an authentic admitted local execution surface appears; if the first post-anchor packet is a verified changed DELTA with non-empty `gradient_inputs`, consume it only through the existing StegBrain live-gradient consumer and retain both packet/gradient receipts.
4. Preserve GP10 runtime-proof completion and StegTalk's external-only AURI-007 boundary.
5. Preserve StegFin USER_ONLY signing/broadcast outside machine completion.
6. Promote resident/runtime/provider/public predicates only from authentic receipts.

## README impact

These repairs close internal control-plane/request-cleanup defects but do not change `.github` or TVC public interfaces, authority boundaries, credential ownership, or user-facing behavior. Existing README descriptions remain materially correct; canonical handoffs were updated instead of fabricating a product-function change.

## Completion predicates

- all 15 previously role-functional repositories remain role-functional after dependency regression review;
- each of the 7 partial repositories reaches its established functional role with direct evidence, or its remaining non-machine authority/evidence condition is isolated after machine-remediable dependencies are complete;
- dependency defects get canonical owners/tasks instead of remaining prose;
- README/handoff state remains current where function materially changes;
- no runtime/provider/public-E2E claim is made without direct evidence.

## Current state

`ACTIVE / CHECKED_OUT`.

This continuation repaired two concrete source/control defects that would otherwise degrade authentic execution: COSV task policy-binding skew and TVC non-default resident-request cleanup. No resident/runtime predicates were promoted. The remaining COSV/StegBrain and TVC/StegMusic transitions still require authentic local execution evidence.
