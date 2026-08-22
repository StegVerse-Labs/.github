# Heartbeat External Timing Match Mirror Handoff

Updated: 2026-08-22

## Authority and goal

```text
goal_id: HEARTBEAT-EXTERNAL-TIMING-MATCH-191
repository: StegVerse-Labs/.github
canonical_issue: StegVerse-Labs/.github#192
source_merge: ea90b6761c9919ebdf2567b03357a1639838ef65
source_scope: COMPLETE_VALIDATED_MERGED_RELEASED
live_producer_owner: StegVerse-Labs/.github#122 / HEARTBEAT-CARRIER-RUNTIME-SEPARATION-122-LIVE-MIGRATION
credential_authority: TV/TVC
github_token_runtime_authority: NONE
non_tv_tvc_secret_or_token_required: false
render_dependency: PROHIBITED
```

The source/schema lane is complete and released. Live producer consumption remains separately owned by #122; workflow hygiene does not acquire or modify that runtime obligation.

## Canonical semantics

- The StegVerse logical heartbeat cadence is constant after timing-profile selection/lock.
- Heartbeat min/max are workload-health bounds per pulse, not an allowable variable heartbeat-frequency band.
- Exterior timing sources are observed/profiled and never become StegVerse authority.
- S/NS topology is explicit authenticated metadata and is never inferred from frequency/waveform.
- Phase/waveform matching may assist synchronization, recognition, drift detection, and bridging but grants no execution, credential, claim, routing, custody, governance, consent, intent, or semantic authority.
- Re-profile/re-lock is bounded to material exterior timing changes and cannot silently mutate the selected StegVerse logical cadence.

## Authoritative source and validation surfaces

```text
docs/HEARTBEAT_EXTERNAL_TIMING_MATCH_MIRROR_HANDOFF.md
schemas/external-timing-capability.schema.json
heartbeat_runtime/external_timing_match.py
control/external-timing-match-contract.json
tests/test_external_timing_match.py
receipts/external-timing-match/source-validation-20260815.json
.github/workflows/heartbeat-worker-project.yml
```

The former standalone `.github/workflows/external-timing-match-validation.yml` was a validation-only entry surface. StegVerse-Healer #34 determined that it did not carry runtime authority and that its validation semantics could be retained by the stable Heartbeat Worker dispatcher. Its deletion is workflow-surface hygiene only; it does not change the six source/evidence artifacts above or the #122 live-consumer boundary.

## Validation semantics retained in the stable dispatcher

`heartbeat-worker-project.yml` retains:

1. credential-clean anonymous checkout and `permissions: {}`;
2. recursive JSON parsing covering the timing schema and contract;
3. complete repository unittest execution including all seven `tests.test_external_timing_match` cases;
4. an explicit focused `tests.test_external_timing_match` run;
5. explicit contract assertions requiring:
   - `FIXED_AFTER_PROFILE_SELECTION_AND_LOCK`;
   - workload-health min/max semantics;
   - no workload-driven period change;
   - `credential_authority=TV/TVC`;
   - `github_token_runtime_authority=NONE`;
   - `non_tv_tvc_secret_or_token_allowed=false`;
   - `render_dependency=PROHIBITED`;
   - all `timing_match_grants_*` fields false.

The stable dispatcher already covers timing implementation, schema, contract, tests, docs, and workflow changes on pull requests. No new automatic-main trigger was added for this consolidation because the retired timing workflow itself had no automatic-main trigger.

## Historical validation evidence

```text
PR #193: MERGED
validated source head: 2198366abfb39b0f6b6524d442027a707d37fc07
External Timing Match Validation: 31921871531 SUCCESS
handoff-only validation: 31921909383 SUCCESS
focused timing tests: 7/7 PASS
fixed-cadence / workload separation / zero-authority proof: PASS
```

Healer consolidation evidence is recorded by the workflow-hygiene PR that removes the standalone workflow and by the exact-head Heartbeat Worker / organization-control validation runs on that PR. The original evidence above remains provenance and is not replaced by the consolidation.

## Cross-repository consumers and collision boundaries

- `.github#122` remains the live producer/runtime consumption owner.
- `StegVerse-Labs/StegBrain#860` may observe typed timing deviation under separate authority.
- `StegVerse-Labs/StegNeuro` may consume timing normalization without neural READ/WRITE authority.
- `StegVerse-org/StegVerse-SDK#13` may consume device timing capability metadata without duplicate timing authority.

```text
control/heartbeat-state.json: NOT MUTATED BY THIS SOURCE/HYGIENE LANE
active claims/fences/leases: NOT MUTATED
resident heartbeat/carrier processes: NOT MUTATED
production carrier switch: OWNED BY #122
TV/TVC protected values: NOT READ/WRITTEN
provider/model/wallet state: OUT OF SCOPE
Master Records custody mutation: PROHIBITED
```

## Completion and continuation

```text
source implementation: COMPLETE_RELEASED
source validation: COMPLETE_RELEASED
workflow hygiene: CONSOLIDATED_INTO_STABLE_HEARTBEAT_VALIDATOR
live producer activation: PENDING/SEPARATELY_OWNED_BY_122
```

Source completion does not satisfy #122 live activation. Conversely, #122's pending live work does not justify retaining a redundant GitHub-hosted validation entry surface.

Canonical continuation for runtime consumption remains `StegVerse-Labs/.github#122`. Repository workflow hygiene remains `StegVerse-Labs/StegVerse-Healer#34`.
