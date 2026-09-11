# Device <-> KV <-> SKAP Roundtrip Mirror Handoff

Updated: 2026-09-10

```text
goal_id: STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001
parent_goal: KV-CONNECTION-REVALIDATION-WORKER-001
cosv_id: 50000000102000
state: ACTIVE
canonical_owner: StegVerse-Labs/.github
implementation_owner: StegVerse-Labs/StegOS
transition_authority: Interlock/InTr
credential_authority: TV/TVC
github_runtime_authority: NONE
hosted_runtime_fallback: NONE
second_user_operated_device_required: false
persistent_transport_runtime_required: false
event_ephemeral_materialization_allowed: true
```

## Goal

Make the sovereign single-device path genuinely bidirectional across one authentic operation lineage:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one receipt-hash chain, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Ephemeral Node transport correction

Review of the current StegOS Universal InTr and retained-node documentation establishes an important separation:

```text
PERSISTENT
Node identity / genesis / continuity generation / append-only evidence commitments

EPHEMERAL
current Interlock/InTr invocation / transport connection / task process / provider session
```

Universal InTr does not require an always-on receiving process. Exact packets may be transported immediately, durably queued, or cause bounded `EVENT_EPHEMERAL` materialization. Therefore this task MUST NOT require a continuously resident physical StegOS process, TestFlight deployment, or always-on listener merely to satisfy the Device<->KV<->SKAP data-transport proof.

What remains required is authentic execution of the bounded operation: the ephemeral Node invocation must bind to the canonical Node identity/continuity context and emit the required Interlock/InTr receipts and exact readback evidence. Ephemeral transport does not mean synthetic transport, fixture-only proof, or loss of Node continuity identity.

Canonical references:

- `StegVerse-Labs/StegOS/docs/UNIVERSAL_INTERLOCK_PROTOCOL_MIRROR_HANDOFF.md`
- `StegVerse-Labs/StegOS/docs/STEGBROWSER_RETAINED_NODE_BOOTSTRAP_MIRROR_HANDOFF.md`
- `management/UNIVERSAL_DATA_TRANSPORT_INVARIANT.json`

## Merged source

- StegOS #326 merged at `2339f2f2fc8c28eb4d63077387013154dac9b75c`; exact-head CI `34517908014` SUCCESS.
- LLM-adapter #331 merged at `f4db7005818c7b77bf7e25345c86df1277760a93`; Gateway ingress emits the canonical DEVICE->KV first-hop sidecar without credential plaintext.
- TVC #377 merged at `72aa78c8f60226621c19d58751ec776f777583f9`; TVC validates the sidecar and remains the single SKAP ciphertext custody writer.
- `.github` #1332 merged at `42996a4582e2fb9e4d3207dd3e45b764dc727723`; WorkerCoordinator can continue from the Gateway/TVC evidence into the canonical return chain.
- `.github` #1339 merged at `861647893df88c30f591e374a8be30fccaf7c64f`; the canonical task no longer incorrectly requires a persistent physical transport process or always-on receiver.
- `.github` #1352 merged at `ec7594aac88b8d60b0d230be15f7901f1040b0fa`; exact-head `742461f32253579a1b3148a074160814e304fffb` passed the complete deterministic repository suite, organization-control validation, and deterministic diagnostics after converting the new test to canonical stdlib `unittest`.

## Preferred custody continuation

After TVC has admitted one authentic sealed ciphertext, `scripts/continue_device_kv_skap_from_tvc_custody.py`:

1. validates the canonical DEVICE->KV sidecar;
2. validates terminal TVC custody and exact SKAP readback;
3. uses canonical `kv-skap` REFERENCE semantics for KV->SKAP;
4. emits chained SKAP->KV evidence;
5. persists and exact-readbacks the KV return;
6. emits final KV->DEVICE receipt chained to SKAP->KV;
7. materializes the four-leg manifest;
8. runs the terminal verifier.

TVC remains the single ciphertext custody writer. `consume_kv_skap_custody_materialization_request.py` is compatibility/direct custody only and MUST NOT duplicate a TVC custody write for the same ciphertext.

The worker itself does not fabricate or self-authorize hop receipts. After the prerequisite current-device and TVC custody evidence is already admitted, the worker may invoke the canonical StegOS Interlock/InTr connector. That connector may materialize the receipts for those invoked transitions under its own transition semantics. GitHub, WorkerCoordinator, the carrier, and the verifier still grant no transition or credential authority.

## Bounded event execution surface

`scripts/execute_device_kv_skap_roundtrip_event.py` is the dedicated one-shot execution surface for this task. It:

1. requires an already-local canonical source root, bounded runtime root, canonical StegOS root, Gateway DEVICE->KV sidecar, and terminal TVC drain receipt;
2. rejects hosted execution markers;
3. refreshes already-local WorkerCoordinator source into the bounded event runtime;
4. validates `STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001 + 50000000102000` against the refreshed COSV task-vector index;
5. forwards only the non-secret evidence paths required by the registered worker;
6. invokes `scripts/run_worker_runtime.py --task-id STEGOS-DEVICE-KV-SKAP-ROUNDTRIP-001`, preserving normal WorkerCoordinator fresh claim/fence semantics;
7. reports terminal success only when the nested worker returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

This execution wrapper grants no execution, transition, provider, or credential authority. It exists to make the already-admissible task actually targetable on an `EVENT_EPHEMERAL` sovereign runtime without a persistent listener.

## Current evidence state after #1352

Repository-wide source search after merge found no retained authentic outcome carrying `status: ADMITTED_TO_SKAP_VAULT_CUSTODY` together with `canonical_roundtrip_eligible: true`. The only matches were producer/consumer implementation and tests. Therefore no existing repository artifact may be promoted into the required runtime input pair.

The exact next prerequisite is one authentic current-device pair produced by the already-merged ingress/custody path:

```text
A. Gateway sidecar
schema = stegverse.service-gateway.device-kv-canonical-stage/v1
contains canonical DEVICE_SYSTEM -> KV intent + RECEIVED receipt
credential_material_present = false
authority_effect = NONE_EVIDENCE_ONLY

B. TVC terminal drain receipt
status = ADMITTED_TO_SKAP_VAULT_CUSTODY
canonical_roundtrip_eligible = true
canonical_device_kv_binding.receipt_hash matches A
credential_persistence_ref points to the exact TVC-written SKAP ciphertext
```

The TVC producer is `StegVerse-Labs/TVC/tools/coinbase_gateway_stage_drain.py`; it writes drain receipts under the TVC `_Vault/SKAP/Receipts/coinbase-drain` custody tree. A test fixture, reconstructed receipt, repository-only synthetic packet, GitHub Actions artifact, or hosted substitute is not eligible.

## MyKV relationship

MyKV personal-information ingestion already uses DEVICE_KV read/write with exact-readback requirements for canonical Personal KV records. Ordinary personal information belongs in KV. Credential/signing material belongs in SKAP; MyKV retains only a SKAP reference. This child proves the transport/evidence lane connecting those boundaries rather than moving ordinary personal data wholesale into SKAP.

## Correct completion contract

One authentic bounded event-ephemeral execution must prove:

```text
1 DEVICE->KV receipt
2 KV->SKAP receipt chained to #1
3 SKAP->KV receipt chained to #2
4 KV->DEVICE receipt chained to #3
all packet bytes match intent hashes
all hops preserve Interlock/InTr admission
SKAP exact ciphertext/reference readback verified
KV exact return readback verified
TV/TVC credential authority preserved
TVC single ciphertext custody writer preserved
credential plaintext absent from ordinary transport/evidence
canonical Node identity/continuity binding preserved
persistent transport process required = false
always-on receiver required = false
event-ephemeral materialization allowed = true
hosted_runtime_used = false
second_user_operated_device_used = false
terminal state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
```

A persistent resident/physical runtime is not itself a completion predicate. Source/CI alone also remains insufficient; the bounded event-ephemeral operation must actually execute and produce its evidence.

## Current blockers

```text
AUTHENTIC_CURRENT_DEVICE_GATEWAY_SIDECAR_NOT_YET_OBSERVED
AUTHENTIC_TVC_CANONICAL_ROUNDTRIP_ELIGIBLE_DRAIN_RECEIPT_NOT_YET_OBSERVED
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

These are execution/evidence conditions only. `PHYSICAL_RUNTIME_NOT_PRESENT`, `ALWAYS_ON_RECEIVER_NOT_PRESENT`, or `TESTFLIGHT_NOT_INSTALLED` MUST NOT be introduced as blockers for this data-transport proof unless a separate capability explicitly depends on them.

## Next

1. Produce or locate one authentic current-device Gateway canonical sidecar and its matching TVC `ADMITTED_TO_SKAP_VAULT_CUSTODY` drain receipt through the existing non-hosted TV/TVC path.
2. Execute `scripts/execute_device_kv_skap_roundtrip_event.py` against that exact pair on a bounded sovereign `EVENT_EPHEMERAL` runtime bound to the retained Node identity/continuity context.
3. Retain the four chained receipts and exact SKAP/KV readbacks.
4. Close the evidence conditions only when the terminal verifier returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## Manual work

None. No continuously running physical node or second user-operated device is required by the Universal InTr transport contract.
