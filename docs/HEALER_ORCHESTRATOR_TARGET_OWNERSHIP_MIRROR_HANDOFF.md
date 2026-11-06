# HEALER-ORCHESTRATOR-TARGET-OWNERSHIP-001 mirror handoff

State: PROPOSED, record-only (no aggregate Registry row, no generation bump). Authority effect: NONE.

## Why
StegVerse-Healer#119 (`app/owning_goal.py`, commit `3c009a1`) derives each orchestrator target's owning goal from Labs
canonical task records. Against Labs main `978b888`, 12 targets in `data/orchestrator_targets.json` declare no
`canonical_owner` and no record names them, so each fell back to a lane default goal unrelated to the target
(`TARGET_OWNING_GOAL_NOT_IN_REGISTRY`, Healer#119 comment 6256271474).

No existing record's own text covers any of the 12 (searched by workflow stem and alias; the only hits were hash
fragments or unrelated field names). Three target repositories (SCW, Continuity, repo-standards) are not readable from
the drafting session, so no target-specific goal was invented.

## What this record does
It names one bounded goal that owns exactly these 12 targets until each is released to a target-specific owner. Each
target carries a FAIL_CLOSED blocker `TARGET_SPECIFIC_OWNING_GOAL_NOT_DECLARED` with the six fields.

| Repository | Component |
|---|---|
| StegVerse-Labs/Site | site-task-runner, site-b27-native-validation, marketplace-coinbase-local-observer, marketplace-coinbase-local-projection-import, child-safety-public-deployment-observer |
| StegVerse-Labs/repo-standards | st018-local-task-manager |
| StegVerse-Labs/SCW | scw_orchestrator, uptime |
| StegVerse-Labs/TV | tv_self_heal |
| StegVerse-Labs/Continuity | continuity |
| StegVerse-Labs/StegVerse-Healer | quiet_enforcer, stegdeploy-publication-relay |

## Release
When a target's owner is declared (a record naming it, or `canonical_owner` in Healer), remove the component and its
blocker here. When none remain, the record moves to COMPLETE.

## Registration
Record-only. Inserting an aggregate Registry row is the owner's step and takes one generation bump (tip + 1), the same
path as `register_from_record` in `scripts/apply_task_record_data.py`.
