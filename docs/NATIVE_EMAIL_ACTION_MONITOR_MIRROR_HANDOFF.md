# Native Email Action Monitor Mirror Handoff

Updated: 2026-09-06
Repository: `StegVerse-Labs/.github`
Provider implementation owner: `StegVerse-Labs/StegOps-Orchestrator`
Credential authority: `TV/TVC`
GitHub token runtime authority: `NONE`
Status: `SOURCE_IMPLEMENTED_PROVIDER_ROUTE_RUNTIME_PENDING`

## Purpose

Move the established StegVerse email-action monitor out of an assistant-mediated loop and into a deterministic StegVerse-native handler without creating a second mail provider stack, credential authority, scheduler, WorkerCoordinator, or runtime authority.

## Reused canonical implementation

Email failure clustering reuses `scripts/normalize_github_failure_email_events.py`. GitHub and Task Update emails remain observation/attention signals only. An email cluster is `INCIDENT_PROPOSED_NOT_ADMITTED`; technical work still requires canonical task ingress.

Gmail/provider ownership reuses the existing `StegVerse-Labs/StegOps-Orchestrator` Gmail integration surface. The old consumer-side Google OAuth credential path remains retired. The provider-side adapter is `scripts/native_email_tvc_broker.py` in StegOps and delegates only to an already-local TV/TVC-admitted provider route.

## Native monitor sequence

`StegVerse-Labs/.github/scripts/run_native_email_action_monitor.py` performs exactly one bounded pass:

```text
SEARCH_MESSAGES newest INBOX slice, max 100
-> SEARCH_IDS same slice before mutation
-> cluster GitHub / [Task Update] observations
-> ARCHIVE_IDS exact resolved IDs
-> SEARCH_IDS actionable query, max 100
-> GET_LABEL_COUNTS INBOX
-> emit stegverse.native-email-action-monitor-receipt/v1
```

The separate exact-ID query is mandatory because a provider may return fewer expanded message objects than IDs in the bounded result.

If the actionable query returns a continuation token, the handler records a lower bound rather than inventing a total. Partial archive retains exact failed IDs and emits `PARTIAL_ARCHIVE_FAILURE`.

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

No Google token, refresh token, OAuth client secret, GitHub token, or other credential material may cross into `.github`, monitor receipts, incident proposals, or logs.

## Authority invariants

- email observation is not runtime evidence;
- archive success is not runtime evidence;
- GitHub/CI notification content is not proof of source, merge, deployment, runtime failure, or activation;
- incident proposal does not admit technical work;
- HeartBeat/HB-derived carriage grants no authority;
- WorkerCoordinator remains claim/fence authority;
- Interlock/InTr remains task-transition authority;
- TV/TVC remains credential/provider authorization authority;
- no second user-operated machine is required by the source design.

## README impact preflight

`material_function_change=true`.

README updates are required and included in both source owners:

- `StegVerse-Labs/.github/README.md` documents the native bounded monitor workflow, exact-ID archive invariant, incident semantics, receipt semantics, and provider boundary.
- `StegVerse-Labs/StegOps-Orchestrator/README.md` documents the bounded TVC-governed Gmail broker and retirement of consumer-side provider credentials.
- `StegVerse-Labs/StegOps-Orchestrator/README_GMAIL.md` is reconciled so it no longer presents the retired direct OAuth path as current authority.

README completeness grants no runtime or provider authority.

## Source completion

Source implementation includes:

- `.github/scripts/run_native_email_action_monitor.py`;
- `.github/tests/test_native_email_action_monitor.py`;
- StegOps `scripts/native_email_tvc_broker.py`;
- StegOps `tests/test_native_email_tvc_broker.py`;
- README updates in both repositories.

## Authentic completion boundary

Source, PR, merge, or CI does not prove live Gmail execution. Authentic native completion requires the StegVerse runtime to invoke the monitor through the StegOps broker and an actually admitted TV/TVC Gmail provider route, with a qualifying non-secret provider result and the resulting monitor receipt retained.

Until that occurs, status remains `SOURCE_IMPLEMENTED_PROVIDER_ROUTE_RUNTIME_PENDING`.

## User action

None required for source integration. Provider authorization, when needed, remains governed by the existing TV/TVC provider-session model rather than a new manual credential-entry path in this handler.
