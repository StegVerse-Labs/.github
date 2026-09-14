# MIR SDK return carrier routing mirror handoff

Updated: 2026-09-14
Goal Task ID: `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`
COSV ID: `50000000100000`
Canonical issue: `StegVerse-Labs/.github#1891`
Carrier repair issue: `StegVerse-Labs/.github#1900`
Status: `ACTIVE / SOURCE REPAIR IMPLEMENTED / VALIDATION PENDING / RUNTIME PREDICATES UNCHANGED`

## State-transition rule

Every step in this round trip is a state transition. Observation, exact-byte retention/materialization, owner routing, egress framing, Interlock/InTr admission and transport, far-side arrival, return transport, durable return recording, and final transport-exit acceptance are separate transitions. Evidence for one transition must not promote another.

## Observed defect

The existing resident Publisher consumer `scripts/consume_publisher_intr_materialization_request.py` produced the canonical reverse `stegverse.publisher.artifact-return/v1` packet but hard-coded the reverse materialization `downstream_owner_ref` to `StegVerse-Labs/continuity-vault-kit`.

That owner is correct for ordinary KV document return. For a verified MIR-bound Publisher return carrying `stegverse.publisher.mir-roundtrip-binding/v1`, the next existing owner is `StegVerse-org/StegVerse-SDK`, which owns the merged exact SDK return assembly/materialization seam.

## Implemented bounded repair

The existing Publisher reverse InTr carrier is retained. After `verify_artifact_return(return_bytes)` succeeds, `select_return_owner()` now resolves the next owner from the verified return state:

- verified MIR-bound return -> `StegVerse-org/StegVerse-SDK`;
- non-MIR ordinary return -> `StegVerse-Labs/continuity-vault-kit`.

The selector fails closed if a MIR-bound return has the wrong profile, lacks `publisher_transition_observed=true`, expands authority, or has already promoted any post-Publisher predicate. The existing `build_materialization_request()` and carrier-binding path is reused unchanged except for receiving the verified selected owner.

The consumption receipt now records `return_downstream_owner_ref` and explicitly retains false downstream predicates:

- `sdk_return_binding_observed=false`;
- `final_stegverse_side_egress_transition_observed=false`;
- `interlock_intr_egress_observed=false`;
- `far_side_transition_observed=false`;
- `authentic_external_mir_endpoint_substitution_observed=false`;
- `communication_complete=false`.

Routing remains non-authorizing; TV/TVC credential authority and GitHub runtime authority `NONE` are unchanged.

## Tests added

`tests/test_publisher_intr_materialization.py` now covers:

- ordinary Publisher returns remain routed to the KV owner;
- verified MIR-bound returns route to the SDK owner;
- MIR owner selection preserves all downstream predicates false;
- downstream-predicate promotion fails closed;
- authority expansion fails closed;
- missing observed Publisher transition fails closed;
- reverse materialization source uses `return_owner` and records the chosen owner without promoting completion.

## Current truth

The source delivery defect is implemented on branch `mir-sdk-return-carrier-routing-001`. Exact-head validation is still required before merge.

`authentic_predecessor_sdk_return_input_observed=false` remains correct. No authentic runtime packet was created or inferred by this source repair.

No claim is made for SDK return materialization, final StegVerse-side egress, Interlock/InTr egress, far-side transition, authentic MIR endpoint substitution, successful transport round-trip identification, or communication completion.

## Next transition

Validate the exact branch head through existing repository checks. Merge only if the applicable checks pass. Then inspect the authorized resident carrier for an authentic same-execution MIR Publisher return delivered to the SDK owner; if present, bind the exact original manifest, manifest receipt ID, Publisher return bytes, and SDK completion capsule into the already-merged SDK materialization surface. Do not synthesize runtime evidence or provenance.
