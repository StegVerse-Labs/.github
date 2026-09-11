# HIL ESRL Exact Intake Reconciliation — 2026-09-11

Repository: `StegVerse-Labs/.github`  
Parent goal: `SHWP-HIL-SOVEREIGN-RECEIVER-001`  
Canonical parent handoff: `docs/HIL_RESIDENT_SESSION_MANIFOLD_ACTIVATION_MIRROR_HANDOFF.md`

## Exact physical artifact

The exact user-exported current-iPhone ESRL artifact has now been received and preserved verbatim at:

`evidence/physical/hil-esrl-lease-open-a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92.json`

Exact byte facts:

- size: `2011` bytes;
- SHA256: `a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92`;
- schema: `stegverse.hil-browser-esrl-lease-open/v1`;
- state / lease state: `LEASE_OPEN`;
- lease: `HIL-BROWSER-ESRL-7bafde4a280e847758da157e`;
- task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`;
- request: `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`;
- browser context: `ctx_d151139d2db1eeecb6512f5844058246`;
- node: `stegnode-web-f24e3bfb7f5343cb37323187a88e51f3`;
- claim/fence: `SHWP-SHWP-HIL-SOVEREIGN-RECEIVER-001-G25` / `25`;
- source execution entry: `8ddd8c6fc08038ce4111b349f47a5f44bd48a7bfbc551fae1bfb59a1a384da69`;
- journal replay: `PASS`;
- runtime materialized: `true`;
- local identity verified: `true`;
- execution surface: `CURRENT_USER_IPHONE`;
- credential authority: `TV/TVC`;
- GitHub runtime authority: `NONE`.

The artifact explicitly leaves custody, post-restart exact-byte proof, TVC lifecycle receipt, and broader HIL lifecycle completion false.

## Canonical intake result

The artifact satisfies the merged `scripts/intake_hil_browser_esrl_evidence.py` contract against the canonical G25 request-consumption receipt.

Accepted intake receipt:

`receipts/sovereign-host/hil-browser-esrl-evidence-intake.latest.json`

with:

- `state=ACCEPTED`;
- `esrl_lease_open_observed=true`;
- exact `source_artifact_sha256=sha256:a6756c54da15f09cd6a3dbb201375891803f6589fd644db4c545be39ebe41b92`;
- unchanged downstream false claims.

The already-merged reconciliation contract then yields:

`receipts/sovereign-host/hil-esrl-acceptance-reconciliation-proposal.latest.json`

with the exact lawful transition:

```text
50000000103000 -> 50000000102000
remove AUTHENTIC_ESRL_HIL_LEASE_OPEN_NOT_YET_OBSERVED
retain POST_RESTART_EXACT_BYTE_PROOF_NOT_YET_PRESERVED
retain TVC_HIL_LIFECYCLE_HANDOFF_NOT_YET_PROVEN
next runtime stage = HIL_RECEIVER_READY_AND_CUSTODY
```

## Canonical state reconciliation

This change reconciles the task vector and HIL worker registry to two remaining blockers while preserving:

- `HANDOFF_READY`;
- `archive_eligible=false`;
- `activated=false`;
- `propagated=false`;
- existing G25 claim/fence lineage;
- no second claim;
- no second machine requirement;
- no promotion of post-restart or TVC lifecycle evidence.

The next execution/evidence stage is `HIL_RECEIVER_READY_AND_CUSTODY`, followed independently by post-restart exact-byte reconstruction proof and TVC lifecycle handoff.

## README maintenance

`README.md` was re-reviewed. This is a task-specific canonical evidence reconciliation and does not alter the documented public repository/runtime interface, so no README prose change is required.
