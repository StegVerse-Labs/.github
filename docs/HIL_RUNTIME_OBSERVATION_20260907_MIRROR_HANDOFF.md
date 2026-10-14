# HIL Runtime Observation Mirror Handoff

Updated: 2026-10-14
Repository: `StegVerse-Labs/.github`
Primary task: `SHWP-HIL-SOVEREIGN-RECEIVER-001`
COSV ID: `50000000105000`
Canonical parent: `docs/HIL_SOVEREIGN_RECEIVER_ACTIVATION_MIRROR_HANDOFF.md`
Issue: `StegVerse-Labs/.github#246`

## Reconciled current state

This handoff reconciles the historical same-device blocker text in the parent handoff with the current merged repository and issue state.

```text
worker_state: HANDOFF_READY
executor_binding: AUTHORIZED
same_device_execution_required: true
requires_other_machine: false
public_gateway_required_for_lease_open: false
same_device_local_lease_source_installed: true
source_implementation_required_before_runtime_observation: false
resident_request: RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
resident_consumption_predicate: PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002
resident_consumption_predicate_state: UNKNOWN
authentic_runtime_execution_observed: false
receiver_ready_observed: false
tvc_lifecycle_receipt_observed: false
master_record_release_ready: false
release_tag_authority: false
```

Issue #889 is resolved. Routine HIL activation no longer requires the remote shared Service Gateway to be READY before ESRL `LEASE_OPEN`. Local verified same-device runtime identity/readiness is sufficient for the source-level lease path; public observation remains downstream and optional for local lease opening.

## Superseded for the participant path (2026-10-14)

Owner direction on `StegVerse-Labs/.github#3106` (2026-10-13): no external machine is or will be awaiting anything, and every action is bound to a state transition. The continuation below (a same-device resident dispatcher consuming `RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002`, ESRL `LEASE_OPEN`, WorkerCoordinator claim/fence) is therefore **not** a prerequisite for a HIL participant submission, and nothing waits on it:

- **Observed path.** The participant path is observed working without it. A participant submits from `stegverse.org` to the Cloudflare Worker receiver (`StegVerse-Labs/Site` `src/worker.js`, D1 `HIL_REGISTRY`, backend `portable-sqlite-chunks-v1`). The Site HIL Participant Readiness Gate (run 38324642386) and an owner packet both verified end to end.
- **Canonical state.** `StegVerse-Labs/Site` `docs/HIL_SITE_MIRROR_HANDOFF.md` records the current state, in its 2026-10-13 and 2026-10-14 sections.
- **Unsent packets.** An unsent packet is a held outbox state on the participant's device (`HIL_SUBMISSION_HELD_IN_OUTBOX`). Delivery happens on the participant's next action, never on receiver liveness (Site#1590).
- **Recorded, not passed.** The predicates below remain recorded as they were. This note marks none of them as satisfied and claims no runtime, custody, TVC or Master Records evidence.

## Highest-priority continuation

No additional HIL source adapter, WorkerCoordinator, claim/fence plane, scheduler, heartbeat, or second-machine path should be created.

The next authentic transition is:

```text
existing same-device resident dispatcher
-> consume RESIDENT-EXEC-HIL-SOVEREIGN-RECEIVER-002
-> satisfy PRED-RESIDENT-REQUEST-CONSUMED-HIL-SOVEREIGN-RECEIVER-002
-> same-device ESRL materialization
-> local identity/readiness verification
-> LEASE_OPEN
-> WorkerCoordinator real claim + fresh fence
-> HIL sovereign receiver READY
-> receiver/custody evidence
-> controlled browser HIL-RECEIVER-RECEIPT-v2
-> controlled restart/replacement exact-byte reconstruction
-> TVC HIL lifecycle receiving/admission
-> separately governed private review/publication
-> Master Records release eligibility
```

Source, CI, GitHub Actions, documentation, heartbeat progression, request issuance, or public availability must not be substituted for those authentic runtime observations.

## Evidence expected from the resident path

At minimum, continuation should surface authentic component-produced evidence equivalent to:

```text
receipts/sovereign-host/resident-request-dispatch.latest.json
receipts/sovereign-host/hil-resident-execution-request-consumption.latest.json
receipts/sovereign-host/resident-targeted-execution.latest.json
receipts/sovereign-network/hil-intr-ingress.latest.json
receipts/sovereign-host/hil-intr-materialization-consumption.latest.json
receipts/hil-sovereign-receiver/SHWP-HIL-SOVEREIGN-RECEIVER-001.json
```

The exact current receipt locations remain governed by the existing resident runtime implementation; this handoff does not fabricate or pre-claim them.

## Authority boundaries

```text
credential_authority: TV/TVC
github_token_runtime_authority: NONE
request_grants_execution_authority: false
heartbeat_grants_execution_authority: false
transport_grants_execution_authority: false
manual_claim_or_fence_minting_allowed: false
second_user_machine_required: false
third_party_runtime_authority: false
```

HIL must not consume or satisfy the claim/fence or completion predicates of G18, Ecosystem Chat, or another worker lane merely because they share the resident substrate.

## Known remaining integration destinations

These are downstream only after their existing predicates become eligible; none may be pre-promoted by this handoff:

- `StegVerse-Labs/Site` — direct HIL participant/readiness/receipt projection.
- `StegVerse-Labs/TVC` — HIL lifecycle receiving/admission and private-review path.
- `master-records` — custody/reconstruction/release only after its own predicates.
- `GCAT-BCAT-Engine/Publisher` — publication propagation only after authorized release.
- `admissibility-wiki` — documentation propagation only after release state is proven.
- `stegguardian-wiki` — documentation propagation only after release state is proven.

## Completion boundary

The repository-side HIL implementation is treated as fully developed for the currently identified same-device activation source path, with no known HIL source scaffolding/stubs required before resident execution. The task itself remains incomplete because authentic runtime, custody, reconstruction, TVC lifecycle, review/publication, and Master Records evidence are not yet proven.

Do not close `StegVerse-Labs/.github#246` and do not tag/release HIL from this task until those authentic predicates are satisfied.
