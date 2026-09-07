# Native Email Action Monitor Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Resident request: `RESIDENT-EXEC-NATIVE-EMAIL-ACTION-MONITOR-001`
Failure-remediation task-creation owner: `StegVerse-Labs/StegHealth`
StegHealth owner task: `STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001`
StegHealth COSV task vector: `10100000100000`
Provider implementation owner: `StegVerse-Labs/StegOps-Orchestrator`
Provider credential/execution authority: `StegVerse-Labs/TVC`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Status: `HANDOFF_REINITIATION_UNTIL_GITHUB_INBOX_EMPTY_AND_STEGHEALTH_FAILURE_TASK_OWNERSHIP_SOURCE_IMPLEMENTED / AUTHENTIC_RUNTIME_TERMINAL_AND_REPLAY_RECEIPTS_PENDING`

## Purpose

Move the established StegVerse email-action monitor out of an assistant-mediated loop and into the deterministic StegVerse-native resident path without losing the original corrective-work behavior. The user initiates the goal; the ecosystem continues the task from its canonical Task ID + COSV pointer until the GitHub operational inbox predicate is empty, while actionable failure observations are mapped and handed to StegHealth for corrective-task creation/resumption.

No ChatGPT mailbox loop, second scheduler, second WorkerCoordinator, second heartbeat, second provider stack, alternate credential authority, or email-owned repair authority is introduced.

## Canonical continuation contract

```text
STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001
10100000100000
```

Every successful bounded pass is classified from the exact GitHub/[Task Update] mailbox result:

```text
processed_exact_count > 0
  -> state = HANDOFF_READY
  -> handoff_task_id = STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001
  -> handoff_cosv_task_vector = 10100000100000
  -> handoff_action = RESOLVE_POINTER_AND_INITIATE_TASK_AGAIN

processed_exact_count == 0
  AND all mapped failures have durable StegHealth ownership/handoff
  -> github_inbox_empty = true
  -> state = COMPLETED
  -> no successor email-monitor handoff pointer
```

A successful archive pass is not task completion. It is one bounded iteration. The normal terminal predicate is:

`GITHUB_INBOX_MATCHING_OPERATIONAL_QUERY_EMPTY_AND_FAILURE_RECONCILIATION_DURABLE`

## Mailbox scope

`run_native_email_action_monitor.py` selects only:

```text
-in:spam -in:trash
(from:notifications@github.com OR from:noreply@github.com OR subject:"[Task Update]")
```

with `INBOX` label binding and a maximum bounded batch of 100. Unrelated inbox mail is outside the selection predicate and may not be archived by this task.

Each bounded pass remains:

```text
SEARCH_MESSAGES exact GitHub/[Task Update] INBOX slice
-> SEARCH_IDS same exact slice
-> normalize / cluster failure observations
-> ARCHIVE_IDS exact reviewed operational IDs only
-> SEARCH_IDS actionable GitHub failure query
-> GET_LABEL_COUNTS INBOX
-> emit native monitor receipt
```

## Failure mapping and StegHealth ownership

The original monitor behavior requires actionable failure observations to continue into corrective work rather than stop at reporting.

Ownership is now explicit:

```text
GitHub / [Task Update] failure email
-> normalize repository / workflow / error signature
-> stable failure/incident map
-> exact existing Task/COSV hint when available
-> StegHealth failure-remediation consumer
-> reuse existing corrective task OR create StegHealth-owned corrective Task/COSV
-> import StegHealth-created canonical candidate
-> Canonical Work / Interlock-InTr ingress
-> WorkerCoordinator claim/fence
-> admitted corrective execution
-> validation / durable evidence / Master Records
```

`.github/scripts/reconcile_email_failure_incidents.py` is mapping/delegation only. It MUST NOT invent corrective task identity. StegHealth owns creation through:

- `StegVerse-Labs/StegHealth/tasks/STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001.json`
- `StegVerse-Labs/StegHealth/tools/consume_ecosystem_failure_map.py`
- `StegVerse-Labs/StegHealth/docs/STEGHEALTH_ECOSYSTEM_FAILURE_REMEDIATION_MIRROR_HANDOFF.md`

The `.github` path may import only StegHealth-created canonical candidates into the live Canonical Task Registry/task-vector index for ordinary Canonical Work ingress. Task creation and registry import grant no execution authority.

## Archived-email replay correction

GitHub/[Task Update] messages archived before the StegHealth ownership path was installed must be replayed as observations through the same failure-map contract. Replay:

- does not restore messages to INBOX merely to process them;
- does not treat each email as a distinct failure;
- clusters repeated notifications by normalized repository/workflow/error signature;
- reuses existing Task/COSV when already tracked;
- sends unresolved distinct failure lineages to StegHealth exactly once for corrective-task creation;
- retains archived message IDs as evidence references so mailbox cleanup cannot erase the corrective-work lineage.

## Canonical runtime linkage

```text
HB32 / canonical oscillator reference
-> existing resident WorkerCoordinator cycle
-> scripts/dispatch_resident_execution_requests.py
-> standing native email request
-> scripts/consume_native_email_action_monitor_request.py
-> scripts/run_native_email_action_monitor.py
-> StegOps native_email_tvc_broker.py
-> TVC tvc_mail_provider_operation.py
-> Gmail under exact TV/TVC owner session
-> native monitor receipt
-> scripts/reconcile_email_failure_incidents.py
-> already-local StegHealth failure-remediation consumer
-> StegHealth Task/COSV handoff
-> Canonical Work / InTr where new work is required
-> email monitor HANDOFF_READY until terminal predicate is satisfied
```

HB/oscillator progression provides continuation opportunity only and grants no admission, mailbox, claim/fence, credential, task, route, transition, or execution authority.

## Authority invariants

- Task ID/COSV grants no execution authority;
- handoff grants no execution authority;
- email observation is not technical-task runtime evidence;
- archive success is not corrective-task completion evidence;
- GitHub/CI notification content is not proof of source, merge, deployment, runtime failure, or activation;
- StegHealth task creation is coordination, not execution authority;
- WorkerCoordinator remains claim/fence authority;
- Interlock/InTr remains task-transition authority;
- TV/TVC remains credential/provider authorization authority;
- no second user-operated machine is required by the source design.

## Behavioral-parity invariant

The native migration must preserve the superseded monitor's evaluation and corrective-work behavior. A migration/refactor/replacement that retains transport/security but drops failure mapping, corrective-task creation/resumption, continuation, validation, or downstream evidence behavior is incomplete unless an explicit canonical decision authorizes that behavior change.

`session_build_preflight.py` now exposes a behavioral-parity completeness gate for migration/replacement work. This gate is non-authorizing and does not replace source tests or runtime proof.

## README impact determination

The StegHealth side is a material repository responsibility change and its `README.md` is updated in the same change set.

For `.github`, the root README already states the ecosystem-owned continuation model, adjacent-task derivation/reuse contract, Canonical Work/InTr boundary, WorkerCoordinator authority separation, and migration completeness/readme-preflight model. The detailed email-monitor-to-StegHealth owner routing is task-scoped operational ownership and is maintained in this canonical handoff. No additional root README behavioral claim is required for this scoped owner correction; this determination is evidence-supported by the existing autonomous-goal-resolution and Canonical Work sections plus this handoff.

## Source surfaces

```text
StegVerse-Labs/.github:
  control/task-vectors/STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001.json
  data/reusable-task-registry.json
  scripts/run_native_email_action_monitor.py
  scripts/normalize_github_failure_email_events.py
  scripts/reconcile_email_failure_incidents.py
  scripts/consume_native_email_action_monitor_request.py
  scripts/dispatch_resident_execution_requests.py
  scripts/refresh_sovereign_worker_runtime_source.py
  scripts/session_build_preflight.py
  control/resident-execution-request.d/native-email-action-monitor-001.json
  tests/test_native_email_action_monitor.py
  tests/test_native_email_resident_integration.py
  tests/test_native_email_handoff_continuation.py

StegVerse-Labs/StegHealth:
  tasks/STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001.json
  tools/consume_ecosystem_failure_map.py
  tests/test_ecosystem_failure_remediation.py
  docs/STEGHEALTH_ECOSYSTEM_FAILURE_REMEDIATION_MIRROR_HANDOFF.md
  README.md

StegVerse-Labs/StegOps-Orchestrator:
  scripts/native_email_tvc_broker.py

StegVerse-Labs/TVC:
  tasks/TVC-NATIVE-EMAIL-GMAIL-OWNER-SESSION-001.json
  scripts/tvc_mail_provider_operation.py
```

## Authentic completion boundary

Authentic completion requires all of the following:

```text
1. resident source refresh materializes the current monitor/mapping source;
2. the exact TV/TVC Gmail owner session is active;
3. resident dispatch consumes the standing monitor request;
4. each non-empty pass maps actionable failure evidence before/archive-time evidence is discarded from the inbox;
5. mapped failures reach the already-local StegHealth consumer;
6. StegHealth reuses or creates the expected corrective Task/COSV;
7. new StegHealth tasks enter ordinary Canonical Work/InTr ingress;
8. corrective work proceeds under WorkerCoordinator/InTr where admitted;
9. archived historical failure emails are replayed without duplicate task proliferation;
10. a later monitor pass observes zero matching GitHub/[Task Update] inbox messages;
11. the consumption receipt reports github_inbox_empty=true and state=COMPLETED;
12. no unrelated inbox messages were selected for archive.
```

Source, merge, CI, heartbeat progression, or a prior archive pass does not satisfy those runtime predicates.

## Human action

No human re-entry of Task ID/COSV is required between ordinary iterations. Human action is required only if an actual provider/authority path reaches a genuine human boundary such as owner-present Google reauthorization. No provider credential, refresh token, OAuth client secret, or access token may be entered into chat, GitHub, repository files, workflow secrets, argv, or ordinary environment variables.
