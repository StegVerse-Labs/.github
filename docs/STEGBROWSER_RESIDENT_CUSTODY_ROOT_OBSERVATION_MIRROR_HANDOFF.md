# StegBrowser Resident Custody Root Observation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Parent/decomposed-from: `STEG-BROWSER-AUTHENTIC-RUNTIME-RECEIPT-OBSERVATION-001`
- Issue: `StegVerse-Labs/.github#1860`
- COSV: `40000100100000`
- Canonical task record: `data/canonical-task-records/STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001.json`
- Successor remediation: `STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001` / `StegVerse-Labs/.github#1866`
- Successor handoff: `docs/STEGBROWSER_RUNTIME_MATERIALIZATION_REMEDIATION_MIRROR_HANDOFF.md`
- Status: `ACTIVE / CHECKED_OUT / SUCCESSOR_REMEDIATION_BOUND`
- External/second user-operated device required: `false`

## Why this exists

`STEG-BROWSER-AUTHENTIC-RUNTIME-RECEIPT-OBSERVATION-001` reached the Goal Prompt Count `20/20` boundary with canonical source/configuration state verified, but no authentic resident custody root or retained StegBrowser runtime-consumption receipt was observed. The next separable defect is the absence of an authenticated resident-root observation that can be classified by the existing non-authorizing receipt reachability verifier.

## Current inherited evidence

- `.github#1857` remains the parent authentic-runtime-receipt observation issue.
- Parent handoff: `docs/STEGBROWSER_AUTHENTIC_RUNTIME_RECEIPT_OBSERVATION_MIRROR_HANDOFF.md`.
- Parent first unresolved predicate: `CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`.
- Required retained receipt remains `receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json`.
- `StegVerse-Healer` schedule binding already enables `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` hourly through the existing neutral scheduler carrier with no second scheduler or second user-operated device.
- `.github#1862` merged the successor handoff and task record as commit `b7d0ebd5de207c3db0989d0017ebc759304cad11` without claiming runtime completion.
- `.github#1863` later merged `STEGAGENTS-GOVERNED-RUNTIME-001` binding to this same resident-root owner as commit `afa6ec5defc24a920b2dc5e9d3d46cbe24e79549`; that PR explicitly left all runtime substrates pending because no authentic resident custody root was observable.
- `.github#1864` classified the available evidence as `RESIDENT_CUSTODY_ROOT_NOT_OBSERVED` and merged as `e95af1cf5c2449480cdc1b4eba7003c3ba2d39f3`.
- `StegVerse-Healer#81` merged as `b7d37a91fa464a716a85c0a8a28cffd6e5022fb6` after exact-head Test Readiness run `34880822258` passed for head `44f69f236f90bc000446ad15cc082cef244f5284`.
- `.github#1866` now owns the single bounded runtime-materialization remediation path for the remaining post-repair packet observation gate.

## Prompt 2/20 repair — Healer resident-root observation packet

Classification transition: `BIND_RUNTIME_MATERIALIZATION_REMEDIATION -> OBSERVE_RESIDENT_CUSTODY_ROOT`

Implemented source-side repair:

```text
StegVerse-Labs/StegVerse-Healer#81
StegVerse-Labs/StegVerse-Healer@b7d37a91fa464a716a85c0a8a28cffd6e5022fb6
```

The existing Healer neutral reusable-task carrier now emits a structured, non-authorizing `resident_custody_root_observation` packet. The packet is task-bound to `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`, COSV-bound to `40000100100000`, and reports observed/missing/invalid/ambiguous resident-root state from the existing `STEGVERSE_HEARTBEAT_ROOT` / canonical local runtime discovery path.

The packet preserves:

- GitHub runtime authority: `NONE`.
- Credential authority: `TV/TVC`.
- Healer role: `SCHEDULING_AND_INVOCATION_TRANSPORT_ONLY`.
- No second scheduler.
- No dispatcher or runtime-plane creation.
- No WorkerCoordinator bypass.
- No provider authority.
- No second user-operated device.

This repair does not authenticate a current resident root by itself. It only ensures the next authentic Healer carrier cycle can expose the exact root-observation classification needed by this goal.

## Prompt 4/20 remediation binding — runtime-materialization successor

Because an authentic root remains unobserved after classification and because the source-only Healer packet repair still requires post-repair carrier observation, remediation is bound to exactly one successor:

```text
STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001
StegVerse-Labs/.github#1866
```

The successor adds a canonical handoff, task record, and dry-run/non-authorizing evidence-predicate surface. It does not add a second scheduler, dispatcher, credential path, GitHub authority path, runtime plane, MIR-specific transport, or second user-operated device.

## First unresolved predicate

```text
RESIDENT_CUSTODY_ROOT_AUTHENTICALLY_OBSERVED_FOR_STEGBROWSER
```

## Required next observation surface

Observe the post-merge Healer carrier output from the existing resident path and bind its `resident_custody_root_observation` packet. If the packet state is `RESIDENT_CUSTODY_ROOT_OBSERVED`, run the existing non-authorizing classifier against that exact root and classify:

```text
<resident-root>/receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
<resident-root>/receipts/sovereign-host/stegbrowser-runtime-consumption-evidence-custody.latest.json
<resident-root>/receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
<resident-root>/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
```

The `.github` verifier remains non-authorizing:

```text
scripts/check_stegbrowser_runtime_consumption_receipts.py
```

It may classify only an existing resident custody root as missing, invalid, or valid/bindable.

## Canonical continuation

```text
Task Registry CONTINUE
-> STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001
-> STEG-BROWSER-RUNTIME-MATERIALIZATION-REMEDIATION-001 while root observation remains post-repair pending
-> standing Healer resident scheduler carrier
-> neutral RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
-> emitted resident_custody_root_observation packet
-> observed resident custody root, if packet state proves it
-> non-authorizing exact receipt reachability classification
-> parent predicate CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED when retained receipt is present
-> WorkerCoordinator claim/fence evidence
-> Interlock/InTr admission evidence
-> TVC source-promotion consumption evidence
-> pinned TVC materialization/restart evidence
-> immutable observer / OWNER_INGRESS_READY evidence
-> Master Records custody/reconstruction evidence
```

## Required execution discipline

1. Reuse only the existing Healer resident scheduler carrier and neutral `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` path.
2. Do not introduce a StegBrowser-specific scheduler, dispatcher, transport, credential route, GitHub authority path, runtime plane, or second user-operated device.
3. Treat source/configuration, CI success, PR merge state, and GitHub artifacts as non-authorizing context only.
4. If no resident root is observed, bind the emitted packet state as the next exact defect.
5. If multiple roots are observed, record `RESIDENT_CUSTODY_ROOT_AMBIGUOUS` with exact paths/evidence refs.
6. If a root is observed but required receipt paths are missing or invalid, record the exact missing/invalid paths and keep the parent completion predicate unresolved.
7. If the required retained receipt is valid/bindable, return to the parent completion chain and continue with WorkerCoordinator, Interlock/InTr, TVC, observer, and Master Records evidence checks.

## Authority invariants

- Task Registry: coordination only.
- Healer carrier / neutral reusable scheduler: scheduling and invocation transport only.
- WorkerCoordinator: claim/fence authority.
- Interlock/InTr: governed transition authority.
- TV/TVC: credential/provider authority.
- KV/SKAP Vault: user-verification/custody authority.
- Master Records: observed-reality/reconstruction authority.
- GitHub/CI: source validation/evidence transport only; runtime authority `NONE`.

## Completion predicate

Complete this successor only when a resident custody root is authentically observed and the StegBrowser retained receipt reachability state is classified with exact paths and evidence hashes, or when root absence/ambiguity/invalidity is bound to a further runtime-materialization remediation task with concrete evidence. `.github#1866` is now the single bounded remediation owner for the current post-repair packet observation gate.

This task does not by itself complete the full parent runtime-consumption chain unless the parent predicates are also satisfied by authentic retained evidence.

## Current state

`ACTIVE / CHECKED_OUT / SUCCESSOR_REMEDIATION_BOUND / HEALER_RESIDENT_ROOT_OBSERVATION_PACKET_REPAIR_MERGED / POST_REPAIR_HEALER_CARRIER_PACKET_OBSERVATION_PENDING / CANONICAL_WORK_RECEIPT_NOT_CLASSIFIED / RUNTIME_CONSUMPTION_NOT_CLAIMED / REMOTE_DEVICE_NOT_REQUIRED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.


## Endpoint-binding terminal intake — 2026-09-19

`MASTER-RECORDS-STEGBROWSER-ENDPOINT-BINDING-001` is retired at Goal Prompt 20 with no runtime completion claim. Its unresolved `RESIDENT_REQUEST_DISPATCH_VISIT` predicate is bound here, under the unchanged global/root-observation/materialization owner chain. This is an intake into the existing task and issue #1860, not a new successor, request, invocation, or authority transfer. The retired Goal's `runtime_evidence_terminal_prompt20` and canonical handoff retain the exact immutable invocation, six-field retention seam, Prompt 15 correction, and downstream custody predicates.

Require the authentic exact Healer outcome and six retention fields, with exactly one `packet_state=RESIDENT_CUSTODY_ROOT_OBSERVED` root, before running the existing non-authorizing classifier. Preserve the checkpoint/outer-envelope distinction documented by the retired Goal. Only then evaluate WorkerCoordinator, Interlock/InTr, and the immutable runtime tuple in order, requiring Master Records RECORDED, required-evidence validation PASS, reconstruction PASS, and exact digest equality. Current runtime predicates remain unproven. No connector-device gate or additional execution path is introduced.
