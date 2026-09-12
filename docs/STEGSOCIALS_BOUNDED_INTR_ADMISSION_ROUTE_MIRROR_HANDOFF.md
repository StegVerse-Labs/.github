# StegSocials Bounded InTr Admission Route Mirror Handoff

Updated: 2026-09-12

- Goal Task ID: `SS-KV-SKAP-SOCIAL-RELEASE-001`
- COSV: `60000000102000`
- Parent handoff: `StegVerse-Labs/StegSocials/docs/STEGSOCIALS_NATIVE_STEGBROWSER_TRANSPORT_MIRROR_HANDOFF.md`
- Organization boundary owner: `StegVerse-Labs/.github`
- Status: `ACTIVE`
- Source state: `RUNTIME_INPUT_MATERIALIZER_IMPLEMENTED_VALIDATION_OPEN`

## Purpose

Close the source seam from the already-merged StegSocials canonical `stegverse.universal-work-interlock/v1` `INGRESS/RECEIVED` record to the existing sovereign shared Universal InTr listener without creating a second listener, scheduler, WorkerCoordinator, heartbeat, credential surface, or publication authority.

## Merged baseline

`.github` PR #1428 merged the organization-owned `StegSocials:BoundedSocialIngress` builder, adapter, shared-listener route installer, deterministic tests, and README/handoff changes at merge `621bf9a349ad6439e8a75cd4bbe1ffd795900497`. PR #1439 merged the resident bounded-InTr consumer at `ef97fc882412cb13c5c54f5b6498a8762b5b3933`. PR #1462 merged dispatcher registration at `b76a301361337290aa7d228b4d1813fa89ac3e75`. PR #1482 reconciled the canonical post-registration state at `d55af379c89e6bdf3cf15a4d3ac5584c0c0b4798`.

PR #1496 merged resident propagation of `consume_stegsocials_bounded_intr_admission_request.py` at `d6cb21f360d99d3c15d7d6b58cbed678353aad4b`. PR #1557 then repaired the dynamically loaded builder dependency: exact head `599f47a22ff827b3281184f4f04d15e9e16dc359` passed organization control `34670560789`, Heartbeat `34670560415`, SDK WorkSpace reseal validation `34670560538`, Workspace DEVICE_KV validation `34670560362`, and deterministic repository suite `34670560434`, then merged at `2ea069abd466a1803dab31cd26f6d8c684f7dce6`. PR #1559 reconciled that merged state at `5d36c977b459e8da5bdf7d2220db25b0f2daf884` without a separate validation claim because no workflows attached to its metadata-only head.

The route, consumer, dispatcher registration, builder, and resident source-refresh propagation remain non-authorizing. Source and CI do not prove authentic admission.

## Runtime input materialization seam

Continuation audit found that the consumer required `runtime-state/stegsocials/bounded-intr-admission-input.json`, but no producer for `stegverse.stegsocials-bounded-intr-admission-input/v1` existed anywhere in the StegVerse-Labs source graph. That meant the registered resident consumer could only remain in `INPUT_NOT_MATERIALIZED` unless some unrecorded external step manually created the pointer.

Branch `materialize-socials-runtime-input-001` adds `scripts/materialize_stegsocials_bounded_intr_admission_input.py` and integrates it into the existing consumer. When the pointer is absent, the consumer may invoke this materializer before returning a wait state.

The materializer uses only the already-forwarded resident relay artifact references:

- `STEGVERSE_RELAY_EGRESS_BINDING`;
- `STEGVERSE_RELAY_EGRESS_AUTHORIZATION`;
- `STEGVERSE_RELAY_EGRESS_PAYLOAD`.

It materializes the Socials pointer only when all of the following are true:

- the relay payload is a runtime-local JSON `stegverse.universal-work-interlock/v1` record;
- the record is exactly `direction=INGRESS,state=RECEIVED,next_owner=INTERLOCK_INTR`;
- `source.identity` and `bounded_social_intent.task_id` are exactly `SS-KV-SKAP-SOCIAL-RELEASE-001`;
- the RECEIVED record carries no admission receipt and does not claim runtime admission;
- the relay binding uses `stegos.sovereign_relay_egress_binding.v1`;
- the authorization uses `stegverse.tvc.sovereign-relay-egress-authorization/v1`, decision `ALLOW_RELAY_EGRESS`, issuer/credential authority `TV/TVC`, and does not claim runtime execution;
- binding ID, route ID, transport ID, and next-hop endpoint agree exactly between binding and authorization;
- the authorization payload SHA-256 and payload size bind the exact RECEIVED bytes;
- the authorized next-hop endpoint is loopback HTTP with exact path `/intr/materialization`;
- an existing authorization ID is present.

Only then is the hash-bound pointer written with `transport_origin=TVC_RELAY_EGRESS`, `request_grants_execution_authority=false`, and `authority_effect=NONE_INPUT_ONLY`. The materializer never creates TVC authorization, never starts a listener, never emits InTr admission, and never authorizes provider execution.

Both canonical and base resident source-refresh lists now include the input materializer along with the consumer and builder. Regression coverage requires all three runtime dependencies to propagate together.

## Current resident-consumption implementation

`scripts/consume_stegsocials_bounded_intr_admission_request.py` remains the bounded consumer for one authentic local Socials RECEIVED object. If its pointer already exists, it validates and consumes it as before. If absent, it invokes the non-authorizing materializer. A missing or incomplete authentic relay artifact set returns a wait state with no transport attempt. A valid materialized pointer then allows the consumer to build the exact Socials InTr materialization request and submit it to the already-authorized shared loopback listener.

Only a returned authentic `stegverse.stegsocials-bounded-intr-materialization-ingress/v1` receipt with `state=INGRESS_ADMITTED` advances ownership to `TV/TVC_SKAP_SESSION_MATERIALIZATION`.

## Current runtime observation

At the 2026-09-12 continuation check, the authorized remote-device connector again returned no devices. This is not proof that no sovereign runtime exists outside that connector. It means this session cannot observe or invoke an authentic current resident execution surface, so no runtime admission, TV/TVC-SKAP receipt, provider publication, KV mutation, or custody evidence is claimed.

Root `README.md` was re-reviewed. Its existing bounded StegSocials Universal InTr section remains semantically correct; no README wording change is required for this narrow input-materialization repair.

## Authority and evidence boundaries

```text
source implementation is authentic ingress: false
CI validation is authentic ingress: false
Universal Work RECEIVED is ADMITTED: false
input materializer may create TVC authorization: false
input materializer may start listener: false
input materializer may create InTr admission: false
input materializer may authorize provider operation: false
shared-listener invocation may emit ingress admission evidence: true
resident consumer may manufacture group approval: false
resident consumer may manufacture TVC authorization: false
resident consumer may start a second listener: false
resident dispatcher registration grants authority: false
source refresh propagation grants authority: false
INPUT_NOT_MATERIALIZED authorizes execution: false
InTr admission grants provider/publication authority: false
TV/TVC remains credential authority: true
persistent transport runtime required: false
always-on receiver required: false
event-ephemeral materialization allowed: true
hosted runtime fallback: none
second user-operated device required: false
```

## Remaining execution sequence

1. Validate and merge the authentic relay-bound Socials runtime-input materializer.
2. On an authentic resident execution surface, allow the existing TV/TVC relay binding/authorization/payload to materialize the exact hash-bound Socials input pointer.
3. Reuse the shared Universal InTr listener and retain the authentic `INGRESS_ADMITTED` receipt.
4. Materialize task-scoped TV/TVC-SKAP session authority and retain its authentic receipt.
5. Continue through the merged StegSocials native event bridge, StegBrowser provider execution, terminal destruction proof, execution reconciliation, existing Site CAS, exact KV readback, second bounded use, refusal proof, and Master Records reconstruction.

## Manual work

None at present. Participant interaction is required only if a social provider presents an unavoidable authentication challenge not satisfiable from already-authorized TV/TVC material.
