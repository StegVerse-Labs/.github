# HIL Portable iPhone WorkerCoordinator Package Mirror Handoff

Updated: 2026-09-08
Repository: `StegVerse-Labs/.github`
Parent task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
COSV: `50000000105000`
Canonical runtime issue: `#246`
StegOS native materialization source: `StegVerse-Labs/StegOS@efc9d5e1e8140759a5f971484ae593cf545b9203`
State: `IMPLEMENTATION_STARTED / PORTABLE_HIL_CHECKOUT_PACKAGE_NOT_YET_RELEASED`
Authority effect: `NONE_SOURCE_PACKAGE_ONLY`

## Purpose

Provide the existing canonical portable WorkerCoordinator checkout module with an exact HIL task package so `CURRENT_USER_IPHONE` can obtain a fresh HIL claim/fence locally without another machine and without moving claim/fence authority into StegOS.

The portable checkout implementation remains `workercoordinator/portable_checkout.js`. This lane adds only a task package bound to the existing HIL registry fragment, executable handoff, task state vector, current global WorkerCoordinator predecessor registry, and the existing portable checkout implementation.

## Required invariants

- canonical authority owner remains `StegVerse-Labs/.github WorkerCoordinator`;
- task id remains `SHWP-HIL-SOVEREIGN-RECEIVER-001`;
- task must remain `HANDOFF_READY` with claim unset before checkout;
- worker id resolves to `hil-sovereign-receiver-worker`;
- execution surface is `CURRENT_USER_IPHONE`;
- credential authority is `TV/TVC`;
- GitHub token runtime authority is `NONE`;
- heartbeat grants no execution authority;
- no parallel WorkerCoordinator claim issuance;
- checkout uses the existing monotonic portable state lineage;
- package floor must be stricter than the task registry's historical `>21` floor and must not reuse observed G23/G24 fences;
- source/package/CI must not be represented as an authentic checkout or HIL receiver execution.

## Source bindings observed before package creation

```text
worker registry fragment: control/worker-registry.d/hil-sovereign-receiver-001.json
blob: b990a4e68586e4596e9ef2b32437fbb14217989e

executable handoff: handoffs/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
blob: 8762486fdf6cfcd228b22d2f6cdd48a50cac3b58

task state vector: control/task-vectors/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
blob: cd7d0f121a93ad6f73d0fec561a003d22b7d3a04

global WorkerCoordinator registry: control/worker-registry.json
blob: d860e4c09aaeffaf896a3a95b440334984547dce

portable checkout implementation: workercoordinator/portable_checkout.js
blob: 558ca71f6cdaf461deb65ff96f077a7c2df78493
```

## Fence floor

Observed portable lineage already preserves G23/G24. The existing Ecosystem Chat package therefore uses `minimum_fencing_token_exclusive=24`; HIL must reuse that global portable lineage floor or advance beyond a newer authentically observed floor. A fresh/reset HIL checkout may not issue G23 or G24.

## Runtime boundary

A released HIL portable package authorizes the existing checkout algorithm to create a HIL claim/fence when actually executed on the portable state surface. It does not itself create that claim/fence. It also does not satisfy `PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002`, prove native iOS receiver readiness, or establish any downstream public/restart/TVC lifecycle predicate.
