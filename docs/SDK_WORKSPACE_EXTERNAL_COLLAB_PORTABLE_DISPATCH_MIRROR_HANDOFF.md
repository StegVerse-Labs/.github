# SDK WorkSpace External-Collaboration Portable Dispatch Mirror Handoff

Updated: 2026-09-10
Repository: `StegVerse-Labs/.github`
Goal Task ID: `SDK-GENERIC-MANIFEST-DOWNSTREAM-PROPAGATION-003`
Canonical controlling handoff: `StegVerse-org/StegVerse-SDK:docs/SHARED_DOCS_EPHEMERAL_MANIFEST_WORKSPACE_MIRROR_HANDOFF.md`
Status: `ACTIVE / PORTABLE EXACT-DISPATCH REPAIR SOURCE IMPLEMENTED / VALIDATION PENDING`

## Pre-mutation Task Registry reconciliation

The canonical anti-collision evaluator was merged while this goal was still absent from `data/canonical-task-records`. Fresh inspection therefore exposed a deterministic `STOP_NOT_REGISTERED` prerequisite before further source mutation.

Registration PR `StegVerse-Labs/.github#1389` merged at `66cb83f9d8bed7dbadedde935fb005f6d186bd38`, adding the existing ACTIVE goal as `checkout_state=UNCLAIMED`, with COSV `71000000100110`, current handoff refs, exact mutation scope, unresolved predicates, and authority separation. The registration does not invent a WorkerCoordinator claim/fence.

The intended portable-bridge mutation shares the `.github` repository with ACTIVE `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`, so it is treated as a convergence surface rather than ignored. The current Global Runtime handoff was re-read before mutation. Its first unresolved predicate is the distinct current-iPhone TASK-2026-0011 G7 allocation evidence path on the Site/StegOS projection lane. This repair does not rerun TASK-0010/0011, alter allocator state, mutate retained iPhone state, create a resident runtime, or modify the global runtime profile/source-refresh implementation. It only makes two already-registered lower-level resident consumers addressable through the existing portable exact-selector bridge.

`TASK-REGISTRY-ANTI-COLLISION-AGGREGATION-001` remains coordination infrastructure only and grants no execution authority. No hard same-component/lineage collision was identified for this narrow portable-selector repair.

## Defect

The lower-level canonical dispatcher already registers:

```text
sdk_workspace_external_collab_client_secret_reseal
sdk_workspace_external_collab_consent_listener
```

and `refresh_sovereign_worker_runtime_source.py` already carries `control/resident-execution-request.d/` wholesale. However `scripts/refresh_and_dispatch_resident_requests.py` omitted both selectors from `ALLOWED_TARGET_CONSUMERS`. It also omitted the listener's three required non-secret resident configuration values from `NONSECRET_FORWARD`:

```text
STEGVERSE_GOOGLE_DRIVE_CLIENT_ID
STEGVERSE_OWNER_BINDING_DIGEST
STEGVERSE_STEGFIN_SOURCE_ROOT
```

Therefore an already-existing sovereign resident using the portable `refresh -> exact targeted dispatch` bridge could not select either merged WorkSpace consumer, and even a listener selection would have lost its required non-secret configuration before reaching the lower-level dispatcher.

## Repair

The existing portable bridge now:

1. admits exactly the two WorkSpace selectors without changing the historical default `cross_framework_current_basis_v04`;
2. forwards only the three required listener configuration values in addition to the existing non-secret allowlist;
3. retains the forbidden credential-environment rejection including GitHub tokens and provider API-key variables;
4. still refreshes only already-local canonical source with no network source fetch;
5. still invokes the existing generic dispatcher with one exact `--only-consumer` selector;
6. still requires an exact one-consumer dispatcher receipt before `REFRESH_AND_DISPATCH_COMPLETE`;
7. mints no claim/fence and grants no runtime, credential, transition, readiness, Gateway, Google-consent, provider-contact, signing, broadcast, or Heartbeat authority.

## Validation

`tests/test_sdk_workspace_external_collab_portable_dispatch.py` proves:

- both selectors are admitted and the historical default is unchanged;
- the three required non-secret listener values survive the portable bridge;
- undeclared environment values are not forwarded;
- GitHub-token-bearing execution remains rejected;
- each selector is passed to the generic dispatcher as exactly one consumer;
- completion requires the exact selector receipt;
- bridge authority remains NONE and source refresh remains non-runtime evidence.

Hosted CI is source validation only. It cannot prove resident refresh, request consumption, target custody, loopback health, public callback reachability, owner consent, provider execution, or WorkSpace readiness.

## README review

Root README already describes Task Registry/collision ordering, resident source refresh, TV/TVC credential authority, Interlock/InTr transition authority, and GitHub validation-only posture. This repair exposes no new public capability and creates no new runtime, so no README text change is required.

## Next sequence

1. validate this exact source head through repository, organization-control, Heartbeat, and applicable resident-dispatch regressions;
2. merge only if exact-head validation is green;
3. refresh the already-existing authorized sovereign resident from already-local canonical source and exact-dispatch `sdk_workspace_external_collab_client_secret_reseal` and `sdk_workspace_external_collab_consent_listener` independently;
4. retain their authentic secret-free receipts;
5. remediate only the exact returned resident blocker, if any;
6. do not initiate owner-present Google consent until target custody and sovereign callback reachability are both authentically proven.

## Human action

None.
