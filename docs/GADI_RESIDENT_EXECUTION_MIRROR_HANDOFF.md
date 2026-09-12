# GADI Resident Execution Mirror Handoff

Updated: 2026-09-12
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / SOURCE-CHAIN-MERGED / RETAINED-STEGBROWSER-STEGOS-SUBSTRATE-SELECTED / PROVIDER-VERIFICATION-BINDING-MATERIALIZER-MERGED / GADI-RETAINED-DISCOVERY-OBSERVER-MERGED / RUNTIME-PRESENCE-RENDEZVOUS-SUBJECT-PROPAGATION-MERGED / CURRENT-IPHONE-RECEIPT-READ-SURFACE-MERGED / CURRENT-RUNTIME-DISCOVERY-EVIDENCE-PENDING / AUTHENTIC-RESIDENT-EXECUTION-PENDING`

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

Missing current discovery/runtime evidence is `EVIDENCE_REACHABILITY`, not evidence that another physical device is required.

## Retained discovery observer — merged

`.github` PR #1555 merged as `6374478f9f48d4923c61d53c5e3659fc61aca464` after exact head `f6b706061b058fb31724b768b5518309b0da75ac` passed Heartbeat run 3307, organization-control run 3025, and deterministic-suite run 556.

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

There is no hosted fallback and no new listener/page/protocol. The Site KV wrapper is not used. GADI readiness requires current retained discovery and exact node equality with the stronger current runtime-binding subject before WorkerCoordinator may be visited.

Source/CI validation is not current discovery evidence.

## Current-iPhone discovery receipt read surface — merged

StegOS PR #350 merged as:

```text
40ecd6417a953975d2382722880f3dbcc11fa96e
```

Its exact pre-merge head `fca07189a53dcf98d960921ade2260fefd86f41c` passed StegOS CI, GADI authorized-adversarial validation, GADI capability-discovery validation, GADI native defensive-control-plane validation, GADI native boundary-defense validation, GADI handoff-reconciliation validation, iOS Device Package Validation, and iOS Apple Toolchain Validation. The Apple run compiled StegOS Mobile and the embedded extensions successfully without signing.

The existing StegOSMobile app already persists current-iPhone retained-discovery observations to:

```text
stegos-stegbrowser-current-iphone-rendezvous-receipts.jsonl
```

Before #350 that app-local receipt had no canonical read path through the selected bounded native listener. #350 closes only that source-level reachability gap by extending the existing `StegBrowserNativeResidentRendezvousListener` on `127.0.0.1:8000` with:

```text
GET /api/resident-rendezvous/v1/evidence/current-iphone-discovery?target_node_ref=SV-NODE-<24 lowercase hex>
```

The route is GET-only. It reads the latest already-persisted receipt and fails closed unless it matches the exact requested/retained node plus the established current-device/non-authority invariants:

```text
schema = stegos.stegbrowser.current-iphone-rendezvous-observation/v1
state = LOCAL_DISCOVERY_OBSERVED
execution_surface = CURRENT_USER_IPHONE
node_origin = STEGBROWSER_RESIDENT
heartbeat_grants_authority = false
intr_admission_observed = false
workercoordinator_claim_observed = false
canonical_request_consumption_observed = false
provider_session_observed = false
publication_observed = false
credential_authority = TV/TVC
github_token_runtime_authority = NONE
authority_effect = NONE_COMPONENT_EVIDENCE_ONLY
```

The fetch wrapper itself is explicitly `NONE_EVIDENCE_READ_ONLY`. No POST/mutation route, second listener, page, runtime, scheduler, WorkerCoordinator, claim/fence plane, InTr authority, credential route, remote device, or second user-operated machine was added.

This merged source path does not prove that the current iPhone is presently running the listener or that an authentic receipt can presently be read. Runtime truth remains pending direct current-device observation.

## Runtime-presence retained-node subject propagation — merged

`.github` PR #1562 merged as:

```text
cc53257c7e57347d2481dd4fd680aed9b8cf2f6d
```

Validated exact head:

```text
a9264f70f94c647932f3c5662468b9f6e972294b
Validate organization control plane run 3032 — SUCCESS
Deterministic Repository Suite run 563 — SUCCESS
Heartbeat Worker Project run 3315 — SUCCESS
```

The repair closes a shared subject-propagation defect rather than adding GADI authority.

The selected native service already records the retained resident identity in activation evidence as:

```text
resident_rendezvous_node_ref = SV-NODE-<24 lowercase hex>
```

`repair_resident_worker_presence.py` preserves prior activation fields into self-heal supervision evidence. Before #1562, `heartbeat_runtime/runtime_presence_projection.py` projected `resident.node_id` only from `node_id` or `sovereign_node`, so a healthy selected retained StegBrowser/StegOS runtime could still produce `resident.node_id = null`.

After #1562 the shared projector resolves identity in this order:

```text
1. existing nonempty node_id
2. existing nonempty sovereign_node
3. resident_rendezvous_node_ref only when ^SV-NODE-[0-9a-f]{24}$
```

It also records `resident.node_identity_source`. Malformed rendezvous refs remain unusable. Runtime-alive recognition, fresh WorkerCoordinator-cycle requirements, canonical carrier/worker supervision, HB non-authority, TV/TVC credential authority, and GitHub-token non-authority are unchanged.

This is observation-only subject propagation; a rendezvous node reference does not prove runtime liveness and grants no runtime binding, claim/fence, admission, credential, transition, or execution authority.

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
-> read-only current-iPhone persisted discovery receipt for same node
-> exact same-node current runtime presence/supervision
-> materialize_gadi_runtime_binding.py
-> CURRENT_RUNTIME_SUBJECT_BOUND
```

Discovery, receipt presence, or node identity alone never satisfies runtime binding.

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

The authorized connected-device surface was empty during the latest inspection. This is a reachability observation only and does not imply an external/second device is required.

## Immediate continuation

1. On the actual current-device sovereign runtime, let #1555 observe the existing localhost retained-node discovery; do not create another listener/page/protocol or use the KV wrapper.
2. Through merged StegOS #350, read the already-persisted current-iPhone discovery receipt for that exact retained `SV-NODE-*`; treat `NO_EVIDENCE` or listener unreachability as an observation requiring continuation, not authority to synthesize evidence.
3. Require canonical runtime-presence/self-heal evidence to project that same retained node via merged #1562 while also satisfying current liveness/supervision/freshness predicates.
4. Run the existing GADI runtime-binding projector only after the current discovery, receipt readback, and runtime-presence observations agree on the exact node.
5. Continue through the already-merged external-evidence, Governance/InTr, command, controlled-output, readiness, WorkerCoordinator, resident-consumption, reassessment/termination, Continuity, and Master Records chain.

## Collision boundary

No second heartbeat, resident service, runtime scheduler, listener, activation page, WorkerCoordinator, claim/fence plane, InTr authority, Governance evaluator, credential route, evidence-provider authority, actuator implementation, or Master Records custody path may be created.

## Manual work

None at this stage. Do not ask the user to activate a HIL/KV page for GADI. A user action should be requested only if the existing native retained-resident discovery cannot be observed through an already-valid current-device surface and Task Registry confirms a collision-safe action surface.
