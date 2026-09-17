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

## 2026-09-17 TVC resident invocation reconciliation

Four exact immutable private-source requests are staged in `StegVerse-Labs/TVC` for this Goal and remain the only admitted source-materialization inputs:

```text
requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-TT.json
requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-RTG.json
requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-GTG.json
requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-AE.json
```

The existing runtime sequence is already implemented and must be reused unchanged:

```text
RT-TVC-PRIMARY-RUNTIME-BINDING-001
-> TVC-PRIMARY-RUNTIME-BINDER-005
-> TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006
-> tvc.primary_runtime_binder.activate
-> existing singleton scripts/tvc_resident_service_self_heal.py --watch
-> existing TVC private-source watcher
-> consume staged immutable requests
```

`TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006` is released to existing TV/TVC runtime authority; source/preflight completion is not runtime execution evidence. `TVC-RESIDENT-SERVICE-SELF-HEAL-001` remains `SOURCE_REBIND_VALIDATED_AUTHENTIC_HOST_EXECUTION_PENDING` and its authentic host receipt remains unobserved.

The generic reusable-task trigger can execute `RT-TVC-PRIMARY-RUNTIME-BINDING-001` only from an already-materialized admitted resident source/runtime context. The current direct resident connector exposes no online device. The canonical resident dispatcher does not register a dedicated selector for this child Goal or for `TVC-RESIDENT-SERVICE-SELF-HEAL-001`; adding one would create a new execution path and is prohibited by this Goal.

Therefore the current blocker is:

`EXISTING_EVENT_EPHEMERAL_TVC_RUNTIME_INVOCATION_SURFACE_NOT_CURRENTLY_OBSERVED`

This is not permission to add a listener, worker, scheduler, host, generic GitHub credential, second device, or alternate source-read implementation. The next authentic transition must consume the already-existing TV/TVC runtime binding/self-heal path and emit the retained resident receipts.

## 2026-09-17 immutable receipt retention repair

After the latest runtime re-observation, TVC main added a narrow source repair for the existing private-source resident path:

- `a9c41b7effe90bb09123aef975cb78e30f0af824` — preserve immutable private-source receipts and suppress terminal replay;
- `a38d82b0ab997ec98e84f1d48d53a4114f7be4da` — regression coverage for replay suppression, immutable receipt retention, and materialization-ID request binding.

The existing resident executor now retains terminal COMPLETE receipts under:

```text
/var/lib/stegverse/private-source-read/receipts/by-materialization/<materialization_id>.json
```

Each immutable receipt is bound to the exact request SHA-256 and materialization ID. A terminal replay with the same request reuses the immutable receipt without reloading credentials or re-executing the source read; a different request attempting to reuse the same materialization ID fails closed. The receipt continues to carry `authorized_exact_sha`, `observed_exact_sha`, process-only `SYSTEMD_LOADCREDENTIAL` transport, `credential_value_exposed=false`, and no persisted credential value.

This repair strengthens retention and exactly-once evidence for the four staged SV002 requests once authentic resident execution occurs. It does not prove that the resident service is installed, that a credential is present, that the four requests have been consumed, or that any frozen source has been materialized. The current direct resident surface remains unavailable and no authentic terminal receipt has yet been observed for this Goal.

Required authentic receipts before bundle construction:

1. TVC service installation state `SERVICE_INSTALLED_VERIFIED`;
2. resident-state receipt proving the existing watcher/runtime state without reading credential value;
3. four private-source execution/materialization receipts bound one-to-one to the staged requests;
4. for each request, `authorized_exact_sha == observed_exact_sha == requested exact_sha`;
5. exact materialized checkout available credential-free to the unchanged SV002 native resource-bundle builder.

No Goal 1/Goal 2 closure, bundle verification, or production execution claim is permitted before those predicates are observed.

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
