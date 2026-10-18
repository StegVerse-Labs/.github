# AWAIT-SURFACE-TRANSITION-OWNERSHIP-001 mirror handoff

State: PROPOSED, record-only (no aggregate Registry row, no generation bump). Authority effect: NONE.

## Why
R-P3 (StegVerse-Labs/.github#3183 comment 6256315196 (R-P3 NO_OWNING_TASK)) found six await surfaces (polls, retries, a schedule and validation-time DNS resolution) that the
organization-role standard requires to be manifest-bound state transitions. None could be registered in
`data/organization-role-exemption-register.json`, because the register requires an owner with a canonical task record
and no record names them. No owner was invented.

## What this record does
It names one bounded goal that owns exactly these six surfaces and their exemption entries until each is released to
a surface-specific owner, converted, or retired. Each surface carries a FAIL_CLOSED blocker
`SURFACE_SPECIFIC_OWNING_GOAL_NOT_DECLARED` with the six fields, and an exemption entry (review 2026-11-18).

| Repository | Surface | Exemption code |
|---|---|---|
| StegVerse-Labs/.github | `scripts/restart_sovereign_ephemeral_node.py::_wait_for_worker_tick` | `WORKER_TICK_POLL_GATES_RESTART_RECEIPT` |
| StegVerse-Labs/Site | `.github/workflows/hil-live-probe.yml` | `SCHEDULED_PUBLIC_ORIGIN_PROBE` |
| StegVerse-Labs/Site | `scripts/check_hil_deployed_controlled_cycle_evidence.py::valid_https_origin` | `VALIDATION_RESOLVES_DNS` |
| StegVerse-Labs/Site | `scripts/check_evaluator_review_public.py::fetch` | `PUBLIC_SITE_FETCH_RETRY_LOOP` |
| StegVerse-Labs/Site | `.github/workflows/verify-nvidia-hf-publication.yml` | `PR_CHECK_POLLS_PUBLIC_SITE` |
| StegVerse-Labs/Site | `.github/workflows/verify-thought-experiments-publication.yml` | `PR_CHECK_POLLS_PUBLIC_SITE` |

Surfaces were read at StegVerse-Labs/.github@978b8880 and StegVerse-Labs/Site@a7071d44.

## Release
When a surface's owner is declared, move its exemption entry's `owning_existing_goal` to that owner and remove the
component and blocker here. When a surface is converted or retired, remove its exemption entry too. When none remain,
the record moves to COMPLETE.

## Registration
Record-only. Inserting an aggregate Registry row is the owner's step and takes one generation bump (tip + 1), the same
path as `register_from_record` in `scripts/apply_task_record_data.py`.
