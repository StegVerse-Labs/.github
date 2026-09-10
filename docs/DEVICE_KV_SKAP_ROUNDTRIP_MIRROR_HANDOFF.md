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
AUTHENTIC_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

These are execution/evidence blockers only. `PHYSICAL_RUNTIME_NOT_PRESENT`, `ALWAYS_ON_RECEIVER_NOT_PRESENT`, or `TESTFLIGHT_NOT_INSTALLED` MUST NOT be introduced as blockers for this data-transport proof unless a separate capability explicitly depends on them.

## Next

1. Validate and merge this ephemeral-runtime contract reconciliation.
2. Execute one already-authorized, non-destructive bounded event-ephemeral Device->KV->SKAP->KV->Device operation using the existing canonical Node identity/continuity context.
3. Retain the four receipts and exact SKAP/KV readbacks.
4. Close the three evidence blockers only when the terminal verifier returns `DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED`.

## Manual work

None for this documentation/source reconciliation. No continuously running physical node or second user-operated device is required by the Universal InTr transport contract.
