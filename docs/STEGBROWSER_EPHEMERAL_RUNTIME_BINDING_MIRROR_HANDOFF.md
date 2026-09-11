# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`

## Current objective

The Goal remains ACTIVE and not superseded. The immediate target is authentic resident consumption of `stegbrowser_tvc_source_promotion`, followed by exact TVC materialization, same-primary-runtime restart, simultaneous `8765/8775`, Apple `OWNER_INGRESS_READY`, current-iPhone SKAP custody, signing, TestFlight installation, and resident discovery.

## Current merged source path

```text
Canonical Work StegBrowser ingress
-> task-specific convergence bootstrap
-> global convergence visitor
-> stegbrowser_tvc_source_promotion
-> existing resident dispatcher
-> exact TVC promotion consumer
-> private-source handoff
-> TVC aef6b6f5dc99d2a531718ca475d20858ae8e68a6
-> #387 transient promotion
-> #386 same-primary-runtime restart
-> 127.0.0.1:8765 + 127.0.0.1:8775
-> Apple OWNER_INGRESS_READY
```

Relevant merged evidence:

```text
.github #1358  merge 9776ceba4877f8c213af534176f277c28ec58d39
.github #1437  merge 495b329392669d979253a609a45dd62b3195dfe8
.github #1440  merge 7f2b83b7abf4bc7163e0e3e5dde6946f547e9f79
.github #1441  merge 55c33048e1671143d7cc30ccb74b677f9e8241f1
.github #1461  merge 4179a3e630c25a1430decd6f072866e6c6fc3798
.github #1465  merge f128716def180dfdeb2f0b0eeb6bff0da6086841
.github #1469  merge eea45d164be4d570d4e8eb6ca5e5d960c6cdac24
TVC #386      merge 2e1bda01699439731569dce45d5d7b4c5b342424
TVC #387      merge aef6b6f5dc99d2a531718ca475d20858ae8e68a6
```

The task-specific Canonical Work bootstrap and the portable exact-selector bridge are both source-valid. The portable path requires an already-local `.github` checkout and performs no clone/fetch/pull/network source transport.

## Source-revision evidence contract

`scripts/refresh_sovereign_worker_runtime_source.py` already records the local canonical source revision as:

```text
receipts/sovereign-host/worker-source-refresh.latest.json
  source_git_head = <exact local .github HEAD>
```

`scripts/refresh_and_dispatch_resident_requests.py` preserves that entire refresh receipt inside:

```text
receipts/sovereign-host/resident-refresh-dispatch.latest.json
  refresh_receipt.source_git_head
  target_consumer = stegbrowser_tvc_source_promotion
  exact_consumer_selection_observed = true
  dispatch_receipt.selected_consumers = [stegbrowser_tvc_source_promotion]
```

The current evidence-hardening change adds a behavioral regression test requiring the exact source Git HEAD and exact selector to survive together into the persisted portable bridge receipt. Runtime behavior is unchanged. This test exists so a future resident execution can prove both **which local source revision executed** and **which single consumer was selected**, rather than inferring source freshness from repository state.

No source/CI result substitutes for the authentic resident receipt.

## Remote computer / ephemeral Node interpretation

A connected Remote Computer is eligible StegOS execution capacity only as an admitted ephemeral Node/runtime substrate under the existing StegOS + Interlock/InTr protocol. Presence alone grants no execution, claim/fence, credential, transition, custody, publication, or completion authority. This does not create a dependency on a second user-operated machine.

## Authentic runtime evidence

Expected first dedicated receipt:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

Expected supporting provenance receipts:

```text
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-refresh-dispatch.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
```

Current canonical search still does not show an authentic source-promotion consumption receipt, and the authorized remote resident connector currently reports no online device. Therefore these remain unclaimed:

```text
resident local source revision at execution: NOT OBSERVED
resident source-promotion consumption:       NOT OBSERVED
exact TVC request staging:                   NOT OBSERVED
pinned TVC materialization:                  NOT OBSERVED
#387 transient promotion:                    NOT OBSERVED
#386 primary-runtime restart:                NOT OBSERVED
simultaneous 8765/8775:                      NOT OBSERVED
Apple OWNER_INGRESS_READY:                   NOT OBSERVED
real Apple SKAP custody:                     NOT OBSERVED
current-iPhone signing/TestFlight:           NOT OBSERVED
resident discovery:                          NOT OBSERVED
```

GitHub Actions remains validation/evidence transport only. TV/TVC remains credential authority; Interlock/InTr remains transition authority; WorkerCoordinator remains claim/fence authority; Master Records remains runtime-reality/provenance authority.

## Remaining sequence

1. Validate and merge the source-head/selector evidence-contract regression test.
2. When an authorized sovereign resident or admitted Remote Computer ephemeral Node is reachable, verify its local `.github` source HEAD is `f128716def180dfdeb2f0b0eeb6bff0da6086841` or a later compatible commit containing #1461 and #1465.
3. Execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion` and retain all three provenance/dispatch receipts plus the dedicated consumption receipt.
4. Observe exact TVC materialization, #387 promotion, #386 same-service restart, and simultaneous `8765/8775`.
5. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
6. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
7. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
8. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. This change hardens a task-specific evidence assertion and does not require repository-wide README text changes.

## Current state

`ACTIVE_NOT_SUPERSEDED / TASK_REGISTRY_AND_COSV_RECONCILED_1437 / GLOBAL_CONVERGENCE_SELECTOR_REPAIR_MERGED_VALIDATED_1440 / STEGBROWSER_BOOTSTRAP_REACHABILITY_MERGED_VALIDATED_1461 / PORTABLE_STEGBROWSER_PROMOTION_DISPATCH_MERGED_VALIDATED_1465 / HANDOFF_RECONCILED_1469 / SOURCE_HEAD_PLUS_EXACT_SELECTOR_EVIDENCE_TEST_IMPLEMENTED_VALIDATION_PENDING / REMOTE_COMPUTER_ELIGIBLE_AS_ADMITTED_EPHEMERAL_STEGOS_CAPACITY / REMOTE_COMPUTER_CURRENTLY_UNAVAILABLE / AUTHENTIC_RESIDENT_SOURCE_REVISION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
