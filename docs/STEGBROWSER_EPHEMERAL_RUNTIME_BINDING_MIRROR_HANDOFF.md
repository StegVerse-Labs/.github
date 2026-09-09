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

StegBrowser has authentic public Chromium execution evidence for `https://stegverse.org/` and the supplied StegVerse Facebook publication surface, with terminal session destruction and minimized retained evidence. These observations prove the ephemeral browser substrate and public-surface reachability; they do not prove governed resident admission, provider authentication, a browser-created publication, or current-iPhone resident availability.

## Merged native Facebook source path

Merged StegBrowser source includes opaque TV/TVC + SKAP credential-session binding, callback-only in-memory credential injection, a credential-aware ephemeral runner, bounded Facebook runtime/profile checks, concrete semantic Playwright Page interaction, publication proof semantics, canonical URL/object identity validation, and terminal destruction.

Key merged source includes:

- `StegVerse-Labs/StegBrowser@42f9a78b513586d19ff9c5447b725ef29c168390`
- `StegVerse-Labs/StegBrowser@fabcc468dde8bca1161a2e564fb17af389404cb3`
- `StegVerse-Labs/StegBrowser@3f27c8420cca8fc72e6caad305ba52cdd3cd3821`
- `StegVerse-Labs/StegBrowser@4d929f8f82a19663233ebbe7cd958ef686c1d228`

## Native iOS resident source, app target, and durable custody

`StegVerse-Labs/StegBrowser@86cb4c42bbde1366ca03088a01983273f73de400` merged the standalone loopback-only iOS resident listener and bounded lifecycle source.

`StegVerse-Labs/StegOS@eb99b9222eba056478aa8d7ed3bc3bafb54fc194` then compiled the resident core/listener/lifecycle into the existing `StegOSMobile` application target. Its app-target validation passed StegOS CI `34304328189` and Apple toolchain run `34304328284`.

The next source gap was durability: validated Site custody evidence was retained only in process memory. That gap is now closed in source. `StegVerse-Labs/StegOS@bfa580942ee834799f87fdff3a9f1ea8d78067d4` merges app-local retained evidence storage keyed by canonical `SV-NODE-[0-9a-f]{24}` identity with these invariants:

```text
same proof -> idempotent RETAINED
conflicting proof -> refuse
app/process reconstruction -> reload and revalidate exact retained envelope
corrupt or mismatched retained state -> fail closed
write -> atomic
persistence authority -> NONE_EVIDENCE_ONLY
```

Exact-head validation for the durable source passed:

- StegOS CI `34306233655`: SUCCESS;
- iOS Apple Toolchain Validation `34306233903`: SUCCESS.

The durable store does not grant WorkerCoordinator, InTr, credential, Master Records, publication, heartbeat, node-identity, or SV002 authority. Source durability also does not prove that any authentic Site custody envelope has yet been retained on the current iPhone.

## Canonical Site node binding

Current `StegOSMobile` source already contains the canonical Site node-binding path through `stegverse://resident-rendezvous/activate`. It requires a canonical `SV-NODE-[0-9a-f]{24}` reference and Node Receipt #1 SHA-256, retains the binding locally with authority effect `NONE_BINDING_ONLY`, and starts the bounded local lifecycle from that canonical identity rather than deriving a node from mutable hardware metadata.

Current source state therefore separates three facts:

1. app-target transport source is compiled and validated;
2. durable local evidence retention is merged and validated;
3. authentic current-iPhone listener readiness and discovery readback are still unobserved.

## Ecosystem caller state

The native Facebook publication caller is merged at `StegVerse-Labs/StegSocials@122811f8f44dc2494a1d5e771d50c210d1d8a555` after validation run `34302291053` passed.

A complete live publication still requires the exact approved content commitment, target account, visible result, real Facebook object ID, canonical Facebook URL, successful terminal destruction, and absence of retained secret/session/profile state.

## Canonical InTr / resident staging state

Generic sharded Canonical Work ingress and task-specific resident request staging are merged. The request remains COSV-bound to `40000100100000`, uses TV/TVC as credential authority, grants no execution authority, requires no GitHub runtime token, and permits no network source fetch.

Expected authentic evidence remains:

- `receipts/sovereign-host/canonical-work-stegbrowser-ephemeral-runtime-binding-request-consumption.latest.json`;
- `runtime/canonical-work-stegbrowser-ephemeral-runtime-binding/receipts/sovereign-host/canonical-work-event-bootstrap.latest.json`;
- task-specific shared InTr `INGRESS_ADMITTED` evidence;
- authentic WorkerCoordinator claim/fence produced after governed reconciliation.

Source, CI, merge, local persistence capability, task staging, or heartbeat progression must not substitute for those receipts.

## WorkerCoordinator projection

The canonical record remains pre-activation with `worker_claim.projection_only=true` and no fabricated claim/fence reference. WorkerCoordinator remains authoritative for authentic execution claim/fence state.

## Active continuation

1. Extend the existing canonical Site node-bound `SV001ResidentActivationController` with a same-device discovery probe rather than introducing a second activation/binding controller.
2. After the bounded loopback session starts, read `GET /api/resident-rendezvous/v1/discovery` from `127.0.0.1:8000` and verify exact schema, state, canonical node reference, TV/TVC credential authority, and NONE discovery authority.
3. Persist a component runtime receipt only after exact discovery readback; explicitly keep InTr admission, WorkerCoordinator claim, canonical request consumption, provider session, and publication observations false until separately observed.
4. Compile and validate that source with StegOS CI and Apple toolchain, then merge.
5. Materialize the canonical Site node binding on the current iPhone and obtain authentic local listener/discovery evidence.
6. Observe authentic resident request consumption and task-specific shared InTr `INGRESS_ADMITTED` evidence.
7. Reconcile through Master Records / WorkerCoordinator and obtain authentic claim/fence evidence.
8. Resolve one admitted Facebook provider session through the existing TV/TVC + SKAP callback-only boundary.
9. Execute exactly one already-approved StegSocials Facebook release through the merged StegBrowser path.
10. Verify Facebook object ID, canonical URL, exact content commitment, visibility, terminal destruction, and publication custody.
11. Implement LinkedIn company-page parity, then verify propagation under `STEGBROWSER-ECOSYSTEM-PROPAGATION-VERIFY-001`.

## Installation / integration remainder

- Same-device discovery/self-readback source -> `StegVerse-Labs/StegOS`
- Authentic current-iPhone listener/discovery proof -> `StegVerse-Labs/StegOS`
- Resident request consumption / InTr evidence -> `StegVerse-Labs/.github`
- WorkerCoordinator reconciliation -> `StegVerse-Labs/.github` + `master-records/orchestration`
- Admitted Facebook provider session -> `StegVerse-Labs/TVC` + `StegVerse-Labs/StegBrowser`
- First live Facebook publication/readback proof -> `StegVerse-Labs/StegBrowser` + `StegVerse-Labs/StegSocials`
- Publication receipt custody -> `master-records/orchestration`
- LinkedIn runtime/profile -> `StegVerse-Labs/StegBrowser`
- LinkedIn caller parity -> `StegVerse-Labs/StegSocials`
- Release propagation/status -> `StegVerse-Labs/Site`
- Publication provenance -> `GCAT-BCAT-Engine/Publisher`
- Governance/admissibility docs -> `StegVerse-Labs/admissibility-wiki`
- Guardian/security docs -> `StegVerse-Labs/stegguardian-wiki`

## Current state

`NATIVE_FACEBOOK_SOURCE_PATH_MERGED_VALIDATED / STEGSOCIALS_NATIVE_CALLER_MERGED_VALIDATED / STEGOSMOBILE_RESIDENT_APP_TARGET_MERGED_APPLE_COMPILED / STEGOSMOBILE_DURABLE_LOCAL_CUSTODY_SOURCE_MERGED_APPLE_COMPILED / CANONICAL_TASK_COSV_INSTALLED / AUTHENTIC_CURRENT_IPHONE_WORKER_INTR_SESSION_PUBLICATION_READBACK_CUSTODY_PENDING`
