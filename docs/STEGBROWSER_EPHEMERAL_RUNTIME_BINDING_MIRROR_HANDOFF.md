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

Relevant merged source/evidence-contract work includes `.github` #1461, #1465, #1487, #1522, #1533, #1556, and #1566, plus TVC #386/#387.

## Dedicated-consumption evidence semantics

PR #1533 made a complete portable StegBrowser refresh+dispatch require the dedicated consumption receipt to be present, identity-valid, hash-bound, and tied to the pinned TVC SHA.

Post-#1533 inspection identified one semantic defect: the StegBrowser consumer returns:

```text
outcome = HANDOFF_READY
pending_reason = PRIVATE_SOURCE_REQUEST_SLOT_OCCUPIED_BY_OTHER_TASK
```

when another task owns `tvc-handoff/private-source-request.json`. In that state the pinned StegBrowser TVC request is not staged.

PR #1556 closes that gap. Successful StegBrowser target-consumption evidence is now limited to:

```text
STAGED
ALREADY_STAGED
RESTAGED_EXACT_SOURCE
```

`HANDOFF_READY` remains an authentic consumer observation, but the portable bridge now fails closed as `REFRESH_COMPLETE_DISPATCH_INCOMPLETE` until the exact StegBrowser request actually occupies the private-source slot.

PR #1556 merged at `5a206b31613629497feb5d12a810bcf3e368ae39` after all four exact-head lanes passed:

```text
Cross-Framework Current-Basis Resident Request Validation: success
Validate organization control plane: success
Deterministic Repository Suite: success
Heartbeat Worker Project validation: success
```

This repair changes no task identity, selector, runtime, scheduler, dispatcher, heartbeat, credential path, transition authority, WorkerCoordinator authority, machine requirement, or downstream TVC promotion wiring.

## Task Registry staged-consumption reconciliation

PR #1566 reconciled the canonical Task Registry with #1533/#1556 and merged at `ed75c02e8f2809b58538156c0abc7caf9eb1e95d` after exact-head organization-control, Heartbeat, and complete deterministic-suite validation passed.

The canonical record now requires `STEGBROWSER_TVC_DEDICATED_CONSUMPTION_STAGED_OUTCOME_OBSERVED`, binds the identity-valid dedicated receipt and canonical SHA-256 alongside source HEAD, exact selector, and one-consumer dispatch evidence, and recognizes only `STAGED`, `ALREADY_STAGED`, or `RESTAGED_EXACT_SOURCE` as complete StegBrowser consumption evidence.

## Current-dispatch binding repair

Post-#1566 inspection found one remaining replay gap in `scripts/refresh_and_dispatch_resident_requests.py`.

The generic resident dispatcher already embeds the exact current consumer machine result in:

```text
receipts/sovereign-host/resident-request-dispatch.latest.json
  outcomes[0].consumer = stegbrowser_tvc_source_promotion
  outcomes[0].attempted = true
  outcomes[0].returncode = 0
  outcomes[0].result = <current consumer result>
```

The portable bridge, however, validated the separately persisted dedicated receipt without proving that it was identical to that current dispatch result. A stale prior dedicated receipt with otherwise-valid task/SHA/outcome fields could therefore satisfy the bridge after a later dispatcher success.

The current repair fails closed unless the dedicated receipt exactly equals the current exact-selector dispatch outcome result. The persisted bridge evidence now records:

```text
target_consumption_matches_current_dispatch_result = true
```

as a mandatory condition of `REFRESH_AND_DISPATCH_COMPLETE` for `stegbrowser_tvc_source_promotion`. A deterministic regression preserves a prior valid receipt while emitting a different current dispatcher result and requires `REFRESH_COMPLETE_DISPATCH_INCOMPLETE`.

This repair adds no executor, listener, scheduler, heartbeat, credential path, source transport, transition authority, WorkerCoordinator authority, or machine dependency. Runtime execution remains unobserved pending authentic resident capacity.

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

1. Validate and merge the current-dispatch dedicated-consumption binding repair.
2. Reconcile the canonical Task Registry with the merged current-dispatch binding requirement.
3. When an authorized sovereign resident or admitted Remote Computer ephemeral Node is reachable, verify its local `.github` source contains the merged current-dispatch repair and canonical reconciliation or a later compatible main.
4. Execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion`; complete evidence must bind current local source HEAD, exact selector, current dispatcher result, and identical dedicated staged-consumption receipt.
5. Observe exact TVC materialization, transient promotion, same-service restart, and simultaneous `8765/8775`.
6. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
7. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
8. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
9. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. The current-dispatch binding is task-specific evidence semantics and requires no repository-wide README text change.

## Current state

`ACTIVE_NOT_SUPERSEDED / TASK_REGISTRY_RUNTIME_EVIDENCE_CONTRACT_RECONCILED_1522 / DEDICATED_CONSUMPTION_EVIDENCE_BINDING_MERGED_VALIDATED_1533 / HANDOFF_READY_FAIL_CLOSED_REPAIR_MERGED_VALIDATED_1556 / TASK_REGISTRY_STAGED_CONSUMPTION_SEMANTICS_RECONCILED_1566 / CURRENT_DISPATCH_DEDICATED_CONSUMPTION_BINDING_IMPLEMENTED_VALIDATION_PENDING / REMOTE_COMPUTER_CURRENTLY_UNAVAILABLE / AUTHENTIC_RESIDENT_SOURCE_REVISION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
