# MIR SDK return ingress materialization mirror handoff

Updated: 2026-09-14
Goal Task ID: `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`
COSV ID: `50000000100000`
Canonical issue: `StegVerse-Labs/.github#1891`
Repair issue: `StegVerse-Labs/.github#1904`
Predecessor carrier-routing merge: `bf8a726da8688bcfbf625b82a388ae8c79080666`
Status: `ACTIVE / NEXT DELIVERY DEFECT IDENTIFIED / SOURCE REPAIR IN PROGRESS / RUNTIME PREDICATES UNCHANGED`

## State-transition rule

Every process step is a distinct state transition. The repaired Publisher owner-selection transition does not prove the subsequent universal-ingress admission or SDK materialization transitions.

## Observed next defect

`workers/universal_intr_profiled_ingress.py` recognizes the Publisher return path only when the reverse materialization request has `downstream_owner_ref = StegVerse-Labs/continuity-vault-kit`. After merge `bf8a726da8688bcfbf625b82a388ae8c79080666`, a verified MIR Publisher return correctly selects `downstream_owner_ref = StegVerse-org/StegVerse-SDK`, but no ingress discriminator or consumer exists for that owner. The request therefore cannot reach the merged `stegverse-materialize-sdk-return` transition through the existing universal InTr ingress.

## Bounded repair

Reuse the existing universal InTr materialization endpoint, reverse transport intent, reverse receipt chain, carrier binding, and exact payload sidecars. Add only an SDK-owned Publisher-return admission/consumer branch.

The consumer must:

- require `downstream_owner_ref = StegVerse-org/StegVerse-SDK`;
- validate the same exact reverse payload, transport intent, receipt chain, and carrier binding used by the existing Publisher-return path;
- require exact canonical `stegverse.publisher.artifact-return/v1` bytes with `stegverse.publisher.mir-roundtrip-binding/v1`;
- recover the original admitted manifest from `roundtrip_binding.sdk_processor_state.manifest`;
- require the original `manifest_receipt_id` from `roundtrip_binding.sdk_processor_state.processor_result.manifest_receipt_id`;
- use the exact carried `roundtrip_binding.downstream_completion_capsule` as the original completion capsule, while relying on the SDK materializer to verify exact equality and manifest continuity;
- invoke only the merged StegVerse-SDK `materialize_publisher_return_binding()` seam from local source;
- retain exact SDK return binding bytes plus a non-authorizing materialization receipt;
- promote only the SDK-return materialization transition represented by `sdk_return_binding_observed=true` after successful exact materialization;
- keep final StegVerse egress, Interlock/InTr egress, far-side transition, governed return durability, final transport exit, successful transport round trip, authentic MIR substitution, and communication completion false.

No second transport, scheduler, dispatcher plane, credential authority, governance authority, or runtime plane may be introduced.

## Current truth

No authentic post-repair same-execution MIR Publisher return addressed to the SDK owner has been found in retained GitHub surfaces. This repair therefore remains source-path remediation until an authentic resident carrier execution is observed.

## Next transition

Implement the SDK-owned return ingress/consumer with fail-closed tests, validate exact head, and merge only with passing evidence. Then inspect the authorized resident carrier again for an authentic same-execution SDK-owned MIR return. Only authentic execution of the merged materialization seam may advance `authentic_predecessor_sdk_return_input_observed` / `sdk_return_runtime_observed` and enable `RTC-STEGVERSE-EGRESS-007`.
