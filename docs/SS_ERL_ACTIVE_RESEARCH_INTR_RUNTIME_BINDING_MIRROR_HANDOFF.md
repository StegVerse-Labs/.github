# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-12

## Goal Task ID

`SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`

Parent goal: `SS-EVIDENCE-COMPARISON-001`

COSV: `40000100100000`

Status: `ACTIVE / CLAIMED_INTEGRATION`

## Purpose

Bind the already-merged ERL active-research Universal InTr intent to the existing sovereign Universal InTr resident execution owner without creating a second runtime owner, dispatcher, scheduler, heartbeat, credential path, provider operation, or synthetic transport receipt.

## Canonical owner and path

Existing terminal owner remains `SHWP-DEVICE-KV-INTR-OBSERVATION-001` through the shared `workers/universal_intr_profiled_ingress.py`, `scripts/consume_device_kv_intr_materialization_request.py`, and downstream owner `StegVerse-Labs/continuity-vault-kit#79`. TV/TVC remains credential authority for transitions that require credentials; GitHub runtime authority is `NONE`.

Canonical logical path:

```text
EXTERNAL_SYSTEM
-> STEGOS_ECOSYSTEM
-> DEVICE_SYSTEM
-> KV
```

One operation identity, one packet identity, one exact acquisition-envelope payload hash, and prior-receipt lineage must be preserved across all three authentic adjacent transitions.

## Merged implementation evidence

- PR #1424 merged at `b89a1ec010fc8d94ef770d900cb8244c11afe363` after organization-control, Heartbeat validation, and deterministic-suite PASS. It added the ERL shared-ingress profile, route installer, DEVICE_KV prior-lineage preservation, and tests.
- PR #1444 merged at `0bcfba4a7a99b1fc2b641580e805543a320a9f80` after the same three exact-head validation classes PASS. It added bounded resident source preparation.
- PR #1468 merged at `233992aead73e054f9ded66d62af29b0980107a8` from exact head `ceab2ab090ca8d8edd813400180b12d25df1c873` after organization-control, Heartbeat validation, and deterministic-suite PASS. It added the canonical resident request, binding-materialization consumer, resident request wiring installer, resident-source copy wiring, and deterministic tests.
- PR #1476 merged at `af0fcb239956e9744fdd4129bb454655efd54243` from exact head `5fb90e43675b5fdefe403171bea668727d3bf1d8` after organization-control, Heartbeat/repository validation, deterministic-suite diagnostics, and DeepSeek resident validation all passed. It added the bounded loopback ERL submitter, existing-dispatcher submission consumer, resident-source copy wiring, digest normalization, canonical `unittest` regression coverage, and README runtime-interface documentation.
- PR #1546 merged at `83a1b090ab850bf347c30f1818279064102d87d9` after exact-head control-plane validation PASS. It reconciled the canonical task record so already-completed implementation/validation steps are no longer listed as future transitions; completion and activation remain false.
- PR #1554 merged at `aaf663112db68b031019c0e9ea274ff6bb9382d2` from exact head `b2b9591deda89e2aa5f7f3618329c1da8f889ba9` after both validation lanes, deterministic-suite diagnostics, and DeepSeek resident validation passed. It added submission-input materialization and exposed the transport-origin dependency corrected later.
- PR #1568 merged at `ebac65426065a78863c6613fcd3f9c63ecb0e67e` after exact-head validation PASS. It reconciled the handoff after #1554 without claiming runtime evidence.
- PR #1585 merged at `fd1d7b3f3d42c6bb2fe1bb59838121f45ace5a55` from exact head `fb2a7ffc212f6bd5a68cd3030954f6e3da6c9089` after both validation lanes, full Heartbeat/repository validation, deterministic-suite diagnostics, and DeepSeek resident validation all passed. It corrected ERL loopback carriage to the credentialless `STEGOS_RESIDENT_LOCAL` transport origin, removed the active dependency on sovereign-relay authorization, added exact retained-resident local-source convergence, tests, README documentation, and canonical Task Registry reconciliation.
- PR #1605 merged at `c6434d85a89a0cc283bdfc1262411152ecf6ae13` from exact head `c5ae49f5d31cbba16c00cc8d85305a1dd3b61c6f` after organization-control, full Heartbeat/repository validation, and deterministic-suite diagnostics all passed on the rebuilt current-main baseline. It added exact-byte recomputation for both upstream hop receipt hashes, terminal request hash validation, exact ingress-response hashing, and tamper-rejection regression coverage before resident submission evidence can be persisted.

Merged source does not prove resident execution, authentic shared-ingress observation, any authentic InTr hop, terminal KV receipt, or provider replay.

## Resident-local transport correction

Investigation on 2026-09-12 established that the earlier ERL submitter incorrectly used `TVC_RELAY_EGRESS` as the transport origin for a resident-local loopback handoff.

Canonical TVC source `docs/SOVEREIGN_RELAY_EGRESS_AUTHORIZATION_MIRROR_HANDOFF.md` defines sovereign relay EGRESS authorization as exact-scope and single-use, bound to a real admitted relay route, exact opaque payload hash/size, and a live TVC execution grant. TVC also records `live_egress_authorization: false`. That authorization class is therefore neither presently available nor semantically appropriate for the ERL resident-local loopback handoff.

The shared HIL transport validator independently confirms the distinction: `TVC_RELAY_EGRESS` requires an authorization identifier because it represents a governed sovereign relay, while local transport origins must not claim a TVC relay authorization.

Merged correction:

- `workers/erl_active_research_transport.py`
  - defines ERL-only transport origin `STEGOS_RESIDENT_LOCAL`;
  - requires `InTr`, JSON, exact raw-body SHA-256, and no authorization header;
  - is invoked only after the shared listener identifies an ERL active-research binding;
  - does not become a generic HIL origin and grants no authority.
- `scripts/install_erl_active_research_universal_intr_route.py`
  - migrates fresh or already-installed ERL route source from HIL relay-header validation to the ERL-specific resident-local validator;
  - leaves non-ERL routes on their existing validators unchanged.
- `scripts/materialize_erl_active_research_intr_resident_local_input.py`
  - consumes the already-materialized binding receipt and requires only the explicit authentic loopback ingress URL;
  - creates no TVC authorization and carries none in the input;
  - records `transport_origin=STEGOS_RESIDENT_LOCAL` and `transport_credential_required=false`.
- `scripts/submit_erl_active_research_intr_binding_local.py`
  - reuses the already-validated ERL binding and profile-admission validators;
  - sends exact binding bytes with `X-StegVerse-Transport-Origin: STEGOS_RESIDENT_LOCAL`;
  - emits no `X-StegVerse-Authorization-Id` header;
  - rejects any resident-local input that contains a TVC relay authorization field.
- `control/resident-execution-request.d/consume-erl-active-research-intr-submission.py`
  - selects the resident-local materializer and resident-local submitter as the active ERL resident path.
- `scripts/install_erl_resident_request_wiring.py`
  - propagates the resident-local transport validator/materializer/submitter through the existing resident source path;
  - requires only `STEGVERSE_UNIVERSAL_INTR_INGRESS_URL` for ERL local submission;
  - creates no second listener, runtime, scheduler, heartbeat, WorkerCoordinator, claim/fence path, credential issuer, or provider operation.

The legacy relay submitter/materializer remain source history but are no longer selected by the active ERL resident dispatcher. Their existence does not authorize relay use.

## Retained-resident exact local source convergence

Inspection of `scripts/refresh_sovereign_worker_runtime_source.py` showed that retained-runtime refresh already propagates the `workers/` tree and `control/resident-execution-request.d/` consumers, but does not generically copy every ERL `scripts/...` dependency. A refreshed resident could therefore receive the ERL consumer while still lacking one or more exact scripts that consumer invokes.

Merged #1585 closes that gap without widening generic refresh:

- both the binding and submission consumers carry the same exact allow-list of ERL source dependencies;
- dependencies are copied only from the already-local canonical source root to a distinct resident runtime root;
- missing dependencies fail closed;
- target drift is atomically repaired and SHA-256 parity is verified after every copy;
- canonical source and runtime roots are forbidden from aliasing, preventing mutation of the canonical checkout;
- no clone, fetch, pull, network source transport, credential acquisition, or repository mutation occurs;
- the binding consumer applies `scripts/prepare_erl_active_research_intr_runtime_source.py` and immediately verifies the idempotent `--check` state before building the deterministic binding;
- the submission consumer performs the same local-source convergence/preparation independently so selected-subset dispatch does not depend on a prior binding-consumer visit;
- this source convergence grants no execution, claim/fence, credential, Interlock/InTr transition, provider, or completion authority and does not itself prove authentic traversal.

Deterministic regression coverage verifies exact allow-list materialization, drift repair, missing-dependency fail-closed behavior, independent submission-lane source completeness, source/runtime root separation, and preparation apply-then-check ordering.

## Merged profile / terminal contract retained

The ERL profile still:

- validates the deterministic ERL binding, exact acquisition-envelope hash, and full logical boundary path;
- emits hop 1 only after the exact binding reaches and passes the authentic shared STEGOS_ECOSYSTEM ingress;
- emits hop 2 when the same packet is projected into the existing device-materialization path;
- projects only the terminal `DEVICE_SYSTEM -> KV` request to `StegVerse-Labs/continuity-vault-kit#79`;
- preserves exact operation ID, packet ID, payload hash, and prior-receipt lineage;
- never fabricates hop 3 and never replays the provider operation.

## Merged exact-byte proof-verifier hardening

PR #1605 hardens the resident-local submission verifier before authentic runtime execution. The earlier admission path validated receipt structure and lineage but did not independently recompute every supplied upstream hop `receipt_hash` or the projected terminal request hash before persisting submission evidence.

The merged verifier now fails closed unless:

- each upstream hop receipt hash recomputes from the exact canonical receipt body;
- hop identity, operation identity, packet identity, payload hash, adjacent boundary roles, verification state, authority-transfer prohibition, and plaintext-secret prohibition remain exact;
- hop 2 binds hop 1 through the exact prior-receipt hash;
- the projected terminal request preserves both upstream receipt hashes and binds hop 2 as its immediate predecessor;
- the terminal request hash recomputes from the exact canonical request body;
- the complete shared-ingress response is itself hash-bound before promotion into the resident submission receipt.

This hardening creates no runtime evidence and grants no execution, transition, claim/fence, credential, provider, or completion authority. It exists so a future authentic resident traversal can be independently proven from exact bytes rather than trusted hash fields.

## Existing proof that must not be repeated

- ERL PR #154 active-research dispatch merged.
- ERL PR #155 acquisition consumer merged.
- ERL PR #156 exact three-hop admission contract merged.
- ERL PR #157 reusable non-authorizing runtime binding merged at `bfb76a068717ff0aaf96c32af97ebcc43324149f`.
- CISA/Iran public-source capture provider write and exact-byte provider readback are already authentic and remain separate from InTr transport proof.

## Remaining work

1. On an authentic sovereign resident visit, let the existing ERL consumer self-materialize and verify its exact local source dependencies and apply/check resident preparation; preserve the resulting non-authorizing source-materialization evidence.
2. Materialize the existing local ERL source/dispatch inputs and deterministic binding/envelope through the existing resident dispatcher.
3. Observe the authentic shared loopback ingress URL; let the existing submission consumer materialize the resident-local input automatically without relay authorization.
4. Observe one authentic shared-ingress ERL response, preserving authentic hop 1 and hop 2 receipts and the projected terminal request.
5. Let the existing DEVICE_KV owner execute the terminal bytes and preserve authentic hop 3 with exact prior-receipt continuity.
6. Verify the complete three-receipt chain and bind terminal transport proof to the pre-existing provider readback evidence without provider replay.
7. Reconcile the parent ERL handoff with exact receipt hashes and final proof class.

## Current state

`PROFILE_SOURCE_PREPARATION_RESIDENT_BINDING_LOOPBACK_SUBMISSION_AND_INPUT_MATERIALIZATION_MERGED / RESIDENT_LOCAL_TRANSPORT_ORIGIN_AND_EXACT_LOCAL_SOURCE_CONVERGENCE_MERGED_AND_VALIDATED / EXACT_BYTE_PROOF_VERIFIER_HARDENING_MERGED_AND_VALIDATED / AUTHENTIC_RESIDENT_SOURCE_MATERIALIZATION_NOT_YET_OBSERVED / AUTHENTIC_SHARED_LOOPBACK_INGRESS_NOT_YET_OBSERVED / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED`
