# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-11

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / EXACT KV PROJECTION VALIDATED / TASK-0010 G6 RETAINED / TASK-0011 G7 AUTHENTIC / FOUR KV-GATE FILES PROJECTED / STATIC SUPPORT EXACT-BYTE TRANSPORT UNRESOLVED`

## Canonical architecture

KV is the private governed continuity boundary. Browser presentation is ephemeral. Interlock/InTr owns transition/admission; WorkerCoordinator/canonical allocator owns claim/fence; TV/TVC owns credentials/provider operations; HB is observability only; GitHub Actions are validation/evidence transport only. No Render or hosted fallback is admissible.

## Proven authentic evidence

Two authentic current-iPhone KV projection artifacts were accepted by the merged StegOS consumer:

```text
primary sha256 93caa302f310be097005c21639504bc13a7e8090d161d56cd0823c37363db3f8
repeat  sha256 064c8fcac9e1ee87c6f6dc73807689fded772865ae4b3f461b304d26aaf7df64
purpose CURRENT_IPHONE_TESTFLIGHT_SIGNING
entry_state ADMITTED
browser_capability_state OBSERVED_COMPATIBLE
persistence_effect NONE_EPHEMERAL_CONTEXT_ONLY
authority_effect NONE_PROJECTION_GATE_ONLY
```

TASK-2026-0010 was authentically recovered at generation 6 / fence 6 with `ALLOCATION_COMPLETE`, `CLAIM_GRANT_OBSERVED`, and journal replay `PASS`. It remains immutable predecessor provenance and is not widened.

TASK-2026-0011 was then authentically selected by the canonical allocator on the current iPhone:

```text
selected_task_id: TASK-2026-0011
claim_registry_generation: 7
claim_observation.state: CLAIM_GRANT_OBSERVED
fencing_token: 7
dependency_surface: site:current-iphone-kv-testflight-static-bootstrap
canonical_allocator_receipt.state: ALLOCATION_COMPLETE
canonical receipt sha256: sha256:3cd0aa9245be0ac5e9b81bc6c5a48aae0edc6f7c95162998e854feea04e75520
node journal sequence: 67
node journal entry sha256: 34d649f1227db25f1a9ddb38fbea709c0fdf4ff5ad0148bb781bbee5c18fb5cf
journal replay: PASS
allocator recovery/export mutation: false
```

No TASK-2026-0011 allocator retry is authorized or needed.

## Active Site workspace

```text
repository: StegVerse-Labs/Site
workspace: claim/current-iphone-kv-testflight-static-bootstrap-r1
canonical issue: StegVerse-Labs/Site#1220
pinned StegOS source: 19e2ea02a16bd703767aafcd47e71f5ec5efe3cf
Site handoff: docs/CURRENT_IPHONE_KV_TESTFLIGHT_STATIC_BOOTSTRAP_MIRROR_HANDOFF.md
```

The branch already contains byte-identical copies of all four new KV-gating files; destination Git blob identities exactly equal the pinned StegOS source:

```text
stegos-bootstrap/current-iphone-testflight.html
  c468ceef66a10f1475efc0406c0c9277def004ba
stegos-bootstrap/current-iphone-testflight-bootstrap.js
  e9962ba5589e5f0e3fa2ec32381d65bb41f4f39f
stegos-bootstrap/kv-bound-ephemeral-projection-context.js
  11f69313eae67b9a7f9126f2e1af331331291dec
stegos-bootstrap/kv-projection-file-loader.js
  2682b2f9203770203010146bafcd539313a42948
```

These four files alone are not a runnable product chain because the bootstrap imports the unchanged static predecessor support package.

## Exact static support package still required

The frozen StegOS successor manifest at the same pinned commit identifies the unchanged support chain that must be present on Site before merge/runtime claims:

```text
stegos-bootstrap/current-iphone-unsigned-ipa-materializer.js
stegos-bootstrap/StegOSMobile-unsigned-device.ipa
stegos-bootstrap/StegOSMobile-unsigned-device-manifest.json
stegos-bootstrap/StegOSMobile.signing-requirements.json
stegos-bootstrap/current-iphone-wasm-materializer.js
stegos-bootstrap/stegos_current_iphone_ipa_signer.js
stegos-bootstrap/stegos_current_iphone_ipa_signer_bg.wasm
stegos-bootstrap/current-iphone-wasm-signing-engine.js
stegos-bootstrap/current-iphone-ipa-signing-executor.js
stegos-bootstrap/current-iphone-tvc-provider-client.js
stegos-bootstrap/current-iphone-testflight-signing-action.js
contracts/current-iphone-ipa-signing-executor.v1.json
```

Frozen binary commitments:

```text
StegOSMobile-unsigned-device.ipa
  sha256 557d559082bdefca5fcc69c86f342d8cc035c2d803d154de5ed45b5677f80c35
  bytes 389564
  git blob 3183c95dbcd73ab7d86acad9b68aef41ea1110b0

stegos_current_iphone_ipa_signer_bg.wasm
  sha256 699dc3054788d779ba7920e332c661ef7eac001156f93ab7b1fe1b64ee5a4b93
  bytes 2277815
  git blob 74d9ece3a911c20ce9f89e879c91e027fab10c12
```

The authentic source artifacts were recovered through authorized StegOS workflow-artifact access: unsigned-device artifact `10119511850` and WASM artifact `10120870613`. Local hash verification matched the frozen successor commitments. Artifact recovery proves source availability only; it does not prove destination materialization.

## Transport investigation

The first Site transport run `34558913408` failed before mutation because `raw.githubusercontent.com` returned HTTP 404 for the non-public StegOS source.

Site commit `541823fec8c5b40201e98dfb767697e68cb79763` repaired the transport workflow to attempt a pinned second checkout and made the workflow self-triggering. Exact-head Site validation started successfully, but transport run `34611288342` failed at the StegOS checkout because the Site-scoped `GITHUB_TOKEN` has no cross-repository StegOS read permission (`Repository not found`). No product support bytes were committed by either failed run.

A direct connector-side Git tree experiment also established that a StegOS binary blob SHA cannot simply be referenced from the Site repository: GitHub rejected source blob `3183c95dbcd73ab7d86acad9b68aef41ea1110b0` as not a valid Site blob. Exact binary bytes must be transferred into Site's object database.

The failure is therefore a bounded exact-byte transport condition, not a KV, allocator, StegOS source, or runtime-architecture failure. Do not solve it by exposing a private StegOS credential in Site, widening GitHub Actions authority, using Render, or requiring a second user-operated machine.

## Current first unresolved predicate

`EXACT_STATIC_SIGNING_CHAIN_MATERIALIZED_AND_VERIFIED_ON_TASK_2026_0011_PRODUCT_BRANCH`

The next continuation should:

1. use the existing authorized connector/evidence channel to place the frozen support bytes into the TASK-2026-0011 Site workspace without exposing private-repository credentials;
2. verify every destination Git blob and frozen SHA-256/size commitment;
3. validate positive and fail-closed KV projection behavior against the complete product chain;
4. update Site README and both Site/canonical handoffs with exact validation evidence;
5. open the product PR only after the complete exact-byte chain exists;
6. merge only after exact-head checks pass and publication is observed;
7. then continue current-iPhone KV selection -> same-device signing -> TV/TVC Build Upload -> TestFlight install -> retained StegOS/StegBrowser evidence -> one frozen global measurement pass.

## Coordination hygiene

During connector write-capability discovery, an accidental empty `noop` file was created on `StegVerse-Labs/.github` main at commit `4a956862fc061e2ae5178c7a35997ebe91c046cf` and immediately deleted at `9d27831384028f9a5de375702f96f05e98a56a4f`. There is no net tree change and neither commit is task/runtime/validation evidence.

## Manual work

None. The current condition is repository-side exact-byte transport and validation.
