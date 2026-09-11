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
.github #1487  merge 1d007fc696dc35b2e16f7b52bbd0f9ddd094f26b
TVC #386      merge 2e1bda01699439731569dce45d5d7b4c5b342424
TVC #387      merge aef6b6f5dc99d2a531718ca475d20858ae8e68a6
```

The task-specific Canonical Work bootstrap and the portable exact-selector bridge are source-valid. The portable path requires an already-local `.github` checkout and performs no clone/fetch/pull/network source transport.

## Source-revision evidence contract

`scripts/refresh_sovereign_worker_runtime_source.py` records the local canonical source revision as:

```text
receipts/sovereign-host/worker-source-refresh.latest.json
  source_git_head = <exact local .github HEAD>
```

`scripts/refresh_and_dispatch_resident_requests.py` preserves that refresh receipt inside:

```text
receipts/sovereign-host/resident-refresh-dispatch.latest.json
  refresh_receipt.source_git_head
  target_consumer = stegbrowser_tvc_source_promotion
  exact_consumer_selection_observed = true
  dispatch_receipt.selected_consumers = [stegbrowser_tvc_source_promotion]
```

PR #1487 added a behavioral regression test requiring the exact source Git HEAD and exact selector to survive together into the persisted portable bridge receipt. All three exact-head validation lanes passed before merge: organization control-plane validation, Heartbeat validation, and the complete deterministic repository suite. Runtime behavior is unchanged.

This allows future resident evidence to prove both **which local source revision executed** and **which single consumer was selected**, without inferring source freshness from repository state. No source/CI result substitutes for the authentic resident receipt.

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

1. When an authorized sovereign resident or admitted Remote Computer ephemeral Node is reachable, verify its local `.github` source HEAD contains #1461, #1465, and #1487 or a later compatible main.
2. Execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion` and retain all three provenance/dispatch receipts plus the dedicated consumption receipt.
3. Observe exact TVC materialization, #387 promotion, #386 same-service restart, and simultaneous `8765/8775`.
4. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
5. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
6. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
7. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. The source-head/selector evidence hardening is task-specific and requires no repository-wide README text change.

## Current state

`ACTIVE_NOT_SUPERSEDED / TASK_REGISTRY_AND_COSV_RECONCILED_1437 / GLOBAL_CONVERGENCE_SELECTOR_REPAIR_MERGED_VALIDATED_1440 / STEGBROWSER_BOOTSTRAP_REACHABILITY_MERGED_VALIDATED_1461 / PORTABLE_STEGBROWSER_PROMOTION_DISPATCH_MERGED_VALIDATED_1465 / HANDOFF_RECONCILED_1469 / SOURCE_HEAD_PLUS_EXACT_SELECTOR_EVIDENCE_TEST_MERGED_VALIDATED_1487 / REMOTE_COMPUTER_ELIGIBLE_AS_ADMITTED_EPHEMERAL_STEGOS_CAPACITY / REMOTE_COMPUTER_CURRENTLY_UNAVAILABLE / AUTHENTIC_RESIDENT_SOURCE_REVISION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
