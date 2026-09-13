# StegBrowser Ephemeral Runtime Binding Mirror Handoff

Updated: 2026-09-13

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`

## Current objective

The Goal remains ACTIVE and not superseded. The immediate target remains authentic resident consumption of `stegbrowser_tvc_source_promotion`, exact TVC materialization, same-primary-runtime restart, bounded post-restart observation, Apple `OWNER_INGRESS_READY`, current-iPhone SKAP custody, signing, TestFlight installation, resident discovery, and then the separately required publication/readback branches.

The previous exact-source observer-alignment source predicate is now resolved through the canonical reusable-component option: the primary runtime promotion remains pinned to immutable TVC `aef6b6f5dc99d2a531718ca475d20858ae8e68a6`, while the observation-only component is independently pinned through `RTC-MANIFEST-001` to immutable TVC `4c78f8653b8a5899350479d57c58e936b50e023a`. Source binding does not prove execution.

## Canonical execution-substrate model

This task follows the Task Registry substrate invariant. The execution model is not defined by a Remote Computer connector or by availability of any particular remote machine.

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
- current-device StegOS and StegBrowser ephemeral lease are reusable parts of the same architecture;
- additional temporary execution capacity is eligible only when it materializes as an `ADMITTED-EPHEMERAL-STEGOS-NODE` under Interlock/InTr;
- Remote Computer is transport/discovery only and is not an execution authority, durable machine dependency, runtime class, credential authority, transition authority, or completion predicate;
- an empty connector inventory is only `EVIDENCE_REACHABILITY` and cannot create an external-device requirement;
- `REMOTE-OR-EXTERNAL-DEVICE-LAST-RESORT` is not selected and no second user-operated device is allowed.

Presence or connectivity never grants execution. Interlock/InTr remains admission/transition authority, WorkerCoordinator remains claim/fence authority, TV/TVC remains credential/provider authority, KV/SKAP Vault remains sole user-verification authority, and Master Records remains observed-reality/provenance authority.

## Reusable Task Component composition

The Goal is reconciled to the Reusable Task Component Model. Architecture is composed from reusable capabilities instead of treating the historical end-to-end sequence as one mandatory monolith.

Selected reusable transport components:

```text
RTC-MANIFEST-001
RTC-GOVERNED-PROCESSING-002
RTC-ROUNDTRIP-003                 repeatable
RTC-EVIDENCE-CUSTODY-004
RTC-PUBLISHER-005                 publication stages only
RTC-STEGVERSE-EGRESS-007          where governed egress is required
RTC-INTERLOCK-INTR-TRANSPORT-008  repeatable
RTC-FARSIDE-FINAL-009             provider/far-side confirmation stages
```

`RTC-SDK-RETURN-006` is not applicable.

Execution materialization/cleanup reuses `data/reusable-task-ephemeral-construct-contract.json`. No new scheduler, dispatcher, credential resolver, provider-session manager, publication transport, custody writer, or Remote Computer execution class may be added merely to advance this Goal.

## Current merged source chain

The primary-runtime promotion component remains:

```text
Canonical Work StegBrowser ingress
-> task-specific convergence bootstrap
-> global convergence visitor
-> stegbrowser_tvc_source_promotion
-> existing resident dispatcher
-> exact TVC promotion consumer
-> private-source handoff
-> primary runtime source pin: TVC aef6b6f5dc99d2a531718ca475d20858ae8e68a6
-> transient post-read promotion
-> same stegtvc-primary-runtime.service restart
```

Relevant merged source/evidence-contract work includes `.github` #1461, #1465, #1487, #1522, #1533, #1556, #1566, #1579, and #1590, plus TVC #386/#387.

TVC subsequently advanced the same parent trajectory:

```text
TVC #411  merge bb648278c1947cb4234c7cd985e27f8166c7a45d
  automatic private-source read -> post-read promotion -> same-primary-runtime restart wiring

TVC #413  merge 040b6b4837bd827205537a2b77d254f09bd0db83
  bounded post-restart App Store Connect SKAP runtime observation

TVC #418  merge 5edf023aa7d45e1f525dd1bb556d25cacd35ae74
  canonical vault-agent recipient signing

TVC #419  merge 4c78f8653b8a5899350479d57c58e936b50e023a
  immutable observer source coordinate used by the reusable binding
```

## Post-restart observation component and exact source binding

TVC #413 provides the observation-only entrypoint:

```text
scripts/observe_app_store_connect_skap_runtime.py
```

The canonical source binding is:

```text
control/source-bindings/stegbrowser-tvc-runtime-observer.json
```

It binds:

```text
component_id = RTC-MANIFEST-001
component_role = RUNTIME_OBSERVATION_EVIDENCE_ONLY
source_repository = StegVerse-Labs/TVC
reference_mode = IMMUTABLE_COMMIT
exact_sha = 4c78f8653b8a5899350479d57c58e936b50e023a
primary_runtime_source_pin_preserved = aef6b6f5dc99d2a531718ca475d20858ae8e68a6
observer_source_revision_separate = true
authority_effect = NONE_SOURCE_BINDING_ONLY
```

This binding merged through `.github` PR #1701 at `3ec50b61c2dddf2303abd0d66ef0520a2c3d7c21`.

Therefore:

```text
EXACT_TVC_SOURCE_PIN_OBSERVER_ALIGNMENT = SATISFIED_BY_SEPARATE_IMMUTABLE_REUSABLE_COMPONENT_BINDING
```

This is source architecture only. It does not establish observer execution, listener liveness, `OWNER_INGRESS_READY_OBSERVED`, admission, credential availability, or any later runtime predicate.

The observer consumes already-existing Apple activation, liveness, public-config, and InTr-route evidence and probes only:

```text
127.0.0.1:8765  canonical TVC primary runtime
127.0.0.1:8775  existing shared SKAP ingress
```

Its retained receipt is:

```text
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
```

The terminal observation is `OWNER_INGRESS_READY_OBSERVED` only when both loopback listeners are live in the same observation and activation/liveness/public-route evidence binds the same runtime instance and recipient, the route is `ROUTE_LIVE`, public config is owner-ingress ready, and route receipt hash matches.

## Dedicated-consumption and current-dispatch semantics

PR #1533 requires a dedicated StegBrowser TVC consumption receipt. PR #1556 limits successful staged-consumption outcomes to:

```text
STAGED
ALREADY_STAGED
RESTAGED_EXACT_SOURCE
```

`HANDOFF_READY` remains authentic but incomplete because another task owns the private-source request slot.

PR #1579 closed the stale-receipt replay gap. A complete bridge result requires:

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

The dedicated receipt must bind task `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`, primary runtime TVC SHA `aef6b6f5dc99d2a531718ca475d20858ae8e68a6`, zero credential material, zero network source fetch, and one of the three staged outcomes above. The later observation stage must separately bind observer TVC SHA `4c78f8653b8a5899350479d57c58e936b50e023a` through the reusable source-binding record.

## Task Registry reconciliation

The Task Registry preserves the original exact primary-runtime source pin for the execution/consumption contract and now separately records the immutable observer source binding. This prevents the observation component from silently changing the primary runtime coordinate and prevents the older runtime pin from falsely claiming to contain post-restart observer source.

The two coordinates have distinct roles:

```text
primary runtime promotion source:
  aef6b6f5dc99d2a531718ca475d20858ae8e68a6

post-restart observation component source:
  4c78f8653b8a5899350479d57c58e936b50e023a
```

Neither source binding grants execution, transition, credential, claim/fence, custody, publication, or completion authority.

## Authentic runtime evidence

Expected first dedicated runtime receipt:

```text
receipts/sovereign-host/stegbrowser-tvc-source-promotion-request-consumption.latest.json
```

The runtime profile also requires the earlier Canonical Work prerequisite receipt:

```text
receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json
```

Expected supporting evidence:

```text
receipts/sovereign-host/worker-source-refresh.latest.json
receipts/sovereign-host/resident-refresh-dispatch.latest.json
receipts/sovereign-host/resident-request-dispatch.latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/dispatch-latest.json
/var/lib/stegverse/tvc/primary-runtime-source-promotion/latest.json
/var/lib/stegverse/skap/browser-recipient/apple/receipts/runtime-observation-latest.json
```

No authentic admitted StegBrowser/StegOS execution instance has yet produced the required receipts. Connector inventory may aid discovery but is not a task-state predicate. These remain unclaimed:

```text
Canonical Work resident consumption:          NOT OBSERVED
resident local source revision at execution:  NOT OBSERVED
resident source-promotion consumption:        NOT OBSERVED
exact TVC request staging:                    NOT OBSERVED
pinned TVC materialization:                   NOT OBSERVED
transient promotion:                          NOT OBSERVED
primary-runtime restart:                      NOT OBSERVED
simultaneous 8765/8775:                       NOT OBSERVED
runtime observation receipt:                  NOT OBSERVED
Apple OWNER_INGRESS_READY:                    NOT OBSERVED
real Apple SKAP custody:                      NOT OBSERVED
current-iPhone signing/TestFlight:            NOT OBSERVED
resident discovery:                           NOT OBSERVED
Facebook publication/readback:                NOT OBSERVED
LinkedIn publication/readback:                NOT OBSERVED
Master Records custody/reconstruction:        NOT OBSERVED
```

GitHub Actions remains validation/evidence transport only. TV/TVC remains credential/provider authority; Interlock/InTr remains transition authority; WorkerCoordinator remains claim/fence authority; KV/SKAP Vault remains sole user-verification authority; Master Records remains runtime-reality/provenance authority.

## Runtime preflight convergence boundary discovered 2026-09-13

The first runtime boundary is more specific than merely waiting for a consumption receipt. The existing Canonical Work wrapper performs `scripts/evaluate_task_registry_collision_checkin.py` before any route mutation and proceeds only when the exact disposition is `CONTINUE`. `COORDINATE_CONVERGENCE` and every `STOP_*` disposition fail closed before Canonical Work can reach Interlock/InTr.

Current canonical coordination state contains active convergence work that overlaps this Goal. In particular, `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001` is `ACTIVE / CLAIMED_INTEGRATION`, targets `StegVerse-Labs/.github`, explicitly lists this Goal as adjacent, and is the canonical owner of the shared retained-runtime evidence convergence lane. Under the anti-collision contract, repository/component/lineage/adjacency/substrate overlap can therefore produce `COORDINATE_CONVERGENCE`; this is intentional coordination behavior, not evidence that a second runtime, scheduler, dispatcher, or device is needed.

The remediation path is:

```text
Task Registry exact check-in for this Goal
-> if CONTINUE: proceed with the existing Canonical Work bootstrap
-> if COORDINATE_CONVERGENCE: reconcile with the returned canonical collision/convergence owner(s), preserving this Goal identity
-> require a subsequent exact check-in that returns CONTINUE before mutation
-> only then run Canonical Work -> WorkerCoordinator claim/fence review -> Interlock/InTr admission -> exact stegbrowser_tvc_source_promotion consumption
```

Do not bypass or weaken the fail-closed preflight. Do not reinterpret `COORDINATE_CONVERGENCE` as runtime unavailability. Do not create a StegBrowser-specific collision engine. The general coordination behavior remains owned by `TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001`; the global runtime convergence lane remains owned by `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`.

This discovery does not establish that an authentic resident check-in has already returned `COORDINATE_CONVERGENCE`; no runtime execution is claimed. It establishes from current source and canonical registry state that registry convergence is a required pre-mutation condition that must be observed and resolved before a successful Canonical Work consumption receipt can exist.

## Remaining sequence

1. Perform the exact canonical Task Registry check-in for this Goal on the authentic retained/admitted execution substrate. Require `CONTINUE`; if the observed disposition is `COORDINATE_CONVERGENCE`, reconcile through the returned canonical convergence owner(s) and repeat check-in rather than adding bespoke orchestration.
2. Observe authentic Canonical Work/resident consumption for this Goal on an eligible retained or admitted ephemeral StegBrowser/StegOS execution substrate.
3. Require applicable WorkerCoordinator claim/fence and Interlock/InTr admission; no component source receipt substitutes for either authority.
4. Execute the existing exact-selector governed-processing path for `stegbrowser_tvc_source_promotion` and require current-dispatch-bound dedicated consumption evidence for primary runtime TVC SHA `aef6b6f5dc99d2a531718ca475d20858ae8e68a6`.
5. Observe exact TVC materialization, transient promotion, and same-primary-runtime restart.
6. Invoke the separately immutable-bound observation component from TVC `4c78f8653b8a5899350479d57c58e936b50e023a` and require its authentic runtime observation receipt plus simultaneous `8765/8775` and same-runtime Apple-route bindings.
7. Require `OWNER_INGRESS_READY_OBSERVED` before owner credential ingress.
8. When owner ingress is authentically ready, seal the real App Store Connect credential from the current iPhone into SKAP without export; do not use GitHub secrets or device-local user verification.
9. Complete current-iPhone signing, TVC Build Upload, TestFlight installation, and same-device resident discovery with authentic receipts.
10. Execute Facebook and LinkedIn publication/readback as independent reusable Publisher/round-trip branches only after working-instance proof.
11. Submit required authentic evidence for Master Records custody/reconstruction, then perform terminal cleanup/entropy recovery only where the reusable construct contract permits it.

## README disposition

Repository `README.md` already contains the Reusable Task Component Model projection and authority separation. This update narrows the runtime preflight condition without changing repository-wide architecture, so no README mutation is required by this reconciliation.

## Current state

`ACTIVE_NOT_SUPERSEDED / REUSABLE_COMPONENT_MODEL_RECONCILED / CANONICAL_EXECUTION_SUBSTRATE_MODEL_RESTORED / RETAINED_STEGBROWSER_STEGOS_NODE_SELECTED / ADMITTED_EPHEMERAL_STEGOS_NODE_CAPACITY_ALLOWED / REMOTE_COMPUTER_TRANSPORT_NOT_TASK_STATE / SECOND_USER_OPERATED_DEVICE_NOT_ALLOWED / PRIMARY_RUNTIME_TVC_SOURCE_PIN_PRESERVED_AEF6B6F5 / OBSERVER_IMMUTABLE_SOURCE_BOUND_4C78F865 / EXACT_TVC_SOURCE_PIN_OBSERVER_ALIGNMENT_SATISFIED / TASK_REGISTRY_RUNTIME_EVIDENCE_CONTRACT_RECONCILED_1522 / DEDICATED_CONSUMPTION_EVIDENCE_BINDING_MERGED_VALIDATED_1533 / HANDOFF_READY_FAIL_CLOSED_REPAIR_MERGED_VALIDATED_1556 / TASK_REGISTRY_STAGED_CONSUMPTION_SEMANTICS_RECONCILED_1566 / CURRENT_DISPATCH_DEDICATED_CONSUMPTION_BINDING_MERGED_VALIDATED_1579 / TASK_REGISTRY_CURRENT_DISPATCH_BINDING_RECONCILED_1590 / TVC_AUTOMATIC_POST_READ_PROMOTION_RECONCILED_411 / TVC_POST_RESTART_OBSERVER_MERGED_VALIDATED_413 / TASK_REGISTRY_PREFLIGHT_CONTINUE_REQUIRED_BEFORE_MUTATION / CONVERGENCE_OWNER_RECONCILIATION_REQUIRED_IF_COORDINATE_CONVERGENCE_OBSERVED / AUTHENTIC_CANONICAL_WORK_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_RESIDENT_SOURCE_PROMOTION_CONSUMPTION_NOT_OBSERVED / AUTHENTIC_TVC_MATERIALIZATION_AND_RESTART_NOT_OBSERVED / AUTHENTIC_TVC_RUNTIME_OBSERVATION_NOT_OBSERVED / LIVE_APPLE_OWNER_INGRESS_READY_NOT_OBSERVED / AUTHENTIC_CURRENT_IPHONE_INSTALL_LISTENER_DISCOVERY_PENDING`
