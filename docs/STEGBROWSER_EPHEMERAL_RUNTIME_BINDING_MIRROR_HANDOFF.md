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

StegBrowser has authentic public Chromium execution evidence for both `https://stegverse.org/` and the supplied StegVerse Facebook publication surface, with terminal session destruction and minimized retained evidence.

Those observations prove the ephemeral browser substrate and external public-surface reachability. They do not prove governed resident admission, provider authentication, or a browser-created publication.

## Merged native Facebook source path

The source path has advanced beyond observation-only integration. Merged StegBrowser source now includes:

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
- current reconciled StegBrowser main: `2948b4d3a70ccba3a4d09faaf8d9f8b4b46ed030`

The implementation-branch validation runs for the Facebook runtime/profile, concrete driver, and end-to-end entrypoint passed before merge.

## Ecosystem caller state

StegSocials now has both observation and native publication callers.

The native Facebook publication caller is merged at `StegVerse-Labs/StegSocials@122811f8f44dc2494a1d5e771d50c210d1d8a555` after `Validate StegSocials Objects` run `34302291053` passed.

The caller converts a READY Personal-KV/SKAP release decision into a bounded StegBrowser lease, exact social publication request, and opaque credential-session request. It emits no publication proof from connector/browser completion alone.

A COMPLETE live publication requires the exact approved content commitment, target account, visible result, real Facebook object ID, canonical Facebook URL, successful terminal destruction, and no retained secret/session/profile state.

## Canonical InTr / resident staging state

Generic sharded Canonical Work ingress and the task-specific resident request staging are merged. The request remains COSV-bound to `40000100100000`, uses TV/TVC as credential authority, grants no execution authority, requires no GitHub token, and permits no network source fetch.

Expected authentic resident evidence remains:

- `receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json`
- nested `runtime/canonical-work-stegbrowser-ephemeral-runtime-binding/receipts/sovereign-host/canonical-work-event-bootstrap.latest.json`
- task-specific `INGRESS_ADMITTED` ingress/consumption evidence from the shared Canonical Work/InTr path
- authentic WorkerCoordinator claim/fence produced after governed reconciliation

Source, CI, merge, request staging, heartbeat progression, or task registry state must not substitute for those receipts.

## Credential-session boundary

StegBrowser reuses the existing owner-browser TV/TVC + SKAP/InTr credential pattern rather than creating another credential system.

Required invariants remain:

- TV/TVC retains credential authority;
- SKAP or KV-hosted SKAP Vault retains sealed credential custody;
- the browser is an ephemeral owner-authorized execution edge;
- ordinary KV has no credential decryption authority;
- GitHub has no runtime credential authority;
- plaintext credential carriage is forbidden;
- live session handles remain outside lease payloads, argv, repository state, logs, and retained evidence;
- browser profile/cookie/history persistence is forbidden;
- credential resolution occurs callback-only at the execution edge.

## WorkerCoordinator projection

The canonical record remains pre-activation with `worker_claim.projection_only=true` and no fabricated claim/fence reference. WorkerCoordinator remains authoritative for authentic execution claim/fence state.

## Active continuation

1. Observe authentic resident request consumption and task-specific shared InTr `INGRESS_ADMITTED` evidence.
2. Reconcile the admitted task through Master Records / WorkerCoordinator and obtain authentic claim/fence evidence.
3. Resolve one admitted Facebook provider session only through the existing TV/TVC + SKAP callback-only boundary.
4. Supply that live capability in memory to the merged StegBrowser Facebook publication entrypoint.
5. Execute exactly one already-approved StegSocials Facebook release.
6. Independently verify the resulting Facebook object ID, canonical URL, exact content commitment, visibility, and terminal destruction receipt.
7. Emit the StegSocials live publication-attempt receipt and complete KV / Master Records custody.
8. Implement LinkedIn company-page parity using the same boundaries.
9. After authentic publication/custody proof, review release readiness and verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## Installation / integration remainder

- Authentic resident Facebook session execution -> existing `StegVerse-Labs/TVC` + `StegVerse-Labs/.github` resident edge
- First live Facebook publication/readback proof -> `StegVerse-Labs/StegBrowser` + `StegVerse-Labs/StegSocials`
- Publication receipt custody -> `master-records/orchestration`
- LinkedIn interaction/runtime profile -> `StegVerse-Labs/StegBrowser`
- LinkedIn caller parity -> `StegVerse-Labs/StegSocials`
- Release propagation/status -> `StegVerse-Labs/Site`
- Publication provenance -> `GCAT-BCAT-Engine/Publisher`
- Governance/admissibility docs -> `StegVerse-Labs/admissibility-wiki`
- Guardian/security docs -> `StegVerse-Labs/stegguardian-wiki`

## Current state

`NATIVE_FACEBOOK_SOURCE_PATH_MERGED_VALIDATED / STEGSOCIALS_NATIVE_CALLER_MERGED_VALIDATED / CANONICAL_TASK_COSV_INSTALLED / AUTHENTIC_WORKER_INTR_SESSION_PUBLICATION_READBACK_CUSTODY_PENDING`
