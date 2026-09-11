# Global Runtime Evidence Closure Mirror Handoff

Goal Task ID: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
Canonical issue: `StegVerse-Labs/.github#1260`
COSV: `50000000100000`
Status: `ACTIVE / TASK-0010 G6 RETAINED PROVENANCE / TASK-0011 V2 PUBLISHED / AUTHENTIC CURRENT-IPHONE G7 EVIDENCE NEXT`

## Canonical runtime model

```text
retained StegOS node identity + source-device HB lineage
-> ephemeral request consumption
-> WorkerCoordinator/canonical allocator claim/fence
-> Interlock/InTr admission
-> bounded TV/TVC provider/credential session
-> component execution
-> exact receipt commitment
-> Master Records reconstruction
-> downstream propagation
```

HB is observability only. WorkerCoordinator/canonical allocator owns claim/fence authority. Interlock/InTr owns governed transition authority. TV/TVC owns credential/provider authority. Master Records owns observed-reality/reconstruction. GitHub Actions are validation/evidence transport only.

## Proven current-iPhone evidence

Two exact 620-byte KV TestFlight projection files satisfy the merged StegOS projection validator:

```text
primary sha256 93caa302f310be097005c21639504bc13a7e8090d161d56cd0823c37363db3f8
repeat  sha256 064c8fcac9e1ee87c6f6dc73807689fded772865ae4b3f461b304d26aaf7df64
purpose CURRENT_IPHONE_TESTFLIGHT_SIGNING
entry_state ADMITTED
browser_capability_state OBSERVED_COMPATIBLE
```

Read-only immutable journal recovery then proved the prior green allocator execution was authentic:

```text
TASK-2026-0010 selected
claim registry generation 6
fencing token 6
claim observation CLAIM_GRANT_OBSERVED
canonical allocator receipt ALLOCATION_COMPLETE
node journal sequence 66
node journal replay PASS
recovery allocator mutation false
```

The recovered receipt remains authentic provenance and must not be rerun or reconstructed.

## Scope reconciliation

Before mutating the TASK-0010 product branch, current StegOS source was compared with the pre-KV successor package. Merged StegOS PR #314 (`19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`) added two mandatory modules to the TestFlight path:

```text
mobile/web-bootstrap/kv-bound-ephemeral-projection-context.js
mobile/web-bootstrap/kv-projection-file-loader.js
```

The current TestFlight page loads the KV projection JSON from Files, validates it in memory, and the bootstrap validates the projection before unsigned IPA/WASM materialization.

Those two paths are absent from the authentic TASK-0010 G6 scoped-exclusive claim. Therefore G6 cannot be widened retroactively to publish the complete current package. Site support PR #1219 was closed unmerged before any product-byte transport occurred.

## Fresh successor

Canonical successor `TASK-2026-0011` was registered for the complete KV-gated package under Site issue #1220. Its scope uses a new product branch and includes the two KV modules explicitly. TASK-0010 remains predecessor provenance with reactivation/widening prohibited.

The exact current-iPhone allocator source and retained-state TASK-0011 package were transported from merged `.github` source through Site PR #1224 and materialized at Site commit `c63b23babbcffe4f58c0cd8a49454a8fd7dcb088`.

Site PR #1225 then merged the immutable TASK-0011 G7 v1 carrier. Authentic current-iPhone execution failed closed because the retained allocator snapshot omitted historical predecessor `task_statuses`, causing canonical preview to select TASK-2026-0009. No allocator mutation occurred.

Site PR #1230 merged the immutable TASK-0011 G7 v2 journal-status reconciliation at merge commit `437a519f7a2557f39ec3505eb5b9e0b8e2794574`. The repair preserves v1 evidence, cryptographically replays the retained node journal, derives predecessor status only from matching canonical allocator receipt/observation pairs, requires retained TASK-2026-0010 evidence, reconstructs only missing/queued predecessor status to `active`, never synthesizes `completed`, and still requires exact TASK-2026-0011 preview selection plus generation +1 before raw-state CAS.

Exact-head validation for PR #1230 passed, including Site Bootstrap Validate, StegOS Node Public Observation, Site Handoff Orchestrator, and Ecosystem Heartbeat Orchestration. Push validation for the merge commit also passed. Source/CI evidence does not itself prove G7 allocation.

Current sequence:

```text
open only the published immutable TASK-2026-0011 v2 entrypoint on the established current iPhone
-> preserve all IndexedDB / node-journal / browser continuity state
-> observe exact canonical TASK-2026-0011 preview and generation-7/fence-7 allocation or preserve exact fail-closed result
-> export exact allocation evidence
-> project exact KV-gated StegOS package to Site under the authentic G7 claim
-> feed retained primary KV projection through the published page
-> TV/TVC provision/sign/native Build Upload
-> TestFlight install
-> retained StegOS/StegBrowser observation
-> exactly one frozen global measurement pass
```

## Current first unresolved condition

`AUTHENTIC_TASK_2026_0011_V2_CURRENT_IPHONE_CANONICAL_ALLOCATION_EVIDENCE`

Do not repeat TASK-2026-0010 allocation. Do not clear IndexedDB, Safari site data, node journal, or retained allocator/browser state. Do not widen the G6 claim. The next mutation, if admitted, must be the canonical G6 -> G7 / fence-7 TASK-2026-0011 transition on the established current iPhone.

## README impact

`.github` root README was reviewed for this reconciliation. No repository-wide authority or workflow semantics changed; this update only advances the canonical operational handoff to already-merged Site evidence, so no README text change is required.

## Manual work

On the established current iPhone in Safari, open the published immutable TASK-2026-0011 v2 allocator entrypoint and perform exactly one successor allocation attempt without clearing or resetting any retained state. Export the exact evidence shown after the attempt. Preserve any fail-closed result exactly as observed.
