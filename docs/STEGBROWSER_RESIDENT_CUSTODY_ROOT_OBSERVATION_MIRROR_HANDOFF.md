# StegBrowser Resident Custody Root Observation Mirror Handoff

Updated: 2026-09-14

## Task pointer

- Goal Task ID: `STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001`
- Parent/decomposed-from: `STEG-BROWSER-AUTHENTIC-RUNTIME-RECEIPT-OBSERVATION-001`
- Issue: `StegVerse-Labs/.github#1860`
- COSV: `40000100100000`
- Canonical task record: `data/canonical-task-records/STEG-BROWSER-RESIDENT-CUSTODY-ROOT-OBSERVATION-001.json`
- Status: `ACTIVE / CHECKED_OUT`
- External/second user-operated device required: `false`

## Why this exists

`STEG-BROWSER-AUTHENTIC-RUNTIME-RECEIPT-OBSERVATION-001` reached the Goal Prompt Count `20/20` boundary with canonical source/configuration state verified, but no authentic resident custody root or retained StegBrowser runtime-consumption receipt was observed. The next separable defect is not another source repair. It is the absence of an authenticated resident-root observation that can be classified by the existing non-authorizing receipt reachability verifier.

## Current inherited evidence

- `.github#1857` remains the parent authentic-runtime-receipt observation issue.
- Parent handoff: `docs/STEGBROWSER_AUTHENTIC_RUNTIME_RECEIPT_OBSERVATION_MIRROR_HANDOFF.md`.
- Parent first unresolved predicate: `CANONICAL_WORK_RESIDENT_CONSUMPTION_OBSERVED`.
- Required retained receipt remains:

```text
receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
```

- `StegVerse-Healer` schedule binding already enables `RT-STEGBROWSER-RUNTIME-CONSUMPTION-001` hourly through the existing neutral scheduler carrier with no second scheduler or second user-operated device.
- Latest referenced Healer main push run `34873584233` was `Test Readiness`, head `41740a6468f7d801b1cad492352c9fc77941fb92`, conclusion `success`, artifacts `0`. It is validation-only and does not prove runtime consumption.

## First unresolved predicate

```text
RESIDENT_CUSTODY_ROOT_AUTHENTICALLY_OBSERVED_FOR_STEGBROWSER
```

## Required observation surface

A current resident custody root must be observed by retained runtime marker/receipt evidence. The observation must not rely on GitHub source state, PR merge state, workflow success, workflow artifact presence, or a synthetic local checkout.

Candidate exact receipt path after root observation:

```text
<resident-root>/receipts/sovereign-host/canonical-work-stegbrowser-runtime-consumption-request-consumption.latest.json
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
-> standing Healer resident scheduler carrier
-> neutral RT-STEGBROWSER-RUNTIME-CONSUMPTION-001
-> observed resident custody root
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
4. If no resident root is observed, record `RESIDENT_CUSTODY_ROOT_NOT_OBSERVED` as the next exact defect.
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

Complete this successor only when a resident custody root is authentically observed and the StegBrowser retained receipt reachability state is classified with exact paths and evidence hashes, or when root absence/ambiguity/invalidity is bound to a further runtime-materialization remediation task with concrete evidence.

This task does not by itself complete the full parent runtime-consumption chain unless the parent predicates are also satisfied by authentic retained evidence.

## Current state

`ACTIVE / CHECKED_OUT / DECOMPOSED_FROM_STEGBROWSER_AUTHENTIC_RUNTIME_RECEIPT_OBSERVATION_AT_PROMPT_20 / RESIDENT_CUSTODY_ROOT_NOT_OBSERVED / CANONICAL_WORK_RECEIPT_NOT_CLASSIFIED / RUNTIME_CONSUMPTION_NOT_CLAIMED / REMOTE_DEVICE_NOT_REQUIRED / NO_SECOND_USER_OPERATED_DEVICE`

## Manual work

None.
