# DEVICE_KV_INTR Sovereign Observation Mirror Handoff

Updated: 2026-08-30

```text
goal_id: SHWP-DEVICE-KV-INTR-OBSERVATION-001
repository: StegVerse-Labs/.github
issue: #479
source_pr: #499
source_merge: f5691026575578d70f137b6fc660a051f97097ff
branch: main
parent_goal: SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
runtime_owner: existing sovereign WorkerCoordinator / resident runtime only
state: SOURCE_MERGED_VALIDATED_RUNTIME_PENDING
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_grants_execution_authority: false
physical_additional_machine_required: false
third_party_runtime_required: false
runtime_activation: false
authority_effect: NONE_SOURCE_ONLY
```

## Goal

Observe one authentic, non-sensitive `DEVICE_KV_INTR` traversal on the already-admitted sovereign Node-KV runtime after the existing relay Node-KV continuity task completes.

This is the runtime producer missing between the already-merged consumers:

```text
continuity-vault-kit generic KV-INTERLOCK-v1 DEVICE<->KV envelope + endpoint core
StegOS canonical InTr receipt/delivery admission
Site admitted KV-readiness browser apply
KnowledgeVault typed transport fact DEVICE_KV_INTR
```

The lane must not invent a second endpoint authority, scheduler, runtime owner, transport broker, credential path, or Node identity.

## Current lifecycle standing

The complete source/control implementation was merged through PR #499 at `f5691026575578d70f137b6fc660a051f97097ff` after both exact-head repository validation workflows passed. The superseded stale PR #485 was closed without merge.

This advances only the source lifecycle:

```text
IMPLEMENTED=true
VALIDATED=true
MERGED=true
DEPLOYED=false
ACTIVATED=false
OBSERVED=false
RECONSTRUCTED=false
RELEASED=false
COMPLETE=false
```

CI and merge evidence do not satisfy the runtime observation predicate.

## Parent prerequisite

Authentic parent evidence is mandatory:

```text
receipts/stegos-sovereign-relay/SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001.json
state=COMPLETED
transition_id=RELAY_NODE_KV_CONTINUITY_VERIFIED
```

The parent must prove real teardown/recreation and preserved Node-KV state-root continuity. Hosted fixtures, CI, or source claims cannot substitute. As of this reconciliation, the canonical parent receipt is not present in repository evidence and the parent handoff remains `PENDING_PARENT_AND_MACHINE_EXECUTION`.

## Runtime design

The observation uses one bounded deployment-local TCP transport on loopback inside the existing sovereign runtime. Loopback is the carrier only; the StegVerse capability type is `DEVICE_KV_INTR`.

```text
existing sovereign Node-KV runtime
-> fresh WorkerCoordinator claim/fence for this task
-> resolve already-local StegOS and continuity-vault-kit source
-> derive bounded Node/KV boundary identities from authentic parent continuity evidence
-> construct deterministic non-sensitive KV-INTERLOCK DISCOVER request
-> create exact sealed DEVICE->KV envelope
-> start bounded KV boundary receiver on 127.0.0.1:ephemeral-port
-> send exact framed request bytes through the kernel TCP stack
-> receiver independently hashes/parses/validates exact bytes
-> receiver issues canonical DEVICE->KV stegverse.intr.hop_receipt/v1
-> receiver invokes merged continuity-vault-kit KVInterlockRuntime using that receipt reference
-> receipt_store return is captured directly as the endpoint receipt reference
-> receiver constructs canonical KV->DEVICE response transport intent/receipt
-> send exact response bytes back through TCP
-> client independently rehashes/revalidates response and receipt chain
-> durable observation receipt + reconstruction projection
```

The test harness may initiate the bounded event, but it may not manufacture `VERIFIED` boundary state without the authenticated parent Node-KV continuity identity. The actual boundary receiver issues the transport receipts only after receiving and validating the bytes over the socket.

## Controlled payload

The observation payload contains no personal records, PII, PHI, credentials, provider data, or canonical-state mutation.

Canonical operation:

```text
schema_version=kv.interlock.request.v1
operation=DISCOVER
record_class=transport-capability-observation
requested_scope=[capability_status]
disclosure_mode=SOURCE_REFERENCE_ONLY
purpose=DEVICE_KV_INTR sovereign transport observation
authority_ref=CONTROLLED_NON_SENSITIVE_OBSERVATION_ONLY
```

The injected authority validator is bounded to this exact deterministic observation request and exact verified DEVICE->KV envelope. The policy evaluator may return only non-sensitive capability-status context and source references. No owner/private-record authority is inferred.

## Receipt invariants

Required authentic evidence:

```text
capability_type=DEVICE_KV_INTR
carrier=LOOPBACK_TCP
parent_node_kv_continuity=VERIFIED
DEVICE->KV exact request bytes transported=true
DEVICE->KV boundary_verification=VERIFIED
DEVICE->KV transition_state=RECEIVED
KV endpoint response produced=true
KV->DEVICE exact response bytes transported=true
KV->DEVICE boundary_verification=VERIFIED
KV->DEVICE transition_state=RECEIVED
payload/response digests independently match
canonical receipt hashes validate
receipt prior-hash lineage validates
secret_plaintext_present=false
authority_transfer=false
credential_authority=TV/TVC
provider_operation_authorized=false
canonical_kv_mutation=false
runtime_activation_claimed=false
authority_effect=NONE
```

## Lifecycle/non-claims

```text
source implementation != runtime observation
CI validation != runtime observation
merge != deployment
parent Node-KV continuity != DEVICE_KV_INTR observation
loopback carrier != public HTTPS ingress
DEVICE_KV_INTR observation != production Interlock global activation
DEVICE_KV_INTR observation != credential/provider authority
DEVICE_KV_INTR observation != HIL observation
DEVICE_KV_INTR observation != G18 completion
```

This task is independent task-control work sharing the existing sovereign runtime substrate. It does not require HIL or G18 completion and does not consume their claims/fences.

## Expected durable evidence

```text
receipts/device-kv-intr/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json
schema=stegverse.device-kv-intr.canonical-observation-evidence/v1
state=OBSERVED
```

Only that authentic terminal observation may later be admitted by KnowledgeVault to advance `transport_capabilities_observed.DEVICE_KV_INTR=true`.

## Source surfaces

```text
docs/DEVICE_KV_INTR_SOVEREIGN_OBSERVATION_MIRROR_HANDOFF.md
handoffs/SHWP-DEVICE-KV-INTR-OBSERVATION-001.json
workers/device_kv_intr_observation_worker.py
control/worker-registry.d/device-kv-intr-observation-001.json
control/process-worker-adapters.d/device-kv-intr-observation-001.json
cost-basis/worker-runtime/device-kv-intr-observation.json
control/admissible-existence-retrospective-conformance.d/device-kv-intr-observation-001.json
tests/test_device_kv_intr_observation_worker.py
```

## Next executable action

Do not create another runtime owner or naïve one-shot resident consumer. First satisfy the already-admitted parent chain on the deployment-local sovereign runtime:

```text
SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
-> authentic SOVEREIGN_RELAY_LEASE_OPEN
-> SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
-> authentic RELAY_NODE_KV_CONTINUITY_VERIFIED
-> SHWP-DEVICE-KV-INTR-OBSERVATION-001
-> authentic DEVICE_KV_INTR_OBSERVED
```

When the parent continuity receipt exists, the existing WorkerCoordinator independently admits this HANDOFF_READY task under a fresh fence greater than 21 and invokes `process:device-kv-intr-observation-v1` on the deployment-local sovereign carrier.

## 2026-08-31 Universal InTr event-first reconciliation

Issue #575 reconciles this bounded observation lane with the newer canonical
Universal InTr availability rule:

```text
event_triggered=true
always_on_receiver_required=false
receiver_unavailable_disposition=DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION
```

The historical relay -> Node-KV continuity chain remains a valid stronger
reconstruction/continuity proof, but it is no longer a universal prerequisite
for creation or admission of a DEVICE_KV transport event.

The existing task remains the sole DEVICE_KV observation owner. It may now be
independently admitted when either authentic RELAY_NODE_KV_CONTINUITY_VERIFIED
evidence exists or shared profiled Universal InTr ingress has independently
validated and persisted a canonical device-kv materialization request and
ingress receipt.

Event ingress is non-authorizing. It cannot mint a WorkerCoordinator claim/fence,
credential, route authority, KV write authority, or activation fact. The
materialization consumer merely invokes the existing targeted executor. The
original exact packet remains eligible for exact-packet retry; blind retry of
downstream consequences remains prohibited.

Source/merge/CI do not establish DEVICE_KV_INTR_OBSERVED.


## HB-derived carrier execution — issue #623

The bounded sovereign DEVICE_KV runtime now uses the canonical HB-derived carrier
as the actual request and response wire representation instead of attaching carrier
evidence after raw TCP transport.

Execution order:

```text
governed DEVICE_KV request + InTr envelope
  -> canonical exact request bytes
  -> precommit deterministic DEVICE->KV hop receipt
  -> canonical HB 100 Hz reference
  -> stegverse.heartbeat-intr-derived-carrier/v1
  -> TCP frame carries the carrier object
  -> KV receiver recovers exact request bytes from carrier
  -> exact-byte identity + zero-authority carrier checks
  -> persist exact precommitted InTr receipt
  -> KV Interlock evaluation

KV response
  -> precommit deterministic KV->DEVICE return receipt
  -> canonical HB-derived carrier
  -> TCP frame carries the carrier object
  -> Device recovers exact response bytes
  -> exact-byte / receipt / lineage reconstruction
```

This is stronger than post-hoc carrier association: the transport frame itself is the
canonical derived-carrier object and the application/InTr bytes are recovered from it
before endpoint processing.

The resulting runtime receipt may set
`hb_derived_carrier_transport_observed=true` only when that authentic execution
completes under the existing WorkerCoordinator claim/fence. Source, tests, merge, or
fixture execution do not satisfy that predicate. HB and the derived carrier grant no
admission, execution, credential, routing, transition, or receiving authority.


## Resident chain reissue for HB-carrier terminal proof — issue #636

The existing machine-owned StegOS/KV resident chain remains the canonical execution
path:

```text
SHWP-STEGOS-SOVEREIGN-RELAY-MATERIALIZATION-001
  -> SHWP-STEGOS-RELAY-NODE-KV-CONTINUITY-001
  -> SHWP-DEVICE-KV-INTR-OBSERVATION-001
```

The request was reissued as
`RESIDENT-EXEC-STEGOS-KV-INTR-CHAIN-002` after the canonical HB-carrier wire,
resident carrier-materialization, and `STEGVERSE_KV_ROOT` fixes.

A DEVICE_KV receipt is terminal for this chain only when it additionally proves:

```text
hb_derived_carrier_transport_observed=true
request_transported_on_hb_derived_carrier=true
response_transported_on_hb_derived_carrier=true
request_carrier_packet_recovery_verified=true
response_carrier_packet_recovery_verified=true
```

This prevents a historical pre-carrier `DEVICE_KV_INTR_OBSERVED` receipt from
satisfying the stronger current objective. The generic dispatcher and portable
refresh+dispatch bridge now preserve the existing non-secret `STEGVERSE_KV_ROOT`
binding so the resident does not lose its private KV destination between layers.

The reissued request remains intent-only. It grants no claim, fence, credential,
routing, receiving, transition, or execution authority.
