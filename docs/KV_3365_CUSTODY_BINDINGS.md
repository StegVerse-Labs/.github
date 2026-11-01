# #3365 existing custody bindings and remaining finish-point composition

Status: SOURCE_INSPECTED / OWNER_BINDING_PENDING. Authority effect: NONE.
Observation: 2026-10-29. Labs source `751e6bc9c5feffa501d9e4a733b6c9e79037985c`; CVK source `44e7ae56f4efee0a19dfd3d7db5c524b68adc46b`.

## Existing owner; do not allocate another custody task

The accepted Registry generation 326 / 122 rows identifies `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` as ACTIVE, COSV `10000000100000`. It owns organization receipt replay and related reconstruction, not #3365's migration identity or the authority to write personal source records.

- Owner handoff: [ORGANIZATION_BATCH_CUSTODY_REPLAY_MIRROR_HANDOFF.md](ORGANIZATION_BATCH_CUSTODY_REPLAY_MIRROR_HANDOFF.md).
- Existing owning issue: [#2810](https://github.com/StegVerse-Labs/.github/issues/2810).
- Existing reader repair: [#3376](https://github.com/StegVerse-Labs/.github/pull/3376), observed open at `d810644ddc6ce290dd1a21f75c7c12d8c3fe05df`. Consume that owner's repair; do not fork a competing reader.
- Registry-event custody stays with `TASK-REGISTRY-SOVEREIGN-KV-EVENT-CUSTODY-001`, ACTIVE / COSV `50000000100000`; its event scope is not a personal-document migration.

## Exact source interface

| Surface | Source Git blob | Boundary |
| --- | --- | --- |
| `resident-runtime/organization_custody_readback.py::readback` | `85066f1472af50c5efd9b860c590874e4e7100a8` | Complete organization HEAD/source replay from the declared store; correlation filtering does not shorten the chain validation |
| `scripts/consume_organization_custody_readback_request.py` | `d1158f51ace6bdae80d4f1b2f49c4c16b759a98d` | Existing trusted governed-attempt consumer; a source-tree request alone does not trigger native readback |
| `runtime/kv_receipt_ledgers.py::receipt_on_ledger` in CVK | `25335cc28d54f68a8e340753ce4fac4a1d80ae22` | Membership on the designated KV read-back chain; not source-byte comparison or a corpus inventory |

The custody request schema is `stegverse.organization-custody-readback-request/v1`; its task/COSV are the custody owner's, its mode is `READ_ONLY_ORGANIZATION_CUSTODY_REPLAY`, and it admits 1–16 distinct bounded correlation IDs. Its credential authority stays TV/TVC and `request_grants_authority=false`. It must be bound to the original trusted attempt, predecessor and InTr organization receipts verified by the consumer. Caller-authored origin strings and source commits cannot establish those facts.

The consumer selects `module.org.organization_store()`, the same manifest-declared store as append. Do not supply a decoy root, substitute a GitHub contents response for native custody, or bypass the governed-attempt path. This describes an existing interface; no request was deposited and no invocation was made here.

The reader returns `VERIFIED_LOCAL_READBACK`, complete-chain/source-digest outcomes, HEAD digest, receipt and batch counts, requested correlation IDs, matching transition records and `authority_effect=NONE_READBACK_ONLY`. A verified chain with zero matches does not establish migration custody. A generic match must still bind the migration's actual task, manifest, object revision and transition. The source API does not independently compare arbitrary source/destination file bytes.

Master Records submission/reconstruction fields report downstream evidence. They do not grant an ALLOW or become a new precondition for Organization runtime reality. Preserve the existing separation between original Organization receipts and downstream reconstruction.

## Remaining finite-batch verifier composition

The existing migration source proposal still needs an approved task identity, finite revision batch, named consumers, and a concrete owner-reviewed acceptance entrypoint. Reuse the existing primitives above to verify the applicable original receipt chain, while the migration-specific composition verifies:

1. Exactly the owner-approved source revisions and dispositions; no title/size-based identity collapse or unapproved privacy disclosure.
2. Independently read original source and native destination bytes, exact SHA-256 and byte length, plus revision/provenance binding.
3. Authentic task/manifest-bound provider operation and receipt evidence, correlated to the independently verified native chain.
4. Preserved ORIGINAL/COPY/MIRROR/DERIVED relationships and contradictions; unresolved members keep completion false.
5. Separately manifested named-consumer cutover and any legacy-write retirement after custody; no premature source deletion.

CVK `.stegverse/finish_point_verdict.py` is a test-set selection helper (SELECTED/NOT_SELECTED), not a migration completion verifier. Do not bind the Goal to it because of its filename. CVK's vault-lineage validator remains useful only for its declared lineage subject.

## What is established and what is not

Source ownership, callable signatures and declared evidence boundaries were inspected. No native invocation, migration registration, claim/fence, source batch approval, provider write, byte readback or sovereign coordination-directory mutation was performed. No new runtime, writer, ledger, credential path, device requirement or authority is proposed.

The separate KV-SKAP registration plan reported at generation 326 is evidence for that Goal only. Neither its proposed vector nor its adjacency ruling or ALLOW may be inserted into #3365's request.

Continue through [the owner inputs](KV_3365_REGISTRATION_INPUTS.json) and [migration handoff](PERSONAL_ECOSYSTEM_KV_MIGRATION_MIRROR_HANDOFF.md); original Registry owner decisions precede a real candidate plan/apply/verify.
