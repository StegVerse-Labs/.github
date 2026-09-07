# Native Email Action Monitor Mirror Handoff

Updated: 2026-09-07
Repository: `StegVerse-Labs/.github`
Task: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
COSV task vector: `10100000100000`
Reusable identity: `RT-NATIVE-EMAIL-ACTION-MONITOR-001`
Resident request: `RESIDENT-EXEC-NATIVE-EMAIL-ACTION-MONITOR-001`
Provider implementation owner: `StegVerse-Labs/StegOps-Orchestrator`
Provider credential/execution authority: `StegVerse-Labs/TVC`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Status: `HANDOFF_REINITIATION_UNTIL_GITHUB_INBOX_EMPTY_SOURCE_IMPLEMENTED / AUTHENTIC_RUNTIME_TERMINAL_RECEIPT_PENDING`

## Purpose

Move the established StegVerse email-action monitor out of an assistant-mediated loop and into the deterministic StegVerse-native resident path. The user initiates the goal; the ecosystem continues the task from its canonical Task ID + COSV pointer until the terminal mailbox predicate is satisfied or a genuine human-authority boundary occurs.

No ChatGPT mailbox loop, second scheduler, second WorkerCoordinator, second heartbeat, second provider stack, or alternate credential authority is introduced.

## Canonical continuation contract

The canonical continuation pointer is:

```text
STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001
10100000100000
```

Every successful bounded pass is classified from the mailbox result:

```text
processed_exact_count > 0
  -> state = HANDOFF_READY
  -> handoff_task_id = STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001
  -> handoff_cosv_task_vector = 10100000100000
  -> handoff_action = RESOLVE_POINTER_AND_INITIATE_TASK_AGAIN
  -> existing resident dispatcher resolves the same canonical task/handoff again

processed_exact_count == 0
  -> github_inbox_empty = true
  -> state = COMPLETED
  -> no successor handoff pointer
```

A successful pass that archived GitHub mail is therefore **not task completion**. It is evidence for one bounded iteration and produces the same canonical handoff pointer for the next iteration.

The normal terminal predicate is exactly:

`GITHUB_INBOX_MATCHING_OPERATIONAL_QUERY_EMPTY`

The task must not claim normal completion merely because one bounded archive pass succeeded.

## Canonical runtime linkage

```text
HB32 / canonical oscillator reference
-> existing resident WorkerCoordinator cycle
-> scripts/dispatch_resident_execution_requests.py
-> standing request control/resident-execution-request.d/native-email-action-monitor-001.json
-> scripts/consume_native_email_action_monitor_request.py
-> resolve canonical Task/COSV pointer
-> scripts/run_native_email_action_monitor.py
-> StegOps scripts/native_email_tvc_broker.py
-> TVC scripts/tvc_mail_provider_operation.py
-> Gmail provider operation under exact TV/TVC owner session
-> native monitor receipt
-> consumption classification
-> HANDOFF_READY + same Task/COSV when mail was processed
-> next resident cycle resolves pointer and initiates task again
-> COMPLETED only after a later bounded pass observes zero matching inbox messages
```

HB/oscillator progression provides continuation opportunity only and grants no admission, mailbox, claim/fence, credential, task, route, transition, or execution authority.

## Native bounded pass

`StegVerse-Labs/.github/scripts/run_native_email_action_monitor.py` remains a one-pass bounded mailbox handler:

```text
SEARCH_MESSAGES operational GitHub/[Task Update] INBOX slice, max 100
-> SEARCH_IDS same operational slice before mutation
-> cluster GitHub / [Task Update] observations
-> ARCHIVE_IDS exact resolved IDs only
-> SEARCH_IDS actionable query, max 100
-> GET_LABEL_COUNTS INBOX
-> emit stegverse.native-email-action-monitor-receipt/v1
```

The operational search remains restricted to GitHub notification senders and `[Task Update]` mail. Unrelated inbox mail is not selected for archive.

The resident consumer—not the bounded provider operation—owns iteration classification. This preserves one bounded provider operation per iteration while allowing canonical Task/COSV handoff continuation across resident cycles.

## Reused canonical implementation

Email failure clustering reuses `scripts/normalize_github_failure_email_events.py`. GitHub and Task Update emails remain observation/attention signals only. An email cluster is `INCIDENT_PROPOSED_NOT_ADMITTED`; technical work still requires canonical task ingress.

Gmail/provider ownership reuses `StegVerse-Labs/StegOps-Orchestrator`. The provider-side adapter remains `scripts/native_email_tvc_broker.py` and delegates only to the exact TV/TVC Gmail provider command.

TVC exact credential-class authority remains bounded by `TVC-NATIVE-EMAIL-GMAIL-OWNER-SESSION-001` under credential-model invariant `CMI-015`. No generalized OAuth manager or new credential authority is created.

## Provider boundary

StegOps may normalize a TVC provider result into `stegverse.native-email-broker-response/v1` only when all are true:

```text
provider = GMAIL
credential_authority = TV/TVC
credential_material_exported = false
provider_operation_authority_transferred = false
operation in {SEARCH_MESSAGES, SEARCH_IDS, ARCHIVE_IDS, GET_LABEL_COUNTS}
```

TVC resolves only `vault://tvc/providers/gmail/owner-session` inside the TV/TVC process boundary and requires the exact `gmail.modify` scope. No provider credential material may cross into `.github`, StegOps, monitor receipts, incident proposals, or logs.

## Authority invariants

- the Task ID or COSV vector grants no authority;
- a handoff grants no authority;
- email observation is not technical-task runtime evidence;
- archive success is not technical-task completion evidence;
- GitHub/CI notification content is not proof of source, merge, deployment, runtime failure, or activation;
- incident proposal does not admit technical work;
- HeartBeat/HB-derived carriage grants no authority;
- WorkerCoordinator remains claim/fence authority;
- Interlock/InTr remains task-transition authority;
- TV/TVC remains credential/provider authorization authority;
- no second user-operated machine is required by the source design.

## README impact determination

The 2026-09-07 correction changes internal completion bookkeeping for an already-documented standing, retryable native monitor. The root README already states that the monitor is resident, bounded, standing/retryable, uses no assistant-mediated loop, reuses the existing HB continuation path, and does not grant new authority. This correction does not change mailbox selection, provider operations, interfaces, credential boundaries, external prerequisites, or authority semantics.

Detailed Task/COSV re-initiation and the exact terminal predicate are maintained in this canonical task handoff and consumer receipts. Root README remains accurate; no additional root README mutation is required for this correction.

## Source surfaces

```text
StegVerse-Labs/.github:
  control/task-vectors/STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001.json
  data/reusable-task-registry.json
  scripts/run_native_email_action_monitor.py
  scripts/consume_native_email_action_monitor_request.py
  scripts/dispatch_resident_execution_requests.py
  scripts/refresh_sovereign_worker_runtime_source.py
  control/resident-execution-request.d/native-email-action-monitor-001.json
  tests/test_native_email_action_monitor.py
  tests/test_native_email_resident_integration.py
  tests/test_native_email_handoff_continuation.py

StegVerse-Labs/StegOps-Orchestrator:
  scripts/native_email_tvc_broker.py
  tests/test_native_email_tvc_broker.py
  README_GMAIL.md

StegVerse-Labs/TVC:
  tasks/TVC-NATIVE-EMAIL-GMAIL-OWNER-SESSION-001.json
  tvc_gmail_owner_session.py
  scripts/tvc_mail_provider_operation.py
  tests/test_tvc_native_email_gmail.py
```

## Authentic completion boundary

Authentic completion requires all of the following:

```text
1. current source owners are available to the resident path;
2. resident source refresh has materialized the monitor consumer/request;
3. an exact TV/TVC Gmail owner session is active;
4. resident dispatch consumes the standing request;
5. every successful non-empty pass returns the same Task/COSV handoff pointer;
6. that pointer is resolved and initiates the next resident iteration without human transcription;
7. a later native monitor receipt reports processed_exact_count == 0;
8. the associated consumption receipt reports github_inbox_empty=true and state=COMPLETED;
9. no unrelated inbox messages were selected for archive.
```

Source, merge, CI, heartbeat progression, or a prior successful archive pass does not satisfy the terminal predicate.

## Human action

No human re-entry of Task ID/COSV is required between ordinary iterations. Human action is required only if the actual provider/authority path reaches a genuine human boundary, such as owner-present Google reauthorization. No provider credential, refresh token, OAuth client secret, or access token may be entered into chat, GitHub, repository files, workflow secrets, argv, or ordinary environment variables.
