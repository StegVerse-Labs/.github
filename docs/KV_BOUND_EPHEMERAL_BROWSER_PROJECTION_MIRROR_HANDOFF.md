# KV-Bound Ephemeral Browser Projection Mirror Handoff

Updated: 2026-09-10

Goal Task ID: `KV-BOUND-EPHEMERAL-BROWSER-PROJECTION-001`
Parent Goal: `GLOBAL-RUNTIME-EVIDENCE-MEASUREMENT-001`
Root Goal: `GLOBAL-RUNTIME-EVIDENCE-CLOSURE-001`
COSV: `50000010100000`
Canonical issue: `StegVerse-Labs/.github#1299`
Status: `ACTIVE / EXACT CURRENT-IPHONE KV PROJECTION ARTIFACTS VALIDATED / IMMUTABLE ALLOCATOR JOURNAL RECOVERY MERGED / RETAINED TASK-0010 EVIDENCE NEXT`

## Canonical architecture

KV remains the private governed continuity boundary. Device/browser presentation is interchangeable and ephemeral after continuity proof. Interlock/InTr owns transition/admission; WorkerCoordinator/canonical allocator owns claim/fence authority; TV/TVC owns credential/provider authority; HB is observability only; GitHub Actions are validation/evidence transport only.

```text
current iPhone
-> Device→KV Universal InTr
-> CURRENT_IPHONE_TESTFLIGHT_SIGNING admission
-> verified KV installation
-> browser capability observation
-> opaque KV projection
-> canonical TASK-2026-0010 claim/fence
-> Site TestFlight bootstrap projection
-> StegOS projection consumer
-> TV/TVC provision/sign/upload
-> TestFlight install
-> retained StegOS/StegBrowser observation
-> one frozen global measurement pass
```

## Proven projection evidence

Merged source:
- KV producer `continuity-vault-kit#206` -> `47c363611210b7501cbb50abce768cfe0911057f`;
- StegOS consumer `StegOS#314` -> `19e2ea02a16bd703767aafcd47e71f5ec5efe3cf`;
- Site Device→KV adapter `Site#1178` -> `3da593a61a536a625fcea4a26df8d1f491f00b44`;
- Safari resident-KV recovery `Site#1197` -> `bd4c64a4dfa8130d3b8c015a242fbab5afc67fa1`.

Authentic current-iPhone Safari reached `PROJECTION_CONTEXT_READY`. Two exact 620-byte files independently satisfy the merged StegOS projection validator:

```text
primary sha256 93caa302f310be097005c21639504bc13a7e8090d161d56cd0823c37363db3f8
repeat  sha256 064c8fcac9e1ee87c6f6dc73807689fded772865ae4b3f461b304d26aaf7df64
purpose CURRENT_IPHONE_TESTFLIGHT_SIGNING
entry_state ADMITTED
browser_capability_state OBSERVED_COMPATIBLE
persistence_effect NONE_EPHEMERAL_CONTEXT_ONLY
authority_effect NONE_PROJECTION_GATE_ONLY
```

## Allocator stale-document observation

`TASK-2026-0010` remains the canonical Site TestFlight-bootstrap allocation target. Site#1205 removed a wrapper-only false assumption that the queue must contain exactly one successor. Current source permits multiple queued tasks and requires that TASK-0010 be present and that the canonical allocator actually select TASK-0010.

After that repair, the user observed one current-iPhone ChatGPT-browser allocator opening as green/successful, then later ChatGPT-browser/Safari presentations of the obsolete single-queue failure. Because the obsolete predicate is absent from current source, those later red screens are stale presentation code. A successful first green execution may already have written the TASK-0010 same-device execution receipt and claim observation to the established StegOS node journal.

Repeated mutation is therefore not the first continuation action.

## Immutable journal-recovery implementation

`Site#1210` merged at `764a14ec4fc6b975254f56cc05e1d17b1372d2e9` after Site Bootstrap, Site Handoff, Ecosystem Heartbeat, and StegOS Node Public Observation exact-head checks passed. Claim terminalization `Site#1211` merged at `f09939293e9a5f7ef2b1312e638cd0b1527c1cf9`.

New release-immutable surfaces:

```text
/stegos-node/org-allocator-evidence-recovery-task0010-g6-v1.html
  validates node/device continuity and complete journal replay
  searches only for retained stegos.org_allocator_same_device_execution_receipt/v1
  requires selected_task_id TASK-2026-0010 plus canonical receipt selection and claim observation
  exports evidence without opening allocator state or performing mutation

/stegos-node/org-allocator-bootstrap-task0010-g6-v2.html
  checks the retained journal before allocation
  if TASK-0010 is already present, exports retained evidence with allocator_mutation_performed=false
  otherwise runs the existing canonical preview/CAS flow
  still fails closed when TASK-0010 is absent or not canonically selected
```

Allocator execution URLs are now release-immutable by rule. Later fixes require a new path. Service-worker lineage `stegos-node-shell-v11-immutable-allocator-recovery-v1` makes both current immutable surfaces network-only.

## Current first unresolved predicate

`RETAINED_TASK_2026_0010_EXECUTION_RECEIPT_RECOVERY_OR_FRESH_IMMUTABLE_G6_EXECUTION`

Next sequence:

1. use the read-only recovery surface first on the same current-iPhone browser storage partition that showed green;
2. if TASK-0010 evidence is found, export the exact JSON and validate generation/fencing/claim observation;
3. do not run allocator mutation again in that case;
4. only if recovery reports no retained TASK-0010 receipt, use the immutable `task0010-g6-v2` execution page;
5. after authentic claim/fence evidence exists, bind it to the Site TestFlight-bootstrap product work, project the exact StegOS successor assets, then continue the already-validated KV projection -> StegOS -> TV/TVC -> TestFlight -> retained-runtime -> frozen-global-measurement sequence.

## README impact

Site `stegos-node/README.md` documents immutable execution/recovery semantics. No new `.github` root README semantic is required.

## Manual work

Read-only retained-journal recovery first. Fresh immutable G6 execution only when recovery proves TASK-0010 was not already retained.
