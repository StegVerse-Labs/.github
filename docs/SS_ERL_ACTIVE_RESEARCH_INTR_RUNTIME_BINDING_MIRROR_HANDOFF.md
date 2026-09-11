# ERL Active-Research Universal InTr Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Goal Task ID

`SS-ERL-ACTIVE-RESEARCH-INTR-RUNTIME-BINDING-001`

Parent goal: `SS-EVIDENCE-COMPARISON-001`

COSV: `40000100100000`

Status: `ACTIVE / CLAIMED_INTEGRATION`

## Purpose

Bind the already-merged ERL active-research Universal InTr intent to the existing sovereign Universal InTr resident execution owner without creating a second runtime owner, dispatcher, scheduler, heartbeat, credential path, or synthetic transport receipt.

## Reconciled canonical owner

GitHub inspection established that `StegVerse-Labs/Executive_Rhetoric_Ledger:active-research-kv-consumer` is an ERL repository-side consumer identity, not an independently authorized resident Universal InTr execution owner.

The existing resident DEVICE_SYSTEM -> KV materialization owner is:

- canonical runtime task: `SHWP-DEVICE-KV-INTR-OBSERVATION-001`
- profiled ingress: `workers/universal_intr_profiled_ingress.py`
- materialization consumer: `scripts/consume_device_kv_intr_materialization_request.py`
- downstream owner: `StegVerse-Labs/continuity-vault-kit#79`
- resident refresh/execute bridge: `scripts/refresh_and_execute_resident_task.py`
- credential authority: `TV/TVC`
- GitHub runtime authority: `NONE`

The existing task explicitly forbids a second runtime owner and requires VERIFIED boundary receipts only after authentic byte receipt/validation.

## Required binding shape

The ERL source intent remains the canonical full path:

```text
EXTERNAL_SYSTEM
-> STEGOS_ECOSYSTEM
-> DEVICE_SYSTEM
-> KV
```

The binding must therefore preserve one packet identity, one operation identity, and the exact acquisition-envelope payload hash across three adjacent authentic hops. It may adapt the final DEVICE_SYSTEM -> KV event to the existing resident owner only after the first two adjacent hops have actually executed and produced their authentic chained receipts.

The adapter must not rewrite the full-path intent into a false one-hop history, and it must not use `build_hop_receipt()` or fixture construction as evidence that runtime transport occurred. Receipt builders remain schema/policy utilities; authentic receipts are emitted only by the observing runtime at the corresponding boundary transition.

## Implementation target

Add a reusable ERL active-research profile to the existing Universal InTr resident ingress/consumer stack rather than creating a new ingress service. The profile must:

1. admit only `stegverse.erl.active-research-intr-binding/v1` / `stegverse.universal-intr-materialization-request/v1` requests whose payload hash matches the exact admitted acquisition envelope;
2. require the canonical path `EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM -> DEVICE_SYSTEM -> KV`;
3. preserve the ERL operation/packet identity and prior-receipt lineage;
4. persist write-once authentic ingress/transition evidence for the first two hops when those bytes actually cross the corresponding resident boundaries;
5. project the terminal DEVICE_SYSTEM -> KV materialization event onto the existing `SHWP-DEVICE-KV-INTR-OBSERVATION-001` / `StegVerse-Labs/continuity-vault-kit#79` owner instead of inventing an ERL runtime owner;
6. retain the three canonical `stegverse.intr.hop_receipt/v1` receipts for ERL consumer verification;
7. keep `request_grants_execution_authority=false`, `claim_or_fence_minted=false`, `authority_transfer=false`, `credential_authority=TV/TVC`, and `github_token_runtime_authority=NONE`;
8. bind terminal transport proof to the existing authentic MyKV provider-write/readback proof without re-running or reclassifying that provider operation.

## Existing proof that must not be repeated

- ERL PR #154 active-research dispatch merged.
- ERL PR #155 acquisition consumer merged.
- ERL PR #156 exact three-hop admission contract merged.
- ERL PR #157 reusable non-authorizing runtime binding merged at `bfb76a068717ff0aaf96c32af97ebcc43324149f`.
- CISA/Iran public-source capture provider write and exact-byte provider readback are already authentic and separate from InTr transport proof.

## Completion predicates

This goal is complete only when:

- the existing resident Universal InTr stack has an ERL active-research profile bound to the canonical owner above;
- exact-head validation passes for the implementation;
- one authentic admitted ERL acquisition envelope traverses all three adjacent boundaries;
- all three real chained receipts are retained and accepted by the merged ERL consumer;
- the terminal KV receipt is bound to the pre-existing authentic provider readback evidence;
- the parent ERL handoff is reconciled with the exact receipt hashes and proof class;
- no hosted/fixture/generated receipt is promoted to runtime evidence.

## Current state

`CANONICAL_RUNTIME_OWNER_IDENTIFIED / SUCCESSOR_RUNTIME_BINDING_TASK_REGISTERED / PROFILE_IMPLEMENTATION_AND_AUTHENTIC_TRAVERSAL_PENDING`
