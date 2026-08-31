# SV-DN-1 Universal InTr Adjacent-Hop Runtime Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-ROUTE-SPECIFIC-INTR-RUNTIME-001
task_id: SV-DN1-INTR-RUNTIME-001
repository: StegVerse-Labs/.github
branch: main
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
upstream task: SV-DN1-RESIDENT-OBSERVER-001
downstream surface: StegVerse-org/stegverse-demo-suite/scripts/build_sv_dn1_sdk_ingress_manifest.py
credential_authority: TV/TVC
github_token_runtime_authority: NONE
authority_effect: NONE
```

## Goal

Execute the first authentic route-specific SV-DN-1 InTr traversal on the admitted sovereign carrier after the resident observer has emitted a real source-capture and HF-facing semantic exchange.

This lane binds the already-observed semantic exchange through an explicit transit boundary and revalidates it at the StegVerse-facing destination before emitting the route-specific runtime receipt required by the canonical SDK 0B bridge.

It MUST NOT:

- fetch Hugging Face independently;
- duplicate the resident observer;
- claim Universal Interlock canonical adoption;
- claim global/production Universal Interlock runtime activation;
- claim SDK admission;
- perform StegCore/StegGate governance;
- perform Master Records custody;
- write repositories;
- use provider/GitHub credentials.

## Source of truth order

1. `docs/SV_DN1_INTR_RUNTIME_MIRROR_HANDOFF.md`
2. `handoffs/SV-DN1-INTR-RUNTIME-001.json`
3. `control/worker-registry.d/sv-dn1-intr-runtime-001.json`
4. `control/process-worker-adapters.d/sv-dn1-intr-runtime-001.json`
5. `workers/sv_dn1_intr_runtime_worker.py`
6. `StegVerse-org/stegverse-demo-suite/schemas/sv-dn1-intr-runtime-receipt.schema.json`
7. `StegVerse-org/stegverse-demo-suite/scripts/build_sv_dn1_sdk_ingress_manifest.py`
8. `StegVerse-Labs/StegOS/docs/UNIVERSAL_INTERLOCK_PROTOCOL_MIRROR_HANDOFF.md`

Newer authentic runtime evidence overrides older chat/session claims.

## Upstream completion requirement

The worker may execute only after the canonical resident observer has completed:

```text
state: COMPLETE
transition_id: SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE
runtime_source_pin_verified: true
raw_response_sha256_present: true
semantic_exchange_valid: true
credential_used: false
github_token_used: false
repository_writeback_performed: false
sdk_admitted: false
```

Required local evidence:

```text
~/.stegverse/state/sv-dn1-resident-observer/receipts/latest.json
~/.stegverse/state/sv-dn1-resident-observer/observed/source-capture.json
~/.stegverse/state/sv-dn1-resident-observer/observed/exchange.json
~/.stegverse/source/stegverse-demo-suite/
```

The exchange id, source-capture identity, raw digest, transformation hash and resident claim must remain continuous.

## Transit model

For this first route-specific traversal, InTr is the bounded production transit between the HF-facing semantic boundary and the StegVerse-facing admission boundary on the admitted sovereign carrier.

Transport profile:

`stegverse.sv-dn1.intr.sovereign-bound-state/v1`

The route is:

```text
resident HF semantic exchange
-> immutable read from resident bound state
-> fenced InTr route worker
-> exact exchange copy into InTr bound state
-> canonical StegVerse-side exchange validation
-> route-specific InTr receipt
```

This is real execution of the SV-DN-1 route on sovereign bound state; it is not fixture replay. It does not imply a network hop or a globally activated Universal Interlock.

## Universal Interlock boundary

Current canonical StegOS state remains:

```text
protocol_id: SV-INTERLOCK-v0.4-candidate
canonical_protocol_adopted: false
runtime_activation: false
production_interlock_runtime_activated: false
```

Accordingly the route receipt MUST preserve:

```text
claims.canonical_protocol_adopted=false
claims.production_interlock_runtime_activated=false
```

SV-DN-1 route execution is bounded and reference-compatible. It is not evidence that the Universal Interlock protocol has been canonically adopted or globally activated.

## Destination validation

The worker must load the exact materialized demo-suite destination validator:

`scripts/sv_dn1_stegverse_interlock.py`

and require:

`validate_exchange(exchange) == []`

The following identities are also checked explicitly:

- resident receipt semantic_exchange_id == exchange.exchange_id;
- source capture raw_sha256 == resident receipt raw_response_sha256;
- exchange raw preserved-native-fields == source capture parsed_json;
- far-side authority effect == NONE;
- InTr exchange placeholder authority effect == NONE;
- source transformation hash == far-side transformation receipt hash;
- previous receipt hash == exchange InTr previous receipt hash.

## Runtime receipt

The worker emits exactly the schema consumed by the demo-suite SDK bridge:

`stegverse.sv-dn1.intr-runtime-receipt/v1`

Required runtime receipt posture:

```text
route_id: SV-DN-1-HF-PUBLIC
state: COMPLETE
transport_profile: stegverse.sv-dn1.intr.sovereign-bound-state/v1
destination_validation: PASS
lineage_verified: true
authority_effect: NONE
```

The deterministic `receipt_hash` is SHA-256 over canonical JSON of the receipt body excluding `receipt_hash`.

## Bound-state outputs

Only this worker's bounded state may be written:

```text
~/.stegverse/state/sv-dn1-intr-runtime/
  observed/exchange.json
  receipts/latest.json
```

The resident observer state is read-only.

## Completion boundary

Completion transition:

`SV_DN1_ROUTE_SPECIFIC_INTR_COMPLETE`

Completion means:

```text
resident authentic observation: VERIFIED
exchange identity continuity: VERIFIED
source transformation continuity: VERIFIED
StegVerse destination validation: PASS
route-specific InTr receipt: COMPLETE
lineage_verified: true
credential_used: false
sdk_admitted: false
canonical_protocol_adopted: false
production_interlock_runtime_activated: false
```

## Successor

After completion, the canonical demo-suite SDK bridge can consume:

```text
resident receipt
+ source capture
+ semantic exchange
+ route-specific InTr receipt
-> READY_FOR_SDK_0B
```

The next machine lane is canonical sovereign SDK 0B governed execution. This InTr worker does not manufacture that result.

## Collision boundary

There must be exactly one route-specific InTr runtime owner for the first SV-DN-1 public observation. Do not create a second worker that emits the same `SV-DN-1-HF-PUBLIC` runtime receipt while this task is HANDOFF_READY, CLAIMED, ACTIVE, or completed for the same exchange.

## Independent task-control dependency

PR #343 merged the explicit resident dependency:

```text
dependency: SV-DN1-RESIDENT-OBSERVER-001
parent terminal state: COMPLETED
parent terminal transition: SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE
authority_domain: INDEPENDENT_TASK_CONTROL
fresh fence: >22
heartbeat_grants_execution_authority: false
merge_commit: 75fbb638a8003d42517620cc95b383070ea3b15e
```

PR #348 merged the sovereign first-round chain that targets this task only after the resident task is terminal. Authentic route execution remains NOT OBSERVED.

## Current state

```text
source-materialization predecessor: MERGED / runtime receipt NOT OBSERVED
resident observer source: MERGED / runtime receipt NOT OBSERVED
route-specific InTr schema: MERGED
SDK bridge InTr validator: MERGED
dedicated InTr executable handoff: MERGED
dedicated InTr worker: MERGED
route-specific runtime receipt: NOT OBSERVED
SDK READY_FOR_SDK_0B: NOT OBSERVED
```

## Merge and validation evidence

```text
PR #339: MERGED
merge_commit: ab6172bb1938bdb00ec7af80858547c3dcbd45ed
validated_head: 62ecd89d38728846b9dd0b3a6263f3ff45346039
organization control plane run 33135865030 / job 98735573027: PASS
heartbeat worker validation run 33135865038 / job 98735573069: PASS
complete deterministic repository suite: PASS
executable handoff validation: PASS
AE conformance: PASS
no GitHub token authority: PASS
```

The route-specific InTr worker is registered and source-valid on main. Authentic runtime completion remains pending on the upstream resident observation and a sovereign WorkerCoordinator claim/fence.

## Archive readiness

This handoff is the canonical continuation source for the first route-specific SV-DN-1 InTr runtime traversal. Once merged, the lane is recoverable without the originating conversation.


## Universal InTr reconciliation — 2026-08-29

**This section supersedes every earlier statement in this handoff that says
`canonical_protocol_adopted=false`, that the SV-DN-1 hop is exempt from the
organization-wide transport invariant, or that the transport profile is the
pre-adoption sovereign-bound-state profile.**

PR #407 was merged as `d0de32281c2e29258146e084e93ce4587568d683` and
established `STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001` as the canonical
organization transport policy.

The first SV-DN-1 ingress is therefore represented as the canonical adjacent
boundary hop:

```text
EXTERNAL_SYSTEM
  -> external-side Interlock / exact HF semantic exchange
  -> InTr
  -> STEGOS_ECOSYSTEM receiving Interlock
  -> destination validation
  -> chained hop receipt
```

Required execution contract:

```text
transport_profile: stegverse.universal-intr.adjacent-hop/v1
universal_intr_policy_id: STEGVERSE-UNIVERSAL-INTR-TRANSPORT-001
canonical_protocol_adopted: true
boundary_from: EXTERNAL_SYSTEM
boundary_to: STEGOS_ECOSYSTEM
interlock_required_per_hop: true
receipt_hash_chain_required: true
runtime_activation_claimed: false
production_interlock_runtime_activated: false
sdk_admitted: false
authority_effect: NONE
```

`canonical_protocol_adopted=true` reports the already-established
organization policy fact. It does **not** grant this worker protocol-adoption
authority. The worker retains
`canonical_protocol_adoption_authority=false` and may not claim global
runtime activation.

The resident exchange's far-side transformation receipt remains the prior
receipt identity. The Universal InTr hop MUST preserve that exact
`previous_receipt_hash`, validate the receiving boundary, and emit a new
deterministic receipt hash. Direct non-adjacent transport, cross-boundary state
mutation, plaintext payload in receipts, or blind retry of downstream
consequences is prohibited.

Current runtime truth remains:

```text
source materialization receipt: NOT OBSERVED
resident Hugging Face capture receipt: NOT OBSERVED
Universal InTr EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM hop receipt: NOT OBSERVED
SDK live admission: NOT OBSERVED
first authentic round analyzed: NOT OBSERVED
```

Source reconciliation branch:
`fix/sv-dn1-universal-intr-reconcile-20260829`.


## 2026-08-31 HB-derived carrier binding

HB/InTr carrier analysis found that the local heartbeat runtime already propagates
derived subsignals and already has deterministic phase-slot planning. The missing generic
InTr binding is now implemented by the HB-derived carrier profile:

```text
docs/HB_INTR_DERIVED_CARRIER_MIRROR_HANDOFF.md
heartbeat_runtime/intr_derived_carrier.py
schema: stegverse.heartbeat-intr-derived-carrier/v1
```

For SV-DN-1, the canonical Universal InTr packet may therefore be carried as exact opaque
bytes on a deterministic signal derived from the canonical HB reference.

Required binding evidence for a future authentic runtime observation:

```text
route_id: SV-DN-1-HF-PUBLIC
transport_profile: stegverse.universal-intr.adjacent-hop/v1
boundary_from: EXTERNAL_SYSTEM
boundary_to: STEGOS_ECOSYSTEM
exact InTr receipt_hash
exact packet_sha256
exact heartbeat_epoch/reference
deterministic channel_slot
deterministic phase_offset_deg
packet bytes recover exactly
heartbeat progression_dependency: OSCILLATOR_ONLY
authority_effect: NONE_CARRIER_ONLY
```

This carrier binding does not replace the existing InTr receipt and does not itself
admit, route, execute, receive, transition, or authorize the packet. InTr remains the
packet-governance layer. HB supplies only the synchronization/carrier coordinates.

Existing authentic Universal InTr traversal evidence remains valid. A new
carrier-binding receipt is a stronger transport-observation predicate and must not be
inferred retroactively from the existing InTr receipt.
## 2026-08-31 shared HB signal publication

Issue #645 binds the already-derived SV-DN-1 route carrier frame into the canonical shared local HB signal surface after exact carrier recovery/validation.

Execution now includes:
```text
route-specific exchange
-> canonical HB/InTr carrier frame
-> exact recovery verification
-> persist exact same carrier frame into shared heartbeat runtime
-> re-seal carrier-binding receipt with shared signal ref + digest
-> preserve route-specific completion
```

New evidence fields:
- carrier-binding receipt: `shared_hb_signal_ref`, `shared_hb_signal_sha256`
- worker completion: `hb_shared_signal_ref`, `hb_shared_signal_sha256`

The persistence operation does not re-sample HB, does not derive a second signal, and grants no authority. Authentic SV-DN-1 runtime observation remains distinct from source/CI/merge.


## 2026-08-31 resident terminal verification — issue #650

Shared publication fields are no longer informational for the current sovereign chain. The chain validates `carrier-binding.latest.json` against the main InTr receipt and then independently validates the exact shared carrier signal named by `shared_hb_signal_ref`.

Required reconciliation includes:
- `intr_receipt_hash == receipts/latest.json.receipt_hash`;
- exact shared signal recovery succeeds;
- canonical shared signal digest equals `shared_hb_signal_sha256`;
- shared signal id equals `carrier_signal_id`;
- shared carrier binding digest equals `carrier_binding_sha256`;
- shared packet SHA-256 equals the carrier receipt packet SHA-256;
- HB progression remains `OSCILLATOR_ONLY`;
- carrier authority remains `NONE_CARRIER_ONLY`.

This is a terminal evidence predicate only and does not grant execution or heartbeat authority.
