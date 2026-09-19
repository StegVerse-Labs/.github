# SV002 Frozen Corpus Materialization Mirror Handoff

Status: ACTIVE
Updated: 2026-09-17

## Task pointer

- Goal Task ID: `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001`
- Parent: `SHWP-SV002-ACTION-TRANSITION-EVIDENCE-001` — decomposed at Goal Prompt Count 20/20
- COSV task vector: `50000000107001`
- Canonical registry shard: `data/canonical-task-records/SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001.json`
- Tracking issue: `StegVerse-Labs/.github#2064`

## Goal

Materialize the complete exact frozen TT/RTG/GTG/AE corpus, build and verify the native SV002 resource bundle with the unchanged production builder, then reuse the already-proven sandbox native adapter/v0.3 exporter/corrected egress/Master Records/origin-return chain. Goal 1 and Goal 2 close only from the complete authentic run.

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

Organization capability snapshot SHA-256 remains pinned at:
`a691449e40e87ffae8f6c51efde915bae1d35e491137aee18a734fc7ad5f2462`.

## Exact bundle invariant

`StegVerse-002/micro-node-runtime/tools/sv002_native_resource_bundle.py` requires for each source:

1. exact frozen commit identity;
2. every non-symlink blob from the frozen Git tree;
3. SHA-256 of every blob in the ordered `source_index`, including non-UTF8 blobs excluded from searchable `files`;
4. canonical `source_sha256` over the complete ordered source index;
5. complete bundle verification before native search/read execution.

A top-read subset, current branch, semantic reconstruction, UTF8-only subset, or synthetic source index is not sufficient.

## Proven sandbox work to reuse, not recreate

The parent established provisional sandbox evidence for:

- executable native replacement adapter with historical Python round-trip runner poison-tested at zero calls;
- hosted/second-machine drift fail-closed;
- native-result-to-v0.3 exporter passing current Master Records reconstruction predicates;
- response publication before `EGRESS_EMITTED`;
- organization-root finalization after actual egress;
- Master Records reconstruction/custody/readback before origin delivery;
- forced response-publication failure producing no false `EGRESS_EMITTED`;
- tampered egress and custody rejection blocking origin delivery.

These remain sandbox/provisional findings and are not authentic production runtime proof.

## Four exact staged TVC requests

The only admitted source-materialization inputs remain:

```text
StegVerse-Labs/TVC/requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-TT.json
StegVerse-Labs/TVC/requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-RTG.json
StegVerse-Labs/TVC/requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-GTG.json
StegVerse-Labs/TVC/requests/private-source-read/SHWP-SV002-FROZEN-CORPUS-AE.json
```

No generic GitHub credential, second source-read implementation, or alternate materializer is permitted.

## Existing TVC runtime chain

The existing TV/TVC-owned runtime path remains:

```text
RT-TVC-PRIMARY-RUNTIME-BINDING-001
-> TVC-PRIMARY-RUNTIME-BINDER-005
-> TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006
-> tvc.primary_runtime_binder.activate
-> existing singleton scripts/tvc_resident_service_self_heal.py --watch
-> existing TVC private-source watcher
-> consume staged immutable requests
```

No second runtime, host, listener, selector, scheduler, WorkerCoordinator, credential route, or user-operated device may be introduced.

## Immutable private-source receipt semantics

TVC main contains:

- `a9c41b7effe90bb09123aef975cb78e30f0af824` — immutable terminal receipt retention and terminal replay suppression;
- `a38d82b0ab997ec98e84f1d48d53a4114f7be4da` — regression coverage.

Terminal COMPLETE receipts are retained at:

```text
/var/lib/stegverse/private-source-read/receipts/by-materialization/<materialization_id>.json
```

Each terminal receipt is bound to request SHA-256 + materialization ID, carries `authorized_exact_sha` and `observed_exact_sha`, uses process-only `SYSTEMD_LOADCREDENTIAL`, exposes no credential value, and cannot be rebound to a different request. Exact terminal replay reuses the immutable receipt without reloading credentials or re-executing the source read.

## 2026-09-17 callable-path repair — supersedes connected-device framing

The previous blocker `EXISTING_EVENT_EPHEMERAL_TVC_RUNTIME_INVOCATION_SURFACE_NOT_CURRENTLY_OBSERVED` is superseded.

Investigation found that StegVerse already had the required generic callable-task machinery:

```text
StegVerse-Healer existing sovereign carrier
-> RT-REUSABLE-TASK-SCHEDULER-001
-> scripts/trigger_reusable_task.py
-> RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001
-> scripts/run_tvc_runtime_boundary_reusable.py
-> RT-TVC-PRIMARY-RUNTIME-BINDING-001
-> existing TVC preflight + activate
-> existing TVC self-heal/private-source path
```

The architecture therefore does not require an idle connected remote-desktop device. The direct device connector is only one possible carrier and is not the definition of task callability.

Two concrete source defects blocked this existing path:

1. `materialize_reusable_task_construct.py` read only the historical aggregate `control/task-vector-index.json`, while the repository already uses canonical `control/task-vector-index.d/*.json` shards. The child COSV `50000000107001` could not therefore be resolved through the generic trigger without rewriting the aggregate.
2. The existing fleet functionalization COSV shard `ORG-GITHUB-FLEET-FUNCTIONALIZATION-001.json` was malformed: it lacked the required shard schema and `vector_state`, causing the deterministic shard suite to fail once this path was exercised.

Repairs merged through `.github` PR #2066 after exact-head validation:

```text
merge commit: a7cc366a7f39bdcfed06bafd693ac0d7170091a7
Deterministic Repository Suite run: 35274133956 = SUCCESS
Organization control validation: SUCCESS
```

The merge:

- makes the generic reusable constructor resolve aggregate + canonical non-conflicting COSV index shards;
- fails closed when a shard disagrees with an aggregate row;
- verifies the referenced task-vector source and exact task/COSV parity;
- registers `SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001` with COSV `50000000107001` through a canonical task-vector record and index shard;
- fixes the pre-existing malformed fleet shard;
- adds regression coverage that constructs the SV002 invocation through `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001` and rejects COSV mismatch.

The existing neutral Healer scheduler was then bound to this Goal through StegVerse-Healer PR #88 after both exact-head `repo-smoke` checks passed:

```text
Healer merge commit: f2e91e1969e0c16fd8347931aca59c10ae6db252
reusable task: RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001
tracking task: SHWP-SV002-FROZEN-CORPUS-MATERIALIZATION-001
COSV: 50000000107001
remote_desktop_required: false
persistent_runner_required: false
second_scheduler_required: false
second_user_operated_device_required: false
network_source_fetch_allowed: false
```

The row is eligible in every UTC hour and uses the scheduler's existing bounded same-slot retry semantics. This is reuse of the already-existing neutral scheduler/Healer carrier, not creation of a standing scheduler dependency for this Goal.

## Current authentic blocker

The callable invocation **source path is now canonical and validated**. The unresolved boundary is authentic runtime consumption of that path:

`NEUTRAL_REUSABLE_TVC_INVOCATION_SOURCE_COMPLETE_RESIDENT_CYCLE_RECEIPT_PENDING`

No retained scheduler/reusable-task receipt for this Goal has yet been observed after the merge. Therefore none of the following may yet be promoted:

- `SERVICE_INSTALLED_VERIFIED`;
- private-source resident-state active;
- TV/TVC credential presence;
- consumption of any of the four staged requests;
- immutable COMPLETE materialization receipts;
- complete frozen native bundle;
- Goal 1 or Goal 2.

Future continuation must inspect the neutral scheduler/reusable-task receipt surfaces first. Do not regress to treating `Remote_Desktop_Commander.list_devices()==[]` as proof that the task is uncallable.

## Required authentic evidence before bundle construction

1. neutral scheduler/reusable-task receipt bound to this Goal/COSV and `RT-TVC-RUNTIME-BOUNDARY-OBSERVATION-001`;
2. authentic TVC `SERVICE_INSTALLED_VERIFIED`;
3. resident-state receipt proving the existing watcher/runtime state without exposing credential value;
4. four immutable private-source COMPLETE receipts, one per staged request;
5. for every request: `authorized_exact_sha == observed_exact_sha == requested exact_sha`;
6. exact materialized checkouts available credential-free to the unchanged native bundle builder.

## Required continuation after all six pass

1. Run unchanged `sv002_native_resource_bundle.py` against all four exact materializations.
2. Verify every ordered source index and `source_sha256`.
3. Verify the complete `stegverse.sv002-native-resource-bundle/v1` bundle.
4. Run the real native action-policy against that complete bundle.
5. Feed that same native execution into the already-proven v0.3 exporter.
6. Publish the correlated response packet; only then finalize `EGRESS_EMITTED`.
7. Run Master Records reconstruction/custody/readback.
8. Deliver the same correlated return to origin only after custody/readback.
9. Close Goal 1 and Goal 2 only from that complete authentic run.

## Manual work

None.


## 2026-09-19 TVC reusable service-delivery carriage correction

The existing neutral Healer/reusable-task path remained callable but its local TVC runner bypassed the released service-delivery leg: after preflight it called `tvc.primary_runtime_binder.activate` directly. That direct call cannot establish the post-#445 invariant requiring a same-service restart correlated to a new startup-source receipt.

The existing `scripts/run_tvc_runtime_boundary_reusable.py` is corrected in place to retain preflight, invoke `StegVerse-Labs/TVC:scripts/install_tvc_primary_runtime_service.py --activate` against the already-local TVC checkout, and then run the existing runtime observer. This follows `RT-TVC-PRIMARY-RUNTIME-BINDING-001`'s already-declared runner templates and creates no second scheduler, selector, runtime, host, listener, credential route, or device dependency.

Authentic runtime consumption remains required; source repair alone does not establish `SERVICE_INSTALLED_VERIFIED` or any frozen-corpus materialization predicate.


The reusable TVC service-delivery carriage correction merged through StegVerse-Labs/.github PR #2222 at `f5c64120d381842db16ca1a5156bb881c8e383f8`. The existing neutral Healer/reusable-task path now reaches the released same-service installer after preflight instead of bypassing it with direct dispatcher activation. Authentic scheduler/reusable-task consumption and the resulting TVC restart/startup receipt remain unobserved.


## 2026-09-19 TVC service-owned preflight correction

After the reusable service-delivery carriage repair, source tracing found that the neutral Healer/reusable runner still executed `tvc.primary_runtime_binder.preflight` before invoking the TVC service installer. That preflight requires `STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY=TV/TVC`, while the neutral Healer carrier intentionally does not mint or inject TV/TVC authority. This created an ambient-authority dependency before the execution path could enter the existing TVC-owned service.

The reusable runner now enters the released `install_tvc_primary_runtime_service.py --activate` path directly after resolving already-local TVC source. The restarted `stegtvc-primary-runtime.service` retains `Environment=STEGTV_PRIMARY_RUNTIME_ACTIVATION_AUTHORITY=TV/TVC`, retains the vault-socket `ExecStartPre`, and invokes `tvc.primary_runtime_binder.activate`, whose existing `task_activate` executes `task_preflight` before serving. The neutral carrier therefore neither bypasses TVC preflight nor manufactures TV/TVC authority; the preflight remains inside its existing authority owner.

No runtime predicate is promoted by this source correction.


## 2026-09-19 strict state-transition dependency correction

The execution chain is now represented as a strict predecessor/successor graph rather than a set of independently satisfiable predicates. Every successor is admissible only after authentic evidence consumes its immediate predecessor state.

The neutral reusable scheduler also no longer reports `ALL_DUE_REUSABLE_TASKS_ADVANCED_TO_COMPLETION_OR_AUTHENTIC_BOUNDARY` unconditionally. A due child in `DEFERRED` or any other non-advanced state keeps the scheduler successor transition inadmissible, clears scheduler completion predicates, records the blocking child state, and returns non-success so the existing reusable trigger retains the boundary instead of projecting a later state.

For this SV002 path, the only currently admissible successor is `REUSABLE_TVC_INVOCATION_OBSERVED`. Restart, loaded-source, self-heal, exact c5e6a793 materialization, Astra, quantum, SV002 runtime activation, and REQUEST_BOUND custody are all explicitly `BLOCKED_ON_PREDECESSOR`.
