# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / 18 HB32 PROFILE-DERIVED NODES / MEASUREMENT HARDENING MERGED / EXACT CURRENT-IPHONE KV PROJECTION VALIDATED / TASK-2026-0010 ALLOCATION RETRY NEXT`

## Canonical runtime model

```text
runtime/node profile
-> retained StegOS node identity + source-device HB lineage
-> ephemeral request consumption
-> WorkerCoordinator claim/fence
-> Interlock/InTr admission
-> bounded transport/provider/credential session
-> component execution
-> exact receipt commitment
-> Master Records reconstruction
-> downstream propagation
```

HB is observability/freshness/correlation only. WorkerCoordinator owns claim/fence authority. Interlock/InTr owns governed admission/transition authority. TV/TVC owns credentials/provider authority. Master Records owns observed-reality/reconstruction. GitHub Actions are validation/evidence transport only.

## Global measurement state

Merged:
- 18 HB32 runtime-node profiles plus profiled convergence runner;
- StegClaw executable profile;
- VACC executable profile;
- typed ten-stage first-failure responses via `.github#1292` at `e64c5d518af05dac6b9d09c3355d38d75bc27295`;
- one-pass measurement hardening via `.github#1293` at `44c6d88abb42351ec26a576e3136caec3400a613`;
- measurement ingress repair via `.github#1296`.

Authentic global measurement still requires one frozen run ID and `receipts/sovereign-host/global-runtime-node-profile-convergence.latest.json`. No lane failure histogram is authoritative before that receipt exists.

## Current source-device trajectory

Active child: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`.

The Site-first bootstrap ordering remains superseded. The current sequence is:

```text
current iPhone Device→KV/InTr admission
-> verified KV installation
-> browser capability observation
-> exact opaque KV projection
-> canonical TASK-2026-0010 allocation/fence
-> Site TestFlight bootstrap projection
-> StegOS projection gate
-> TV/TVC provision/sign/upload
-> TestFlight install
-> retained StegOS/StegBrowser observation
-> frozen global measurement
```

## Evidence advanced in this session

Authentic current-iPhone Safari reached `PROJECTION_CONTEXT_READY` for `CURRENT_IPHONE_TESTFLIGHT_SIGNING`. Two exact downloaded 620-byte projection artifacts were retained and independently checked against the merged StegOS projection validator:

```text
primary sha256: 93caa302f310be097005c21639504bc13a7e8090d161d56cd0823c37363db3f8
repeat sha256: 064c8fcac9e1ee87c6f6dc73807689fded772865ae4b3f461b304d26aaf7df64
schema: stegos.kv-bound-ephemeral-projection-context/v1
entry_state: ADMITTED
browser_capability_state: OBSERVED_COMPATIBLE
persistence_effect: NONE_EPHEMERAL_CONTEXT_ONLY
authority_effect: NONE_PROJECTION_GATE_ONLY
```

That retires `EXACT_KV_PROJECTION_FILE_BYTES_BOUND_TO_STEGOS_CONSUMER` as the first unresolved condition.

The next current-iPhone allocator attempt verified the established StegOS node continuity but failed before mutation with `FAIL_CLOSED: auto-execution requires exactly one queued canonical successor`; displayed evidence explicitly reported `mutation_performed:false`.

Inspection showed that restriction was wrapper-local. The canonical allocator supports multiple queued tasks and owns deterministic selection. `Site#1205` removed only the false single-queue restriction, requires `TASK-2026-0010` to be present and canonically selected, and continues to fail closed if another task wins. It merged at `281bcb0c56d84eef933e57a21f6ed1ef91660dfb` after Site Handoff, Site Bootstrap, Ecosystem Heartbeat, and StegOS Node Public Observation exact-head checks passed. The repaired page was published through Site Pages. Claim-only `Site#1206` merged at `66c30c269d546520e75fa65a50c912a076ea7b6e` after corrected release-only terminalization checks passed.

## Current first unresolved condition

`AUTHENTIC_CURRENT_IPHONE_TASK_2026_0010_CANONICAL_ALLOCATION_RETRY_AND_CLAIM_EVIDENCE`

Required next evidence:

1. current iPhone again verifies the established node continuity;
2. canonical allocator queue contains `TASK-2026-0010`;
3. canonical allocator selects `TASK-2026-0010`;
4. retained allocator CAS commits the next generation;
5. fresh claim/fencing evidence is emitted and exported exactly.

Do not mutate the task-gated TestFlight product branch until that authentic claim/fence exists.

## After successful allocation

1. Bind the emitted `TASK-2026-0010` claim/fence to `claim/current-iphone-testflight-static-bootstrap-r1`.
2. Re-observe Site `main` and project exact StegOS successor assets under the fresh fence.
3. Validate/merge the Site bootstrap projection and update successor provenance.
4. Feed the primary exact KV projection artifact into the published StegOS TestFlight bootstrap.
5. Continue TV/TVC app-resource resolution, provisioning, ephemeral same-device signing, same-session verification and native Build Upload.
6. Install through TestFlight and observe retained StegOS/StegBrowser node state, source-HB lineage, same-device discovery and receipt-to-transition execution.
7. Materialize current canonical measurement source and run exactly one measurement-only convergence pass without same-run repair/retry.
8. Preserve the global receipt and first-failure histogram before remediation.

DE-006 remains expected to expose exact parent rebinding/re-execution only if the authentic visitor reaches that stage; readiness must not pre-classify it.

## README impact

No new `.github` product semantics are introduced by this evidence reconciliation; existing root README semantics remain sufficient. Functional Site changes maintain their repo-local handoff/tests.

## Manual work

On the current iPhone in Safari, open `https://stegverse.org/stegos-node/org-allocator-bootstrap-auto.html`. If it reports `Canonical allocation auto-executed: TASK-2026-0010`, export the exact allocator evidence JSON and return it. If it fails closed, retain the exact displayed result and do not reset allocator/browser state.
