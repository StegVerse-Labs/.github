# GADI Resident Execution Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / SOURCE-CHAIN-MERGED / RETAINED-STEGBROWSER-STEGOS-SUBSTRATE-SELECTED / PROVIDER-VERIFICATION-BINDING-MATERIALIZER-MERGED / GADI-RETAINED-DISCOVERY-OBSERVER-MERGED / CURRENT-IPHONE-RECEIPT-READ-SURFACE-MERGED / CURRENT-IPHONE-RECEIPT-OBSERVER-IN-VALIDATION / RUNTIME-PRESENCE-RENDEZVOUS-SUBJECT-PROPAGATION-MERGED / CURRENT-RUNTIME-DISCOVERY-EVIDENCE-PENDING / AUTHENTIC-RESIDENT-EXECUTION-PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and not superseded. Authentic current resident execution remains unobserved.

Canonical single-device substrate:

```text
SELECTED: STEG-BROWSER-RETAINED-RESIDENT-NODE
SUITABLE: STEGOS-CURRENT-DEVICE-NODE
SUITABLE: STEG-BROWSER-EPHEMERAL-LEASE
SUITABLE: SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER
NOT_APPLICABLE: ADMITTED-EPHEMERAL-STEGOS-NODE
NOT_APPLICABLE: REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT
external_device_required=false
second_user_operated_device_allowed=false
authority_effect=NONE
```

The remaining pre-runtime condition is `EVIDENCE_REACHABILITY`, not evidence that a second physical device is required.

## Retained discovery observer — merged

`.github` PR #1555 merged as `6374478f9f48d4923c61d53c5e3659fc61aca464` after exact-head validation PASS.

`scripts/observe_gadi_retained_resident_discovery.py` observes only the existing task-agnostic localhost contract:

```text
GET http://127.0.0.1:8000/api/resident-rendezvous/v1/discovery
GET http://localhost:8000/api/resident-rendezvous/v1/discovery
schema = stegverse.resident-rendezvous.discovery/v1
state = AVAILABLE
target_node_ref = SV-NODE-<24 lowercase hex>
gateway_execution_authority = NONE
credential_authority = TV/TVC
discovery_grants_authority = false
authority_effect = NONE_DISCOVERY_ONLY
```

There is no hosted fallback and no new listener/page/protocol. Source/CI validation is not current discovery evidence.

## Current-iPhone discovery receipt read surface — merged

StegOS PR #350 merged as:

```text
40ecd6417a953975d2382722880f3dbcc11fa96e
```

Its exact pre-merge head `fca07189a53dcf98d960921ade2260fefd86f41c` passed StegOS CI, all GADI validation workflows, iOS Device Package Validation, and iOS Apple Toolchain Validation.

StegOSMobile already persists current-iPhone retained-discovery observations to:

```text
stegos-stegbrowser-current-iphone-rendezvous-receipts.jsonl
```

PR #350 extended only the existing `StegBrowserNativeResidentRendezvousListener` on `127.0.0.1:8000` with the GET-only evidence projection:

```text
GET /api/resident-rendezvous/v1/evidence/current-iphone-discovery?target_node_ref=SV-NODE-<24 lowercase hex>
```

The route reads the latest already-persisted receipt and fails closed unless it matches the exact requested/retained node plus current-device/non-authority invariants. The fetch wrapper is `NONE_EVIDENCE_READ_ONLY`. No POST/mutation route, second listener, page, runtime, scheduler, WorkerCoordinator, claim/fence plane, InTr authority, credential route, remote device, or second user-operated machine was added.

The merged read surface does not prove the current iPhone is presently running the listener or that an authentic receipt can presently be read.

## Current-iPhone receipt observer — source in validation

Current branch:

```text
gadi-current-iphone-receipt-observer-001
```

New source:

```text
scripts/observe_gadi_current_iphone_discovery_receipt.py
tests/test_gadi_current_iphone_discovery_receipt.py
```

The observer consumes only the merged StegOS #350 GET surface. It accepts an exact canonical retained `SV-NODE-*` from the already-observed generic discovery result and probes only:

```text
http://127.0.0.1:8000
http://localhost:8000
```

It validates the fetch wrapper as:

```text
schema = stegos.stegbrowser.current-iphone-rendezvous-observation-fetch/v1
state = EVIDENCE_AVAILABLE | NO_EVIDENCE
target_node_ref = exact retained node
gateway_execution_authority = NONE
credential_authority = TV/TVC
evidence_grants_authority = false
authority_effect = NONE_EVIDENCE_READ_ONLY
```

For `EVIDENCE_AVAILABLE`, it delegates validation of the embedded receipt to the already-existing canonical `materialize_gadi_retained_node_discovery.py` projector rather than creating a second receipt semantics implementation. This rechecks the exact current-iPhone execution surface, retained node identity, receipt/envelope hashes, retained-node lineage binding, embedded discovery contract, HB/GitHub non-authority, TV/TVC credential authority, and no InTr/WorkerCoordinator/request-consumption assertion.

Successful observation emits only:

```text
state = CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED
authority_effect = NONE_EVIDENCE_READ_ONLY
runtime_presence_observed = false
runtime_subject_bound = false
claim_or_fence_granted = false
intr_admission_granted = false
execution_authority_granted = false
```

`NO_EVIDENCE`, listener unreachability, malformed wrappers, node mismatch, receipt invariant mismatch, or authority drift fail closed. There is no hosted fallback and no POST path.

## Receipt-gated targeted runtime readiness — source in validation

`scripts/run_gadi_targeted_runtime_if_ready.py` now enforces this exact order:

```text
CURRENT RETAINED NODE DISCOVERY
-> CURRENT READ-ONLY PERSISTED CURRENT-IPHONE RECEIPT READBACK FOR SAME NODE
-> CURRENT GADI RUNTIME BINDING FOR SAME NODE
-> NONCLAIM SOURCE COHERENCE
-> ONLY THEN TARGETED WORKERCOORDINATOR VISIT
```

The runtime-binding projector is not invoked when current receipt readback is absent. New fail-closed readiness conditions include:

```text
CURRENT_RETAINED_RESIDENT_CURRENT_IPHONE_RECEIPT_NOT_OBSERVED
DISCOVERY_CURRENT_IPHONE_RECEIPT_SUBJECT_MISMATCH
CURRENT_IPHONE_RECEIPT_RUNTIME_SUBJECT_MISMATCH
```

The child canonical task record now registers:

```text
scripts/observe_gadi_current_iphone_discovery_receipt.py
DEP-GADI-CURRENT-IPHONE-RECEIPT-READBACK = UNRESOLVED runtime evidence
CURRENT_RETAINED_STEGBROWSER_STEGOS_CURRENT_IPHONE_RECEIPT_READBACK_OBSERVED
```

This is source gating only. It does not establish the runtime evidence predicate.

## Runtime-presence retained-node subject propagation — merged

`.github` PR #1562 merged as:

```text
cc53257c7e57347d2481dd4fd680aed9b8cf2f6d
```

The shared runtime-presence projector may resolve resident identity from the existing `resident_rendezvous_node_ref` only when it is a canonical `SV-NODE-*`. This is observation-only subject propagation; node identity does not prove runtime liveness or grant runtime binding, claim/fence, admission, credential, transition, or execution authority.

## GADI runtime-binding boundary

`scripts/materialize_gadi_runtime_binding.py` remains the only GADI runtime-binding projector. A binding is emitted only when current canonical runtime-presence evidence establishes:

```text
runtime_root exact subject match
resident.node_id present
runtime_alive_observed = true
present_worker_runtime_observed = true
worker_cycle_fresh = true
canonical carrier runtime observed
canonical WorkerCoordinator runtime observed
carrier/worker supervision active
HB authority effect NONE
credential authority TV/TVC
GitHub runtime authority NONE
```

Correct sequence:

```text
current retained-node discovery
-> current read-only persisted current-iPhone receipt readback for same node
-> exact same-node current runtime presence/supervision
-> materialize_gadi_runtime_binding.py
-> CURRENT_RUNTIME_SUBJECT_BOUND
```

Discovery, receipt presence, node identity, source merge, or CI alone never satisfies runtime binding.

## Provider-verification source boundary — merged

```text
StegCore #207 independently verified external-evidence requirement — MERGED
StegOS #345 trusted-key Ed25519 verifier — MERGED
StegOS #346 independent provider-evidence verification binding materializer — MERGED
```

Current authentic provider/signature/chain/freshness inputs remain unobserved. No envelope may self-assert those predicates.

## Existing merged GADI execution lineage

Representative lineage:

```text
.github #1388 WorkerCoordinator registration repair
.github #1395 post-claim dispatcher bridge
.github #1405 non-claim readiness + stale replay protection
Governance #40 authoritative GADI profile
StegCore #202 Governance decision -> GADI Admission
.github #1413 runtime-root/node subject binding
StegOS #331 controlled actuator-output seam
StegOS #337 native command bridge
StegOS #342 native plan materializer
StegCore #204 local InTr/Governance admission materializer
StegOS #344 native command CLI
StegCore #205 PENDING request + Governance candidate
.github #1479 canonical pre-claim artifact chain
StegCore #206 external evidence -> Governance facts
StegCore #207 independently verified external evidence
StegOS #345 trusted-key Ed25519 verifier
StegOS #346 provider-evidence verification binding materializer
.github #1539 Task Registry single-device-first substrate sorting
.github #1541 retained StegBrowser/StegOS substrate reconciliation
.github #1555 retained native discovery observer + readiness subject match
.github #1562 retained rendezvous node -> shared runtime-presence subject propagation
StegOS #350 current-iPhone persisted discovery receipt -> existing loopback read surface
```

## Canonical execution sequence

```text
CURRENT RETAINED STEGBROWSER/STEGOS NATIVE DISCOVERY
-> CURRENT READ-ONLY PERSISTED CURRENT-IPHONE DISCOVERY RECEIPT FOR SAME NODE
-> CURRENT RESIDENT-PRESENCE + SUPERVISION SUBJECT OBSERVATION FOR SAME NODE
-> CURRENT GADI RUNTIME BINDING
-> CURRENT THREAT / BOUNDARY OBSERVATIONS
-> CURRENT GADI-SCOPED EXTERNAL-EVIDENCE ENVELOPE
-> CURRENT INDEPENDENT SIGNATURE / PROVIDER / CHAIN / FRESHNESS EVIDENCE
-> CURRENT VERIFIED-EXTERNAL-EVIDENCE BINDING
-> CURRENT PRE-ADMISSION NATIVE DEFENSE PLAN
-> PROJECTED CURRENT THREE-LAYER GOVERNANCE FACTS
-> CURRENT PENDING INTERVENTION REQUEST + HASH-BOUND GOVERNANCE CANDIDATE
-> LOCAL CANONICAL INTR TRANSPORT + GOVERNANCE EVALUATION
-> CURRENT ADMITTED GADI REQUEST
-> NATIVE STEGOS COMMAND BOUND TO EXACT RUNTIME SUBJECT
-> CONTROLLED PREAUTHORIZED OUTPUT OBSERVATION
-> NON-CLAIM READINESS
-> TARGETED WORKERCOORDINATOR CLAIM/FENCE
-> SOURCE RESOLUTION WITH CLAIM DEFERRED
-> FRESH CLAIM PROJECTION
-> MATERIALIZATION
-> PREFLIGHT
-> RESIDENT CONSUMPTION
-> REASSESSMENT / TERMINATION
-> CONTINUITY / MASTER RECORDS RECONSTRUCTION
```

WorkerCoordinator remains sole claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential authority. HB/runtime-presence remains observation only. GitHub validation remains non-authorizing.

## Current authentic evidence boundary

Still unobserved for GADI:

```text
CURRENT_RETAINED_STEGBROWSER_STEGOS_NODE_DISCOVERY
CURRENT_RETAINED_STEGBROWSER_STEGOS_CURRENT_IPHONE_RECEIPT_READBACK
CURRENT_GADI_RUNTIME_PRESENCE_SUBJECT
CURRENT_GADI_RUNTIME_BINDING
CURRENT_GADI_BOUNDARY_INTERACTION
CURRENT_GADI_THREAT_OBSERVATION
CURRENT_GADI_EXTERNAL_EVIDENCE_ENVELOPE
CURRENT_GADI_SIGNATURE_VERIFICATION
CURRENT_GADI_PROVIDER_AUTHORIZATION
CURRENT_GADI_CHAIN_VERIFICATION
CURRENT_GADI_FRESHNESS_VERIFICATION
CURRENT_GADI_VERIFIED_EXTERNAL_EVIDENCE_BINDING
CURRENT_GADI_PRE_ADMISSION_PLAN
CURRENT_GADI_RESOLVED_GOVERNANCE_FACTS
CURRENT_GADI_PENDING_INTERVENTION_REQUEST
CURRENT_GADI_INTR_ADMISSION
CURRENT_GADI_NATIVE_COMMAND
CONTROLLED_PREAUTHORIZED_ACTUATOR_RESULT
CURRENT_GADI_WORKERCOORDINATOR_CLAIM_FENCE
CURRENT_GADI_RESIDENT_CONSUMPTION
```

The latest authorized connected-device observation was empty. This is a reachability observation only and does not imply an external/second device is required.

## Immediate continuation

1. Validate the current receipt observer/readiness branch with organization-control, deterministic repository, Heartbeat, and focused GADI tests.
2. Merge only on an exact fully green head.
3. On the authentic current-device sovereign runtime, let the retained discovery observer obtain the exact current `SV-NODE-*`.
4. Use the merged receipt observer to read StegOS #350's persisted current-iPhone receipt projection for that exact node; treat `NO_EVIDENCE` or listener unreachability as runtime observation, never as authority to synthesize evidence.
5. Only after successful receipt readback, require canonical runtime presence/self-heal to establish the same node plus liveness/supervision/freshness and run the existing runtime-binding projector.
6. Continue through the merged external-evidence, Governance/InTr, command, controlled-output, readiness, WorkerCoordinator, resident-consumption, reassessment/termination, Continuity, and Master Records chain.

## Collision boundary

No second heartbeat, resident service, runtime scheduler, listener, activation page, WorkerCoordinator, claim/fence plane, InTr authority, Governance evaluator, credential route, evidence-provider authority, actuator implementation, or Master Records custody path may be created.

## README impact

The repository README already documents the retained current-iPhone resident, canonical authority separation, and the rule that source/CI cannot substitute for runtime evidence. This change narrows internal GADI readiness by consuming that existing evidence surface and does not change the public architecture contract; no README text replacement is required for this branch.

## Manual work

None at this stage. Do not ask the user to activate a HIL/KV page for GADI. A user action should be requested only if the existing native retained-resident path remains unreachable after the source observer is merged and Task Registry confirms a collision-safe action surface.
