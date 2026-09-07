# Native Email Action Monitor Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Provider implementation owner: `StegVerse-Labs/StegOps-Orchestrator`
Provider credential/execution authority: `StegVerse-Labs/TVC`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Canonical Task Registry identifier: `STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001`
Resident request identifier: `RESIDENT-EXEC-NATIVE-EMAIL-ACTION-MONITOR-001`
Canonical Task Registry source state: `PROPOSED`
Allowed next governed transition: `INGRESS_ADMITTED`
Status: `HB_RESIDENT_BINDING_IMPLEMENTED / CANONICAL_SOURCE_REGISTRATION_RECONCILED / AUTHENTIC_RUNTIME_PENDING`

## Purpose

Move the established StegVerse email-action monitor out of an assistant-mediated loop and into a deterministic StegVerse-native handler without creating a second mail provider stack, credential authority, scheduler, WorkerCoordinator, heartbeat, or runtime authority.

## Canonical coordination reconciliation — 2026-09-06

The native email source and resident request existed before the work item was present in the authoritative canonical Task Registry. That was a coordination defect: source existence did not establish canonical work intent, and no WorkerCoordinator claim/fence or Master Records observation could be inferred to fill that gap.

The existing identity is now registered as source-state coordination only:

```text
task_id: STEGVERSE-NATIVE-EMAIL-ACTION-MONITOR-001
coordination_state: PROPOSED
allowed_next_transition: INGRESS_ADMITTED
worker_claim: null
worker_fence: null
runtime_execution_claimed: false
master_records_reconciliation_claimed: false
```

Canonical registration is in `data/canonical-task-registry.json` generation 16. The governing preflight receipt is `receipts/session-build-preflight/native-email-action-monitor-001-source-registration.json`. It applies the existing `REGISTER_EXISTING_TASK_AS_PROPOSED_SOURCE_STATE` precedent rather than creating a new task allocator, scheduler, WorkerCoordinator, monitor, provider broker, or credential path.

Cross-task evidence is projected by `control/cross-task-coordination.d/native-email-action-monitor-001.json`. It preserves three separate predicates:

```text
PRED-NATIVE-EMAIL-REQUEST-STAGED-001 = SATISFIED
PRED-RESIDENT-REQUEST-CONSUMED-NATIVE-EMAIL-ACTION-MONITOR-001 = UNKNOWN
PRED-NATIVE-EMAIL-MONITOR-RECEIPT-001 = UNKNOWN
```

The first predicate proves only canonical source staging. The latter two require authentic resident/provider-produced receipts and may not be satisfied by source, merge, CI, heartbeat progression, email content, or GitHub notification state.

Master Records remains the observed-reality/reconstruction authority. No native-email Master Records runtime observation is claimed by this source registration. WorkerCoordinator remains the only claim/fence authority; this registration mints neither. Interlock/InTr remains the required governed transition boundary before the task can advance beyond `PROPOSED`.

An unrelated active G18 claim/fence remains foreign to this task and is not reused, modified, released, or treated as native-email authority.

### README impact determination

This coordination reconciliation is non-material to repository behavior. `README.md` already documents the native email capability, its existing HB/oscillator resident path, the TV/TVC provider boundary, and canonical Task Registry / WorkerCoordinator / Master Records authority separation. The machine preflight therefore records `NO_README_CHANGE_REQUIRED` with evidence; no README behavior claim is changed by registration.

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

- Task Registry records work intent/coordination only;
- source registration is not governed ingress;
- WorkerCoordinator alone owns execution claim/fence;
- Master Records alone owns observed reality/reconstruction;
- email observation is not runtime evidence;
- archive success is not technical-task runtime evidence;
- GitHub/CI notification content is not proof of source, merge, deployment, runtime failure, or activation;
- incident proposal does not admit technical work;
- HeartBeat/HB-derived carriage grants no authority;
- oscillator progression remains `OSCILLATOR_ONLY`;
- Interlock/InTr remains task-transition authority;
- TV/TVC remains credential/provider authorization authority;
- no second user-operated machine is required by the source design.

## README impact preflight

The original native runtime/provider linkage was a material function change and its required README updates were completed in that implementation change set.

The current canonical Task Registry/cross-task reconciliation is `material_function_change=false`. The machine preflight records `NO_README_CHANGE_REQUIRED` because it changes coordination source state only and does not alter runtime behavior, interfaces, authority boundaries, evidence semantics, prerequisites, dependencies, failure behavior, provider operations, or capability meaning.

## Source surfaces

```text
StegVerse-Labs/.github:
  data/canonical-task-registry.json
  control/cross-task-coordination.d/native-email-action-monitor-001.json
  receipts/session-build-preflight/native-email-action-monitor-001-source-registration.json
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
  tasks/TVC-RESIDENT-SERVICE-SELF-HEAL-001.json
  tasks/TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006.json
  tvc_gmail_owner_session.py
  scripts/tvc_mail_provider_operation.py
  tests/test_tvc_native_email_gmail.py
```

## Related canonical task identities

These are adjacent to the native-email task and may be resolved in the same coordination session without merging their independent authority transitions:

```text
STEGVERSE-CANONICAL-WORK-COORDINATION-001
STEGVERSE-CANONICAL-RUNTIME-PROFILE-MAP-001
TVC-NATIVE-EMAIL-GMAIL-OWNER-SESSION-001
TVC-RESIDENT-SERVICE-SELF-HEAL-001
TVC-PRIMARY-RUNTIME-ACTIVATION-DELIVERY-006
```

The active `SHWP-DURABLE-RUNTIME-ACTIVATION` G18 claim/fence is a collision boundary, not a combinable native-email authority source.

## Authentic completion boundary

Source, PR, merge, or CI does not prove live Gmail execution. Authentic native completion requires:

```text
1. canonical task registration exists as PROPOSED;
2. governed Interlock/InTr ingress advances the exact task identity when admissible;
3. all three source owners are merged/current on the resident host;
4. resident source refresh materializes the native monitor consumer and request;
5. an exact TV/TVC Gmail owner session is active at the local vault-agent boundary;
6. an HB/resident dispatch actually consumes the standing request;
7. native-email-action-monitor-request-consumption.latest.json reports COMPLETED with runtime_execution_attempted=true;
8. native-email-action-monitor.latest.json reports stegverse.native-email-action-monitor-receipt/v1 state PASS;
9. Master Records authentically reconciles the resulting observed reality;
10. mailbox observations confirm only the exact reviewed operational messages were archived.
```

Until those retained runtime receipts are observed, runtime activation remains unproven. Source registration, cross-task predicates, source merge, hosted validation, or HB progression do not substitute for them.

## User action

No provider credential, refresh token, OAuth client secret, or access token may be entered into chat, GitHub, repository files, workflow secrets, argv, or ordinary environment variables. Owner-present Google consent, when an active Gmail owner session must be established or reauthorized, is performed only through the exact TV/TVC provider-session boundary and can be completed from the authorized iPhone browser; no second user-operated machine is required.
