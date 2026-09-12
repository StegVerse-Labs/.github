# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-12

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`

## Current objective

The Goal remains ACTIVE and not superseded. The immediate target is authentic resident consumption of `stegbrowser_tvc_source_promotion`, followed by exact TVC materialization, same-primary-runtime restart, simultaneous `8765/8775`, Apple `OWNER_INGRESS_READY`, current-iPhone SKAP custody, signing, TestFlight installation, and resident discovery.

## Current merged source chain

```text
Canonical Work StegBrowser ingress
-> task-specific convergence bootstrap
-> global convergence visitor
-> stegbrowser_tvc_source_promotion
-> existing resident dispatcher
-> exact TVC promotion consumer
-> private-source handoff
-> TVC aef6b6f5dc99d2a531718ca475d20858ae8e68a6
-> transient post-read promotion
-> same stegtvc-primary-runtime.service restart
-> 127.0.0.1:8765 + 127.0.0.1:8775
-> Apple OWNER_INGRESS_READY
```

Relevant merged source/evidence-contract work includes `.github` #1461, #1465, #1487, #1522, #1533, #1556, #1566, and #1579, plus TVC #386/#387.

## Dedicated-consumption evidence semantics

PR #1533 made a complete portable StegBrowser refresh+dispatch require the dedicated consumption receipt to be present, identity-valid, hash-bound, and tied to the pinned TVC SHA.

PR #1556 closed the occupied-slot semantic gap. Successful StegBrowser target-consumption evidence is limited to:

```text
STAGED
ALREADY_STAGED
RESTAGED_EXACT_SOURCE
```

`HANDOFF_READY` remains an authentic consumer observation, but fails closed as `REFRESH_COMPLETE_DISPATCH_INCOMPLETE` because the exact StegBrowser request does not occupy the private-source slot.

PR #1566 reconciled the canonical Task Registry with #1533/#1556 and merged at `ed75c02e8f2809b58538156c0abc7caf9eb1e95d` after exact-head organization-control, Heartbeat, and complete deterministic-suite validation passed.

## Current-dispatch binding

Post-#1566 inspection found a replay gap: the generic dispatcher already persisted the exact current StegBrowser consumer machine result inside `resident-request-dispatch.latest.json`, but the portable bridge independently trusted the dedicated consumption receipt file without proving the two were the same execution result.

PR #1579 closes that gap. `REFRESH_AND_DISPATCH_COMPLETE` now additionally requires:

```text
resident-request-dispatch.latest.json
  selection_scope = EXACT_SELECTOR
  selected_consumers = [stegbrowser_tvc_source_promotion]
  outcomes[0].consumer = stegbrowser_tvc_source_promotion
  outcomes[0].attempted = true
  outcomes[0].returncode = 0
  outcomes[0].result = <current consumer result>

stegbrowser-tvc-source-promotion-request-consumption.latest.json
  == outcomes[0].result

resident-refresh-dispatch.latest.json
  target_consumption_matches_current_dispatch_result = true
```

A stale prior dedicated receipt can no longer satisfy a later dispatcher success. The dedicated receipt must be byte-semantic JSON-equivalent to the current exact-selector consumer result and still satisfy the existing task/SHA/staged-outcome checks.

PR #1579 merged at `b6c8a2bf1f0e91c24afa21b2e8d710f60da3b455` after all four exact-head validation lanes passed:

```text
Cross-Framework Current-Basis Resident Request Validation: success
Validate organization control plane: success
Deterministic Repository Suite: success
Heartbeat Worker Project validation: success
```

This changes no executor, listener, scheduler, heartbeat, credential path, source transport, transition authority, WorkerCoordinator authority, machine requirement, or downstream TVC promotion wiring.

## Authentic runtime evidence

Expected first dedicated runtime receipt:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

Expected supporting evidence:

```text
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-refresh-dispatch.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/dispatch-latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/latest.json
```

Current canonical search still does not show an authentic StegBrowser source-promotion consumption receipt. The authorized Remote Computer connector currently reports no online device. Therefore these remain unclaimed:

```text
resident local source revision at execution: NOT OBSERVED
resident source-promotion consumption:       NOT OBSERVED
exact TVC request staging:                   NOT OBSERVED
pinned TVC materialization:                  NOT OBSERVED
transient promotion:                         NOT OBSERVED
primary-runtime restart:                     NOT OBSERVED
simultaneous 8765/8775:                      NOT OBSERVED
Apple OWNER_INGRESS_READY:                   NOT OBSERVED
real Apple SKAP custody:                     NOT OBSERVED
current-iPhone signing/TestFlight:           NOT OBSERVED
resident discovery:                          NOT OBSERVED
```

GitHub Actions remains validation/evidence transport only. TV/TVC remains credential authority; Interlock/InTr remains transition authority; WorkerCoordinator remains claim/fence authority; Master Records remains runtime-reality/provenance authority.

## Remaining sequence

1. Reconcile the canonical Task Registry with the merged #1579 current-dispatch binding requirement.
2. When an authorized sovereign resident or admitted Remote Computer ephemeral Node is reachable, verify its local `.github` source contains #1579 plus the registry reconciliation or a later compatible main.
3. Execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion`; complete evidence must bind current local source HEAD, exact selector, current dispatcher result, identical dedicated staged-consumption receipt, and canonical dedicated-receipt SHA-256.
4. Observe exact TVC materialization, transient promotion, same-service restart, and simultaneous `8765/8775`.
5. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
6. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
7. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
8. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. The #1579 current-dispatch binding is task-specific evidence semantics and requires no repository-wide README text change.

## Current state

`ACTIVE_NOT_SUPERSEDED / TASK_REGISTRY_RUNTIME_EVIDENCE_CONTRACT_RECONCILED_1522 / DEDICATED_CONSUMPTION_EVIDENCE_BINDING_MERGED_VALIDATED_1533 / HANDOFF_READY_FAIL_CLOSED_REPAIR_MERGED_VALIDATED_1556 / TASK_REGISTRY_STAGED_CONSUMPTION_SEMANTICS_RECONCILED_1566 / CURRENT_DISPATCH_DEDICATED_CONSUMPTION_BINDING_MERGED_VALIDATED_1579 / TASK_REGISTRY_CURRENT_DISPATCH_BINDING_RECONCILIATION_PENDING / REMOTE_COMPUTER_CURRENTLY_UNAVAILABLE / AUTHENTIC_RESIDENT_SOURCE_REVISION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
