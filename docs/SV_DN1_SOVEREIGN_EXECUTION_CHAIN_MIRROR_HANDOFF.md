# SV-DN-1 Sovereign Execution Chain Mirror Handoff

## Canonical scope

```text
goal_id: SV-DN1-SOVEREIGN-EXECUTION-CHAIN-001
repository: StegVerse-Labs/.github
branch: main
canonical product owner: StegVerse-org/stegverse-demo-suite
canonical product handoff: docs/SV_DN1_DOUBLE_INTERLOCK_MIRROR_HANDOFF.md
credential_authority: TV/TVC
github_token_runtime_authority: NONE
heartbeat_authority: REFERENCE_ONLY
authority_effect: NONE_ORCHESTRATION_ONLY
```

## Goal

Turn the already-merged SV-DN-1 machine tasks into one executable, non-hosted sovereign first-round progression that can consume a single admitted resident execution opportunity without requiring a persistent third-party scheduler or a second user machine.

The chain owns orchestration only:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
-> SV-DN1-RESIDENT-OBSERVER-001
-> SV-DN1-INTR-RUNTIME-001
-> SV-DN1-PRODUCTION-SOURCE-PREP-001
-> SV-DN1-SDK-FIRST-ROUND-001
-> SV-DN1-PUBLIC-PROMOTION-001
-> SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001
```

Each task retains its own canonical WorkerCoordinator claim/fence, authority ceiling, network boundary, receipts, and completion semantics. This chain grants none of those authorities.

## Source-of-truth order

1. `docs/SV_DN1_SOVEREIGN_EXECUTION_CHAIN_MIRROR_HANDOFF.md`
2. `docs/SV_DN1_SOURCE_MATERIALIZATION_MIRROR_HANDOFF.md`
3. `docs/SV_DN1_RESIDENT_OBSERVER_MIRROR_HANDOFF.md`
4. `docs/SV_DN1_INTR_RUNTIME_MIRROR_HANDOFF.md`
5. `docs/SV_DN1_SDK_FIRST_ROUND_MIRROR_HANDOFF.md`
6. `heartbeat_runtime/worker_runtime.py`
7. `scripts/run_worker_runtime.py`
8. `scripts/refresh_sovereign_worker_runtime_source.py`
9. live runtime registry, bound-state receipts, and source roots

Newer authentic runtime evidence overrides this document.

## Admission correction already merged

PR #343 merged the independent-task-control and dependency correction:

```text
merge_commit: 75fbb638a8003d42517620cc95b383070ea3b15e
organization control plane run 33137868295: PASS
heartbeat worker validation run 33137868303: PASS
```

Canonical dependency contract:

```text
SOURCE MATERIALIZATION
  dependencies: []

RESIDENT OBSERVER
  dependencies:
    - SV-DN1-SOURCE-MATERIALIZATION-001

ROUTE-SPECIFIC InTr
  dependencies:
    - SV-DN1-RESIDENT-OBSERVER-001

PRODUCTION SOURCE PREP
  dependencies:
    - SV-DN1-INTR-RUNTIME-001

SDK FIRST ROUND
  dependencies:
    - SV-DN1-INTR-RUNTIME-001
    - SV-DN1-PRODUCTION-SOURCE-PREP-001
```

All seven SV-DN-1 registry fragments are admitted under:

```text
authority_domain: INDEPENDENT_TASK_CONTROL
claim_state: AUTHORIZED_FOR_INDEPENDENT_TASK_CONTROL_CLAIM
fresh_fence_required: true
minimum_fencing_token_exclusive: 22
carrier_trigger_required: false
heartbeat_grants_execution_authority: false
```

WorkerCoordinator's existing dependency gate only releases a child when every declared dependency is exactly `COMPLETED`.

## Runtime execution model

The chain MAY execute only on an actual StegVerse-owned/federated resident process surface that already has the separated carrier reference materialized.

It MUST reject:

- GitHub Actions;
- Render;
- Vercel;
- Cloudflare hosted workers/pages;
- arbitrary hosted CI;
- GitHub/provider credentials;
- fabricated sovereign-node declarations.

The chain does not require a continuous process. It uses targeted one-shot WorkerCoordinator cycles:

```text
python scripts/run_worker_runtime.py --task-id <task-id>
```

This preserves the current architecture:

- HeartBeat reference does not grant authority;
- WorkerCoordinator independently evaluates task admission;
- each task receives a fresh fence;
- unrelated task execution and carrier packets are suppressed in targeted mode;
- GitHub Actions remains validation-only.

## Local source refresh

A resident may refresh static WorkerCoordinator source from an already-local canonical checkout before execution:

```text
scripts/refresh_sovereign_worker_runtime_source.py
```

Refresh:

- performs no network fetch;
- acquires no credential;
- preserves mutable runtime state;
- does not overwrite claims/fences/receipts;
- copies registry and process-adapter fragments;
- does not itself execute a task.

## Step completion verification

The orchestrator must not rely only on process return code.

After each targeted cycle it must re-read the canonical mutable worker registry and require the task state to be `COMPLETED`.

It must also verify the task-specific durable receipt:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
  ~/.stegverse/state/sv-dn1-source-materialization/receipts/latest.json
  transition_id = SV_DN1_EXACT_SOURCE_MATERIALIZATION_COMPLETE

SV-DN1-RESIDENT-OBSERVER-001
  ~/.stegverse/state/sv-dn1-resident-observer/receipts/latest.json
  transition_id = SV_DN1_RESIDENT_SOURCE_CAPTURE_COMPLETE

SV-DN1-INTR-RUNTIME-001
  ~/.stegverse/state/sv-dn1-intr-runtime/receipts/latest.json
  route_id = SV-DN-1-HF-PUBLIC
  state = COMPLETE
  destination_validation = PASS
  lineage_verified = true

  ~/.stegverse/state/sv-dn1-intr-runtime/receipts/carrier-binding.latest.json
  transition_id = SV_DN1_HB_INTR_CARRIER_BOUND
  packet_recovery_verified = true
  heartbeat_progression_dependency = OSCILLATOR_ONLY
  heartbeat_grants_authority = false
  derived_carrier_grants_authority = false
  authority_effect = NONE_CARRIER_ONLY

SV-DN1-PRODUCTION-SOURCE-PREP-001
  ~/.stegverse/state/sv-dn1-production-source-prep/receipts/latest.json
  schema = stegverse.sv-dn1.production-source-prep-receipt/v2
  transition_id = SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE
  source_identity_scheme = sha256-content-manifest
  exactly four canonical source_identities are present
  exactly four canonical source_roots are present
  source_root_env agrees with source_roots component-by-component
  migration_anchors_verified = true
  network_source_fetch_performed = false
  github_platform_required = false
  credential_used = false
  github_token_used = false
  repository_writeback_performed = false
  sdk_admitted = false

SV-DN1-SDK-FIRST-ROUND-001
  ~/.stegverse/state/sv-dn1-sdk-first-round/receipts/latest.json
  transition_id = SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED
```

If a task returns to `HANDOFF_READY`, becomes `BLOCKED`, or lacks the required durable receipt, the chain stops. It never skips a predecessor or fabricates completion.

## Production source roots

The SDK first-round worker requires exact local canonical roots:

```text
STEGVERSE_SDK_SOURCE_ROOT
STEGVERSE_STEGCORE_SOURCE_ROOT
STEGVERSE_CORE_LITE_SOURCE_ROOT
STEGVERSE_MASTER_RECORDS_SOURCE_ROOT
```

The orchestrator may forward these non-secret locators but may not invent or remotely acquire private repository credentials.

Source preparation is platform-neutral. Any of the four canonical components may be satisfied by an already-local verified root supplied through its non-secret `STEGVERSE_*_SOURCE_ROOT` locator, by a root already present under the canonical materialization tree, or by a local content-addressed StegVerse source package. The source-preparation worker performs no network acquisition and does not require GitHub or the repository broker merely to recognize already-local source. If a component is genuinely absent from all admitted local surfaces, it stops `HANDOFF_READY` and names the required local package location.

## Resident request bridge

A canonical resident request is intent only, not authority.

The chain may be requested through an additional resident request file without replacing the existing Ecosystem Chat request. A resident request consumer may invoke this chain only after local source refresh and still relies on the seven task handoffs for actual claim/fence/network/execution authority.

The request must state:

```text
request_granted_authority: false
heartbeat_grants_execution_authority: false
github_token_required: false
credential_authority: TV/TVC
second_machine_required: false
```

## Actual sovereign execution boundary

Repository evidence does not itself prove that a task-capable sovereign resident process is currently executing this chain. Heartbeat existence must not be confused with worker execution. Actual completion requires fresh WorkerCoordinator claim/fence and task receipts. Source merge, hosted CI, or chat execution cannot substitute.

## Completion

Chain completion transition:

`SV_DN1_SOVEREIGN_FIRST_ROUND_CHAIN_COMPLETE`

It requires all seven tasks `COMPLETED` with their exact durable receipts, including exact-byte public promotion and the repository-persistence package, and the final first-round receipt proving:

```text
sdk_admission: SDK_ADMITTED
master_records_custody_status: RECORDED
replay_consequence_reexecuted: false
reconstruction_consequence_reexecuted: false
first_round_analysis: ANALYZED
dashboard_generated: true
dashboard_publicly_hosted: false
```

Public hosting remains a separate repository/Pages publication gate.

## Current state

```text
independent-task-control correction: MERGED / PASS
source worker: MERGED
resident worker: MERGED
InTr worker: MERGED
production source prep worker: MERGED / VALIDATED
SDK first-round worker: MERGED
single-opportunity sovereign chain orchestrator: MERGED
public promotion worker: MERGED / WAITING ON AUTHENTIC SDK ANALYSIS
repository persistence package worker: MERGED / WAITING ON PUBLIC PROMOTION
resident request bridge: MERGED
current resident request 007: MERGED / REQUESTED
browser evidence Universal InTr ingress: MERGED / VALIDATED / RUNTIME ADMISSION NOT YET OBSERVED
authentic Hugging Face browser observation: OBSERVED
authentic EXTERNAL_SYSTEM -> STEGOS_ECOSYSTEM InTr hop: OBSERVED
authentic chain execution receipt: NOT OBSERVED
public live dashboard: NOT PUBLISHED
```

## v2 production-source receipt correction — 2026-08-30

The sovereign chain validates the canonical v2 source identity/root contract directly and forwards the four verified non-secret locators to the SDK first-round worker only after that validation succeeds. This grants no source acquisition, credential, repository, SDK, governance, or publication authority.

## 2026-08-30 end-to-end analysis continuity correction

The authentic browser observation is a valid upstream evidence object, but a locator is not useful if an orchestration process silently removes it from the environment before the SDK evidence adapter starts.

The exact non-secret local locators required for end-to-end analysis continuity are:

```text
STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE
STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT
```

The first identifies the already-local authentic `stegverse.sv-dn1.browser-resident-observation-bundle/v3` consumed by `workers/sv_dn1_sdk_browser_evidence_adapter.py`. It is not a credential and grants no authority. The second permits an explicitly relocated source-preparation v2 bound-state root to remain continuous across a portable resident invocation.

These locators MUST survive, when present, across all three process boundaries:

```text
scripts/refresh_and_dispatch_resident_requests.py
  -> scripts/consume_sv_dn1_resident_execution_request.py
  -> scripts/run_sv_dn1_first_round_chain.py
  -> WorkerCoordinator adapter environment
```

The portable bridge may select `--only-consumer sv_dn1`. That exact selection only refreshes already-local static source and visits the already-registered `sv_dn1` consumer. It does not create a new dispatcher, scheduler, claim, fence, source transport, browser evidence object, or execution authority. The historical cross-framework consumer remains the default and HIL remains an independent explicit selector.

Success for this correction is source-level only:

```text
sv_dn1 exact portable selector accepted
unrelated consumers not dispatched
browser observation bundle locator preserved if supplied
production source-prep state locator preserved if supplied
hosted and credential-bearing environments still rejected
no network source fetch
no request/execution authority created
```

Authentic analysis remains unobserved until the eligible sovereign resident actually consumes `RESIDENT-EXEC-SV-DN1-FIRST-ROUND-007` and emits `SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED`. Public display remains a separate downstream promotion/deployment gate.


## 2026-08-30 repository-persistence package extension

The canonical resident progression now contains seven independent tasks:

```text
SV-DN1-SOURCE-MATERIALIZATION-001
-> SV-DN1-RESIDENT-OBSERVER-001
-> SV-DN1-INTR-RUNTIME-001
-> SV-DN1-PRODUCTION-SOURCE-PREP-001
-> SV-DN1-SDK-FIRST-ROUND-001
-> SV-DN1-PUBLIC-PROMOTION-001
-> SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001
```

The seventh task does not mutate a remote repository. It freezes the exact five promoted bytes, hashes, target repository/ref/path set, exchange identity and manifest receipt identity into `stegverse.sv-dn1.repository-persistence-package/v1`. Terminal transition is `SV_DN1_REPOSITORY_PERSISTENCE_PACKAGE_READY`.

This removes the runtime-to-repository-content handoff ambiguity without granting GitHub, credential, commit, push, merge or deployment authority. A separately admitted TV/TVC-governed repository mutator remains required for actual persistence.

Request `RESIDENT-EXEC-SV-DN1-FIRST-ROUND-005` is superseded for this seven-step chain. The current exact request is `RESIDENT-EXEC-SV-DN1-FIRST-ROUND-007`, which is merged and `REQUESTED`; it grants no execution, credential, network-source-fetch, repository-writeback, deployment, publication-decision, release, or certification authority.


## Final-chain locator drift repair — 2026-08-30

Live source inspection after public-source publication found implementation drift from the continuity contract above: `scripts/run_sv_dn1_first_round_chain.py` did not include `STEGVERSE_SV_DN1_BROWSER_OBSERVATION_BUNDLE` or `STEGVERSE_SV_DN1_PRODUCTION_SOURCE_PREP_STATE_ROOT` in its clean child environment, and durable source-prep receipt validation ignored the relocated state-root locator.

The repaired contract is:

```text
portable targeted bridge
  preserves browser observation locator + source-prep state locator
resident SV-DN-1 consumer
  preserves the same locators
sovereign first-round chain
  preserves the same locators into WorkerCoordinator children
  resolves production-source-prep receipt from the relocated state root when supplied
```

This correction creates no new network, credential, source-acquisition, repository, SDK, governance, or publication authority. It only prevents already-authentic local evidence/state coordinates from being silently discarded at the final process boundary.


## 2026-08-31 post-analysis publication continuation

The seven-step resident first-round chain remains the bounded analysis/package progression.
It is now followed by two independently governed machine tasks:

```text
SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001
  -> SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001
       -> TVC #264 exact bounded repository transport
       -> terminal: SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED

SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001
  -> separately governed PR merge + Pages deployment
  -> SV-DN1-PUBLICATION-OBSERVER-001
       -> terminal: SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED
```

The persistence-dispatch task is merged at
`0206c30556ebe9210e7ae4ab664e6dc5d3feabac`.

The TVC issue-264 fail-closed admission evaluator is merged in
`StegVerse-Labs/TVC@bcdab574520b2f132120376fe1c85a9ad1020c27`.

The publication observer must not release before the persistence-dispatch task is
`COMPLETED` at `SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED`. PR creation still does not
prove merge/deployment, so public observation remains an independent retryable gate.

The InTr step now also emits the stronger HB-derived carrier-binding receipt merged at
`9344d5a944f4fd6e4f33df4d01826311bfebd894`. Existing Universal InTr lineage remains
required; the carrier-binding receipt adds exact HB reference/channel/phase/packet
evidence and grants no authority.


## 2026-08-31 shared-HB carrier terminal strengthening — issue #650

The current exact resident request is `RESIDENT-EXEC-SV-DN1-FIRST-ROUND-007`.

`SV-DN1-INTR-RUNTIME-001` is now durable-terminal for this chain only when all three evidence surfaces reconcile:

```text
receipts/latest.json
receipts/carrier-binding.latest.json
<heartbeat-runtime>/<shared_hb_signal_ref>
```

The chain validates main InTr receipt lineage, the HB carrier-binding receipt, exact shared-signal digest, carrier signal identity, carrier-binding digest, packet SHA-256, independent exact packet recovery, OSCILLATOR_ONLY progression, and zero HB/derived-carrier authority.

An older first-round result lacking the shared HB signal cannot satisfy request 007 even if its route-specific InTr receipt remains historically valid.


## 2026-08-31 governed merge continuation

The post-analysis publication chain is now explicitly:

```text
SV-DN1-REPOSITORY-PERSISTENCE-PACKAGE-001
  -> SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001
     -> SV_DN1_REPOSITORY_PERSISTENCE_PR_CREATED

SV-DN1-REPOSITORY-PERSISTENCE-DISPATCH-001
  -> SV-DN1-REPOSITORY-MERGE-DISPATCH-001
     -> TVC bounded merge spool
     -> TVC-SV-DN1-REPOSITORY-MERGE-GATE-001
     -> SV_DN1_REPOSITORY_PERSISTENCE_PR_MERGED

SV-DN1-REPOSITORY-MERGE-DISPATCH-001
  -> repository-owned Pages deployment
  -> SV-DN1-PUBLICATION-OBSERVER-001
     -> SV_DN1_AUTHENTIC_PUBLICATION_OBSERVED
```

The merge-dispatch task is credential-free and cannot merge. The TVC merge gate is a
separate bounded authority that independently verifies the exact PR/base/head, exact five
paths, exact frozen bytes, and clean mergeability before using the TV/TVC credential.
GitHub Actions remains validation-only and repository branch protection remains the
required-check authority.
