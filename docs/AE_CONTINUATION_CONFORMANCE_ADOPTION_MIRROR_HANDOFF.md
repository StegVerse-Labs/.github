# AE Continuation Conformance Adoption Mirror Handoff

## Source of truth

```text
organization: StegVerse-Labs
repository: .github
branch: feat/ae-continuation-conformance-123
active_goal_id: AE-CONTINUATION-CONFORMANCE-ADOPTION-001
canonical_issue: #123
claim_issue: #124
upstream_policy_owner: StegVerse-Labs/StegCore#107
upstream_release_pr: StegVerse-Labs/StegCore#114
upstream_release_commit: 78d00ca0e977af3e666c2acec431b111aea0deef
credential_authority: TV/TVC
github_token_runtime_authority: NONE
live_registry_mutation_authority: NONE
archive_ready: false
```

This lane adopts the released StegCore Admissible-Existence continuation-conformance contract as a read-only verification surface for the canonical HANDOFF and Worker Task Registry. It does not mutate `control/worker-registry.json`, claim/fence/lease state, heartbeat state, or runtime ownership.

## Required behavior

1. Pin the released StegCore conformance policy/version and source commit.
2. Read canonical Worker Task Registry state and HANDOFF references without mutation.
3. Require an explicit AE classification for each task under verification: `CAPABILITY` with canonical capability identity/phase/evidence, or `NONE` with rationale.
4. Classify task temporal state as recently completed, current, or future without converting constraints into completion.
5. Reject activation claims without integration evidence and activation proof.
6. Reject heartbeat-as-worker-executor, heartbeat-as-transport, heartbeat-as-custody, Master Records execution authority, non-TV/TVC credential authority, or GitHub-token runtime authority.
7. Reconcile task/goal/owner/capability/phase/blockers/continuation state across HANDOFF and Worker Task Registry projections.
8. Emit a read-only conformance receipt bound to the upstream StegCore policy commit and local registry generation/hash.

## Collision boundary

`.github#122` owns the live worker/control-plane separation refactor. This lane may add read-only verification/adoption files and tests but may not change the live registry schema, claim/fence/lease semantics, worker execution, heartbeat runtime, or current control-plane state until #122 releases or assigns that insertion point.

## Canonical files

```text
docs/AE_CONTINUATION_CONFORMANCE_ADOPTION_MIRROR_HANDOFF.md
control/ae-continuation-conformance-source.json
tools/verify_ae_continuation_adoption.py
tests/test_ae_continuation_adoption.py
```

## Completion condition

Source adoption is complete when the read-only verifier and deterministic tests are merged with hosted validation evidence. Full ecosystem activation remains pending until the org control-plane validation path invokes this verifier against canonical live task projections without colliding with #122.
