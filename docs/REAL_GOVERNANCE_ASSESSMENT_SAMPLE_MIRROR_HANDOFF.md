# Real governance assessment sample (#3393) — canonical handoff

**Goal Task ID:** REAL-GOVERNANCE-ASSESSMENT-SAMPLE-001  
**Canonical owner:** StegVerse-Labs/.github Task Registry (registered by manifest `control/canonical-task-registration-requests/real-governance-assessment-sample-001.json`, PR #3412, merge commit 32f75c5d3a36929b25d37e2109b83b7516d5b252)  
**COSV:** 10500000110000 — derived by `scripts/cosv.py` from the declared `exact_metrics` (lifecycle UNCLAIMED, unassigned_work 5, blocker_count 0); an observation, never an authorization.  
**Registry:** generation 324 row == record; `coordination_state` PROPOSED, `authority_effect` NONE_REGISTRATION_ONLY; `claim_ref` and `fence_ref` null (claim request only).  
**Owner issues:** Parent #3183 · work summary and parallel actions #3393 · handoff integration #3399 · registry mapping and counts #3195.  
**Session Prompt Count:** 3. **Goal Prompt Count:** UNRECONCILED; recoverable lower bound 13 (10 carried forward from earlier sessions + 3 in the originating session; #3195 c6505651966). Registration does not store or reset the count; exact earlier history is reconciled by the Registry owner, not inferred here.  
**Date:** 2026-10-29.

## What registration is, and is not
Registration gives this Goal a canonical identity, a derived COSV and a sealed scope (`control/goal-scope-seals/REAL-GOVERNANCE-ASSESSMENT-SAMPLE-001.json`). It is not worker admission (`ADMIT|UPDATE|RETIRE|BLOCK`), not a WorkerCoordinator claim or fence, not a governed transition, and not source-use, independent-review, publication, customer, price or payment authority. The four DEP-RAS-* dependencies in the manifest stay UNRESOLVED until their owning lanes disposition them.

## Goal
Produce a reproducible real retained-source workflow assessment and, once authorized, a public demonstration, using the existing ERL acquisition and existing publication owners. No new scheduler, host, collector or dependency.

## Completed work (evidence classes preserved)
- Pinned retained ERL cycle: ERL `855c12371ed7c449dec10f6dbd9ff35ac96878bd`, cycle 2026-10-29T05:18:58Z. Eight captures verified against SHA256, size and Git blobs; 24 candidates replayed (11 matches, 13 no-matches); five byte changes versus the prior cycle, zero candidate changes. Historical verification, not fresh collection.
- Consolidated report revision 2: https://github.com/StegVerse-Labs/.github/issues/3396#issuecomment-6502814562 — Markdown SHA256 `983718840ddcd81e0ea298d01359dfa195e0e94cc5580373ffbc505a72cef3b0`. The original PDF and earlier packets are historical; the original no-receipt R1 is withdrawn.
- Packaging correction, edition 2: full eight-source evidence register and 24-row candidate register added; report text unchanged; package ZIP SHA256 `a477580372ba516e3c0bd7164888845c16edc7c1422ad292911d538b5264427f`. A separate analytical reviewer ACCEPTED the packaging correction only (#3397 c6505644583). That is not canonical owner acceptance.
- ERL#245 candidates: runner v2 (c6497048903, patch SHA256 `528abf6fca1b81636417ce9a56a07f04f381d3471d8e6d4516f4e24b13bf9f94`) and the replacement workflow companion (c6500576972, SHA256 `8cfb25f7c5e6e0b6ab59551421aedad9e7a244677293f50a5bd6a9e9796fe934`, supersedes the prior companion; do not stack). Author-side validation only: 20 PASS locally; no CI, runtime or independent sign-off.

## Parallel actions and owners (no claim or fence implied)
| Lane | Owner | Evidence required to close |
|---|---|---|
| #3195 mapping, collision, counts | Registry owner | Scoped reconciliation of cumulative history against the lower bound 13 |
| ERL#245 integrate runner v2 + replacement companion | ERL source holder | Fresh expected head, non-author review, exact-head CI, current-attempt artifact readback |
| ERL#245/#51 extraction, timing, archive controls | ERL source holder | Prepared independently; one integration owner |
| #3394/#3370 source-use and supplement disposition | #3370 commercial holder; source-rights owner | ACCEPT/REVISE/REJECT of c6505537155 against the corrected report, with audience and conditions |
| #3397 independent exact-digest review | Canonical reviewer other than the author | Attributable ACCEPT/REVISE/REJECT bound to report digest, source commit and rendered artifact hashes |
| #3398 accessible rendering and route | Site owner | Publish only after source-use, review and publication authority; live URL, download digest and mobile readback |
| #3399 README and this handoff | .github documentation owner | This file and the README paragraph on main |
| Release and propagation | Site, Publisher, admissibility-wiki, stegguardian-wiki owners | Only after evidenced readiness; separate propagation-verification task |
| Sovereign custody | Native authenticated writer | Exact-byte readback; Drive coordination is not sovereign KV |

Protocol-side work (#3369, #3380, #3403, #3195 protocol rows, #484 pricing inputs) is separate scope and not a prerequisite for #3393.

## Invariants
SKAP Vault inside KV is the only PII and credential store for every user, the ecosystem's own included; the ecosystem holds none (HST citation pending P1 #163). This Goal holds no PII or credentials; sources are public records and no private screenshot or transcript is published. No InTr hop inside an organization; at most two workflows per repository.

## Recovery
Read the Registry row and record, this file, #3393, #3399 and the exact source comments before writing. Inspect owner responses before repeating tests. At a new session the session count resets to 1; preserve cumulative contribution at least 13 and reconcile prior history. No admission, merge of ERL source, independent acceptance, live publication, release or propagation is claimed by this file.
