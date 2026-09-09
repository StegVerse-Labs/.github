# Global Runtime Evidence Measurement Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1294`
Status: `ACTIVE / INGRESS SOURCE REPAIRED / CURRENT-IPHONE SIGNER AND TVC BROWSER ROUTE SOURCE MERGED / STATIC WASM DISTRIBUTION AND AUTHENTIC RESIDENT MATERIALIZATION PENDING`

## Purpose

Execute exactly one authentic current-device/sovereign-resident measurement-only global runtime profile convergence cycle, preserving the frozen run baseline, exact first-failure observations, and before/after retained-node/HB/transition evidence without same-run remediation.

## Measurement invariants

- freeze one run ID before the ten-stage visitor begins;
- preserve exact source/profile/projection hashes;
- preserve before/after retained-node, source/current HB, state and transition commitments;
- `measurement_only=true`;
- `same_run_remediation_allowed=false`;
- `automatic_retry_after_first_failure=false`;
- preserve `PASS_CURRENT_RUN`, `PASS_HISTORICAL_EVIDENCE`, `FAILED_CURRENT_RUN`, and `NOT_REACHED` as distinct meanings;
- do not substitute GitHub Actions, hosted containers, source merge, unsigned build evidence, signing source, or browser transport source for authentic source-device runtime evidence.

## Attempt 1 — pre-loop ingress failure

The first measurement attempt never entered the ten-stage convergence loop. No measurement run ID was frozen and no `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` was produced.

Inspection found four concrete source defects:

1. the generic Canonical Work resident consumer did not include the global measurement request in its fixed `REQUEST_SPECS` set;
2. the measurement child was `ACTIVE`, while Canonical Work ingress requires the `PROPOSED -> INGRESS_ADMITTED` lifecycle;
3. stale resident monolithic-registry recovery could not resolve a newly registered exact canonical task shard;
4. the Canonical Work bootstrap triggered global node-profile convergence only for Runtime Profile Map, not for the dedicated measurement child.

## Ingress remediation

PR `StegVerse-Labs/.github#1296` repaired all four defects and merged at:

`607cedc2fed1c81cf20ff6250fa3421089284a8a`

The final README-complete source head `971877bbae3225704ab7fb03126f47c8fd86ae1c` passed exact-head deterministic, Heartbeat, organization validation, and resident-oriented validation checks before merge.

Merged behavior includes:

- explicit request `control/resident-execution-request.d/canonical-work-global-runtime-evidence-measurement-001.json`;
- `GLOBAL_MEASUREMENT_SPEC` in the existing Canonical Work resident consumer;
- exact canonical task-shard fallback when a preserved resident monolithic registry is stale;
- canonical `PROPOSED -> INGRESS_ADMITTED` lifecycle for the measurement child;
- dedicated measurement child invocation of the existing global node-profile convergence visitor;
- deterministic ingress regressions;
- README documentation of shard recovery and measurement-only child behavior.

No second dispatcher, scheduler, listener, WorkerCoordinator, heartbeat, or hosted runtime was introduced.

## Attempt 2 — post-ingress-repair observation

After PR #1296 merged, the authentic evidence surfaces were inspected again.

```text
measurement-child source request: MERGED
measurement-child consumer selector: MERGED
stale-registry shard recovery: MERGED
measurement-child convergence trigger: MERGED
measurement consumption receipt: NOT OBSERVED
global convergence receipt: NOT OBSERVED
frozen measurement run ID: NOT OBSERVED
ten-stage visitor entered: NO
```

The repaired source ingress is no longer the first unresolved condition. None of the 18 lanes may honestly be assigned a stage-01 through stage-10 failure from this observation.

## Source-device propagation finding

`scripts/refresh_sovereign_worker_runtime_source.py` refreshes from an already-local canonical source tree. It deliberately performs no clone, fetch, pull, network lookup, credential acquisition, or source transport.

`scripts/install_sovereign_worker_source_refresh_service.py` likewise watches an already-local source tree and is Linux/systemd-user specific. It cannot cause a remote GitHub merge to become source-device-local code on the current iPhone.

Once canonical source is local, that refresh layer may propagate source into applicable runtimes. The missing source-device transition occurs before that refresh: authentic current-iPhone resident/materialized distribution.

## Current-iPhone TestFlight source convergence — 2026-09-09

The current-iPhone delivery path advanced materially after the earlier rerun.

### Retained-node measurement baseline

StegOS PR #311 merged at:

`f85f815d830ffa07eef54f7e47f3dfe84a56cbc4`

The exact Python, unsigned device-package, and macOS/Xcode source-build gates passed before merge. This establishes source/build compatibility for the frozen current-iPhone measurement baseline; it is not physical-device evidence.

### Current-iPhone WASM signer convergence

StegOS PR #312 merged at:

`4692ab506838affcf39a628c4e01dc9994abbb7b`

Validated source head:

`d93e02857c09b912a46422f4cda58e9c684b9fb7`

All four exact-head gates passed after aligning the validation `wasm-bindgen` CLI to the Rust dependency schema version `0.2.128`.

Merged semantics include:

```text
execution_surface: CURRENT_USER_IPHONE
executor_class: SAME_DEVICE_BROWSER_WASM_IPA_SIGNER
external_machine_required: false
second_user_operated_machine_allowed: false
github_actions_execution_allowed: false
credential_authority: TV/TVC
credential custody: SKAP_SEALED_TV_TVC_OWNED
private signing key: opaque ephemeral current-iPhone WASM session
same-session signed-IPA verification: REQUIRED
App Store Connect app resource ID: TVC-resolved
```

### Current-iPhone TVC provider client

StegOS PR #313 merged at:

`b98fad08b1491f6d7c243b6d23d497cf9c00d62b`

Validated head:

`59db65fa93fe988c60d26b016186c5398d9ce5c6`

All four exact-head gates passed, including the full 1,387-test repository suite.

The signer is no longer source-orphaned. The merged callable action now binds:

```text
current-iPhone WASM signer
-> existing Universal InTr external-provider-operation profile
-> TVC:ProviderOperationBroker
-> https://tvc.stegverse.org/v1/provider-operation
```

The provider client uses no consumer credential and forbids protected authorization/API/admin/GitHub headers. It also corrected the provisioning dependency by separating certificate creation from profile creation and binding the returned certificate resource ID into the profile relationships.

### TVC browser transport exposure

Inspection found the TVC FastAPI provider route lacked browser CORS admission for the StegVerse current-iPhone origin. TVC PR #373 repaired that seam and merged at:

`01fbf9bcb22857db01e421bcc27e6eab6ec7488c`

Validated head:

`a7567b2a74a41fb2e14b17b49340788f02f21688`

The exact focused validation passed.

The primary runtime still serves the same `app.main.app` object, now through a narrow exposure wrapper that permits only:

```text
origin: https://stegverse.org
methods: POST, OPTIONS
headers: content-type, accept
browser credentials: false
```

Wrong-origin preflight is denied; invalid `{}` still returns `403 / unexpected request schema`. Provider-operation authority and credential custody remain TV/TVC.

## Recovered browser WASM package

The exact browser package generated by successful StegOS run `34394101439` remains available as artifact `10120870613`:

```text
artifact: stegos-current-iphone-wasm-web
artifact digest: sha256:cef2ef22a42195dced25bca2f9c99fab9f6a32f21062f1576386ee69a25d48ee
source head: d93e02857c09b912a46422f4cda58e9c684b9fb7
stegos_current_iphone_ipa_signer.js sha256: 17fe61cfdae43cbe5a1d1b211beb39838f58e982efdba90c7156fc36402f3adb
stegos_current_iphone_ipa_signer_bg.wasm sha256: 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
wasm bytes: 2277815
```

The browser WASM package is validated build output, but it is not currently present in the served `mobile/web-bootstrap` source or the `release/current-iphone-site-projection/manifest.json` distribution contract. The existing Site projection manifest predates the signer and contains none of the current-iPhone signer/TVC-client/action/WASM assets.

This is now a specific source-distribution condition rather than an unidentified signing-engine gap.

## Current-iPhone retained-node truth

Source/build now proves substantially more of the delivery chain, but authentic current-iPhone runtime evidence remains absent:

```text
current-iPhone retained node materialization: NOT OBSERVED
current-iPhone listener start: NOT OBSERVED
same-device discovery response: NOT OBSERVED
source-HB-root persistence runtime proof: NOT OBSERVED
authentic receipt-to-transition runtime execution: NOT OBSERVED
real TV/TVC App Store Connect provider operation: NOT OBSERVED
TestFlight upload: NOT OBSERVED
TestFlight installation: NOT OBSERVED
```

The current first unresolved global condition remains:

`PRE_LOOP_AUTHENTIC_SOURCE_DEVICE_RESIDENT_NOT_MATERIALIZED`

The next concrete source condition inside that physical prerequisite is:

`CURRENT_IPHONE_SIGNER_WASM_NOT_MATERIALIZED_IN_SERVED_BOOTSTRAP_DISTRIBUTION`

This remains outside the ten measured runtime stages. It is not evidence that any of the 18 component lanes failed profile resolution, node continuity, request consumption, or a later runtime predicate.

## Architectural implication

The persistent-node/ephemeral-operation architecture remains unchanged. Continuity lives in the profile-derived current-iPhone StegOS node. Signing keys, InTr operations, TVC provider calls, transport sessions, and task execution remain ephemeral.

The current source trajectory no longer requires a second Mac, a new provider broker, a new hosted runtime, Render, a new heartbeat, or a new authority plane.

## Next execution sequence

1. materialize the validated browser WASM package and its glue/action/client modules into the served current-iPhone StegOS/Site bootstrap distribution with exact byte/hash binding;
2. update the current-iPhone Site projection contract to include those assets and re-observe the destination baseline before mutation;
3. preserve GitHub Actions as validation/evidence transport only; the static signer artifact grants no signing/provider authority;
4. activate/observe the already-built TVC primary provider runtime through its existing authority-owned path;
5. execute authentic current-iPhone TVC app-resource resolution, provisioning, ephemeral signing, same-session verification, and native Build Upload;
6. install through TestFlight;
7. obtain authentic retained-node materialization, same-device discovery, source-HB lineage, and receipt-to-transition evidence;
8. deliver/materialize the canonical measurement source into that retained node;
9. rerun exactly one measurement-only convergence pass;
10. require a frozen run ID and `global-runtime-node-profile-convergence.latest.json` before interpreting any 18-lane histogram;
11. remediate measured lane failures only after preserving that first authentic receipt.

## Current result

`INGRESS_SOURCE_REPAIRED_MERGED / CURRENT_IPHONE_SIGNER_AND_TVC_BROWSER_ROUTE_SOURCE_MERGED / STATIC_WASM_DISTRIBUTION_PENDING / PRE_LOOP_AUTHENTIC_SOURCE_DEVICE_RESIDENT_NOT_MATERIALIZED`

## README impact

README reconciliation for the ingress source repair is merged. StegOS and TVC focused handoffs record their current-iPhone signer/provider changes and README review. This global update reconciles cross-repository evidence/state and does not itself change runtime behavior.

## Manual work

None for the current source reconciliation. Physical TestFlight/current-iPhone execution remains downstream of the static browser-package distribution and existing TV/TVC runtime activation path.
