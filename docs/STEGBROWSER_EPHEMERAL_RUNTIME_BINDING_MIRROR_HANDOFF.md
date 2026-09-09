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

`.github` PR #1199 is merged at `04ce23ac8d33551dba401c8fc32fdbd766102042` after all three exact-head validation lanes passed. It stages `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001` through the existing `canonical_work_coordination` resident consumer. The request is COSV-bound to `40000100100000`, uses TV/TVC as credential authority, grants no execution authority, requires no GitHub token, and permits no network source fetch.

The resident consumer seeds the exact StegBrowser task shard when absent and preserves an already-existing resident shard byte-for-byte so a later source refresh cannot overwrite newer resident coordination state. The same existing dispatcher selector and shared Universal InTr listener are reused; no second scheduler, WorkerCoordinator, listener, browser runtime, or credential path is introduced.

Expected authentic resident evidence after resident dispatch:

- `receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json`
- nested `runtime/canonical-work-stegbrowser-ephemeral-runtime-binding/receipts/sovereign-host/canonical-work-event-bootstrap.latest.json`
- task-specific `INGRESS_ADMITTED` ingress/consumption evidence produced by the shared Canonical Work/InTr path

Source, CI, merge, request staging, or heartbeat progression must not substitute for those receipts.

## Credential-session reuse boundary

Repository review identified an existing owner-browser sealing and SKAP/InTr provider-session pattern in Site/TVC. Its relevant invariants are compatible with StegBrowser: TV/TVC remains credential authority, SKAP or KV-hosted SKAP Vault remains sealed credential custody, the current device/browser is an ephemeral owner-authorized edge, ordinary KV has no credential decryption authority, GitHub has no runtime credential authority, plaintext credential carriage is forbidden, browser persistence/logging is forbidden, and destination changes/blind retries fail closed.

StegBrowser credentialed-session work should reuse this boundary rather than creating a new credential architecture. Reuse is source-direction only until an authentic governed provider-session binding and ephemeral browser execution receipt are observed.

## WorkerCoordinator projection

The canonical task record remains pre-ingress with `worker_claim.projection_only=true` and no fabricated claim/fence reference. WorkerCoordinator remains the source for an authentic execution claim/fence after governed admission and reconciliation.

## Active continuation

1. Observe authentic resident request consumption and task-specific shared InTr `INGRESS_ADMITTED` evidence.
2. Reconcile the admitted task through Master Records / WorkerCoordinator without inferring claim authority from the ingress receipt.
3. Bind the admitted StegSocials observation request to StegBrowser execution and preserve terminal destruction evidence.
4. Reuse the existing TV/TVC + SKAP owner-browser provider-session boundary for one credentialed ephemeral browser session without embedding raw credential/session material in repository state, lease payloads, retained artifacts, cookies, history, or a persistent browser profile.
5. Verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## Current state

`RESIDENT_REQUEST_MERGED_GREEN / STEGSOCIALS_CALLER_MERGED / SHARD_AWARE_INTR_MERGED / AUTHENTIC_RESIDENT_ADMISSION_AND_CREDENTIALED_SESSION_PENDING`
