# TVC GitHub Broker Cross-Repository Validation Mirror Handoff

## Source of truth

```text
goal_id: TVC-GITHUB-BROKER-VALIDATION-001
repository: StegVerse-Labs/.github
branch: feat/tvc-github-broker-validation-001
canonical implementation owner: StegVerse-Labs/TVC#19 / PR #20
role: CLAIMED_FOR_VALIDATION
credential_authority: TV/TVC
github_token_required: false
non_tv_tvc_secret_or_token_allowed: false
archive_ready: false
```

## Originating session goal

Complete the remaining autonomous StegVerse formalism/manifold continuation while preserving TV/TVC-only credential authority. The TVC repository-operation broker is the current unique implementation dependency for missing-source materialization and bounded owner-repository mutation. TVC-hosted PR workflows are currently completing with zero executed job steps, so this lane provides an independent non-authorizing hosted validation path rather than treating runner non-allocation as code failure or success.

## Canonical task owner and collision boundary

Implementation remains exclusively owned by `StegVerse-Labs/TVC@feat/github-repository-operation-broker-001`, issue #19, PR #20. This repository may validate only the exact TVC PR merge ref anonymously. It may not modify TVC source, supply credentials, create TVC authorization, execute a live repository operation, merge PR #20, or compete with `TVC-CAPABILITY-RUNTIME-002`, `TVC-PRIMARY-RUNTIME-BINDER-005`, or any StegFin trade/runtime claim.

## Validation claim

```text
task_id: TVC-GITHUB-BROKER-VALIDATION-001
claimant: current ChatGPT formalism/manifold continuation session
claim_state: CLAIMED_FOR_VALIDATION
claim_created_at: 2026-08-14T00:16:00-05:00
claim_release_condition: independent hosted validation of exact TVC PR #20 merge-ref succeeds or produces an inspectable code/test failure; validation result is durably recorded in TVC PR #20 and this handoff
expected evidence: workflow run, job steps/logs, exact tested TVC commit/merge ref, deterministic test result, credential-absence proof
collision_scope: .github workflow and this handoff only
```

## Validation implementation

Required workflow: `.github/workflows/tvc-github-broker-crossrepo-validation.yml`.

The workflow must:

1. declare `permissions: {}`;
2. prove `GITHUB_TOKEN`, `GH_TOKEN`, `GITHUB_PAT`, and `TVC_EPHEMERAL_GITHUB_TOKEN` are absent from the job environment;
3. use anonymous HTTPS `git fetch` against `StegVerse-Labs/TVC` and fetch `refs/pull/20/merge`;
4. record the exact fetched merge commit and both parents;
5. run `python -m unittest -v tests/test_github_repository_operation_broker.py`;
6. compile `github_repository_operation_broker.py` and its CLI;
7. parse both new JSON schemas, task and claim records;
8. scan the broker request/receipt/schema surfaces for accidental secret-value examples or source-level token literals outside the single permitted environment-variable name;
9. perform no persistence or repository mutation.

## Current implementation/validation state

```text
handoff: INSTALLED
workflow: PENDING
hosted execution: PENDING
TVC PR #20 implementation: IMPLEMENTED_UNVALIDATED
TVC runner condition: ZERO_STEPS_OBSERVED_ON FOUR PR WORKFLOWS; one StegTVC Core CI retry also completed with zero steps
```

## Integration and propagation obligations

On PASS, add the independent validation evidence to TVC PR #20 and update the TVC broker handoff/claim. This lane does not itself admit or activate the broker. After broker admission, `.github` must bind the formalism missing-source and owner-mutation continuations to the TVC broker without receiving its credential.

No Site, Publisher, admissibility-wiki, StegGuardian, or Master Records publication is required for this validation-only lane.

## Archive condition

This validation claim may be released after evidence is durable and TVC PR #20 continuation no longer depends on this session for validation. The originating session remains non-archive-ready while TVC broker admission/integration or another unique executable requirement remains session-owned.

## Progress

```text
developed files: 1/2
validation: 0/5
integration: 0/2
goal activation: 10%
session consolidation: preserved in canonical handoffs and issue/PR records
```
