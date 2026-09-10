# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / 18 HB32 PROFILE-DERIVED NODES / MEASUREMENT HARDENING MERGED / KV-BOUND CURRENT-IPHONE RECOVERY MERGED+PUBLISHED / AUTHENTIC SAFARI RETRY NEXT`

## Canonical runtime model

```text
runtime/node profile
-> profile-derived retained StegOS node
-> immutable source-device HB lineage + current HB observation
-> ephemeral request consumption
-> ephemeral WorkerCoordinator claim/fence
-> ephemeral Interlock/InTr admission
-> ephemeral transport/provider/lease
-> component execution
-> exact receipt commitment
-> Master Records reconstruction
-> downstream propagation
```

Node identity/evidence/HB lineage persist. Claims/fences, InTr calls, transports, credentials, provider/browser/model/action sessions, and execution processes remain bounded and ephemeral. HB remains observability/freshness/correlation only.

## Measurement implementation state

- 18 HB32 runtime-node profiles plus profiled convergence runner: merged.
- StegClaw executable profile: merged.
- VACC executable profile: merged.
- typed ten-stage first-failure responses: `.github` PR #1292 merged at `e64c5d518af05dac6b9d09c3355d38d75bc27295`.
- definitive one-pass measurement hardening: PR #1293 merged at `44c6d88abb42351ec26a576e3136caec3400a613`.
- measurement ingress repair: PR #1296 merged.

The authentic measurement still requires one frozen run ID and `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json`. No lane failure histogram is authoritative before that receipt exists.

## Current source-device trajectory

The earlier Site-first static-bootstrap sequence is superseded. The active child is `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`.

```text
current device / minimal rendezvous
-> existing Device→KV Universal InTr
-> purpose CURRENT_IPHONE_TESTFLIGHT_SIGNING admitted in exact request
-> verified resident KV installation
-> same-lineage browser capability observation
-> opaque nine-field KV projection
-> StegOS TestFlight bootstrap validates projection in memory
-> exact IPA/WASM materialization
-> TV/TVC provisioning + ephemeral signing + Build Upload
-> TestFlight install
-> retained StegOS/StegBrowser runtime observation
-> one frozen global measurement pass
```

Merged/source/runtime evidence:

- KV producer: `continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`.
- StegOS consumer: `StegOS#314` -> `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`.
- Site purpose-bound Device→KV adapter/export/page: `Site#1178` -> `3da593a61a536a625fcea4a26df8d1f491f00b44`.
- authentic current-iPhone Safari invocation reached `FAIL_CLOSED: resident KV installation not verified`.
- ChatGPT in-app browser separately exposed an IndexedDB object-store mismatch; that remains partition-local and is not promoted as Safari runtime truth.
- Site recovery PR #1197 merged at `bd4c64a4dfa8130d3b8c015a242fbab5afc67fa1` after KV TestFlight Projection Entry, Site Bootstrap Validate, Site Handoff Orchestrator, and Ecosystem Heartbeat exact-head checks all passed.
- #1197 reuses the existing `StegVerseKVInstallationBridge`, exposes `Admit Existing KV Installation Receipt` only for the resident-verification failure, requires observed DEVICE_KV materialization, then automatically retries the original `CURRENT_IPHONE_TESTFLIGHT_SIGNING` projection. `Save Projection JSON` remains unavailable until `PROJECTION_CONTEXT_READY`.
- Pages build/deployment run `34531380154` for the functional #1197 merge completed successfully.
- the #1197 implementation claim was terminalized by claim-registry-only Site PR #1198, merged at `1df85a660cef242f05819e2b847ef942dff88ae1` after corrected terminalization validation passed.

## Current first unresolved condition

`AUTHENTIC_CURRENT_IPHONE_KV_INSTALLATION_RECEIPT_RECOVERY_AND_PROJECTION_RETRY`

Required current-device evidence:

1. open the repaired published page in Safari;
2. run `Create KV Projection Context`;
3. if resident KV verification still fails, owner-select canonical `_System/installation.receipt.json` via `Admit Existing KV Installation Receipt`;
4. require `device_local_kv_materialization_observed=true`;
5. require automatic retry of the original purpose-bound projection;
6. require purpose-bound `INGRESS_ADMITTED`, `KV_INSTALLATION_VERIFIED`, compatible browser-capability observation, and exact emitted `stegverse-kv-testflight-projection.json`.

Source merge, CI, historical KV data, or Pages deployment alone do not satisfy those runtime predicates.

## Next execution sequence

1. re-run the repaired published projection in Safari on the current iPhone;
2. admit the canonical installation receipt if prompted and retain the automatic retry result;
3. save the exact projection JSON only after `PROJECTION_CONTEXT_READY`;
4. feed that file to the merged StegOS TestFlight bootstrap;
5. execute TV/TVC provisioning, ephemeral same-device signing, same-session verification and native Build Upload;
6. install through TestFlight;
7. observe authentic retained StegOS/StegBrowser node state, source-HB lineage, same-device discovery and receipt-to-transition execution;
8. materialize current canonical measurement source into the retained node;
9. run exactly one measurement-only convergence pass without same-run repair/retry;
10. preserve the receipt and measured first-failure histogram before remediation.

DE-006 remains expected to expose exact parent rebinding/re-execution only if the authentic visitor reaches that stage; readiness must not pre-classify it.

## Authority invariants

Task Registry does not mint execution authority. WorkerCoordinator owns claim/fence authority. Interlock/InTr owns governed admission/transition authority. TV/TVC owns credential/provider authority. Master Records owns observed-reality/reconstruction authority. KV is the private continuity boundary. HB is observability/carrier only. GitHub Actions are validation/evidence transport only.

## README impact

No new `.github` product semantics are introduced by this reconciliation. Site functional source and repo-local handoff were maintained in the implementation work; root `.github` README semantics remain sufficient.

## Manual work

On the current iPhone in Safari, open the published KV TestFlight projection page, tap `Create KV Projection Context`, use `Admit Existing KV Installation Receipt` if the resident verification failure appears, select canonical `_System/installation.receipt.json`, allow the automatic retry, and save `stegverse-kv-testflight-projection.json` only if the state reaches `PROJECTION_CONTEXT_READY`.
