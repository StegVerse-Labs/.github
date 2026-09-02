# SV-011 Phase-5 Resident Bridge Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#787`  
Branch: `feat/sv011-phase5-resident-bridge-787`  
State: SOURCE_IMPLEMENTATION_ACTIVE  
Authority effect: NONE_REQUEST_BRIDGE_ONLY  
Activation effect: false

## Goal

Connect the already-built `SV-011/.github` Phase-5 ALLOW/DENY resident probes to the existing sovereign WorkerCoordinator without creating a second scheduler, runtime authority, heartbeat, credential lane, or claim/fence path.

## Existing authority boundary

The live StegVerse-Labs organization handoffs designate the resident sovereign WorkerCoordinator as machine-owned. This session does not execute or resume that runtime directly.

This bridge may only:
1. register one independently admitted SV-011 Phase-5 task;
2. materialize one intent-only resident execution request;
3. dispatch that request through the existing targeted resident bridge;
4. locate already-local clean `SV-011/.github` source;
5. invoke the SV-011-owned Phase-5 probe runner for its ALLOW and DENY requests;
6. persist secret-free evidence.

## Canonical SV-011 source

Required local source ancestor:

`SV-011/.github@cf2777d9d21a97289f4ec7b0d9b0b21597047666`

Required files:
- `resident-runtime/run_phase5_probe.py`
- `resident-runtime/requests/phase5-allow.json`
- `resident-runtime/requests/phase5-deny.json`
- `org-boundary/runtime/intr_transport.py`
- `org-boundary/runtime/process_boundary.py`
- `org-boundary/runtime/denial_adapter.py`
- `org-boundary/registry/services.json`

## Prohibitions

- no network source fetch;
- no source mutation;
- no GitHub/hosted runtime authority;
- no new heartbeat or scheduler;
- no request-granted claim/fence authority;
- no credential acquisition or transport;
- no provider operation;
- no execution/pub/proof authority widening;
- no inference that CI or merge is authentic resident execution.

## Runtime evidence target

The worker may report COMPLETED only when one resident execution observes:
- SV011-PHASE5-ALLOW-001 -> ALLOW with the five-stage receipt chain;
- SV011-PHASE5-DENY-001 -> DENY with consumed=false and consequence_reachable=false;
- both outputs are written by the SV-011-owned resident probe runner under the same WorkerCoordinator execution.

Until such a resident worker receipt exists, Phase 5 remains open.
