# Public Wiki Governed Submission Publication Mirror Handoff

Status: ACTIVE — CANONICAL_REGISTRATION_IN_PROGRESS  
Task ID: `PUBLIC-WIKI-GOVERNED-SUBMISSION-PUBLICATION-001`  
COSV ID: `71000000100100`

## Goal

Connect the already-existing public External Chat compatibility and delegated-review lifecycle to the already-separated publication candidate, then continue that exact object through the canonical governance and custody path before any wiki mutation.

Required lineage:

```text
public submission
-> compatibility receipt
-> cooperative review package
-> delegated review/correction receipt
-> external_framework_wiki_publication_transition candidate
-> SDK/manifest ingress
-> Interlock/InTr governed publication decision
-> Master Records RECORDED + reconstruction PASS + required-evidence PASS + exact receipt digest equality
-> Publisher mutation
-> repository mutation receipt retained/reconstructable
```

## Existing contract recovered

Admissibility already defines `external_framework_wiki_publication_transition` with:
- `ALLOW_PUBLICATION_CANDIDATE`
- `DENY_PUBLICATION`
- `REVIEW_REQUIRED`

The schema deliberately requires `publication_executed=false`, and the validator requires a separate repository mutation. That boundary is preserved.

The existing doctrine assigns:
- SDK: declaration/manifest and authority-transition ingress;
- Interlock/InTr: governed transition decision path;
- Master Records: retained custody and deterministic reconstruction, without minting authority;
- Publisher: consequential publication enforcement;
- Site/wiki surfaces: public projection only.

## Non-negotiable authority rules

1. A submitter can propose state but cannot write wiki state.
2. `ALLOW_PUBLICATION_CANDIDATE` is not publication authorization.
3. No Publisher mutation may occur before exact Master Records closure of the governed decision.
4. `DENY_PUBLICATION` and `REVIEW_REQUIRED` must produce zero repository mutation.
5. Publisher must bind its mutation receipt to the exact candidate, governed decision receipt, Master Records closure, target repository, target path, and resulting commit/blob identity.
6. Public visibility, compatibility analysis, review acknowledgement, and reconstruction are not publication authority.
7. No new scheduler, runtime, dispatcher, WorkerCoordinator, custody store, authority plane, credential path, or second user-operated device is introduced.

## First implementation target

Admissibility Wiki is the first end-to-end target because it already owns the candidate schema and review-packet validator.

The first missing seam to implement is a deterministic conversion from the existing publication-transition candidate into the existing generic SDK manifest ingress contract without changing the meaning of `publication_executed=false`. The manifest must preserve exact source/correction/package hashes, target path, decision, and publisher reference.

After SDK ingress, reuse existing Interlock/InTr and canonical Master Records predecessor-closure requirements. Only an exact retained governed closure may be presented to Publisher.

## Reuse target

The target profile must be repository/path scoped rather than Admissibility-specific so the same governed mechanism can later serve:
- StegGuardian Wiki;
- StegTalk Wiki;
- future public StegVerse knowledge surfaces.

Repository-specific policy may narrow allowed paths and content classes, but must not create an alternate authority path.

## Completion evidence

Completion requires one authentic Admissibility publication traversing the complete chain and proving:
- no direct submitter mutation;
- governed ALLOW predecessor retained/reconstructable in Master Records;
- exact Publisher mutation bound to that closure;
- mutation receipt retained/reconstructable;
- negative controls for DENY and REVIEW_REQUIRED produce zero mutation;
- reusable target-profile conformance for at least Admissibility, StegGuardian, and StegTalk.

Source implementation alone is not runtime completion.

## Execution-substrate registration disposition

The current canonicalization/implementation phase does not execute the governed runtime chain, so all six canonical execution substrates are `NOT_APPLICABLE` for this registration phase, with no selected substrate, `external_device_required=false`, `second_user_operated_device_allowed=false`, and `authority_effect=NONE`. This satisfies the runtime-capable Task Registry invariant without inventing runtime evidence or changing the later WorkerCoordinator/Interlock/InTr execution contract. Before authentic runtime execution, the canonical record must be reconciled to the actually admitted existing substrate rather than treating this source-phase disposition as runtime authority.
