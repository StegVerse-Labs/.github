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
```

## Goal

Make the current single-device StegOS path genuinely bidirectional across one authentic operation lineage:

```text
DEVICE_SYSTEM -> KV -> SKAP_VAULT -> KV -> DEVICE_SYSTEM
```

Completion requires four adjacent canonical InTr receipts, exact packet/readback verification, one receipt-hash chain, TV/TVC credential authority, no secret plaintext in ordinary KV/device/repository state, no authority transfer, no hosted fallback, and no second user-operated device.

## Merged upstream source

- StegOS #326 merged at `2339f2f2fc8c28eb4d63077387013154dac9b75c`; exact-head CI `34517908014` SUCCESS.
- LLM-adapter #331 merged at `f4db7005818c7b77bf7e25345c86df1277760a93`; Gateway ingress emits the canonical current-device DEVICE->KV first-hop sidecar without credential plaintext.
- TVC #377 merged at `72aa78c8f60226621c19d58751ec776f777583f9`; TVC validates that sidecar and remains the single SKAP ciphertext custody writer while emitting a terminal drain receipt with canonical roundtrip eligibility/binding.

## Current .github source

PR #1332 owns runtime continuation and proof convergence. Exact head `f56b06cd35726e17a9e8c90f12ec13f0b058bb66` previously passed all three canonical workflows:

```text
34524596337 Validate organization control plane SUCCESS
34524596356 Deterministic Repository Suite SUCCESS
34524596188 Heartbeat Worker Project SUCCESS
```

Subsequent source now adds the resident orchestration seam and requires a fresh exact-head validation before merge.

### Preferred current-iPhone path

After TVC has admitted one authentic browser-sealed ciphertext, `.github/scripts/continue_device_kv_skap_from_tvc_custody.py` MUST be used. It:

1. validates the Gateway canonical DEVICE->KV sidecar;
2. validates the terminal TVC custody receipt and exact SKAP ciphertext readback;
3. uses the existing `kv-skap` REFERENCE profile for KV->SKAP `VERIFY_SESSION`;
4. emits the chained SKAP->KV reference result;
5. persists and exact-readbacks the returned object at KV;
6. emits the final KV->DEVICE receipt chained to SKAP->KV;
7. materializes the four-leg runtime manifest;
8. runs the fail-closed terminal verifier.

TVC remains the only ciphertext custody writer. The continuation reads already-admitted custody and does not resolve or copy secret material.

### Direct compatibility path

`scripts/consume_kv_skap_custody_materialization_request.py` remains a direct/compatibility path for cases where TVC has NOT already written the same SKAP ciphertext. It MUST NOT be invoked after the terminal TVC custody event for that same packet, because duplicate custody writes are prohibited.

### WorkerCoordinator binding

`workers/run_device_kv_skap_roundtrip_worker.py` now has two fail-closed modes:

- authentic continuation mode: runtime root + canonical Gateway sidecar + terminal TVC drain receipt + canonical StegOS root + output;
- manifest verification mode: runtime root + pre-existing canonical manifest + output.

Partial continuation inputs fail closed. The process adapter allowlist contains only non-secret local evidence/source paths. No token, password, private key, or credential value environment is admitted.

## MyKV relationship

Site MyKV personal-information ingestion is already implemented through DEVICE_KV read/write with exact-readback requirements for canonical Personal KV records. Ordinary personal information belongs in KV. Credential/signing material belongs in SKAP; MyKV may retain only a SKAP reference. This roundtrip child supplies the canonical KV<->SKAP transport/evidence lane needed to complete that separation rather than moving personal records wholesale into SKAP.

## Runtime completion contract

One authentic current-device execution must prove:

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
hosted_runtime_used = false
second_user_operated_device_used = false
terminal state = DEVICE_KV_SKAP_ROUNDTRIP_VERIFIED
```

## Current blockers

```text
AUTHENTIC_CURRENT_DEVICE_FOUR_LEG_INTR_ROUNDTRIP_NOT_YET_OBSERVED
AUTHENTIC_SKAP_KV_RETURN_RECEIPT_NOT_YET_OBSERVED
KV_SKAP_TERMINAL_EXACT_READBACK_NOT_YET_OBSERVED
```

These are now runtime-proof blockers rather than missing-source-design blockers.

## Next

1. Fresh exact-head validation of PR #1332 after WorkerCoordinator continuation wiring/tests.
2. Merge #1332 only on a clean current head.
3. Propagate merged LLM-adapter, TVC, StegOS, and `.github` continuation source to the sovereign resident.
4. Execute one already-authorized, non-destructive current-device roundtrip when the human interaction queue permits the triggering owner action, or consume an already-existing eligible TVC custody event if present.
5. Retain the terminal proof/readbacks and only then close the three runtime blockers.

## Manual work

None at this source/reconciliation stage. Do not request a duplicate credential/ciphertext submission or a second user-operated device.
