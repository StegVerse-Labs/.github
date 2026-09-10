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
Merged Site Safari recovery: `StegVerse-Labs/Site#1197` -> `bd4c64a4dfa8130d3b8c015a242fbab5afc67fa1`
Status: `ACTIVE / AUTHENTIC SAFARI INVOCATION OBSERVED / RESIDENT KV RECOVERY MERGED+PUBLISHED / AUTHENTIC RETRY NEXT`

## Canonical architecture

KV is the private governed state-transition continuity boundary. A physical device is an interchangeable interoperability node after proof of control/reconstruction of the existing KV. StegOS is the runtime node, StegBrowser is the browser-capability node, and Safari/Chrome/webviews/comparable browser containers are ephemeral presentation carriers rather than identity or continuity roots.

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

## Merged implementation

### KV producer

`continuity-vault-kit#206` merged at `47c363611210b7501cbb50abce768cfe0911057f`. It requires an already-admitted purpose-bound KV entry transition and same-lineage compatible browser-capability observation, rejects cross-lineage mixing and browser identity authority, and emits only opaque non-authorizing projection fields.

### StegOS consumer

`StegOS#314` merged at `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`. The consumer independently validates the exact KV-bound projection before IPA/WASM materialization.

### Site purpose-bound Device -> KV adapter

`Site#1178` merged at `3da593a61a536a625fcea4a26df8d1f491f00b44`. It reuses the existing root-scoped current-device Device -> KV Universal InTr runtime and the supported `MY_KV_INSTALLATION_STATUS` request class, placing exact purpose `CURRENT_IPHONE_TESTFLIGHT_SIGNING` inside the admitted request hash. It requires authentic `INGRESS_ADMITTED`, verified resident KV installation, signer-relevant browser capability observation, and emits only the canonical nine-field projection.

### Authentic current-iPhone observation and recovery

The published page was invoked on the current iPhone. Safari reached the governed adapter and returned:

```text
FAIL_CLOSED: resident KV installation not verified
```

A separate ChatGPT in-app-browser attempt exposed an IndexedDB object-store mismatch. That remains a browser-partition-local observation and is not promoted as Safari runtime truth.

The Safari result established that the page and purpose-bound path execute on the current device but that the resident device-local KV did not currently expose a canonical installation receipt satisfying `KV_INSTALLATION_VERIFIED`.

`Site#1197` therefore reused the already-existing `StegVerseKVInstallationBridge` rather than adding a second KV/admission path. The repaired page exposes `Admit Existing KV Installation Receipt` only after the resident-verification predicate fails, owner-selects canonical `_System/installation.receipt.json`, requires the existing Device→KV path to return `device_local_kv_materialization_observed=true`, then automatically retries the original purpose-bound projection. `Save Projection JSON` remains hidden until `PROJECTION_CONTEXT_READY`.

PR #1197 merged at `bd4c64a4dfa8130d3b8c015a242fbab5afc67fa1` after its focused KV TestFlight, Site Bootstrap, Site Handoff, and Ecosystem Heartbeat validations passed. Pages build/deployment run `34531380154` for that functional merge completed successfully. The implementation claim was subsequently terminalized by claim-registry-only `Site#1198`, merged at `1df85a660cef242f05819e2b847ef942dff88ae1` after corrected terminalization validation passed.

## Superseded Site-first allocation path

The temporary `.github` PR #1302 and Site issue #1180 were derived from the older Site-first static-bootstrap sequence before the KV-bound adapter state was reconciled. They remain closed and are not execution authority or current continuation truth. No `TASK-2026-0010` from that unmerged branch is canonical registry state.

## Current first unresolved predicate

```text
AUTHENTIC_CURRENT_IPHONE_KV_INSTALLATION_RECEIPT_RECOVERY_AND_PROJECTION_RETRY
```

Required evidence from the repaired Safari path:

```text
owner-mediated canonical installation receipt selection if resident verification still fails
Device->KV admission with device_local_kv_materialization_observed=true
automatic retry of CURRENT_IPHONE_TESTFLIGHT_SIGNING
purpose-bound INGRESS_ADMITTED receipt
KV_INSTALLATION_VERIFIED result
same-lineage compatible browser capability observation
exact opaque nine-field projection JSON
```

Source presence, merge state, CI, Pages deployment, or historical KV evidence do not satisfy this runtime proof.

## Next execution sequence

1. re-open the repaired published `kv-testflight-projection.html` route in Safari on the current iPhone;
2. run `Create KV Projection Context`;
3. if resident KV verification fails, use `Admit Existing KV Installation Receipt` and select canonical `_System/installation.receipt.json`;
4. require observed Device→KV admission and automatic projection retry;
5. save `stegverse-kv-testflight-projection.json` exactly as emitted only after `PROJECTION_CONTEXT_READY`;
6. supply that exact file to the merged StegOS TestFlight bootstrap;
7. continue TV/TVC app-resource resolution, provisioning, ephemeral same-device signing, same-session verification, and native Build Upload;
8. install through TestFlight;
9. observe retained StegOS/StegBrowser node materialization, source-HB lineage, same-device discovery and receipt-to-transition execution;
10. materialize current canonical global-measurement source into that retained node;
11. execute exactly one frozen measurement-only global convergence pass and retain `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` before lane remediation.

## Authority boundaries

- KV remains continuity boundary.
- Interlock/InTr remains transition/admission authority.
- TV/TVC remains credential/provider authority.
- WorkerCoordinator remains claim/fence authority where applicable.
- HB remains observability/carrier only.
- Browser capability observation grants no identity or execution authority.
- GitHub Actions remain validation/evidence transport only.
- Site publication does not prove successful recovery/retry, projection emission, signing, TestFlight installation, retained runtime, or global measurement.

## README impact

Functional Site changes include repo-local handoff/test maintenance. This canonical reconciliation changes evidence/continuation state only; no new `.github` README semantics are required.

## Manual work

On the current iPhone in Safari, open the published KV TestFlight projection page and tap `Create KV Projection Context`. If resident verification fails, tap `Admit Existing KV Installation Receipt`, select canonical `_System/installation.receipt.json`, allow the automatic retry, and save `stegverse-kv-testflight-projection.json` only if state reaches `PROJECTION_CONTEXT_READY`.
