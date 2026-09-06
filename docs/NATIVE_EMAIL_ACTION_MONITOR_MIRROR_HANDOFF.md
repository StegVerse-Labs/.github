# Native Email Action Monitor Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Provider implementation owner: `StegVerse-Labs/StegOps-Orchestrator`
Provider credential/execution authority: `StegVerse-Labs/TVC`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Status: `HB_RESIDENT_BINDING_IMPLEMENTED_TVC_GMAIL_ROUTE_SOURCE_INTEGRATION_ACTIVE`

## Purpose

Move the established StegVerse email-action monitor out of an assistant-mediated loop and into a deterministic StegVerse-native handler without creating a second mail provider stack, credential authority, scheduler, WorkerCoordinator, heartbeat, or runtime authority.

## Canonical runtime linkage

The monitor is now bound to the already-existing HB/oscillator resident continuation path rather than an external wall-clock monitor:

```text
HB32 / canonical 100 Hz oscillator reference
-> existing HB machine-continuation / resident worker cycle
-> existing scripts/dispatch_resident_execution_requests.py
-> standing request control/resident-execution-request.d/native-email-action-monitor-001.json
-> scripts/consume_native_email_action_monitor_request.py
-> scripts/run_native_email_action_monitor.py
-> StegOps scripts/native_email_tvc_broker.py
-> TVC scripts/tvc_mail_provider_operation.py
-> Gmail provider operation when an exact TV/TVC owner session is active
-> stegverse.native-email-action-monitor-receipt/v1
```

HB/oscillator progression grants no admission, credential, mailbox, claim/fence, task, route, or execution authority. It provides only the already-canonical deterministic continuation opportunity. The standing resident request remains non-authorizing and retryable so a temporary provider-session absence does not silently terminate the capability.

No ChatGPT automation is part of this native path and no second scheduler is introduced.

## Reused canonical implementation

Email failure clustering reuses `scripts/normalize_github_failure_email_events.py`. GitHub and Task Update emails remain observation/attention signals only. An email cluster is `INCIDENT_PROPOSED_NOT_ADMITTED`; technical work still requires canonical task ingress.

Gmail/provider ownership reuses the existing `StegVerse-Labs/StegOps-Orchestrator` Gmail integration surface. The retired consumer-side Google OAuth path remains retired. The provider-side adapter is `scripts/native_email_tvc_broker.py` in StegOps and delegates only to the exact TV/TVC Gmail provider command.

TVC exact credential-class authority is bounded by `TVC-NATIVE-EMAIL-GMAIL-OWNER-SESSION-001` under credential-model invariant `CMI-015`; this is a provider-specific extension and does not create a generalized OAuth manager or new credential authority.

## Native monitor sequence

`StegVerse-Labs/.github/scripts/run_native_email_action_monitor.py` performs exactly one bounded pass:

```text
SEARCH_MESSAGES operational GitHub/[Task Update] INBOX slice, max 100
-> SEARCH_IDS same operational slice before mutation
-> cluster GitHub / [Task Update] observations
-> ARCHIVE_IDS exact resolved IDs only
-> SEARCH_IDS actionable query, max 100
-> GET_LABEL_COUNTS INBOX
-> emit stegverse.native-email-action-monitor-receipt/v1
```

The operational search is explicitly restricted to GitHub notification senders and `[Task Update]` mail. Unrelated inbox mail is not selected for archive.

The separate exact-ID query is mandatory because a provider may return fewer expanded message objects than IDs in the bounded result. If the actionable query returns a continuation token, the handler records a lower bound rather than inventing a total. Partial archive retains exact failed IDs and emits `PARTIAL_ARCHIVE_FAILURE`.

Nested broker invocation uses an exact JSON command vector so StegOps provider-command options cannot be misparsed by the monitor CLI.

## Provider boundary

The `.github` monitor invokes a local broker command using `stegverse.native-email-broker-request/v1`.

StegOps normalizes a TVC provider result into `stegverse.native-email-broker-response/v1` only when all are true:

```text
provider = GMAIL
credential_authority = TV/TVC
credential_material_exported = false
provider_operation_authority_transferred = false
operation in {SEARCH_MESSAGES, SEARCH_IDS, ARCHIVE_IDS, GET_LABEL_COUNTS}
```

TVC provider execution resolves only `vault://tvc/providers/gmail/owner-session` inside the TV/TVC process boundary, requires the exact `gmail.modify` scope, and returns only bounded mailbox result fields plus secret-free evidence. No Google token, refresh token, OAuth client secret, GitHub token, or other credential material may cross into `.github`, StegOps, monitor receipts, incident proposals, or logs.

## Authority invariants

- email observation is not runtime evidence;
- archive success is not technical-task runtime evidence;
- GitHub/CI notification content is not proof of source, merge, deployment, runtime failure, or activation;
- incident proposal does not admit technical work;
- HeartBeat/HB-derived carriage grants no authority;
- oscillator progression remains `OSCILLATOR_ONLY`;
- WorkerCoordinator remains claim/fence authority;
- Interlock/InTr remains task-transition authority;
- TV/TVC remains credential/provider authorization authority;
- no second user-operated machine is required by the source design.

## README impact preflight

`material_function_change=true`.

README updates are required in the source owners because this change adds resident execution linkage, operational-mail archive scope, and exact provider-session expectations. README completeness grants no runtime or provider authority.

## Source surfaces

```text
StegVerse-Labs/.github:
  scripts/run_native_email_action_monitor.py
  scripts/consume_native_email_action_monitor_request.py
  scripts/dispatch_resident_execution_requests.py
  scripts/refresh_sovereign_worker_runtime_source.py
  control/resident-execution-request.d/native-email-action-monitor-001.json
  tests/test_native_email_action_monitor.py
  tests/test_native_email_resident_integration.py

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

Source, PR, merge, or CI does not prove live Gmail execution. Authentic native completion requires:

```text
1. all three source owners merged/current;
2. resident source refresh materializes the native monitor consumer and request;
3. an exact TV/TVC Gmail owner session is active at the local vault-agent boundary;
4. an HB/resident dispatch actually consumes the standing request;
5. a qualifying stegverse.native-email-action-monitor-receipt/v1 is retained;
6. mailbox observations confirm only the exact reviewed operational messages were archived.
```

Until the retained native receipt is observed, runtime activation remains unproven even though the previous generic “runtime pending” gap has been reduced to the exact provider-session and resident-consumption predicates above.

## User action

No provider credential, refresh token, OAuth client secret, or access token may be entered into chat, GitHub, repository files, workflow secrets, argv, or ordinary environment variables. Owner-present Google consent, when an active Gmail owner session must be established or reauthorized, is performed only through the exact TV/TVC provider-session boundary and can be completed from the authorized iPhone browser; no second user-operated machine is required.
