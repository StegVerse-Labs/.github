# MIR SDK return carrier routing mirror handoff

Updated: 2026-09-14
Goal Task ID: `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`
COSV ID: `50000000100000`
Canonical issue: `StegVerse-Labs/.github#1891`
Carrier repair issue: `StegVerse-Labs/.github#1900`
Status: `ACTIVE / SOURCE DEFECT IDENTIFIED / RUNTIME PREDICATES UNCHANGED`

## State-transition rule

Every step in this round trip is a state transition. Observation, exact-byte retention/materialization, owner routing, egress framing, Interlock/InTr admission and transport, far-side arrival, return transport, and final record acceptance are all separate transitions. Evidence for one transition must not promote another.

## Observed defect

The existing resident Publisher consumer `scripts/consume_publisher_intr_materialization_request.py` produces the canonical reverse `stegverse.publisher.artifact-return/v1` packet, but its reverse materialization request hard-codes `downstream_owner_ref` to `StegVerse-Labs/continuity-vault-kit`.

For ordinary KV document return this is correct. For a verified MIR-bound Publisher return carrying `stegverse.publisher.mir-roundtrip-binding/v1`, the next existing owner is `StegVerse-org/StegVerse-SDK`, which owns the already-merged exact SDK return assembly/materialization seam.

Therefore the missing authentic predecessor SDK-return artifact is currently explained by an existing-carrier owner-routing transition that cannot reach the SDK owner; source/build validation of the SDK materializer does not repair that delivery transition by itself.

## Required bounded repair

Reuse the existing Publisher reverse InTr carrier. Resolve the reverse downstream owner only after Publisher return verification:

- MIR-bound verified return -> `StegVerse-org/StegVerse-SDK`;
- non-MIR/ordinary KV return -> `StegVerse-Labs/continuity-vault-kit`.

The repair must preserve exact return bytes, request/payload hashes, carrier binding, original manifest/completion/retained-packet continuity, TV/TVC credential authority where required, GitHub runtime authority `NONE`, and `authority_effect = NONE`.

Routing alone must not promote `sdk_return_binding_observed`, final StegVerse-side egress, Interlock/InTr egress, far-side transition, authentic MIR endpoint substitution, or `communication_complete`.

## Current truth

`authentic_predecessor_sdk_return_input_observed=false` remains correct. No authentic runtime packet was found during this inspection, and no synthetic packet was created.

## Next transition

Patch the existing Publisher return consumer with fail-closed verified binding-based owner selection, add tests proving MIR-vs-KV routing without authority or state-predicate promotion, validate the exact head, merge only with passing evidence, then inspect the authorized resident carrier again for an authentic same-execution MIR return delivered to the SDK owner.