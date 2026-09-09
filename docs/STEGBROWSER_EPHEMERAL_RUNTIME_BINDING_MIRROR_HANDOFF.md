# StegBrowser Ephemeral Runtime Binding Mirror Handoff

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV profile: `task.v1`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Canonical vector: `control/task-vectors/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Index shard: `control/task-vector-index.d/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Implementation handoff: `StegVerse-Labs/StegBrowser/docs/STEGBROWSER_ECOSYSTEM_EPHEMERAL_MIRROR_HANDOFF.md`

## Observed browser state

Merged StegBrowser source includes a Playwright/Chromium ephemeral execution substrate that consumes the bounded lease contract, opens a fresh browser context, validates origin/action/navigation scope, retains only admitted commitments and receipts, closes the context/browser, and emits a terminal destruction receipt.

Observed execution evidence:

- `StegVerse-Labs/StegBrowser@d9453e9a2e2dd56ed16a99b2ce2b297dc613de48`
- run `34298624360`: authentic Chromium retrieval of `https://stegverse.org/` + terminal destruction validation
- artifact `10084081467`, digest `sha256:a9612d5be08128a5b7dae59114499921ef66fad1101dc6701ec23839c17499d5`
- `StegVerse-Labs/StegBrowser@dd596c4cb3ccbdcd85758b4d12bc8ad9e2ee539d`
- run `34298752980`: authentic bounded Chromium retrieval of the supplied StegVerse Facebook publication URL + terminal destruction validation
- artifact `10084130220`, digest `sha256:eabb6cfe6e8e1c5a9464d3b684260f458f5adb75e72db1599963fb189f5f8a6c`

These observations prove the ephemeral browser substrate and external public-surface reachability. They do not by themselves prove governed resident admission or credentialed-site access.

## Ecosystem caller state

StegSocials PR #4 is merged at `d8e1e0bc19d154cd0f2818fa688dd066558ece3c`. The adapter emits bounded StegBrowser publication-observation requests, requests no credential material or persistent browser identity, validates terminal destruction, and preserves `observation_only=true` / `publication_proven=false` semantics.

## Canonical InTr state

Generic sharded Canonical Work ingress support is merged in `.github` PR #1198 at `934073a6b68427c1823860652b714df5f7ea43b3`. Canonical tasks registered in `data/canonical-task-records/` can resolve through the existing shared Universal InTr route and project post-ingress state without duplication into the legacy monolithic registry.

## Resident request staging

Active PR #1199 stages `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001` through the existing `canonical_work_coordination` resident consumer. The request is COSV-bound to `40000100100000`, uses TV/TVC as credential authority, grants no execution authority, requires no GitHub token, and permits no network source fetch.

The resident consumer now seeds the exact StegBrowser task shard when absent and preserves an already-existing resident shard byte-for-byte so a later source refresh cannot overwrite newer resident coordination state. The same existing dispatcher selector and shared Universal InTr listener are reused; no second scheduler, WorkerCoordinator, listener, or credential path is introduced.

Expected authentic resident evidence after merge and resident dispatch:

- `receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json`
- nested `runtime/canonical-work-stegbrowser-ephemeral-runtime-binding/receipts/sovereign-host/canonical-work-event-bootstrap.latest.json`
- task-specific `INGRESS_ADMITTED` ingress/consumption evidence produced by the shared Canonical Work/InTr path

Source, CI, merge, request staging, or heartbeat progression must not substitute for those receipts.

## WorkerCoordinator projection

The canonical task record remains pre-ingress with `worker_claim.projection_only=true` and no fabricated claim/fence reference. WorkerCoordinator remains the source for an authentic execution claim/fence after governed admission and reconciliation.

## Active continuation

1. Complete and merge PR #1199 only after all repository validation lanes are green.
2. Observe authentic resident request consumption and task-specific shared InTr `INGRESS_ADMITTED` evidence.
3. Reconcile the admitted task through Master Records / WorkerCoordinator without inferring claim authority from the ingress receipt.
4. Bind the admitted StegSocials observation request to StegBrowser execution and preserve terminal destruction evidence.
5. Connect the existing TV/TVC + SKAP runtime boundary for one credentialed ephemeral browser session without embedding raw credential/session material in repository state, lease payloads, or retained artifacts.
6. Verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## Current state

`RESIDENT_REQUEST_STAGED_IN_PR_1199 / STEGSOCIALS_CALLER_MERGED / SHARD_AWARE_INTR_MERGED / AUTHENTIC_RESIDENT_ADMISSION_AND_CREDENTIALED_SESSION_PENDING`
