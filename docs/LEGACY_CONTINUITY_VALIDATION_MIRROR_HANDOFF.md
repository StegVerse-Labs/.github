# Legacy Continuity Validation Mirror Handoff

Updated: 2026-09-04
Repository: `StegVerse-Labs/.github`
Goal: `LEGACY-CONTINUITY-VALIDATION-WORKER-001`
Source repository: `StegVerse-Labs/Continuity`
Exact source commit: `5118c7f9f841a43ef8729c7c8dd20e01d3696713`
State: `HANDOFF_READY_SOURCE_INSTALLATION`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE`

## Purpose

Provide a sovereign/local exact-source validation carrier for the private Continuity legacy-bequest slice without weakening the existing no-GitHub-token runtime rule.

## Required execution model

```text
already-authorized local Continuity checkout
-> require exact HEAD 5118c7f9f841a43ef8729c7c8dd20e01d3696713
-> require clean worktree
-> strip credential-like environment variables
-> run focused legacy + frozen-simulation tests only
-> emit deterministic PASS or FAIL_CLOSED receipt
```

The worker never clones, fetches, pulls, pushes, signs, publishes, releases, contacts a provider, determines a death, notifies a recipient, arms an authentic capsule, creates authentic TVC authorization, or moves StegCoin/StegToken.

## Focused tests

- `tests/test_legacy_trigger.py`
- `tests/test_legacy_participation.py`
- `tests/test_legacy_release_coordination.py`
- `tests/test_legacy_frozen_simulation.py`

The frozen simulation may contain `simulation_armed_only=true` solely to exercise source composition. That does not constitute authentic arming or activation.

## Installed surfaces

- `workers/legacy_continuity_validation_worker.py`
- `control/worker-registry.d/legacy-continuity-validation-001.json`
- `handoffs/LEGACY-CONTINUITY-VALIDATION-WORKER-001.json`
- this handoff

## Current blocker

`AUTHORIZED_LOCAL_CONTINUITY_SOURCE_PATH_NOT_YET_OBSERVED`

Do not substitute GitHub-token private-source checkout, a second user-operated machine, hosted CI runtime authority, or an unrelated provider runtime. The intended execution is the existing StegVerse sovereign/resident carrier consuming an already-authorized exact local source materialization.

## Completion boundary

Source installation and registry readiness are not validation completion. Completion requires an eligible authorized local Continuity source path at the exact bound commit and a retained worker receipt with `state=PASS` proving all four focused tests executed with credentials stripped.

Until then:

```text
SOURCE_VALIDATION=NOT_OBSERVED
RUNTIME_ACTIVATION=false
AUTHENTIC_CAPSULES_ARMED=0
RECIPIENT_NOTIFICATIONS=0
ASSET_TRANSFERS=0
AUTHENTIC_TVC_AUTHORIZATION=false
```
