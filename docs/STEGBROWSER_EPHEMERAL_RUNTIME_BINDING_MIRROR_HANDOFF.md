# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-11

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`

## Current objective

The Goal remains ACTIVE and not superseded. The immediate target is authentic resident consumption of `stegbrowser_tvc_source_promotion`, followed by exact TVC materialization, same-primary-runtime restart, live `8765/8775`, Apple `OWNER_INGRESS_READY`, current-iPhone SKAP custody, signing, TestFlight installation, and resident discovery.

## Merged source path

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
TVC #386      merge 2e1bda01699439731569dce45d5d7b4c5b342424
TVC #387      merge aef6b6f5dc99d2a531718ca475d20858ae8e68a6
```

#1461 passed organization-control, Heartbeat, and complete deterministic-suite validation before merge. It closes the bootstrap reachability gap by adding `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001` to `GLOBAL_CONVERGENCE_TASK_IDS`, so a StegBrowser Canonical Work bootstrap can invoke the already-existing convergence visitor directly.

## Portable refresh+dispatch repair

Post-#1461 inspection found that `scripts/refresh_and_dispatch_resident_requests.py` refreshes already-local sovereign source and can dispatch exactly one registered consumer, but `ALLOWED_TARGET_CONSUMERS` omitted `stegbrowser_tvc_source_promotion`.

The current repair adds only that existing selector to the portable bridge allowlist and adds a regression assertion in `tests/test_stegbrowser_tvc_source_promotion_request.py`. This permits:

```text
already-local current .github source
-> existing refresh_sovereign_worker_runtime_source.refresh
-> exact --only-consumer stegbrowser_tvc_source_promotion
-> existing resident dispatcher
-> existing #1358 consumer
```

It performs no clone/fetch/pull/network source transport, acquires no credential, introduces no new scheduler/dispatcher/heartbeat, and grants no execution authority. It remains source-only until validated and merged.

## Authentic runtime evidence

Expected first dedicated receipt:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

A current canonical search still finds only the consumer definition, not an authentic runtime receipt. The authorized remote resident connector currently reports no online device. Therefore these remain unclaimed:

```text
resident source-promotion consumption: NOT OBSERVED
exact TVC request staging:             NOT OBSERVED
pinned TVC materialization:            NOT OBSERVED
#387 transient promotion:              NOT OBSERVED
#386 primary-runtime restart:          NOT OBSERVED
simultaneous 8765/8775:                NOT OBSERVED
Apple OWNER_INGRESS_READY:             NOT OBSERVED
real Apple SKAP custody:               NOT OBSERVED
current-iPhone signing/TestFlight:     NOT OBSERVED
resident discovery:                    NOT OBSERVED
```

GitHub Actions remains validation/evidence transport only. TV/TVC remains credential authority; Interlock/InTr remains transition authority; source and CI do not prove runtime execution.

## Source-refresh boundary

The portable refresh path deliberately requires an **already-local current `.github` source tree**. It performs no GitHub network fetch. Therefore after this allowlist repair is merged, authentic execution still requires the sovereign resident to have a local source root containing the merged commit. No evidence currently proves that resident-side source revision because the authorized resident connector is offline.

## Remaining sequence

1. Validate and merge the portable `stegbrowser_tvc_source_promotion` refresh+dispatch allowlist repair.
2. When an authorized resident is reachable with current local source, execute the existing refresh+dispatch bridge for exactly `stegbrowser_tvc_source_promotion` and capture its authentic consumption receipt.
3. Observe exact TVC materialization, #387 promotion, #386 same-service restart, and simultaneous `8765/8775`.
4. Observe Apple recipient/liveness/InTr `OWNER_INGRESS_READY`.
5. Resolve the external Apple Terms/account gate, create the Team API key, and seal it from the current iPhone into SKAP without export.
6. Complete authentic Device -> KV -> SKAP custody, TVC Apple operations, same-device IPA signing, Build Upload, TestFlight installation, and resident discovery.
7. Continue native StegSocials publication/readback only after working-instance proof.

## README disposition

Repository `README.md` remains accurate for Canonical Work and authority separation. No README text change is required for this targeted portable-dispatch repair.

## Current state

`ACTIVE_NOT_SUPERSEDED / TASK_REGISTRY_AND_COSV_RECONCILED_1437 / GLOBAL_CONVERGENCE_SELECTOR_REPAIR_MERGED_VALIDATED_1440 / STEGBROWSER_BOOTSTRAP_REACHABILITY_MERGED_VALIDATED_1461 / PORTABLE_STEGBROWSER_PROMOTION_DISPATCH_IMPLEMENTED_VALIDATION_PENDING / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
