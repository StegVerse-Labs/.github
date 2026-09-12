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

## Dedicated-consumption and replay semantics

PR #1533 requires a dedicated StegBrowser TVC consumption receipt. PR #1556 limits successful staged-consumption outcomes to:

```text
STAGED
ALREADY_STAGED
RESTAGED_EXACT_SOURCE
```

`HANDOFF_READY` remains authentic but incomplete because another task owns the private-source request slot.

PR #1566 reconciled those staged-consumption semantics into the canonical Task Registry.

PR #1579 then closed the remaining stale-receipt replay gap. `REFRESH_AND_DISPATCH_COMPLETE` now requires all of the following together:

```text
source_revision_head_kind = GIT_HEAD
source_git_head = exact lowercase 40-hex local .github HEAD
selection_scope = EXACT_SELECTOR
selected_consumers = [stegbrowser_tvc_source_promotion]
consumer_count = 1
outcomes[0].consumer = stegbrowser_tvc_source_promotion
outcomes[0].attempted = true
outcomes[0].returncode = 0
outcomes[0].result = current consumer result
stegbrowser-tvc-source-promotion-request-consumption.latest.json == outcomes[0].result
target_consumption_matches_current_dispatch_result = true
dedicated consumption receipt canonical SHA-256 is retained
```

The dedicated receipt must still bind task `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`, pinned TVC SHA `aef6b6f5dc99d2a531718ca475d20858ae8e68a6`, zero credential material, zero network source fetch, and one of the three staged outcomes above. A stale prior receipt cannot satisfy a later dispatcher success.

PR #1579 merged at `b6c8a2bf1f0e91c24afa21b2e8d710f60da3b455` after Cross-Framework resident-request validation, organization-control validation, complete deterministic repository suite, and Heartbeat validation all passed.

## Task Registry current-dispatch reconciliation

The canonical Task Registry still stopped at the #1566 staged-outcome contract and did not carry #1579's current-dispatch equality requirement.

The current reconciliation updates only canonical evidence semantics. It:

- adds #1579 (`b6c8a2bf1f0e91c24afa21b2e8d710f60da3b455`) to source/evidence lineage;
- adds `STEGBROWSER_TVC_DEDICATED_CONSUMPTION_CURRENT_DISPATCH_BOUND_OBSERVED` to expected evidence;
- requires the exact current dispatcher outcome with `attempted=true` and `returncode=0`;
- requires the dedicated receipt to equal that current dispatcher result;
- requires `target_consumption_matches_current_dispatch_result=true` together with the dedicated receipt SHA-256 commitment.

Coordination state, checkout state, blockers, completion truth, `allowed_next_transitions`, WorkerCoordinator authority, Interlock/InTr authority, and all runtime claims remain unchanged.

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

The authorized Remote Computer connector currently reports no online device. Therefore these remain unclaimed:

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

1. Validate and merge the Task Registry current-dispatch reconciliation.
2. When an authorized sovereign resident or admitted Remote Computer ephemeral Node is reachable, verify its local `.github` source contains #1579 plus the registry reconciliation or a later compatible main.
3. Execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion`; complete evidence must bind current local source HEAD, exact selector, current dispatcher result, identical dedicated staged-consumption receipt, and canonical dedicated-receipt SHA-256.
4. Observe exact TVC materialization, transient promotion, same-service restart, and simultaneous `8765/8775`.
5. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
6. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
7. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
8. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. This reconciliation only aligns the canonical task record with already-merged #1579 evidence semantics and requires no repository-wide README change.

## Current state

`ACTIVE_NOT_SUPERSEDED / TASK_REGISTRY_RUNTIME_EVIDENCE_CONTRACT_RECONCILED_1522 / DEDICATED_CONSUMPTION_EVIDENCE_BINDING_MERGED_VALIDATED_1533 / HANDOFF_READY_FAIL_CLOSED_REPAIR_MERGED_VALIDATED_1556 / TASK_REGISTRY_STAGED_CONSUMPTION_SEMANTICS_RECONCILED_1566 / CURRENT_DISPATCH_DEDICATED_CONSUMPTION_BINDING_MERGED_VALIDATED_1579 / TASK_REGISTRY_CURRENT_DISPATCH_BINDING_RECONCILIATION_IMPLEMENTED_VALIDATION_PENDING / REMOTE_COMPUTER_CURRENTLY_UNAVAILABLE / AUTHENTIC_RESIDENT_SOURCE_REVISION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
