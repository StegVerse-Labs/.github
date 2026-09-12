# GADI Resident Execution Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / SOURCE-CHAIN-MERGED / RETAINED-STEGBROWSER-STEGOS-SUBSTRATE-SELECTED / CURRENT-IPHONE-RUNTIME-DEPENDENCY-EXPLICIT / PROVIDER-VERIFICATION-BINDING-MATERIALIZER-MERGED / GADI-RETAINED-DISCOVERY-OBSERVER-MERGED / RUNTIME-PRESENCE-RENDEZVOUS-SUBJECT-PROPAGATION-MERGED / CURRENT-RUNTIME-DISCOVERY-EVIDENCE-PENDING / AUTHENTIC-RESIDENT-EXECUTION-PENDING`

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

The selected retained node is the identity substrate. It is not itself proof that a task-capable WorkerCoordinator runtime is currently installed or active on the current iPhone.

## Current-iPhone retained-runtime dependency — explicit

Post-#1562 audit reconciled the selected GADI substrate against canonical sibling task `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`.

That sibling currently reports:

```text
DEP-STEGBROWSER-IOS-RESIDENT-LIFECYCLE:
  SOURCE_AND_UNSIGNED_PACKAGE_READY_CURRENT_DEVICE_PROOF_PENDING

DEP-STEGBROWSER-APPLE-SIGNING:
  CURRENT_IPHONE_WASM_SIGNING_SOURCE_IMPLEMENTED_RUNTIME_EVIDENCE_PENDING

CURRENT_IPHONE_SIGNED_INSTALLATION_OBSERVED: NOT OBSERVED
CURRENT_IPHONE_RESIDENT_RENDEZVOUS_AVAILABLE: NOT OBSERVED
```

Therefore GADI now models:

```text
DEP-GADI-CURRENT-IPHONE-RETAINED-RUNTIME
ref = STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001
kind = RUNTIME_EVIDENCE
state = SOURCE_AND_UNSIGNED_PACKAGE_READY_CURRENT_DEVICE_PROOF_PENDING
```

This dependency does not grant GADI execution authority. It only states that the already-selected same-device retained StegBrowser/StegOS substrate must actually be installed and observed before GADI can claim current retained discovery/runtime binding.

Missing current discovery is therefore not merely an isolated tool-connectivity condition. The parent current-iPhone runtime lane itself still lacks authentic signed-install/TestFlight/listener discovery evidence. This remains single-device-first; no second user-operated device is permitted or required.

## Native current-iPhone discovery evidence surfaces

Two non-authorizing evidence surfaces now coexist for different purposes.

### Native StegOSMobile receipt validator

Existing `scripts/materialize_gadi_retained_node_discovery.py` validates the native StegOSMobile JSONL receipt:

```text
schema = stegos.stegbrowser.current-iphone-rendezvous-observation/v1
state = LOCAL_DISCOVERY_OBSERVED
execution_surface = CURRENT_USER_IPHONE
node_origin = STEGBROWSER_RESIDENT
endpoint = http://127.0.0.1:8000
```

It recomputes the source receipt and envelope digests, requires retained-node lineage commitments, requires canonical `SV-NODE-*`, and emits only observation evidence. It cannot emit `CURRENT_RUNTIME_SUBJECT_BOUND`.

### Localhost retained-discovery observer — merged

`.github` PR #1555 merged as `6374478f9f48d4923c61d53c5e3659fc61aca464` after exact head `f6b706061b058fb31724b768b5518309b0da75ac` passed Heartbeat run 3307, organization-control run 3025, and deterministic-suite run 556.

`scripts/observe_gadi_retained_resident_discovery.py` probes only:

```text
GET http://127.0.0.1:8000/api/resident-rendezvous/v1/discovery
GET http://localhost:8000/api/resident-rendezvous/v1/discovery
```

It creates no listener/page/protocol and has no hosted fallback. It exists as the cross-process same-device observer when the native listener is already running. The Site KV wrapper is not reused.

Neither surface proves WorkerCoordinator liveness, GADI runtime binding, claim/fence, InTr admission, credential authority beyond TV/TVC declaration, or execution.

## Runtime-presence retained-node subject propagation — merged

`.github` PR #1562 merged as `cc53257c7e57347d2481dd4fd680aed9b8cf2f6d` after exact head `a9264f70f94c647932f3c5662468b9f6e972294b` passed organization-control run 3032, deterministic-suite run 563, and Heartbeat run 3315.

The selected native service can preserve retained node identity as:

```text
resident_rendezvous_node_ref = SV-NODE-<24 lowercase hex>
```

The shared `heartbeat_runtime/runtime_presence_projection.py` now resolves identity in this order:

```text
1. existing nonempty node_id
2. existing nonempty sovereign_node
3. resident_rendezvous_node_ref only when ^SV-NODE-[0-9a-f]{24}$
```

It records `resident.node_identity_source`. Malformed rendezvous refs remain unusable. Runtime-alive recognition, fresh WorkerCoordinator-cycle requirements, canonical carrier/worker supervision, HB non-authority, TV/TVC credential authority, and GitHub-token non-authority remain unchanged.

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
STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001 current-iPhone install/discovery proof
-> current retained-node discovery
-> exact same-node current runtime presence/supervision
-> materialize_gadi_runtime_binding.py
-> CURRENT_RUNTIME_SUBJECT_BOUND
```

Discovery or node identity alone never satisfies runtime binding.

## Provider-verification source boundary — merged

```text
StegCore #207 independently verified external-evidence requirement — MERGED
StegOS #345 trusted-key Ed25519 verifier — MERGED
StegOS #346 independent provider-evidence verification binding materializer — MERGED
```

Current authentic provider/signature/chain/freshness inputs remain unobserved. No envelope may self-assert those predicates.

## Existing merged GADI execution chain

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
.github #1563 canonical merged-state reconciliation
```

## Canonical execution sequence

```text
AUTHENTIC CURRENT-IPHONE RETAINED STEGBROWSER/STEGOS INSTALL + LISTENER AVAILABILITY
-> CURRENT RETAINED STEGBROWSER/STEGOS NATIVE DISCOVERY
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
CURRENT_IPHONE_SIGNED_INSTALLATION_OBSERVED
CURRENT_IPHONE_RESIDENT_RENDEZVOUS_AVAILABLE
CURRENT_RETAINED_STEGBROWSER_STEGOS_NODE_DISCOVERY
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

The authorized connected-device surface was empty during the latest inspection. That remains reachability evidence only and does not imply an external/second device is required.

## Immediate continuation

1. Reuse `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`; do not build a second iPhone resident installer or listener for GADI.
2. Require authentic current-iPhone signed installation and resident rendezvous availability from that sibling runtime lane.
3. Once the existing native listener is actually available, let #1555 and/or the native receipt validator observe the exact retained `SV-NODE-*`.
4. Require canonical runtime-presence/self-heal evidence to project that same retained node while satisfying current liveness/supervision/freshness predicates.
5. Run the existing GADI runtime-binding projector only after those observations agree.
6. Continue through the already-merged external-evidence, Governance/InTr, command, controlled-output, readiness, WorkerCoordinator, resident-consumption, reassessment/termination, Continuity, and Master Records chain.

## Collision boundary

No second heartbeat, resident service, runtime scheduler, listener, activation page, WorkerCoordinator, claim/fence plane, InTr authority, Governance evaluator, credential route, evidence-provider authority, actuator implementation, iPhone resident installer, signing path, or Master Records custody path may be created.

## Manual work

None at this stage. Do not ask the user to activate a HIL/KV page for GADI. Any user action should originate from the existing `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001` current-iPhone signing/TestFlight/SKAP trajectory when that canonical lane reaches an owner checkpoint.
