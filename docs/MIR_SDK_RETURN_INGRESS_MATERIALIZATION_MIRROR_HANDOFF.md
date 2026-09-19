# MIR SDK return ingress materialization mirror handoff

Updated: 2026-09-14
Goal Task ID: `MIR-ROUNDTRIP-EGRESS-AUTHENTICITY-001`
COSV ID: `50000000100000`
Canonical issue: `StegVerse-Labs/.github#1891`
Repair issue: `StegVerse-Labs/.github#1904`
Predecessor carrier-routing merge: `bf8a726da8688bcfbf625b82a388ae8c79080666`
Status: `ACTIVE / SDK RETURN INGRESS SOURCE REPAIR IMPLEMENTED / EXACT-HEAD VALIDATION PENDING / RUNTIME PREDICATES UNCHANGED`

## State-transition rule

Every process step is a distinct state transition. The repaired Publisher owner-selection transition does not prove the subsequent universal-ingress admission or SDK materialization transitions.

## Observed next defect

`workers/universal_intr_profiled_ingress.py` previously recognized the Publisher return path only when the reverse materialization request had `downstream_owner_ref = StegVerse-Labs/continuity-vault-kit`. After merge `bf8a726da8688bcfbf625b82a388ae8c79080666`, a verified MIR Publisher return correctly selects `downstream_owner_ref = StegVerse-org/StegVerse-SDK`, but that owner could not be admitted/dispatched through the existing Publisher-return ingress.

## Implemented bounded repair

The existing universal InTr materialization endpoint, reverse transport intent, reverse receipt chain, carrier binding, payload sidecars, and consumer dispatch path are reused. No second ingress or transport plane was added.

`consume_kv_publisher_return_materialization_request.py` now exposes a bounded two-owner matcher used by the already-existing universal-ingress discriminator:

- `StegVerse-Labs/continuity-vault-kit` -> existing KV import-candidate path;
- `StegVerse-org/StegVerse-SDK` -> SDK return materialization path.

The exact owner string remains present in the request and is validated before branching. Unknown owners fail closed.

The common transport verifier is shared by both owners and requires the same exact reverse payload, transport intent, receipt chain, endpoint/path identity, local StegOS transport validation, TV/TVC credential boundary, and GitHub runtime authority `NONE`.

For the SDK owner, the consumer then:

- requires exact canonical `stegverse.publisher.artifact-return/v1` bytes carrying `stegverse.publisher.mir-roundtrip-binding/v1`;
- requires `publisher_transition_observed=true` and all later predicates still false;
- recovers the original admitted manifest only from `roundtrip_binding.sdk_processor_state.manifest`;
- requires the original `manifest_receipt_id` only from `roundtrip_binding.sdk_processor_state.processor_result.manifest_receipt_id`;
- takes the original `stegverse.sdk.downstream-completion-capsule/v1` only from the verified roundtrip binding;
- loads local `StegVerse-SDK` source and invokes only `materialize_publisher_return_binding()`;
- retains the exact SDK return binding under the runtime root and emits `stegverse.sdk-publisher-return-intr-materialization-consumption/v1`;
- represents only that SDK-return transition with `sdk_return_binding_observed=true` after successful exact materialization.

The SDK consumption receipt explicitly keeps all later predicates false:

- final StegVerse-side egress transition;
- Interlock/InTr egress;
- far-side transition;
- governed return durable record;
- final allowed transport-exit transition;
- successful data transport round trip identification;
- authentic external MIR endpoint substitution;
- communication completion.

Ordinary KV Publisher returns continue through the existing import-candidate path unchanged in authority and mutation semantics.

## Tests added

`tests/test_sdk_publisher_return_intr_materialization.py` proves:

- the existing universal ingress discriminator recognizes both exact permitted owners without a new ingress plane;
- request validation accepts only those two owners;
- SDK materialization inputs are recovered from carried verified state rather than synthesized;
- missing original manifest receipt ID fails closed;
- downstream predicate promotion fails closed;
- the SDK branch imports only the existing SDK materializer and keeps successful transport/communication predicates false.

## Current truth

No authentic post-repair same-execution MIR Publisher return addressed to the SDK owner has been found in retained GitHub surfaces. Source implementation therefore does not promote `authentic_predecessor_sdk_return_input_observed`, `sdk_return_runtime_observed`, final egress, InTr egress, far-side, return durability, final transport exit, successful round-trip, authentic MIR substitution, or communication completion.

## Next transition

Validate the exact branch head through the repository's existing checks and merge only if those checks pass. Then inspect the authorized resident carrier again for an authentic same-execution SDK-owned MIR Publisher return. Only authentic execution of the merged SDK materialization transition may enable `RTC-STEGVERSE-EGRESS-007`.


## 2026-09-19 canonical Master Records custody repair

The next concrete custody defect was identified after the SDK return materialization source had already been merged: `consume_kv_publisher_return_materialization_request.py` retained the exact `stegverse.sdk.publisher-return-binding/v1` and emitted `SDK_RETURN_BINDING_MATERIALIZED_READY_FOR_FINAL_STEGVERSE_EGRESS`, but that observed `RTC-SDK-RETURN-006` transition was not submitted through canonical Master Records before the result exposed `sdk_return_binding_observed=true`.

The existing consumer now uses the already-established `workers/canonical_state_transition_custody.py` seam. It binds:

- transition `RTC-SDK-RETURN-006`;
- the exact retained SDK Publisher-return binding as required evidence;
- the exact SDK Publisher-return materialization receipt as required evidence;
- the reverse transport terminal receipt as prior-state continuity;
- the exact SDK return binding digest as resulting state;
- the existing operation/materialization correlation;
- authority effect `NONE`.

The consumer fails closed unless the canonical Master Records response is `RECORDED`, reconstruction is `PASS`, required-evidence validation is `PASS`, and the receipt/reconstruction digests are equal. Only after that closure may the local consumption result expose `sdk_return_binding_observed=true`. All later predicates remain false: final StegVerse-side egress, Interlock/InTr egress, far-side transition, authentic external MIR substitution, and communication completion.

This repair adds no runtime, transport, scheduler, dispatcher, custody store, transition authority, or credential authority. It closes only the custody gap on the existing SDK-return materialization transition.


## RTC007 continuation binding — 2026-09-19

After `RTC-SDK-RETURN-006` canonical custody closes, the existing Publisher-return consumer now continues the exact retained SDK return binding through the already-merged LLM Adapter `prepare_sdk_return_for_intr()` implementation for `RTC-STEGVERSE-EGRESS-007`.

The exact LLM Adapter transition object and exact predecessor SDK binding are required evidence for `RTC-STEGVERSE-EGRESS-007`. Master Records must return `RECORDED`, reconstruction `PASS`, required-evidence validation `PASS`, and exact receipt/reconstruction digest equality before the path may proceed.

Only after RTC007 closure does the consumer invoke the already-existing StegOS `prepare_mir_southbound_materialization()` seam. That produces the existing Universal InTr materialization request for RTC008; it does not claim Interlock/InTr admission, RTC009 far-side transition, caller consequence, or communication completion.

No runtime, scheduler, dispatcher, transport, custody store, transition authority, or credential authority is added.
