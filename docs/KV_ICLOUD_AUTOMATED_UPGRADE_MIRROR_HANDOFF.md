# Automated iCloud KnowledgeVault Upgrade Coordination Mirror Handoff

Repository: `StegVerse-Labs/.github`  
Goal Task ID: `KV-ICLOUD-AUTOMATED-UPGRADE-001`  
COSV profile: `task.v1`  
COSV: `40000100100000`  
Coordination state: `ACTIVE`  
Canonical task record: `data/canonical-task-records/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Canonical task vector: `control/task-vectors/KV-ICLOUD-AUTOMATED-UPGRADE-001.json`  
Implementation owner: `StegVerse-Labs/continuity-vault-kit#215`  
Implementation handoff: `StegVerse-Labs/continuity-vault-kit/KV_ICLOUD_AUTOMATED_UPGRADE_MIRROR_HANDOFF.md`

## Goal

Automate the owner-authorized legacy iCloud KnowledgeVault upgrade path so the owner supplies one source copy/archive and receives a rollback-preserved, verified updated copy without manual file-by-file comparison.

## Current truth

The plan-only predecessor `CVK-LEGACY-KV-UPGRADE-174` is merged and remains the deterministic no-mutation planner. This goal owns the separate apply/rollback/verify executor. Source implementation is in progress in `continuity-vault-kit` PR #216. No private iCloud vault bytes have been read or mutated by repository automation, and no runtime upgrade has yet been claimed.

## Collision boundaries

- Preserve the existing legacy planner and its evidence.
- Never mutate the selected live iCloud source in place.
- Never copy private iCloud bytes into GitHub.
- Do not disturb `KV-CONNECTION-REVALIDATION-WORKER-001` or pending Google Drive KV #2 request `SITE-CLOUD-KV-4347408852127319cbda574f02e03edb`.
- Source/CI/merge does not prove owner runtime execution or acceptance.

## Completion predicates

Source completion requires merged green executor, independent package verifier, destructive/tamper/preservation tests, README/iOS documentation, and reconciled implementation handoff. Runtime completion requires authentic owner-selected iCloud bytes, rollback artifact, updated package, independent exact-byte verification, receipt/readback, and owner acceptance.
