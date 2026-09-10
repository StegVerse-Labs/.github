# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / 18 HB32 PROFILE-DERIVED NODES / MEASUREMENT HARDENING MERGED / KV-BOUND CURRENT-IPHONE SOURCE PATH MERGED / AUTHENTIC DEVICE INVOCATION NEXT`

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

The earlier Site-first static-bootstrap sequence is superseded. The active child is:

`KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`

Current architecture:

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

Merged source evidence:

- KV projection producer: `continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`.
- StegOS projection consumer: `StegOS#314` -> `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`.
- purpose-bound Site Device→KV adapter/export/page: `Site#1178` -> `3da593a61a536a625fcea4a26df8d1f491f00b44`.
- Site implementation claim for PR #1178 is released with merge evidence.

The Site adapter does not create a new InTr record class or second service worker. It reuses `MY_KV_INSTALLATION_STATUS`, binds `CURRENT_IPHONE_TESTFLIGHT_SIGNING` into the exact request hash, requires an authentic `INGRESS_ADMITTED` receipt plus verified KV installation, observes only required browser APIs/features, and emits the exact opaque projection expected by StegOS.

## Superseded temporary work

`.github` PR #1302 and Site issue #1180 were created from the older Site-first sequencing before the KV-bound child state was reconciled. Both are now closed without merge/current execution effect. The unmerged `TASK-2026-0010` branch artifact is not canonical Task Registry truth.

## Current first unresolved condition

`AUTHENTIC_CURRENT_IPHONE_KV_TESTFLIGHT_PROJECTION_INVOCATION`

Required current-device evidence:

1. purpose-bound Device→KV `INGRESS_ADMITTED` receipt;
2. verified resident KV installation response;
3. compatible same-lineage browser capability observation;
4. exact emitted `stegverse-kv-testflight-projection.json`.

Source merge, CI, route existence, or historical KV data do not satisfy these predicates.

## Next execution sequence

1. verify the merged `kv-testflight-projection.html` is included in the active Site publication/deployment output;
2. invoke it on the current iPhone and retain the actual admission/capability evidence;
3. save the exact emitted projection JSON;
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

No new `.github` functional semantics are introduced by this coordination reconciliation. Existing README authority/continuation semantics remain sufficient. Functional changes in Site, StegOS and continuity-vault-kit already carry repository README/handoff maintenance.

## Manual work

None until the published current-iPhone invocation route is confirmed. Once confirmed, the user action is to open the published KV TestFlight projection page on the current iPhone, tap `Create KV Projection Context`, and save the resulting `stegverse-kv-testflight-projection.json` to Files.
