# HB Runtime Presence / Resident Observability Mirror Handoff

Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Issue: #813
Goal: HB-RUNTIME-PRESENCE-RESIDENT-OBSERVABILITY-001

## Purpose

This is the shared authority-neutral runtime-observability contract for StegVerse resident consumers. It does not create a second heartbeat, scheduler, runtime, request path, claim/fence source, credential path, receiver, or evidence authority.

Canonical flow:

```text
HB runtime/reference
-> deterministic HB-derived observation frame
-> sovereign node identity + resident freshness
-> Interlock/InTr admission/transport evidence
-> resident request dispatch
-> request-specific consumer
-> WorkerCoordinator admission/claim/fence
-> task execution/state receipt
-> retained evidence
-> replay/reconstruction
```

## Canonical inputs

- `control/heartbeat-protocol-anchor.json`
- `control/heartbeat-carrier-runtime-state.json` when deployment-local observation exists
- `control/worker-runtime-state.json`
- `control/worker-control-plane-coordination.json`
- sovereign node declaration from `STEGVERSE_SOVEREIGN_NODE_MARKER`, `~/.stegverse/node.json`, or `/etc/stegverse/node.json`
- `receipts/sovereign-host/resident-request-dispatch.latest.json`
- request-specific consumer and execution receipts
- Master Records / other canonical reconstruction receipts supplied by the consumer lane

## Contract

`scripts/project_hb_runtime_presence_observability.py` emits one projection with separate fields for:

- node identity;
- resident/runtime presence;
- HB/reference freshness;
- latest resident-request dispatch;
- admitted request identity if observable;
- request-specific consumption evidence references;
- execution/state receipt references;
- retained evidence/reconstruction references.

Missing runtime artifacts remain explicitly `NOT_OBSERVED`. Repository source, CI, merge, release, deployment metadata, and HB progression are never substituted for runtime evidence.

## Authority

```text
HB / HB-derived carrier authority: NONE
Interlock/InTr: transition/admissibility boundary
WorkerCoordinator: admission/claim/fence authority where applicable
credential authority: TV/TVC
GitHub runtime authority: NONE
projection authority effect: NONE_OBSERVATION_ONLY
```

## First consumer: SV001 bounded autonomy

SV001 uses this shared projection only to answer resident identity/freshness/request-observation questions. It does not replace the distinct SV001 completion predicates:

- TVC lease issuance receipt;
- resident request consumption;
- `SV001_BOUNDED_AUTONOMY_CYCLE_COMPLETED`;
- Master Records reconstruction PASS;
- SV002 adversarial disposition.

The projection is diagnostic/observational. Authentic completion still comes from the task-specific runtime and retained evidence surfaces.

## Completion

Source completion requires the shared projector, deterministic tests, this handoff, and at least one consumer binding. Runtime activation is never implied by source completion.
