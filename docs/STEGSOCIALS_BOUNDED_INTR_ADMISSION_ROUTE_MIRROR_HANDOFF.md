# StegSocials Bounded InTr Admission Route Mirror Handoff

Updated: 2026-09-11

- Goal Task ID: `SS-KV-SKAP-SOCIAL-RELEASE-001`
- COSV: `60000000102000`
- Parent handoff: `StegVerse-Labs/StegSocials/docs/STEGSOCIALS_NATIVE_STEGBROWSER_TRANSPORT_MIRROR_HANDOFF.md`
- Organization boundary owner: `StegVerse-Labs/.github`
- Status: `ACTIVE`
- Source state: `BOUNDED_SOCIAL_UNIVERSAL_INTR_ADMISSION_ROUTE_IMPLEMENTED_VALIDATION_PENDING`

## Purpose

Close the source seam between the already-merged StegSocials canonical `stegverse.universal-work-interlock/v1` `INGRESS/RECEIVED` record and the existing sovereign shared Universal InTr materialization listener without creating a second listener, runtime, scheduler, WorkerCoordinator, heartbeat, credential surface, or publication authority.

## Existing owner reused

The canonical organization contract remains:

```text
org-runtime/interlock-intr.json
workers/universal_intr_profiled_ingress.py
```

Application repositories expose bounded profiles and source objects; `.github` owns organization ingress/egress generation. HB/HB-derived carriage remains non-authorizing. TV/TVC remains credential authority. GitHub runtime authority remains `NONE`.

## Added source

```text
scripts/build_stegsocials_bounded_intr_materialization.py
workers/stegsocials_bounded_intr_ingress.py
scripts/install_stegsocials_bounded_universal_intr_route.py
tests/test_stegsocials_bounded_intr_admission_route.py
```

### Builder

`build_stegsocials_bounded_intr_materialization.py` consumes only the already-source-validated StegSocials `INGRESS/RECEIVED` record. It verifies exact task/work/correlation/group/use/content/platform/account and authority bindings and refuses synthetic InTr/SKAP receipts, credential material, provider authority, and execution authority.

It emits the existing `stegverse.universal-intr-materialization-request/v1` shape with:

```text
destination = StegSocials:BoundedSocialIngress
operation = BOUNDED_SOCIAL_INTR_INGRESS
downstream owner = SS-KV-SKAP-SOCIAL-RELEASE-001
event triggered = true
always-on receiver required = false
second user device required = false
receiver unavailable = DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION
request grants execution authority = false
credential authority = TV/TVC
github token runtime authority = NONE
```

The exact received work record is retained in the local payload sidecar and remains `RECEIVED`; the builder does not admit it.

### Shared-ingress adapter

`workers/stegsocials_bounded_intr_ingress.py` owns no listener. It validates the exact materialization request and exact locally materialized payload, persists the request write-once, and emits `stegverse.stegsocials-bounded-intr-materialization-ingress/v1` with `state=INGRESS_ADMITTED` only when invoked by the existing sovereign shared listener.

The receipt binds the exact work/correlation/group/use/platform/account/content/participant-approval/state references and explicitly records:

```text
runtime execution attempted = false
provider operation authorized = false
credential material present = false
claim or fence minted = false
heartbeat grants execution authority = false
admission grants publication authority = false
next owner = TV/TVC_SKAP_SESSION_MATERIALIZATION
```

Node-outbox wrappers are currently rejected by this profile unless their full wrapper hash/identity contract is separately implemented and validated. This prevents an unverified wrapper from contributing node/interlock/outbox identity evidence.

### Route installer

`install_stegsocials_bounded_universal_intr_route.py` idempotently adds the profile to a runtime copy of the existing shared Universal InTr listener and wraps its existing routing expression. It starts no new listener and is designed to compose with other shared-listener profiles such as CanonicalWork.

## Authority and evidence boundaries

```text
source implementation is authentic ingress: false
CI validation is authentic ingress: false
Universal Work RECEIVED is ADMITTED: false
shared-listener invocation may emit ingress admission evidence: true
InTr admission grants provider/publication authority: false
TV/TVC remains credential authority: true
persistent transport runtime required: false
always-on receiver required: false
event-ephemeral materialization allowed: true
hosted runtime fallback: none
second user-operated device required: false
```

## Validation target

Run the repository validation lane including `python -m unittest discover -v tests`. Required deterministic coverage includes exact request/payload binding, source non-authority, write-once admission persistence, synthetic-receipt refusal, secret/provider-authority refusal, route idempotence, and coexistence with the CanonicalWork shared route.

## Remaining authentic execution sequence

1. Materialize one already-authorized bounded social `INGRESS/RECEIVED` record in the sovereign current execution context.
2. Build its exact Universal InTr materialization request and payload sidecar.
3. Install/reuse the StegSocials profile in the existing shared Universal InTr listener.
4. Submit the exact request through that authentic listener and retain the resulting `INGRESS_ADMITTED` receipt.
5. Materialize task-scoped TV/TVC-SKAP session authority and retain its authentic receipt.
6. Continue through the already-merged StegSocials native event bridge, StegBrowser provider execution, terminal destruction proof, execution reconciliation, existing Site CAS, exact KV readback, second bounded use, refusal proof, and Master Records reconstruction.

## README impact

README impact is `MATERIAL` because this adds an organization-owned Universal InTr profile and admission route for bounded StegSocials work. The repository README must describe the shared-listener reuse and authority boundary in the same functional change before merge.

## Manual work

None. Participant interaction is only required if the social provider presents an unavoidable authentication challenge not satisfiable from already-authorized TV/TVC material.
