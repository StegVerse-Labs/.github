# SV-DN-1 Route-Specific InTr Runtime Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-ROUTE-SPECIFIC-INTR-RUNTIME-001
task_id: SV-DN1-INTR-RUNTIME-001
repository: StegVerse-Labs/.github
branch: feature/sv-dn1-intr-runtime
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

## Current state

```text
source-materialization predecessor: MERGED / runtime receipt NOT OBSERVED
resident observer source: MERGED / runtime receipt NOT OBSERVED
route-specific InTr schema: MERGED
SDK bridge InTr validator: MERGED
dedicated InTr executable handoff: IMPLEMENTING
dedicated InTr worker: IMPLEMENTING
route-specific runtime receipt: NOT OBSERVED
SDK READY_FOR_SDK_0B: NOT OBSERVED
```

## Archive readiness

This handoff is the canonical continuation source for the first route-specific SV-DN-1 InTr runtime traversal. Once merged, the lane is recoverable without the originating conversation.
