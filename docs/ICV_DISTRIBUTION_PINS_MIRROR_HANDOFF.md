# ICV distribution pins mirror handoff

Status: DRAFT (Lane A, G-8 draft PR). Updated: 2026-10-18.
Parent: StegVerse-Labs/.github#3183 workstream B. Lane goal: StegVerse-org/.github#165.
No Task Registry record, COSV or generation change is made or implied.

## Scope

Pinned, license-as-declared sources for the packages ICV would distribute; a
stdlib offline install / upgrade / uninstall into a temporary prefix with
receipts; a compatibility matrix. Details: `distribution/icv/README.md`.

## Boundaries

- ICV owns commercial packaging and customer-facing distribution (#3183). The
  SDK, StegCore/StegGate, TV/TVC, Registry and Master Records owners keep their
  authority; nothing here evaluates, admits or releases.
- No ICV repository byte was read: the declared read path is the TVC read grant
  (FAIL_CLOSED, class B, StegVerse-Labs/TVC#520).
- A recorded license is what the cited file declares. It is not a legal
  determination; undeclared stays UNKNOWN_NOT_AUTHENTICALLY_OBSERVED and is
  never installed.
- No new dependency; standard library only.

## Continuation

1. Refresh pins when the SDK, StegCore, core-lite or observatory owners change
   the pinned commits or adopt licenses; re-run `--lifecycle`.
2. When TVC#520 lands, pin ICV repository bytes from the TVC execution receipts.
3. Place the pinned-bytes lifecycle in CI once `ICV_LIFECYCLE_CI_SURFACE_UNDECIDED` is answered.

## Execution ownership and collision partition

Standard: `stegverse.handoff-execution-ownership/v1`.

### MANUAL / SESSION-STARTABLE

```yaml
- task_id: ICV-DISTRIBUTION-PINS-REFRESH
  execution_owner: Lane A (StegVerse-org/.github#165), draft PRs only
  claim_state: SESSION_STARTABLE
  worker_registry_ref: none (no worker; source-only)
  manual_execution_allowed: true
  manual_allowed_role: draft-PR author on its own laneA branch
  collision_scope: distribution/icv/, scripts/icv_distribution_offline_install.py, tests/test_icv_distribution_offline_install.py, this handoff
  release_condition: owner merge or supersession of this draft
  next_executable_action: refresh pins from authenticated source and re-run --lifecycle
```

### WORKER-OWNED / DO NOT COMPETE

```yaml
- task_id: TVC-PRIVATE-SOURCE-READ-001 (ICV census consumer, StegVerse-Labs/TVC#520)
  execution_owner: TVC lane / resident executor
  claim_state: MACHINE_OWNED
  worker_registry_ref: StegVerse-Labs/TVC docs/PRIVATE_SOURCE_READ_MIRROR_HANDOFF.md
  manual_execution_allowed: false
  collision_scope: reading Infrastructure-Continuity-Ventures repository bytes
  release_condition: a TVC execution receipt per ICV repository
  next_executable_action: none here; pin ICV bytes only from those receipts
```

### ESCALATED / AUTHORITY-OWNED

```yaml
- task_id: ICV-LICENSE-ADOPTION (StegCore, core-lite, governance-observatory)
  execution_owner: each repository's rights holder (ECOSYSTEM-OPEN-SOURCE-STRATEGY-001 for StegCore)
  claim_state: ESCALATED
  worker_registry_ref: none
  manual_execution_allowed: false
  collision_scope: LICENSE/NOTICE and package license metadata in those repositories
  release_condition: an operative license observed at a pinned commit
  next_executable_action: none here; refresh pins after adoption
```

### COMPLETED / SUPERSEDED

None.
