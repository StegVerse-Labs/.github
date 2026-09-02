# SV-011 Phase-5 Resident Bridge Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Issue: `#787`  
Final implementation PR: `#798` (rebased; supersedes closed `#788`)  
State: SOURCE_CONTROL_MERGED_VALIDATED / AUTHENTIC_RESIDENT_EXECUTION_PENDING  
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
4. locate either an already-local clean pinned `SV-011/.github` checkout or the exact verified materialized tree produced by `SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001`;
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


## Source/control completion — 2026-09-02

Issue `#787` identified the concrete missing execution wiring: SV-011 had resident probe source and requests, but the canonical sovereign WorkerCoordinator had no SV-011 task, consumer, dispatcher selector, or source-refresh materialization path.

Implemented:
- independently admitted task `SHWP-SV011-PHASE5-BOUNDARY-001`;
- executable handoff and process adapter;
- explicit Admissible-Existence binding at `ADMISSIBLE`;
- COSV task vector `50000000101000` with one authentic-runtime-evidence blocker;
- intent-only request `RESIDENT-EXEC-SV011-PHASE5-BOUNDARY-001`;
- at-most-once consumer;
- resident dispatcher selector `sv011_phase5`;
- source-refresh materialization in both canonical refresh surfaces;
- non-secret local locator `STEGVERSE_SV011_ORG_ROOT`;
- resident worker that accepts only (a) a clean already-local `SV-011/.github` checkout containing `cf2777d9d21a97289f4ec7b0d9b0b21597047666` with exact pinned blobs, or (b) the exact verified materialized tree produced by the dedicated source-materialization task;
- same-task execution of the SV-011-owned ALLOW and DENY probes.

Governance validation initially rejected the new task until its AE and COSV surfaces were installed. Those validators were not weakened; the missing bindings and exact denominator projections were added.

Final implementation:
- PR `#798`
- merge `869a6ad8d9c76fa9066bceee525168745f21a6fa`

Exact-head hosted validation before merge:
- Heartbeat Worker Project run `33677408647`: SUCCESS
- Cross-Framework Current-Basis Resident Request Validation run `33677408560`: SUCCESS
- Validate organization control plane run `33677408547`: SUCCESS

Post-merge request validation:
- run `33677467125`: SUCCESS

These runs establish source/control correctness only. They do not constitute sovereign resident execution.

## Remaining machine-owned runtime transition

The canonical resident source refresh/dispatcher may now materialize and visit the SV-011 request without any chat/session runtime execution.

Required authentic evidence remains:
- resident request consumption receipt for `RESIDENT-EXEC-SV011-PHASE5-BOUNDARY-001`;
- WorkerCoordinator receipt for `SHWP-SV011-PHASE5-BOUNDARY-001`;
- ALLOW observation for `SV011-PHASE5-ALLOW-001` with five ordered receipts;
- DENY observation for `SV011-PHASE5-DENY-001` with `consumed=false` and `consequence_reachable=false`;
- both outcomes bound to one resident WorkerCoordinator execution.

Until those artifacts exist, Phase 5 remains OPEN and no runtime/autonomous activation claim is permitted.


## Exact resident source prerequisite — 2026-09-02

The source prerequisite is now machine-executable rather than assumed.

Canonical predecessor:
- task `SHWP-SV011-PHASE5-SOURCE-MATERIALIZATION-001`
- request `RESIDENT-EXEC-SV011-PHASE5-SOURCE-MATERIALIZATION-001`
- issue `#806`
- implementation PR `#807`
- merge `dccf1015eff9bcc398b43a7e9dd4a4ff1c53111e`

Dispatcher order is explicit:

```text
sv011_phase5_source_materialization
-> sv011_phase5
```

The source materializer has no boundary-execution authority; the Phase-5 worker has no source-acquisition authority. The split is preserved.
