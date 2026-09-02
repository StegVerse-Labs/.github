# HB Runtime Presence / Resident Observability Mirror Handoff

Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Issue: #812
Parent authority:
- docs/HEARTBEAT_CARRIER_SIGNAL_MIRROR_HANDOFF.md
- HB_MACHINE_CONTINUATION_MIRROR_HANDOFF.md
- docs/ORG_MIRROR_HANDOFF.md

## Purpose

This is the shared cross-session observation contract for resident/runtime presence. It consumes existing canonical HB, WorkerCoordinator, resident-request, InTr-adjacent receipt, and reconstruction state. It does not create a new runtime signal, heartbeat, scheduler, executor, request authority, or transport authority.

Canonical observation path:

```text
HB runtime observation
-> deterministic HB reference/freshness
-> resident/node identity
-> native supervision + WorkerCoordinator observation
-> governed request/consumption evidence
-> execution transition evidence
-> retained receipt references
-> replay/reconstruction evidence
```

HB and HB-derived carriers grant no execution, admission, credential, routing, transition, claim/fence, receiving, publication, custody, or consequence authority. TV/TVC remains the only credential authority.

## Shared implementation

```text
scripts/project_hb_runtime_presence.py
schemas/hb-runtime-presence-resident-observability.schema.json
tests/test_hb_runtime_presence_observability.py
control/hb-runtime-presence-resident-observability.json   # deployment-local projection output
```

The projection answers separately:
- which resident/node is observed;
- whether native supervision is observed;
- whether HB sampler state is fresh;
- whether WorkerCoordinator state is fresh;
- which governed resident request is present;
- whether matching request consumption is observed;
- whether runtime execution was attempted/completed;
- which transition ID is evidenced;
- which receipt/evidence references are retained;
- whether replay/reconstruction is independently observed.

It MUST NOT collapse resident request consumption, receiver READY, ingress RECEIVED, egress FORWARDED, principal execution, observer relation, or reconstruction into a generic runtime-active flag.

## First consumer binding

The current StegVerse-001 / Beta_Orionis session is missing the predicate:

```text
resident_process_alive_supervised
```

and, independently after that:

```text
governed_request_consumed
runtime_execution_completed
receipt_retained
replay_reconstruction_proven
```

This shared contract replaces session-local invention. Source completion does not satisfy any deployment-local predicate.

## Installation

The projector source is carried by the existing sovereign:
- bootstrap required-source manifest;
- native heartbeat/worker service materialization;
- worker-source refresh manifest.

No process is added. A resident or operator may invoke the projector when observation is requested; its output is observation-only and grants no authority.

## Completion state

```text
shared contract source: IMPLEMENTED / DETERMINISTIC TESTS PASS
installation manifests: BOOTSTRAP + NATIVE SERVICE MATERIALIZATION + SOURCE REFRESH BOUND
runtime projection from authentic sovereign resident: NOT OBSERVED
StegVerse-001 resident supervision predicate: NOT OBSERVED
GitHub Actions runtime authority: NONE
credential authority: TV/TVC
```
