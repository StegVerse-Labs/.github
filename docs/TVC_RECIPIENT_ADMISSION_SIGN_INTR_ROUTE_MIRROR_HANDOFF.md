# TVC Recipient Admission Sign Universal InTr Route Mirror Handoff

Updated: 2026-09-12

```text
goal_id: TVC-RECIPIENT-ADMISSION-OPAQUE-SIGNER-BACKEND-001
root_goal: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
cosv_id: 50000000102000
repository: StegVerse-Labs/.github
branch: task/tvc-recipient-admission-sign-intr-route-001
user_verification_authority: KV/SKAP Vault
credential_authority: TV/TVC
transition_authority: Interlock/InTr
listener_owner: existing Universal InTr profiled ingress
```

## Purpose

Reuse the existing Universal InTr materialization process for one recipient-admission authority-sign operation. This source does not create a new listener, admission service, scheduler, WorkerCoordinator, signer, device verifier, or credential path.

## Request builder

`scripts/build_tvc_recipient_admission_sign_intr_request.py` accepts the existing platform-sign request and emits:

```text
stegverse.tvc.recipient-admission-sign-intr-payload/v1
stegverse.universal-intr-materialization-request/v1
```

The payload carries only non-secret exact operation bindings:

```text
platform_request_sha256
authority_key_id
authority_public_jwk_sha256
message_sha256
request_nonce
purpose = TVC_RECIPIENT_CAPABILITY_ADMISSION
user_verification_authority = KV/SKAP Vault
user_verification_performed_here = false
credential_material_present = false
private_key_material_present = false
requested_transition = INGRESS_ADMITTED
```

The request is `NONE_REQUEST_ONLY`. Building or transporting it does not prove admission.

## Shared-listener ingress adapter

`workers/tvc_recipient_admission_sign_intr_ingress.py` starts no server. It is intended to be invoked only by the existing `workers/universal_intr_profiled_ingress.py` listener.

It validates the exact materialization request, loads the write-once payload sidecar, verifies the payload hash, then emits one write-once receipt:

```text
schema = stegverse.tvc.recipient-admission-sign-intr-ingress/v1
state = INGRESS_ADMITTED
admission_state = ADMITTED
admission_ref = intr://tvc-recipient-admission-sign/...
transition_authority = Interlock/InTr
authority_effect = INGRESS_TRANSITION_ONLY
runtime_execution_attempted = false
claim_or_fence_minted = false
user_verification_performed_here = false
user_verification_authority = KV/SKAP Vault
credential_authority = TV/TVC
```

The receipt exact-binds `request_hash`, `payload_hash`, `platform_request_sha256`, authority key ID, public-JWK digest, message digest, nonce, and transport evidence. `admission_sha256` is the deterministic digest of the receipt body excluding that digest field.

This is the actual InTr-admission evidence shape suitable for projection into `CurrentInTrAdmissionProvider`. It must not be confused with the separately signed TVC recipient-capability admission: that TVC artifact grants no Interlock/InTr transition authority.

## Shared route installation

`scripts/install_tvc_recipient_admission_sign_universal_intr_route.py` is an idempotent fail-closed source transformer for the existing shared listener. It adds:

```text
profile: TVC:RecipientAdmissionAuthoritySign
route predicate: is_tvc_recipient_admission_sign(payload)
route action: admit_tvc_recipient_admission_sign(...)
```

It creates no second `ThreadingHTTPServer` and no additional runtime service. Source installation does not prove authentic runtime route installation or an authentic admission receipt.

## Validation

`tests/test_tvc_recipient_admission_sign_intr_route.py` covers:

- exact platform-request hashing and non-authorizing request construction;
- no user verification in the request or ingress adapter;
- write-once exact-bound `INGRESS_ADMITTED` receipt generation;
- admission digest validation;
- payload-hash drift rejection;
- required-node/pinned-device rejection;
- private-key request, recipient-key reuse, and public invocation rejection;
- installer idempotence;
- preservation of the existing shared listener count.

## Remaining work

1. Validate and merge this source route.
2. Bind the route to the existing Universal InTr runtime/profile installation path; do not claim runtime installation from source merge.
3. Implement the concrete `CurrentInTrAdmissionProvider` as a projection/reader of the exact current receipt for the exact platform request; it must verify freshness/applicability and must not create admission.
4. Continue with Canonical Runtime interchangeable-node carriage and node-local replay/P-256 capability invocation.

## README review

The organization README already documents Universal InTr as shared transition/admission infrastructure and forbids duplicate listener/authority surfaces. This slice reuses that topology; task-specific details are retained here rather than duplicating the README.

## Manual work

None. No production private-key, credential, assertion, biometric, or authenticator material belongs in repository state, CI, chat, Drive, ordinary KV, logs, screenshots, or model output.
