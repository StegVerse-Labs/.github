# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-12

## Goal Task ID

`SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`

Parent goal: `SS-EVIDENCE-COMPARISON-001`

COSV: `40000100100000`

Status: `ACTIVE / CLAIMED_INTEGRATION`

## Purpose

Bind ERL active research to the existing sovereign Universal InTr resident execution owner and obtain one authentic, reconstructable three-hop `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV` receipt chain without creating a second runtime owner, listener, scheduler, heartbeat, credential path, provider operation, or synthetic receipt.

## Canonical owner and authority model

Terminal owner remains `SHWP-DEVICE-KV-INTR-OBSERVATION-001` through the shared `workers/universal_intr_profiled_ingress.py`, the existing DEVICE_KV materialization path, and downstream owner `StegVerse-Labs/continuity-vault-kit#79`.

- Interlock/InTr remains transition authority.
- TV/TVC remains credential authority where credentials are required.
- HeartBeat remains timing/reference/carriage/observability only.
- GitHub runtime authority is `NONE`.
- Provider-operation replay remains unauthorized.

## Canonical path invariants

```text
EXTERNAL_SYSTEM
-> STEGOS_ECOSYSTEM
-> DEVICE_SYSTEM
-> KV
```

All three authentic receipts must preserve one exact operation identity, packet identity, acquisition-envelope payload hash, and prior-receipt chain. Hop 1 and hop 2 are `FORWARDED`; hop 3 is `RECEIVED`. Receipt hashes must recompute from canonical receipt bodies, payload plaintext is forbidden in receipts, and transport cannot transfer authority.

## Merged implementation evidence

- #1424 `b89a1ec010fc8d94ef770d900cb8244c11afe363`: shared-ingress ERL profile, terminal projection, prior-lineage migration, tests.
- #1444 `0bcfba4a7a99b1fc2b641580e805543a320a9f80`: bounded resident source preparation.
- #1468 `233992aead73e054f9ded66d62af29b0980107a8`: resident request, binding consumer, source wiring.
- #1476 `af0fcb239956e9744fdd4129bb454655efd54243`: bounded loopback submitter and dispatcher integration.
- #1546 `83a1b090ab850bf347c30f1818279064102d87d9`: canonical Task Registry reconciliation.
- #1554 `aaf663112db68b031019c0e9ea274ff6bb9382d2`: submission-input materialization.
- #1568 `ebac65426065a78863c6613fcd3f9c63ecb0e67e`: post-merge reconciliation.
- #1585 `fd1d7b3f3d42c6bb2fe1bb59838121f45ace5a55`: corrected active carriage to credentialless `STEGOS_RESIDENT_LOCAL`; removed inappropriate relay-authorization dependency; added exact retained-runtime local-source convergence.
- #1605 `c6434d85a89a0cc283bdfc1262411152ecf6ae13`: exact recomputation of hop-1/hop-2 receipt hashes, terminal request hash, and complete shared-ingress-response hash before evidence promotion.
- #1645 `e6fa3c2de5c89c1668d91b5815dbc71a1969b860`: durable submission-dispatch reconstruction evidence with exact source/runtime roots and per-dependency SHA-256 digests.
- #1648 `8a1ffeeb223a3d6125caebafd22cfbd8fc58f34d`: corrected the terminal DEVICE_KV path so ERL no longer remints a new controlled-observation packet for hop 3. Exact-head organization control, full Heartbeat/repository validation including the deterministic suite, and deterministic diagnostics all passed before merge.

## Terminal identity continuity correction — merged #1648

Inspection after #1645 found a real runtime-proof blocker. The pre-existing DEVICE_KV event path preserved the ERL hop-2 prior hash but then called the generic `device-kv` connector to create a fresh `kv.interlock.request.v1`, which necessarily minted a new operation ID, packet ID, and payload hash. That could never satisfy this task's three-hop identity invariant.

Merged #1648 corrects the existing owner instead of adding another transport:

- `workers/erl_active_research_intr_profile.py` now carries the exact original full-path `erl_transport_intent` into the terminal materialization request and hash-binds that intent.
- `scripts/submit_erl_active_research_intr_binding_local.py` rejects any terminal projection whose original intent, intent hash, operation ID, packet ID, payload hash, path, or upstream receipt chain diverges.
- `workers/erl_device_kv_terminal.py` is a bounded helper invoked only inside the existing DEVICE_KV owner. It loads the already-materialized canonical acquisition envelope, verifies its hash against the original intent, transports the exact canonical envelope bytes over deployment-local ephemeral loopback carriage, durably reads those exact bytes back at KV, emits hop index 3 from the original full-path intent, and validates the complete three-hop receipt chain.
- `scripts/install_erl_device_kv_prior_lineage.py` now upgrades retained workers to this exact-identity path while leaving non-ERL DEVICE_KV behavior unchanged.
- `scripts/install_erl_resident_request_wiring.py` and the submission consumer propagate/materialize the new helper through the already-existing resident source mechanism.
- Regression coverage verifies migration idempotence, original-intent preservation, hop-3 `DEVICE_SYSTEM -> KV` identity, exact canonical byte transport/readback, and absence of provider replay.

This merged source proves the corrected implementation and deterministic validation only. It does not prove that an authentic sovereign resident has executed the path.

## Existing provider proof — do not replay

The active-research source is `ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET`. Existing canonical ERL evidence records an authentic Google Drive provider write plus independent exact-byte readback:

- parent folder `google-drive:folder:147zp4--w_dnf_cOJzC0nKGZrWtwB2M6n`
- artifact folder `google-drive:folder:1osZ9dvIHmYI58t7PoopRVI6UbrPLxxIG`
- file `google-drive:file:1KKBS1drUFVh-czLpmg5koRgDs4YMf-gG`
- filename `ERL-CYBER-CISA-IRAN-2025-JOINT-FACT-SHEET.capture.txt`
- size `1015`
- SHA-256 `94470c58db24e544c3edfcd390cca395375a348879ec3c53451ba517ff917763`

That evidence proves the provider write/readback class only; it does not substitute for Universal InTr traversal. Provider reexecution remains unauthorized.

## Remaining work

1. On an authentic sovereign resident visit, self-materialize/verify the exact ERL source dependencies and apply/check resident preparation.
2. Materialize the existing active-research dispatch inputs, exact acquisition envelope, and deterministic runtime binding through the existing resident dispatcher.
3. Observe the authentic shared loopback ingress URL and submit via `STEGOS_RESIDENT_LOCAL` without relay authorization.
4. Preserve authentic hop 1 and hop 2 plus the hash-bound terminal materialization request.
5. Let the existing DEVICE_KV owner execute the corrected ERL terminal helper and produce authentic hop 3 from the original full-path intent with exact envelope byte readback at KV.
6. Verify the complete three-receipt chain and bind its source identity to the pre-existing provider write/readback evidence without replay. If no structured provider-proof object exists, create only a non-authorizing machine-readable projection of the already-observed provider evidence; do not claim it as a new provider event.
7. Reconcile the parent ERL handoff with exact receipt hashes and final proof class.

## Current state

`PROFILE_SOURCE_PREPARATION_RESIDENT_BINDING_LOOPBACK_SUBMISSION_AND_INPUT_MATERIALIZATION_MERGED / RESIDENT_LOCAL_TRANSPORT_ORIGIN_AND_EXACT_LOCAL_SOURCE_CONVERGENCE_MERGED_AND_VALIDATED / EXACT_BYTE_PROOF_VERIFIER_HARDENING_MERGED_AND_VALIDATED / SUBMISSION_DISPATCH_RECONSTRUCTION_EVIDENCE_HARDENING_MERGED_AND_VALIDATED / TERMINAL_FULL_INTENT_IDENTITY_CONTINUITY_CORRECTED_AND_VALIDATED / AUTHENTIC_RESIDENT_SOURCE_MATERIALIZATION_NOT_YET_OBSERVED / AUTHENTIC_SHARED_LOOPBACK_INGRESS_NOT_YET_OBSERVED / AUTHENTIC_THREE_HOP_TRAVERSAL_NOT_YET_OBSERVED`
