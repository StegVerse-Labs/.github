# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-10

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Merged KV producer: `StegVerse-Labs/continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`
Merged StegOS consumer: `StegVerse-Labs/StegOS#314` -> `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`
Merged Site purpose-bound adapter: `StegVerse-Labs/Site#1178` -> `3da593a61a536a625fcea4a26df8d1f491f00b44`
Status: `ACTIVE / PRODUCER+CONSUMER+PURPOSE-BOUND SITE ADAPTER MERGED / AUTHENTIC CURRENT-IPHONE INVOCATION NEXT`

## Canonical architecture

KV is the private governed state-transition continuity boundary. A physical device is an interchangeable interoperability node after proof of control/reconstruction of the existing KV. StegOS is the runtime node, StegBrowser is the browser-capability node, and Safari/Chrome/webviews/comparable browser containers are ephemeral presentation carriers rather than identity or continuity roots.

The intended first-install seam is:

```text
minimal rendezvous
-> KV/device continuity confirmation
-> authentic KV entry transition/admission
-> actual browser/container capability observation
-> KV produces opaque purpose-bound projection context
-> current iPhone supplies the projection artifact to the minimal page
-> page validates it in memory
-> exact IPA/WASM signer materializes only after the gate passes
-> TV/TVC signing/upload boundary
-> TestFlight install
-> authentic retained runtime observation
```

No browser-local IndexedDB, cookies, localStorage, sessionStorage, browser profile, user-agent identity, device fingerprint, or public bootstrap is the continuity/privacy root for this path.

## Source implementation now merged

### KV producer

`StegVerse-Labs/continuity-vault-kit#206` merged as `47c363611210b7501cbb50abce768cfe0911057f`. It requires an already-admitted purpose-bound KV entry transition and same-lineage compatible browser-capability observation, rejects cross-lineage mixing and browser identity authority, and emits only opaque non-authorizing projection fields.

### StegOS consumer

`StegVerse-Labs/StegOS#314` merged as `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`. Exact-head StegOS CI, current-iPhone IPA signing validation, and WASM codesign validation passed before merge. The consumer independently validates the exact KV-bound projection before IPA/WASM materialization.

### Site purpose-bound Device -> KV adapter

`StegVerse-Labs/Site#1178` merged as `3da593a61a536a625fcea4a26df8d1f491f00b44`.

The merged adapter reuses the existing root-scoped current-device Device -> KV Universal InTr runtime rather than creating a second admission path. It deliberately reuses the already-supported `MY_KV_INSTALLATION_STATUS` request class and places exact purpose `CURRENT_IPHONE_TESTFLIGHT_SIGNING` inside the admitted request hash.

Merged Site surfaces include:

```text
assets/kv-testflight-projection-entry.js
assets/kv-testflight-projection-export.js
kv-testflight-projection.html
tests/kv-testflight-projection-entry.test.cjs
.github/workflows/kv-testflight-projection-entry.yml
docs/KV_TESTFLIGHT_PROJECTION_ENTRY_MIRROR_HANDOFF.md
```

The adapter requires the authentic `stegverse.device-kv-intr-materialization-ingress/v1` receipt with `state=INGRESS_ADMITTED`, verifies resident KV installation evidence, observes only signer-relevant browser APIs/features, records `browser_identity_authority=false`, and derives same-lineage entry/capability commitments. The export adapter emits only the canonical nine-field projection context and fails closed on lineage leakage or field drift.

The Site implementation claim is already terminalized as `RELEASED` with PR #1178 merge evidence. This closes the prior source-runtime-adapter reconciliation condition.

## Superseded Site-first allocation path

The temporary `.github` PR #1302 and Site issue #1180 were derived from the older Site-first static-bootstrap sequence before the KV-bound adapter state was reconciled. They are now closed unmerged/not-planned and are not execution authority or current continuation truth. No `TASK-2026-0010` from that unmerged branch is canonical registry state.

## Current first unresolved predicate

Source implementation is no longer the first missing predicate. The current unresolved condition is authentic execution on the current iPhone:

```text
AUTHENTIC_CURRENT_IPHONE_KV_TESTFLIGHT_PROJECTION_INVOCATION
```

Required evidence from one real invocation:

```text
purpose-bound Device->KV INGRESS_ADMITTED receipt
verified resident KV installation result
same-lineage compatible browser capability observation
exact opaque nine-field projection JSON
```

Source presence, merge state, CI, browser availability, or historical KV evidence must not be promoted into this runtime proof.

## Next execution sequence

1. verify that the merged `kv-testflight-projection.html` route is present in the active Site publication/deployment output;
2. invoke that route on the current iPhone;
3. require the actual Device->KV InTr admission, verified KV installation result, and capability observation to pass;
4. save the resulting `stegverse-kv-testflight-projection.json` exactly as emitted;
5. supply that exact projection file to the already-merged StegOS TestFlight bootstrap page;
6. continue TV/TVC app-resource resolution, provisioning, ephemeral same-device signing, same-session verification, and native Build Upload;
7. install through TestFlight;
8. observe retained StegOS/StegBrowser node materialization, source-HB lineage, same-device discovery and receipt-to-transition execution;
9. materialize current canonical global-measurement source into that retained node;
10. execute exactly one frozen measurement-only global convergence pass and retain `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` before any lane remediation.

## Authority boundaries

- KV remains continuity boundary.
- Interlock/InTr remains transition/admission authority.
- TV/TVC remains credential/provider authority.
- WorkerCoordinator remains claim/fence authority where applicable.
- HB remains observability/carrier only.
- Browser capability observation grants no identity or execution authority.
- GitHub Actions remain validation/evidence transport only.
- Site publication does not prove current-iPhone execution, signing, TestFlight installation, retained runtime or global measurement.

## README impact

The repositories that received functional source changes already carry their README/handoff updates. This reconciliation changes canonical coordination/evidence state only; no new `.github` README semantics are required.

## Manual work

None until the published current-iPhone invocation surface is confirmed. Once confirmed, the exact manual action is to open the published KV TestFlight projection page on the current iPhone, tap `Create KV Projection Context`, and save the emitted `stegverse-kv-testflight-projection.json` to Files for the next governed bootstrap step.
