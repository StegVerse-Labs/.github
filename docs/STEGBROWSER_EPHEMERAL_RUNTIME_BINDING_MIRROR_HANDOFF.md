# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-12

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`

## Current objective

The Goal remains ACTIVE and not superseded. The immediate target is authentic resident consumption of `stegbrowser_tvc_source_promotion`, followed by exact TVC materialization, same-primary-runtime restart, simultaneous `8765/8775`, Apple `OWNER_INGRESS_READY`, current-iPhone SKAP custody, signing, TestFlight installation, and resident discovery.

## Canonical execution-substrate model

This task follows the already-established Task Registry substrate invariant. The execution model is not defined by a Remote Computer connector or by the availability of any particular remote machine.

Canonical substrate order is:

```text
1. STEG-BROWSER-RETAINED-RESIDENT-NODE
2. STEGOS-CURRENT-DEVICE-NODE
3. STEG-BROWSER-EPHEMERAL-LEASE
4. SAME-DEVICE-SITE-SAFARI-SERVICE-WORKER
5. ADMITTED-EPHEMERAL-STEGOS-NODE
6. REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT
```

For this task:

- `STEG-BROWSER-RETAINED-RESIDENT-NODE` is the selected canonical substrate;
- the current-device StegOS node and StegBrowser ephemeral lease are reusable parts of the same architecture;
- additional temporary execution capacity, including capacity discovered through a Remote Computer transport, is eligible only when it materializes as an `ADMITTED-EPHEMERAL-STEGOS-NODE` and is admitted through the existing Interlock/InTr protocol;
- Remote Computer is transport/discovery only. It is not a distinct execution authority, machine dependency, scheduler, runtime class, credential authority, transition authority, or completion authority;
- an empty Remote Computer inventory or unavailable connector is only an `EVIDENCE_REACHABILITY` observation. It does not make the canonical StegBrowser/StegOS substrate unsuitable and cannot create an external-device requirement;
- `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` is not selected and no second user-operated device is allowed.

Presence or connectivity never grants execution. Interlock/InTr remains admission/transition authority, WorkerCoordinator remains claim/fence authority, TV/TVC remains credential authority, and Master Records remains observed-reality/provenance authority.

This is the existing standard recorded by `docs/TASK_REGISTRY_ANTI_COLLISION_AGGREGATION_MIRROR_HANDOFF.md` and the first StegBrowser StegOS-node milestone; it is not a new interpretation introduced by this handoff.

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

Relevant merged source/evidence-contract work includes `.github` #1461, #1465, #1487, #1522, #1533, #1556, #1566, #1579, and #1590, plus TVC #386/#387.

## Dedicated-consumption and current-dispatch semantics

PR #1533 requires a dedicated StegBrowser TVC consumption receipt. PR #1556 limits successful staged-consumption outcomes to:

```text
STAGED
ALREADY_STAGED
RESTAGED_EXACT_SOURCE
```

`HANDOFF_READY` remains authentic but incomplete because another task owns the private-source request slot.

PR #1579 closed the stale-receipt replay gap. A complete bridge result now requires:

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

The dedicated receipt must bind task `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`, pinned TVC SHA `aef6b6f5dc99d2a531718ca475d20858ae8e68a6`, zero credential material, zero network source fetch, and one of the three staged outcomes above.

PR #1579 merged at `b6c8a2bf1f0e91c24afa21b2e8d710f60da3b455` after Cross-Framework resident-request validation, organization-control validation, complete deterministic repository suite, and Heartbeat validation all passed.

## Task Registry current-dispatch reconciliation

PR #1590 reconciled #1579's stronger current-dispatch requirement into the canonical Task Registry and merged at `b3fa00d0f78c35d1de91fbe80cab131a8f17c5d9` after exact-head organization-control, complete deterministic-suite, and Heartbeat validation passed.

The canonical record now:

- carries #1579 (`b6c8a2bf1f0e91c24afa21b2e8d710f60da3b455`) in source/evidence lineage;
- requires `STEGBROWSER_TVC_DEDICATED_CONSUMPTION_CURRENT_DISPATCH_BOUND_OBSERVED`;
- requires the current exact-selector dispatcher outcome with `attempted=true` and `returncode=0`;
- requires the dedicated receipt to equal that current dispatcher result;
- requires `target_consumption_matches_current_dispatch_result=true` together with the dedicated receipt canonical SHA-256.

This reconciliation changes no coordination state, checkout state, blockers, completion truth, `allowed_next_transitions`, WorkerCoordinator authority, Interlock/InTr authority, runtime, scheduler, listener, credential path, or machine requirement.

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

No authentic admitted StegBrowser/StegOS execution instance has yet produced the required receipts. A connector inventory observation may help discover eligible ephemeral capacity, but connector availability is not itself a task-state predicate. Therefore these remain unclaimed:

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

1. Observe or discover an eligible instance of the existing StegBrowser/StegOS execution substrate. If temporary capacity is surfaced through Remote Computer transport, classify it as an `ADMITTED-EPHEMERAL-STEGOS-NODE` and require normal Interlock/InTr admission before execution.
2. Verify the admitted execution instance uses local `.github` source containing #1579 and #1590 or a later compatible main.
3. Execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion`; complete evidence must bind current local source HEAD, exact selector, current dispatcher result, identical dedicated staged-consumption receipt, and canonical dedicated-receipt SHA-256.
4. Observe exact TVC materialization, transient promotion, same-service restart, and simultaneous `8765/8775`.
5. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
6. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
7. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
8. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. This reconciliation restores the already-established execution-substrate semantics to the task-specific canonical surfaces and requires no repository-wide README change.

## Current state

`ACTIVE_NOT_SUPERSEDED / CANONICAL_EXECUTION_SUBSTRATE_MODEL_RESTORED / RETAINED_STEGBROWSER_STEGOS_NODE_SELECTED / ADMITTED_EPHEMERAL_STEGOS_NODE_CAPACITY_ALLOWED / REMOTE_COMPUTER_TRANSPORT_NOT_TASK_STATE / SECOND_USER_OPERATED_DEVICE_NOT_ALLOWED / TASK_REGISTRY_RUNTIME_EVIDENCE_CONTRACT_RECONCILED_1522 / DEDICATED_CONSUMPTION_EVIDENCE_BINDING_MERGED_VALIDATED_1533 / HANDOFF_READY_FAIL_CLOSED_REPAIR_MERGED_VALIDATED_1556 / TASK_REGISTRY_STAGED_CONSUMPTION_SEMANTICS_RECONCILED_1566 / CURRENT_DISPATCH_DEDICATED_CONSUMPTION_BINDING_MERGED_VALIDATED_1579 / TASK_REGISTRY_CURRENT_DISPATCH_BINDING_RECONCILED_1590 / AUTHENTIC_RESIDENT_SOURCE_REVISION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
