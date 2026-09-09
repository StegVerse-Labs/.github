# StegBrowser Ephemeral Runtime Binding Mirror Handoff

## Task pointer

- Goal Task ID: `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`
- COSV profile: `task.v1`
- COSV vector: `40000100100000`
- Canonical record: `data/canonical-task-records/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Canonical vector: `control/task-vectors/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Index shard: `control/task-vector-index.d/STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001.json`
- Browser implementation handoff: `StegVerse-Labs/StegBrowser/docs/STEGBROWSER_ECOSYSTEM_EPHEMERAL_MIRROR_HANDOFF.md`
- Browser iOS handoff: `StegVerse-Labs/StegBrowser/docs/STEGBROWSER_IOS_RESIDENT_RENDEZVOUS_MIRROR_HANDOFF.md`
- Native app-target handoff: `StegVerse-Labs/StegOS/docs/STEGBROWSER_IOS_RESIDENT_APP_TARGET_MIRROR_HANDOFF.md`

## Observed browser state

StegBrowser has authentic public Chromium execution evidence for both `https://stegverse.org/` and the supplied StegVerse Facebook publication surface, with terminal session destruction and minimized retained evidence.

Those observations prove the ephemeral browser substrate and external public-surface reachability. They do not prove governed resident admission, provider authentication, a browser-created publication, or current-iPhone resident availability.

## Merged native Facebook source path

Merged StegBrowser source includes:

- opaque TV/TVC + SKAP credential-session binding;
- callback-only in-memory credential context injection;
- credential-aware CLI-blind ephemeral runner;
- social publication request/observation proof contract;
- Facebook runtime/profile with exact account/content/lease checks;
- concrete semantic Playwright Facebook Page driver;
- end-to-end Facebook publication entrypoint from transient session injection through Page interaction, visible post observation, canonical URL/object identity validation, and terminal destruction.

Key merged commits:

- `StegVerse-Labs/StegBrowser@42f9a78b513586d19ff9c5447b725ef29c168390`
- `StegVerse-Labs/StegBrowser@fabcc468dde8bca1161a2e564fb17af389404cb3`
- `StegVerse-Labs/StegBrowser@3f27c8420cca8fc72e6caad305ba52cdd3cd3821`
- `StegVerse-Labs/StegBrowser@4d929f8f82a19663233ebbe7cd958ef686c1d228`

## Native iOS resident source and app-target state

`StegVerse-Labs/StegBrowser@86cb4c42bbde1366ca03088a01983273f73de400` merged and validated the standalone iOS loopback listener + bounded lifecycle source:

- loopback-only Network.framework listener on `127.0.0.1`;
- discovery / Site governed-custody evidence routes;
- CORS bounded to `https://stegverse.org` and `https://www.stegverse.org`;
- one local session at a time with maximum 900-second lifetime;
- automatic teardown and stale-session stop refusal;
- no WorkerCoordinator, InTr, credential, custody, node-identity, or execution authority.

The native integration has now advanced into the actual physical iPhone application source. `StegVerse-Labs/StegOS@eb99b9222eba056478aa8d7ed3bc3bafb54fc194` compiles the StegBrowser resident rendezvous core/listener/lifecycle inside the existing `StegOSMobile` target through the already-targeted `MobileRuntimeState.swift` source.

That app-target binding preserves:

- exact resident discovery/evidence schemas;
- canonical G23 proof receipt binding;
- canonical `SV-NODE-[0-9a-f]{24}` requirement;
- no derivation or minting of node identity from local hardware metadata;
- exact `CURRENT_USER_IPHONE`, InTr admission, reconstruction PASS, Master Records owner, and no-authority custody-proof predicates;
- deterministic proof SHA-256 verification;
- loopback-only transport and 900-second maximum lifecycle;
- task `STEG-BROWSER-EPHEMERAL-RUNTIME-BINDING-001`, COSV `40000100100000`, TV/TVC credential authority, GitHub runtime authority NONE.

Validation evidence for the app-target source:

- StegOS CI run `34304328189`: SUCCESS;
- iOS Apple Toolchain Validation run `34304328284`: SUCCESS, including unsigned compilation of `StegOSMobile` and embedded extensions.

This satisfies source/app-target compilation integration. It does **not** prove that the listener has started on the participant's current iPhone.

## Ecosystem caller state

The native Facebook publication caller is merged at `StegVerse-Labs/StegSocials@122811f8f44dc2494a1d5e771d50c210d1d8a555` after `Validate StegSocials Objects` run `34302291053` passed.

The caller converts a READY Personal-KV/SKAP release decision into a bounded StegBrowser lease, exact social publication request, and opaque credential-session request. A COMPLETE live publication requires the exact approved content commitment, target account, visible result, real Facebook object ID, canonical Facebook URL, successful terminal destruction, and no retained secret/session/profile state.

## Canonical InTr / resident staging state

Generic sharded Canonical Work ingress and task-specific resident request staging are merged. The request is COSV-bound to `40000100100000`, uses TV/TVC as credential authority, grants no execution authority, requires no GitHub token, and permits no network source fetch.

Repository-visible inspection in this continuation confirmed:

- `control/resident-execution-request.d/canonical-work-stegbrowser-ephemeral-runtime-binding-001.json` remains `REQUESTED`;
- `receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json` is not present on main;
- `runtime/canonical-work-stegbrowser-ephemeral-runtime-binding/receipts/sovereign-host/canonical-work-event-bootstrap.latest.json` is not present on main.

The consumer source already includes the StegBrowser task selector and expected receipt paths. The remaining gap is authentic current-device resident execution/evidence, not missing repository dispatch scaffolding.

## WorkerCoordinator projection

The canonical record remains pre-activation with `worker_claim.projection_only=true` and no fabricated claim/fence reference. WorkerCoordinator remains authoritative for authentic execution claim/fence state.

## Active continuation

1. Supply the StegOSMobile app-target binding with an externally canonical sovereign node reference from the existing admitted node/WorkerCoordinator path; do not derive one from mutable hardware metadata.
2. Start one bounded current-iPhone resident rendezvous session and retain authentic local listener/discovery evidence.
3. Observe authentic resident request consumption and task-specific shared InTr `INGRESS_ADMITTED` evidence.
4. Reconcile the admitted task through Master Records / WorkerCoordinator and obtain authentic claim/fence evidence.
5. Resolve one admitted Facebook provider session only through the existing TV/TVC + SKAP callback-only boundary.
6. Supply that live capability in memory to the merged StegBrowser Facebook publication entrypoint.
7. Execute exactly one already-approved StegSocials Facebook release.
8. Independently verify the resulting Facebook object ID, canonical URL, exact content commitment, visibility, and terminal destruction receipt.
9. Emit the StegSocials live publication-attempt receipt and complete KV / Master Records custody.
10. Implement LinkedIn company-page parity using the same boundaries.
11. After authentic publication/custody proof, review release readiness and verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## Installation / integration remainder

- Canonical node-ref runtime injection -> `StegVerse-Labs/StegOS` + `StegVerse-Labs/.github`
- Authentic current-iPhone listener/discovery proof -> `StegVerse-Labs/StegOS`
- Authentic resident request consumption / InTr evidence -> `StegVerse-Labs/.github`
- Authentic resident Facebook session execution -> `StegVerse-Labs/TVC` + `StegVerse-Labs/StegBrowser`
- First live Facebook publication/readback proof -> `StegVerse-Labs/StegBrowser` + `StegVerse-Labs/StegSocials`
- Publication receipt custody -> `master-records/orchestration`
- LinkedIn interaction/runtime profile -> `StegVerse-Labs/StegBrowser`
- LinkedIn caller parity -> `StegVerse-Labs/StegSocials`
- Release propagation/status -> `StegVerse-Labs/Site`
- Publication provenance -> `GCAT-BCAT-Engine/Publisher`
- Governance/admissibility docs -> `StegVerse-Labs/admissibility-wiki`
- Guardian/security docs -> `StegVerse-Labs/stegguardian-wiki`

## Current state

`NATIVE_FACEBOOK_SOURCE_PATH_MERGED_VALIDATED / STEGSOCIALS_NATIVE_CALLER_MERGED_VALIDATED / STEGOSMOBILE_RESIDENT_APP_TARGET_SOURCE_MERGED_APPLE_COMPILED / CANONICAL_TASK_COSV_INSTALLED / AUTHENTIC_CURRENT_IPHONE_WORKER_INTR_SESSION_PUBLICATION_READBACK_CUSTODY_PENDING`
