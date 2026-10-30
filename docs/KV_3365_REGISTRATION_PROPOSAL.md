# #3365 migration registration proposal

Status: OWNER_REVIEW_PROPOSAL_ONLY. Goal Task ID and COSV: UNASSIGNED.
Owner coordination: [#3365](https://github.com/StegVerse-Labs/.github/issues/3365), [Registry #3195](https://github.com/StegVerse-Labs/.github/issues/3195).
Authority effect: NONE. This document and its JSON companion are not registration manifests.

## Current accepted source

Pinned main: `0fff5f557e8cec837ebb6da413ec3ec70d5cc562`.
Registry blob: `ea0c6d61881da8b19398e7becbb62d9e727a4379`.
Generation **322**, **120** aggregate rows, **214** task shards. PR #3373 is merged.
The one committed registration request is for EC9; it does not bind #3365.
This supersedes the generation-321 / zero-request observations in the earlier packet.
PR #3380 is still open at `42ea6584059f755e53b500cfaca683fe87a9581d`; re-read accepted state before a new transition.

The complete aggregate was read by the Git blob endpoint. For large files whose contents response is empty, resolve the exact blob from the current tree and fetch that blob; an empty contents response is not an empty Registry.
No aggregate #3365 reference was found. This is not full semantic candidate collision clearance.

## Proposed ownership

Complete one finite, owner-approved source-revision batch of StegVerse ecosystem material from personal Drive into native ecosystem KV custody, retaining source relationships and exclusions, exact bytes and task-bound receipts, then reconcile specifically named consumers. A Drive-to-Drive copy alone does not establish native custody, regardless of the existing endpoint's backing provider.

The proposed components are source classification, the per-object migration register and named-consumer cutover reconciliation. This describes a bounded consumer of existing capabilities, not a new writer or authority. Preserve genuine shared components and dependencies during collision evaluation; changing labels to hide overlap is prohibited.

Existing owners retain Registry allocation/events, WorkerCoordinator claim/fence, CVK provider execution and ledger reading, TVC/SKAP custody and credentials, SDK/InTr admission, organization-ledger append, and general WorkSpace/device continuity. CVK #191's closed historical import scope explicitly excluded migration; do not reopen it by borrowing its identity. Org #167's KV-SKAP Goal and EC9's new registration are separate.

The complete review inputs are in [KV_3365_REGISTRATION_INPUTS.json](KV_3365_REGISTRATION_INPUTS.json). Null identity/COSV/verifier values are intentional and prevent this proposal from being mistaken for the sole executable registration input.

## Decisions needed from the existing owner

| Decision | Proposed basis | Required retained output |
| --- | --- | --- |
| Identity | NEW_IDENTITY only if no exact existing migration identity applies | Canonical proposed identity and truthful parent/root lineage, or exact existing shard |
| Authority | Existing registration procedure and task-specific owner scope | Original applicable authority disposition; no borrowed EC9 approval |
| Scope | Finite revision set, privacy classifications and named consumers | Owner-approved batch/consumer evidence through private locators |
| Finish point | Compose existing receipt verification with byte/provenance and cutover checks | Actual executable verifier path and source pin, with negative cases |
| COSV | Evidence-backed exact metrics | Native derived vector; no manually selected COSV |
| Collision | Full current aggregate and owner-held shard guards | Candidate disposition and exact owner resolutions |

EXISTING_IDENTITY only restores an existing shard missing from the aggregate; it does not extend an already-registered Goal. The registration contract remains SOURCE_IMPLEMENTED_PROPOSED, but that label alone cannot justify a blanket halt: EC9's separately evidenced source registration is now on main. Its result does not authorize this migration.

## Verifier source inspection

CVK source was read at `b1a66008dccad0d301a7e892e6619f47002ec26d`:

- `runtime/kv_receipt_ledgers.py::receipt_on_ledger` verifies membership in the designated read-back chain when invoked through the authentic read path. It does not inventory or compare a migration batch. A caller-supplied cached/test read result must not become an independent source of authority.
- `runtime/task_registry_event_sovereign_kv_binding.py::validate_vault_lineage_custody_result` binds a provider WRITE to vault-lineage readback and access-layer evidence. Its subject is vault lineage, not an arbitrary personal-document corpus.
- `runtime/kv_provider_operation_store.py` persists requests/results; its module expressly does not access remote storage or move data.

These are reusable primitives, not a complete migration finish point. Do not bind one by name and claim the whole Goal is verifiable. The actual verifier must cover the finite owner-approved revision set, exact source/destination byte length and SHA-256, native receipt authentication and task/manifest binding, provenance contradictions, exclusions, and named-consumer transitions. Unknown/unresolved entries keep completion false. Synthetic tests and boolean ALLOW fields cannot establish custody.

The latest source owner [census](https://github.com/StegVerse-Labs/.github/issues/3365#issuecomment-6485704699) reports 180 personal and 209 organizational files, with REVIEW_HOLD classification and text-view divergences. That is reported source evidence, not independently repeated here, not 389 approved transfers, and not byte-equivalence proof. Keep private IDs and contents off public review surfaces.

## Original transition sequence

1. Existing Registry owner resolves and records the table above, including truthful scope and the testable finish point.
2. Build one `stegverse.canonical-task-registration-request/v1` at `control/canonical-task-registration-requests/<request_id>.json`; derive its exact scope digest and declared metrics.
3. At a fresh accepted generation/head, run `scripts/canonical_task_registration_transition.py plan`. Retain the original candidate collision disposition.
4. Resolve hard collisions through their owners. `scripts/adjacency_ruling.py` can clear only recomputed COORDINATE_CONVERGENCE, never STOP_COLLISION; pin finish-point imports/consumed source and protect owner paths.
5. Execute authorized native apply/verify, inspect the five derived surfaces and required exact-head checks, and integrate through the protected owner path. Registration is coordination only; it does not itself append an organization receipt.
6. Obtain actual task admission and WorkerCoordinator claim/fence through the existing chain, then manifested CVK write and independent readback. Consumer cutover follows verified custody.

No valid #3365 registration manifest presently exists in this proposal. No plan/apply/verify, claim/fence or provider execution has been performed for #3365 here. An intentionally malformed request would merely manufacture a schema refusal and is not the next useful operation.

## Documentation and continuity

[Dedicated migration handoff](PERSONAL_ECOSYSTEM_KV_MIGRATION_MIRROR_HANDOFF.md).
[Current overarching coordination handoff](CANONICAL_WORK_COORDINATION_SYSTEM_MIRROR_HANDOFF.md).
This source-review proposal changes no canonical task row, task vector, scope seal, worker record, runtime or credentials. Until protected integration, these documents are branch proposals, not main's canonical state.

Session Prompt Count: 2. Cumulative Goal Prompt Count: UNVERIFIED; do not borrow the parent coordination Goal's exhausted budget or reset the migration's history.
Manual user work: None. Existing owner review is requested through the issues.


## 2026-10-29 continuation: accepted generation 326 and custody owner mapping

Live main `751e6bc9c5feffa501d9e4a733b6c9e79037985c` has Registry generation **326**, **122** rows, **215** task shards, aggregate blob `96f4f1a9212cdda301a05c9075e0e5b09735ba83`. No aggregate #3365 reference or migration registration request was found. The two committed requests belong to EC9 and the assessment Goal. Historical generation-322 counts above are retained as their dated observation.

PR #3390's prior exact head `5da2cd7c82ed1382143815b0de9dd7391863df57` completed all six returned check runs successfully, including ratchet; no submitted review or owner response to its decision table was present at this read. That old-head CI is not validation of this new revision.

[Existing custody binding analysis](KV_3365_CUSTODY_BINDINGS.md) identifies the ACTIVE `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` owner and the precise reader/consumer boundaries. Its identity and the separate KV-SKAP plan cannot register #3365. CVK advanced to `44e7ae56f4efee0a19dfd3d7db5c524b68adc46b`; its test-set finish-point selector is not batch completion evidence. The full migration verifier, identity/authority, approved private batch and metrics still need original-owner resolution. Session Prompt Count: 3; cumulative Goal count remains UNVERIFIED, without reset. No native plan/apply/verify or KV write/readback is claimed.
