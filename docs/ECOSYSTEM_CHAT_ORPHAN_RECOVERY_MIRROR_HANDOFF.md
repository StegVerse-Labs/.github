# Ecosystem Chat Orphan Recovery Mirror Handoff

Updated: 2026-08-22T23:56:00-05:00

## Authority and scope

Canonical recovery task: `RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28`.
Parent task: `SHWP-ECOSYSTEM-CHAT-INFERENCE-001`.

```text
repository: StegVerse-Labs/.github
primary runtime/provider: StegVerse
third-party role: FALLBACK_ONLY
credential authority: TV/TVC
GitHub token runtime authority: NONE
heartbeat task authority: NONE
G18 task authority: NONE
```

Heartbeat is reference-only. Recovery and parent claims/fences belong to independent task control. G18 cleanup, WorkerCoordinator-specific execution, GitHub Actions, Render, and third-party infrastructure are not completion prerequisites.

## Authoritative terminal recovery evidence

Current `main` contains the durable receipt:

`receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json`

It proves:

```text
state: PASS
recovery claim: SHWP-RECOVER-SHWP-ECOSYSTEM-CHAT-INFERENCE-001-ORPHAN-HB28-G22
recovery fence: 22
ended parent fence: 20
checkpoint_valid: true
old_authority_ended: true
old_authority_reused: false
master_records_custody_valid: true
successor_authority_granted: false
next_transition: SEPARATE_HIGHER_FENCE_PARENT_SUCCESSOR_AUTHORIZATION
github_token_required: false
third_party_execution_platform_required: false
authority_effect: NONE
```

This receipt was introduced by runtime commit `b70ece41ecf0ac35eb2b38ca9381b55c33ec50db` and remains present on current `main`. Later handoff/registry projections incorrectly continued to describe recovery as awaiting execution. Under the session evidence rules, the durable current receipt is stronger evidence than those stale projections. Recovery must not be rerun merely to satisfy stale bookkeeping.

## Source and custody portability

The bounded standalone executor is released from PR #245 merge `3bfc17f6d4b59f219b3354f5bdae0ecfe6b96ed5`.

PR #260 merge `5e85a2d602fe7234a4bdff34aa1521b752dc2b49` added the immutable non-authorizing G20 custody record to:

`workloads/master-records/orchestration/custody/worker-lifecycle/SHWP-CUSTODY-ECOSYSTEM-CHAT-INFERENCE-001-G20-001.json`

The custody record is `ACCEPTED_FOR_CUSTODY`, reconstruction `PASS`, authority effect `NONE`, and does not grant execution or successor authority.

## Reconciliation state

```yaml
recovery:
  state: COMPLETED
  terminal_receipt: receipts/ecosystem-chat-sovereign-inference/orphan-recovery-HB28.json
  terminal_fence: 22
  reacquisition_allowed: false

parent:
  task_id: SHWP-ECOSYSTEM-CHAT-INFERENCE-001
  state: HANDOFF_READY
  recovery_dependency: SATISFIED
  required_next_authority: independently admitted fresh fence >22
  recovery_grants_parent_authority: false
```

The recovery registry fragment and generated handoff are reconciled to `COMPLETED`. The parent handoff is released from the recovery block but still has no execution authority until a separate fresh task-control admission occurs.

## Next required execution

```text
independent StegVerse task-control admission
-> fresh parent claim/fence >22
-> real StegVerse local/private model process
-> private/loopback endpoint proof
-> TVC ROUTE_ADMITTED / credential_requirement NONE
-> exact StegVerse LLM-adapter execution
-> measured E1 -> model -> E2 usage
-> same-execution Master Records provider-usage reconstruction PASS
-> same-execution transition reconstruction PASS
```

No heartbeat transition, G18 terminalization, WorkerCoordinator-specific cycle, recovery replay, sibling Master Records checkout, GitHub workflow, Render service, or third-party provider is required to begin that parent transition.

## Validation obligations

Reconciliation validation must prove:

1. terminal recovery evidence remains current and hash-bound;
2. a completed recovery cannot be reacquired by the standalone executor;
3. recovery completion does not create parent authority;
4. parent admission requires a separate fresh fence strictly greater than 22;
5. TV/TVC remains sole credential authority;
6. GitHub/hosted validation remains non-authorizing.

## Archive rule

Recovery itself is terminal. The session remains non-archiveable because parent sovereign inference, TVC route, exact LLM-adapter execution, measured usage, same-execution Master Records proof, Site #388 exact publication, and current-phone governed wallet proof remain nonterminal.
