# Legacy Continuity Validation Mirror Handoff

Updated: 2026-09-03
Repository: `StegVerse-Labs/.github`
Goal: `LEGACY-CONTINUITY-VALIDATION-WORKER-001`
Source repository: `StegVerse-Labs/Continuity`
Exact source commit: `0b814c0d0028e98a67c751ef2aa1768b17da743f`
State: `HANDOFF_READY_SOURCE_INSTALLATION`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Authority effect: `NONE`

## Purpose

Provide a sovereign/local exact-source validation carrier for the private Continuity legacy-bequest slice without weakening the existing no-GitHub-token runtime rule.

## Required execution model

```text
already-authorized local Continuity checkout
-> require exact HEAD 0b814c0d0028e98a67c751ef2aa1768b17da743f
-> require clean worktree
-> strip credential-like environment variables
-> run focused legacy tests only
-> emit deterministic PASS or FAIL_CLOSED receipt
```

The worker never clones, fetches, pulls, pushes, signs, publishes, releases, contacts a provider, determines a death, notifies a recipient, arms a capsule, or moves StegCoin/StegToken.

## Focused tests

- `tests/test_legacy_trigger.py`
- `tests/test_legacy_participation.py`
- `tests/test_legacy_release_coordination.py`

## Installed/required surfaces

- `workers/legacy_continuity_validation_worker.py`
- `control/worker-registry.d/legacy-continuity-validation-001.json`
- this handoff

## Completion boundary

Source installation is not validation completion. Completion requires an eligible authorized local Continuity source path at the exact bound commit and a retained worker receipt with `state=PASS`.

Until then:

```text
SOURCE_VALIDATION=NOT_OBSERVED
RUNTIME_ACTIVATION=false
CAPSULES_ARMED=0
RECIPIENT_NOTIFICATIONS=0
ASSET_TRANSFERS=0
```
