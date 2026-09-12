# GADI Resident Execution Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / SOURCE-CHAIN-MERGED / RETAINED-STEGBROWSER-STEGOS-SUBSTRATE-SELECTED / PROVIDER-VERIFICATION-BINDING-MATERIALIZER-MERGED / GADI-RETAINED-DISCOVERY-OBSERVER-MERGED / RUNTIME-PRESENCE-RENDEZVOUS-SUBJECT-PROPAGATION-IN-VALIDATION / CURRENT-RUNTIME-DISCOVERY-EVIDENCE-PENDING / AUTHENTIC-RESIDENT-EXECUTION-PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and not superseded. Authentic current resident execution remains unobserved.

The canonical single-device substrate remains:

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

`.github` PR #1555 merged at:

```text
6374478f9f48d4923c61d53c5e3659fc61aca464
```

Validated exact head:

```text
f6b706061b058fb31724b768b5518309b0da75ac
Heartbeat Worker Project run 3307 — SUCCESS
Validate organization control plane run 3025 — SUCCESS
Deterministic Repository Suite run 556 — SUCCESS
```

PR #1555 adds `scripts/observe_gadi_retained_resident_discovery.py`, which observes only the existing task-agnostic localhost contract:

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

There is no hosted fallback and no new listener/page/protocol. The Site KV wrapper is not used. The observer writes only `state/gadi-resident-execution/retained-resident-discovery.json` and grants no runtime binding, admission, claim/fence, credential, transition, or execution authority.

`run_gadi_targeted_runtime_if_ready.py` now requires current retained discovery before WorkerCoordinator can be visited and fails closed if the discovered `target_node_ref` differs from the stronger current runtime-binding `node_id`.

Source/CI validation of #1555 is not current discovery evidence.

## Runtime-presence retained-node subject propagation — in validation

Post-#1555 audit found a concrete shared convergence defect.

The selected native service path already writes the retained resident identity into `receipts/sovereign-host/activation.latest.json` as:

```text
resident_rendezvous_node_ref = SV-NODE-<24 lowercase hex>
```

`repair_resident_worker_presence.py` preserves prior activation fields into its self-heal supervision receipt. However, the canonical shared projector `heartbeat_runtime/runtime_presence_projection.py` previously projected `resident.node_id` only from:

```text
node_id
sovereign_node
```

Therefore a healthy selected retained StegBrowser/StegOS native runtime could know the exact retained node while canonical runtime presence still emitted `resident.node_id = null`, making GADI discovery/runtime-subject convergence impossible.

Branch `runtime-presence-rendezvous-node-subject-001` repairs the shared projector, not GADI policy:

- existing nonempty `node_id` remains first priority;
- existing nonempty `sovereign_node` remains second priority;
- `resident_rendezvous_node_ref` is accepted only when it matches `^SV-NODE-[0-9a-f]{24}$`;
- output now records `resident.node_identity_source`;
- malformed rendezvous refs remain unusable;
- runtime-alive, worker freshness, canonical supervision, HB non-authority, credential authority, and all other existing gates are unchanged.

This is observation-only subject propagation. It does not make the rendezvous field a liveness signal and grants no authority.

Regression coverage in `tests/test_runtime_presence_projection.py` requires:

1. canonical native-service rendezvous identity projects into `resident.node_id`;
2. self-heal preserved rendezvous identity projects identically;
3. malformed rendezvous identity does not become a runtime subject;
4. existing historical `node_id` precedence remains compatible;
5. existing liveness/freshness tests remain unchanged.

The shared `HB_RUNTIME_PRESENCE_RESIDENT_OBSERVABILITY_CONTRACT` already defines generic concrete resident presence and does not enumerate identity-source fields, so no authority-contract expansion is required.

## Provider-verification source boundary — merged

Representative verified-evidence lineage remains:

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
```

## Canonical execution sequence

```text
CURRENT RETAINED STEGBROWSER/STEGOS NATIVE DISCOVERY
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

## Immediate continuation

1. Validate and merge the shared runtime-presence retained-node subject repair only on an unchanged exact head with organization-control, deterministic-suite, and Heartbeat success.
2. On the actual sovereign runtime, let the existing #1555 observer obtain current localhost retained discovery; do not create another listener/page/protocol.
3. Require canonical runtime-presence/self-heal evidence to project the exact same retained `SV-NODE-*` identity.
4. Run the existing GADI runtime-binding projector only after current liveness/supervision/freshness evidence exists for that subject.
5. Continue through the already-merged external-evidence, Governance/InTr, command, controlled-output, readiness, WorkerCoordinator, resident-consumption, reassessment/termination, Continuity, and Master Records chain.

## Collision boundary

No second heartbeat, resident service, runtime scheduler, listener, activation page, WorkerCoordinator, claim/fence plane, InTr authority, Governance evaluator, credential route, evidence-provider authority, actuator implementation, or Master Records custody path may be created.

## Manual work

None at this stage. Do not ask the user to activate a HIL/KV page for GADI. A user action should be requested only if the existing native retained-resident discovery cannot be observed through an already-valid current-device surface and Task Registry confirms a collision-safe action surface.
