# StegSocials Bounded InTr Admission Route Mirror Handoff

Updated: 2026-09-12

- Goal Task ID: `SS-KV-SKAP-SOCIAL-RELEASE-001`
- COSV: `60000000102000`
- Parent handoff: `StegVerse-Labs/StegSocials/docs/STEGSOCIALS_NATIVE_STEGBROWSER_TRANSPORT_MIRROR_HANDOFF.md`
- Organization boundary owner: `StegVerse-Labs/.github`
- Status: `ACTIVE`
- Source state: `RUNTIME_INPUT_MATERIALIZER_MERGED_VALIDATED_RUNTIME_EXECUTION_PENDING`

## Purpose

Carry one authentic bounded StegSocials `stegverse.universal-work-interlock/v1` `INGRESS/RECEIVED` record from already-authorized resident relay evidence into the existing shared Universal InTr listener without creating a second listener, scheduler, WorkerCoordinator, heartbeat authority, credential surface, or provider/publication authority.

## Merged source baseline

- PR #1428 merged the organization-owned bounded Socials InTr route at `621bf9a349ad6439e8a75cd4bbe1ffd795900497`.
- PR #1439 merged `consume_stegsocials_bounded_intr_admission_request.py` at `ef97fc882412cb13c5c54f5b6498a8762b5b3933`.
- PR #1462 merged dispatcher selector `stegsocials_bounded_intr_admission` at `b76a301361337290aa7d228b4d1813fa89ac3e75`.
- PR #1482 reconciled the post-registration canonical state at `d55af379c89e6bdf3cf15a4d3ac5584c0c0b4798`.
- PR #1496 merged resident refresh propagation of the Socials consumer at `d6cb21f360d99d3c15d7d6b58cbed678353aad4b`.
- PR #1557 merged propagation of its dynamically loaded materialization builder at `2ea069abd466a1803dab31cd26f6d8c684f7dce6`; exact head `599f47a22ff827b3281184f4f04d15e9e16dc359` passed organization control `34670560789`, Heartbeat `34670560415`, SDK WorkSpace reseal `34670560538`, Workspace DEVICE_KV `34670560362`, and deterministic suite `34670560434`.
- PR #1559 reconciled that source state at `5d36c977b459e8da5bdf7d2220db25b0f2daf884`; its metadata-only head had no attached workflows, so no separate validation claim was made.
- PR #1573 merged the authentic relay-bound runtime-input materializer at `9f0ac1265321fcf53eba96d05416e7685d555179`. Exact head `1969519d48b9df7d1c192537b86f02e1aa4fb0ac` passed organization control `34677433835`, deterministic repository suite `34677433845`, Heartbeat `34677433829`, Workspace DEVICE_KV `34677433836`, and SDK WorkSpace reseal `34677433844`.
- PR #1586 reconciled the post-#1573 handoff/COSV state at `f76fd61f8f78ce6cef20febc7431ebcd455928a0`; exact head `7df0a90bf3d754f9789c94f8848b3c1902646995` passed organization control `34677509787`, deterministic repository suite `34677509751`, and Heartbeat `34677509742`.
- StegSocials PR #49 reconciled the parent native StegBrowser transport handoff at `ac53b3a949651bfb14816c88c362463816b7ffb3`; exact head `0c89a4a905831face0661bd9e3de8a0dd17cd63a` passed Test Readiness `34677703797` and Validate StegSocials Objects `34677703787`.

## Runtime input materialization

`scripts/materialize_stegsocials_bounded_intr_admission_input.py` closes the previously missing producer path for `runtime-state/stegsocials/bounded-intr-admission-input.json`.

It uses only the already-forwarded resident relay artifact references `STEGVERSE_RELAY_EGRESS_BINDING`, `STEGVERSE_RELAY_EGRESS_AUTHORIZATION`, and `STEGVERSE_RELAY_EGRESS_PAYLOAD`. The projector remains non-authorizing. It writes the hash-bound Socials input pointer only when the payload is an exact runtime-local Socials Universal Work `INGRESS/RECEIVED` record; the relay binding is already route-admitted but pre-egress-authorization; the TV/TVC authorization is `ALLOW_RELAY_EGRESS`; binding/authorization route, transport, next-hop identity, and endpoint fields match exactly; the authorization self-hash is valid; exact payload SHA-256 and size match; no payload-inspection, canonical-transition, or settlement authority is present; and the authorized endpoint is loopback HTTP at exact path `/intr/materialization`.

Missing relay artifacts remain a passive non-authorizing wait, including under hosted validation. If authentic relay artifacts are present in a hosted environment, materialization fails closed. The resident consumer preserves the dispatcher-visible state `INPUT_NOT_MATERIALIZED` while retaining the more specific materializer reason inside `input_materialization`.

The materializer never creates TVC authorization, never starts a listener, never emits `INGRESS_ADMITTED`, never authorizes provider execution, and never mutates KV. Canonical and base resident source-refresh paths propagate the consumer, builder, and input materializer together.

## Relay/grant dependency audit

The generic TVC sovereign-relay EGRESS authorization is already payload-agnostic and does not require a Socials-specific authorization path. `tvc_sovereign_relay_egress_authorization.py` binds an exact admitted relay binding plus exact payload hash/size to an existing TVC execution grant and requires the grant context to carry:

```text
request_sha256 = exact relay request-material hash
route_sha256 = exact admitted route candidate hash
action = forward_opaque_relay_frame
resource = exact route_id
service_id = stegverse-sovereign-relay
tool_id = stegos.sovereign-relay-egress.v1
max_uses = 1
use_count = 0
```

The generic execution-grant issuer also requires exact `authority_evidence_sha256`, `cge_decision_sha256`, and the complete scope fields (`provider_id`, `service_id`, `tool_id`, `action`, `resource`, `audience`, `repository`, `environment`, `actor`). The existing service-admissibility binder verifies real authority evidence plus an externally produced CGE decision and emits an execution candidate, but the continuation audit did not find an existing source adapter that deterministically completes that candidate into the full relay-grant scope required by `scripts/execution_grant.py`.

That is now the next source-side dependency to inspect under the existing TVC execution-grant/relay owner. This Socials task must not create a competing TVC grant issuer, alternate credential path, or duplicate relay runtime. A new adapter is justified only after verifying the canonical TVC task/owner and proving no existing transformation already supplies those exact fields.

## Current resident path

```text
Personal-KV bounded-group candidate READY
-> secret-free bounded Socials InTr intent
-> canonical Universal Work INGRESS/RECEIVED
-> authentic post-continuity route admission
-> exact StegOS relay EGRESS binding + exact Socials payload
-> live single-use TVC execution grant
-> TV/TVC bounded relay EGRESS authorization
-> non-authorizing Socials runtime-input materializer
-> hash-bound resident input pointer
-> resident Socials bounded-InTr consumer
-> existing shared Universal InTr listener
-> authentic INGRESS_ADMITTED
-> TV/TVC task-scoped SKAP materialization
-> native StegBrowser/provider event execution
-> terminal session destruction proof
-> Site CAS
-> DEVICE_KV expected-etag commit/readback
-> second bounded use + refusal proof
-> Personal-KV custody + Master Records reconstruction
```

## Current runtime observation

During the 2026-09-12 continuation, the authorized remote-device connector again returned no devices. This proves only that this session had no authorized connector-visible resident device. It is not evidence that no sovereign runtime exists elsewhere. Therefore no authentic runtime-local pointer, `INGRESS_ADMITTED`, TV/TVC-SKAP receipt, provider publication/destruction, KV readback, second-use/refusal proof, or Master Records custody is claimed.

Root `README.md` and the StegSocials root `README.md` were re-reviewed through their existing handoff semantics; no README wording change is required for this dependency audit/reconciliation.

## Authority and evidence boundaries

```text
source/CI is authentic runtime ingress: false
Universal Work RECEIVED is ADMITTED: false
relay binding is relay authorization: false
TVC execution grant is transport execution: false
input materializer creates TVC authorization: false
input materializer starts listener: false
input materializer creates InTr admission: false
input materializer grants provider authority: false
resident dispatcher grants authority: false
Heartbeat grants execution authority: false
shared-listener invocation may emit authentic ingress admission: true
TV/TVC remains credential authority: true
GitHub token runtime authority: NONE
persistent hosted runtime required: false
second user-operated device required: false
```

## Remaining execution sequence

1. Under the existing TVC owner, verify the canonical transformation from real authority/CGE-bound admissibility evidence into the complete exact-scope single-use relay execution-grant candidate; reuse it if present, otherwise repair that source seam there.
2. Observe one authentic post-continuity route admission, exact relay binding, exact Socials payload, and live single-use TVC execution grant.
3. Produce the bounded TV/TVC relay authorization and allow the merged Socials materializer to create the hash-bound pointer.
4. Reuse the existing shared Universal InTr listener and retain authentic `INGRESS_ADMITTED` evidence.
5. Materialize task-scoped TV/TVC-SKAP session authority and retain its receipt.
6. Continue through StegBrowser/provider execution, terminal session destruction, Site CAS, exact DEVICE_KV readback, second bounded use/refusal proof, and Personal-KV/Master Records reconstruction.

## Manual work

None at present. Participant interaction is required only if a social provider presents an unavoidable authentication challenge not satisfiable from already-authorized TV/TVC material.
