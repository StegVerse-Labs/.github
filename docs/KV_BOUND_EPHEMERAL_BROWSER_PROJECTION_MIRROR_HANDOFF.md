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
Status: `ACTIVE / AUTHENTIC CURRENT-IPHONE PROJECTION_CONTEXT_READY OBSERVED / EXACT JSON BYTES -> STEGOS CONSUMER NEXT`

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

### Authentic current-iPhone recovery

The first published Safari invocation reached:

```text
FAIL_CLOSED: resident KV installation not verified
```

A separate ChatGPT in-app-browser attempt exposed an IndexedDB object-store mismatch. That remains a browser-partition-local observation and is not promoted as Safari runtime truth.

`Site#1197` reused the already-existing `StegVerseKVInstallationBridge` rather than adding a second KV/admission path. The repaired page exposes `Admit Existing KV Installation Receipt` only after the resident-verification predicate fails, owner-selects canonical `_System/installation.receipt.json`, requires the existing Device→KV path to return `device_local_kv_materialization_observed=true`, then automatically retries the original purpose-bound projection. `Save Projection JSON` remains hidden until `PROJECTION_CONTEXT_READY`.

PR #1197 merged at `bd4c64a4dfa8130d3b8c015a242fbab5afc67fa1` after focused KV TestFlight, Site Bootstrap, Site Handoff, and Ecosystem Heartbeat validations passed. Pages build/deployment run `34531380154` completed successfully. The implementation claim was terminalized by claim-registry-only `Site#1198`, merged at `1df85a660cef242f05819e2b847ef942dff88ae1`.

## Authentic current-iPhone projection success — 2026-09-10

The repaired published page was invoked again in Safari on the current iPhone. Owner-mediated installation receipt recovery completed sufficiently for the original purpose-bound projection retry to reach:

```text
state: PROJECTION_CONTEXT_READY
purpose: CURRENT_IPHONE_TESTFLIGHT_SIGNING
entry_state: ADMITTED
browser_capability_state: OBSERVED_COMPATIBLE
kv_installation_receipt_sha256: sha256:bd23d0bab718e83c374fc5584d0c6f455f6cd81f715defe220bc855c85ede601
authority_effect: NONE_PROJECTION_ONLY
```

This is authentic current-device evidence that the repaired Safari path crossed the earlier resident-installation failure and produced the governed projection context. It does not by itself prove that the exact downloadable nine-field JSON bytes have been retained outside the page or accepted by the StegOS consumer.

## Current first unresolved predicate

```text
EXACT_KV_PROJECTION_FILE_BYTES_BOUND_TO_STEGOS_CONSUMER
```

Required evidence next:

```text
exact downloaded stegverse-kv-testflight-projection.json
nine-field schema/field-set preserved byte-for-byte from emitted payload
StegOS consumer independently validates the projection
no private lineage/internal evidence leakage
no authority widening
```

## Next execution sequence

1. save `stegverse-kv-testflight-projection.json` from the currently successful Safari page;
2. return/upload that exact file without editing or reconstructing it from the screenshot;
3. feed the exact file to the merged StegOS TestFlight bootstrap projection consumer;
4. require consumer validation before exact IPA/WASM signer materialization;
5. continue TV/TVC app-resource resolution, provisioning, ephemeral same-device signing, same-session verification, and native Build Upload;
6. install through TestFlight;
7. observe retained StegOS/StegBrowser node materialization, source-HB lineage, same-device discovery and receipt-to-transition execution;
8. materialize current canonical global-measurement source into that retained node;
9. execute exactly one frozen measurement-only global convergence pass and retain `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json` before lane remediation.

## Authority boundaries

- KV remains continuity boundary.
- Interlock/InTr remains transition/admission authority.
- TV/TVC remains credential/provider authority.
- WorkerCoordinator remains claim/fence authority where applicable.
- HB remains observability/carrier only.
- Browser capability observation grants no identity or execution authority.
- GitHub Actions remain validation/evidence transport only.
- `PROJECTION_CONTEXT_READY` does not prove exact downloaded file custody, signing, TestFlight installation, retained runtime, or global measurement.

## README impact

Functional Site changes already carry repo-local handoff/test maintenance. This reconciliation changes evidence/continuation state only; no new `.github` README semantics are required.

## Manual work

On the current iPhone Safari page already showing `PROJECTION_CONTEXT_READY`, tap `Save Projection JSON`, save the exact `stegverse-kv-testflight-projection.json` without editing it, then upload that exact file for StegOS consumer validation and continuation.
