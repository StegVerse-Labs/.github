# SV002 Frozen Corpus Materialization Mirror Handoff

Status: ACTIVE
Updated: 2026-09-17

## Task pointer

- Goal Task ID: `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001`
- Parent: `SHWP-SV002-ACTION-TRANSITION-EVIDENCE-001` — decomposed at Goal Prompt Count 20/20
- COSV task vector: `50000000107001`
- Canonical registry shard: `data/canonical-task-records/SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001.json`
- Tracking issue: `StegVerse-Labs/.github#2064`

## Sole unresolved blocker inherited from parent

The parent sandbox proved the provisional execution/custody chain but could not close Goal 1 or Goal 2 because the complete frozen TT/RTG/GTG/AE corpus was not byte-materialized locally.

`StegVerse-002/micro-node-runtime/tools/sv002_native_resource_bundle.py` requires, for each pinned Git tree:

1. exact frozen commit identity;
2. every blob from `git ls-tree -r` except rejected symlinks;
3. SHA-256 of every blob included in a canonical `source_index` even when the blob is non-UTF8 and excluded from searchable `files`;
4. canonical `source_sha256` over the complete ordered source index;
5. complete bundle verification before search/read execution.

Therefore a top-read subset, current default branch, semantic reconstruction, or UTF8-only subset is not sufficient.

## Frozen source identities

```text
TT
  commit: ab60b42934222a2cb5335a5a8194f258a491fc57
  tree:   173e2b6f8b75a8336144b16f36f5270d6bd741ea

RTG
  commit: ca69954cb3dc4ad073c9244e003bc8f0ef3837e2
  tree:   22e87231234e396476ba5af2dc0416462904613b

GTG
  commit: 8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225
  tree:   b01735eaf44b7f1c4bff59c3ac394d2113363579

AE
  commit: 53c8eedddc4e54d8fa0660039d65ab9ac63057a1
  tree:   03643ce2b626f0813ab74707359f2219e9e04551
```

The organization capability snapshot remains pinned separately at SHA-256 `a691449e40e87ffae8f6c51efde915bae1d35e491137aee18a734fc7ad5f2462`.

## Tool-surface finding at decomposition

The connected GitHub source can:

- inspect the exact pinned commits;
- enumerate recursive Git trees;
- fetch individual Git blobs;
- inspect existing workflow runs and download retained workflow artifacts.

The available surface does not expose:

- a repository archive/tarball materialization action into the sandbox filesystem;
- a bulk multi-blob download action;
- a workflow-dispatch action that could create a new exact-source packaging run.

Existing retained bundle-validation workflow artifacts contain readiness receipts only, not the frozen source corpus.

This is a source-materialization limitation only. GitHub runtime authority remains `NONE`.

## Proven sandbox work to reuse, not recreate

The parent established provisional sandbox evidence that must be consumed as prerequisite work rather than reimplemented:

- executable native replacement adapter selects the released native path and poison-tests the historical Python round-trip runner at zero calls;
- hosted/second-machine drift fails closed;
- native-result-to-v0.3 exporter produces the canonical transition/evidence artifact structure and passes the current imported Master Records reconstruction predicates;
- `EGRESS_EMITTED` was corrected to occur only after the correlated response packet is actually published;
- organization-root finalization occurs after egress;
- Master Records reconstruction/custody/readback occurs before origin delivery;
- forced response-publication failure emits no false `EGRESS_EMITTED`;
- tampered egress and custody rejection fail closed before origin delivery.

These are sandbox/provisional findings only and are not authentic production runtime proof.

## Required continuation

1. Materialize every blob represented by each of the four frozen tree identities.
2. Preserve exact blob bytes, modes, and paths; reject symlinks exactly as the builder does.
3. Reconstruct each ordered source index and `source_sha256` exactly.
4. Build and verify the complete `stegverse.sv002-native-resource-bundle/v1` bundle with the existing production builder semantics.
5. Run the real native action-policy against that complete bundle.
6. Feed that same native execution into the already-proven v0.3 exporter.
7. Publish the correlated response packet, then and only then finalize `EGRESS_EMITTED`.
8. Run actual Master Records reconstruction/custody/readback.
9. Deliver the same correlated return to origin only after custody/readback.
10. Close Goal 1 and Goal 2 only from that complete run.

Do not substitute current-branch search, a partial corpus, fixture reads, synthetic source indexes, or the historical Python principal.

## Manual work

None.
