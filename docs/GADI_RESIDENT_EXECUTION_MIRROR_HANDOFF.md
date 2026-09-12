# GADI Resident Execution Mirror Handoff

Updated: 2026-09-11
Repository: `StegVerse-Labs/.github`
Goal ID: `GADI-001`
Task ID: `GADI-RESIDENT-EXECUTION-001`
Parent task: `GADI-001`
COSV ID: `10100000100000`
Canonical issue: `StegVerse-Labs/.github#1239`
Status: `ACTIVE / SOURCE-CHAIN-MERGED / RETAINED-STEGBROWSER-STEGOS-SUBSTRATE-SELECTED / PROVIDER-VERIFICATION-BINDING-MATERIALIZER-MERGED / NATIVE-DISCOVERY-CONTRACT-REUSED / CURRENT-RUNTIME-DISCOVERY-EVIDENCE-PENDING / AUTHENTIC-RESIDENT-EXECUTION-PENDING`

## Current canonical state

`GADI-001` remains ACTIVE and not superseded. Authentic current resident execution remains unobserved.

Task Registry substrate sorting is now explicit for `GADI-RESIDENT-EXECUTION-001`:

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

A missing Remote Computer connection, missing browser receipt, or temporarily unreachable listener is an `EVIDENCE_REACHABILITY` condition. It is not evidence that another physical device is required.

## Retained resident discovery contract

The retained resident node originates in StegBrowser and is loaded/materialized by StegOSMobile before any Site/Safari projection or bounded ephemeral browser lease.

Canonical source lineage includes:

```text
StegVerse-Labs/StegBrowser/ios/StegBrowserResidentNodeStore.swift
StegVerse-Labs/StegBrowser/src/stegbrowser/resident_rendezvous.py
StegVerse-Labs/StegOS/mobile/ios/StegOSMobile/StegBrowserResidentNodeBootstrap.swift
StegVerse-Labs/StegOS/mobile/ios/StegOSMobile/MobileRuntimeState.swift
```

The native retained-resident discovery contract is task-agnostic:

```text
GET /api/resident-rendezvous/v1/discovery
schema = stegverse.resident-rendezvous.discovery/v1
state = AVAILABLE
target_node_ref = SV-NODE-<24 lowercase hex>
gateway_execution_authority = NONE
credential_authority = TV/TVC
discovery_grants_authority = false
authority_effect = NONE_DISCOVERY_ONLY
```

Both the StegBrowser transport-neutral core and the compiled StegOSMobile loopback listener implement this same discovery shape. It contains no GADI/KV task identity and grants no execution, claim/fence, credential, admission, or transition authority.

The Site `assets/kv-ui/resident-rendezvous-client.js` wrapper is different: its validator intentionally binds the generic discovery response to the KV request `RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-003`. That KV wrapper is not a GADI request/submission surface and must not be reused as GADI execution evidence. GADI may reuse the underlying native task-agnostic discovery observation only.

A discovery response proves only retained-node availability and identity. It does not by itself establish the stronger GADI runtime binding.

## GADI runtime-binding boundary

`scripts/materialize_gadi_runtime_binding.py` remains the authoritative non-authorizing GADI runtime-binding projector. It requires current resident runtime-presence evidence plus its supervision receipt, including:

```text
runtime_root subject match
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

Therefore the correct sequence is:

```text
native retained-node discovery
-> current resident presence/supervision observation for that subject
-> materialize_gadi_runtime_binding.py
-> CURRENT_RUNTIME_SUBJECT_BOUND
```

Do not promote discovery alone into `CURRENT_RUNTIME_SUBJECT_BOUND`.

## Provider-verification source boundary — merged

StegOS PR #346 merged at:

```text
4b29ea35ee27d9327da87231ca516475dcee6cd8
```

Validated exact head:

```text
f76a99be9dcfabc5abe1af24896dd5be4c204c12
StegOS CI 34668002777 — SUCCESS
```

PR #346 adds the evidence-only `stegos/provider_evidence_verification.py` materializer. It emits the existing StegCore #207 schema only when four independently supplied verification inputs agree with the exact external-evidence envelope:

1. accepted signature verification from the existing verifier framework;
2. independent provider authorization + authorized scope;
3. independent evidence-chain verification;
4. independent freshness verification.

The materializer does not authorize providers, perform cryptographic verification by itself, create chain truth, decide freshness, mint credentials, perform InTr/Governance admission, or grant execution authority. The envelope cannot self-assert any of those predicates.

Source gap status:

```text
StegCore #207 verified-binding consumer: MERGED
StegOS #345 Ed25519 verifier: MERGED
StegOS #346 independent binding materializer: MERGED
current authentic provider/signature/chain/freshness inputs: NOT OBSERVED
current GADI verified-external-evidence binding: NOT OBSERVED
```

The remaining provider-verification condition is therefore runtime evidence, not missing materializer source.

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
StegCore #206 external evidence -> governance facts
StegCore #207 independently verified external-evidence requirement
StegOS #345 trusted-key Ed25519 verifier
StegOS #346 independent provider-evidence verification binding materializer
.github #1539 Task Registry single-device-first substrate sorting
.github #1541 GADI retained StegBrowser/StegOS substrate reconciliation
```

## Canonical execution sequence

```text
CURRENT RETAINED STEGBROWSER/STEGOS NATIVE DISCOVERY
-> CURRENT RESIDENT-PRESENCE + SUPERVISION SUBJECT OBSERVATION
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

WorkerCoordinator remains sole claim/fence authority. Interlock/InTr remains transition/admission authority. TV/TVC remains credential authority. HB remains observation only. GitHub validation remains non-authorizing.

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

A repository/tooling DNS failure while probing the public endpoint is not resident evidence and is not a runtime failure. It must not be converted into a device requirement.

## Immediate continuation

1. Observe the existing StegBrowser/StegOS native retained-node discovery contract; do not create a new page/listener/protocol.
2. Do not use the Site KV request wrapper as a GADI submission surface.
3. If native discovery is observed, correlate its exact `SV-NODE-*` subject with current resident presence/supervision evidence.
4. Run the existing GADI runtime-binding projector only after that stronger current presence evidence exists.
5. Obtain current threat/boundary observations and the GADI-scoped external-evidence envelope after subject binding.
6. Use StegOS #345 + #346 only with independently sourced signature/provider/chain/freshness evidence; do not infer any predicate from the envelope itself.
7. Continue through existing StegCore facts -> PENDING request -> InTr/Governance admission -> StegOS native command.
8. Observe only the controlled pre-authorized software test-surface effect.
9. Let non-claim readiness complete before a fresh WorkerCoordinator claim/fence.
10. Require exact materialization/preflight, newly changed resident-consumption evidence, reassessment/termination, Continuity custody, Master Records reconciliation, and exact reconstruction.

## Collision boundary

No second heartbeat, resident service, runtime scheduler, listener, activation page, WorkerCoordinator, claim/fence plane, InTr authority, Governance evaluator, credential route, evidence-provider authority, actuator implementation, or Master Records custody path may be created.

## Manual work

None at this stage. Do not ask the user to activate a HIL/KV page for GADI. A user action should be requested only if the existing native retained-resident discovery cannot be observed through an already-valid GADI/current-device surface and Task Registry confirms a collision-safe action surface.
