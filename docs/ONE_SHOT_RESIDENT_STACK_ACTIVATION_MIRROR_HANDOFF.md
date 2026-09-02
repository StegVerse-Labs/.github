# One-Shot Resident Stack Activation Request Mirror Handoff

Updated: 2026-09-02
Repository: StegVerse-Labs/.github
Issue: #774
Goal: SHWP-ONE-SHOT-RESIDENT-STACK-ACTIVATION-001
Parent: handoffs/SHWP-DURABLE-RUNTIME-ACTIVATION.json

## Purpose

Make the already-merged `scripts/activate_resident_stack.py` reachable from the existing sovereign resident request dispatcher without adding a scheduler or task-admission authority.

## Machine path

```text
resident request
-> request-specific non-authorizing consumer
-> resolve already-local source roots
-> activate_resident_stack.py
-> sovereign control bundle
-> local StegDeploy
-> verified bundle materialization
-> resident bootstrap
-> existing WorkerCoordinator admissions
```

## Required local sources

- StegVerse-org/LLM-adapter
- StegVerse-Labs/StegOS
- continuity-vault-kit
- StegVerse-Labs/StegVerse-Healer
- StegVerse-Labs/TV
- StegVerse-Labs/TVC
- master-records/orchestration
- StegVerse-002/micro-node-runtime
- Admissible-Existence/TT
- Admissible-Existence/RTG
- Admissible-Existence/GTG
- Admissible-Existence/AE

The consumer may use preserved non-secret environment locators or `STEGVERSE_REPO_ROOTS_JSON`. Missing roots produce `SOURCE_ROOTS_PENDING`; no network source fetch is attempted.

## Exactly-once

The request retries until the one-shot activation receipt reports `COMPLETE`. After `COMPLETE` for the same request hash, the activator is not re-executed.

## Authority

The request/consumer grants no WorkerCoordinator claim, fence, credential, heartbeat, deployment, provider, repository, network, or sovereign authority. TV/TVC remains credential authority. Downstream task admissions remain governed by the resident bootstrap and existing WorkerCoordinator.

## Authentic completion

Source merge/CI does not prove resident activation.

Required evidence:

`receipts/sovereign-host/one-shot-resident-stack-activation-request-consumption.latest.json`

with `activation_complete=true` and state `COMPLETED` or `ALREADY_CONSUMED`.

Current authentic evidence: NOT OBSERVED.


## Source integration checkpoint

The consumer is registered as resident dispatcher selector:

`one_shot_resident_stack_activation`

Native bootstrap/source-refresh/service materialization includes both:

- `scripts/consume_one_shot_resident_stack_activation_request.py`
- `scripts/activate_resident_stack.py`

Current source state: MERGED / VALIDATED.
Current authentic request consumption: NOT OBSERVED.
Current authentic one-shot activation COMPLETE: NOT OBSERVED.


## Validated source closure — 2026-09-02

Implementation PR #775 merged as `cf4ed69ebe079dd684c501e67ff4a6e70c828d0f`.

Validation:
- Heartbeat Worker Project `33661420619` — SUCCESS
- Cross-Framework Current-Basis Resident Request Validation `33661420625` — SUCCESS
- organization control plane `33661420611` — SUCCESS

The request is durably `REQUESTED` and registered under selector `one_shot_resident_stack_activation`.

Authentic request consumption: NOT OBSERVED.
Authentic one-shot activation `COMPLETE`: NOT OBSERVED.

Source/CI success is not activation evidence.


## Execution-path contract repair — 2026-09-02

Issue #789 repairs a post-merge contract drift between this request consumer and `scripts/activate_resident_stack.py`.

The complete resident activator now requires the pinned SV002 principal/formal source roots. The consumer therefore resolves and passes:

```text
STEGVERSE_MICRO_NODE_RUNTIME_ROOT
STEGVERSE_TT_ROOT
STEGVERSE_RTG_ROOT
STEGVERSE_GTG_ROOT
STEGVERSE_AE_ROOT
```

or the corresponding `STEGVERSE_REPO_ROOTS_JSON` entries.

The consumer does not validate or select formalism commits. Exact pinned-commit validation remains the responsibility of the sovereign bundle packager. Missing roots remain retryable `SOURCE_ROOTS_PENDING`.

This repair matters to SV001 progression because the generic resident dispatcher visits SV001 before the one-shot stack activator. On a fresh resident, the first SV001 attempt may precede complete source materialization. The one-shot activation must therefore be capable of completing its materialize -> StegDeploy -> resident bootstrap path so that the nested/new resident bootstrap dispatch can revisit SV001 with the required TV/TVC/Master Records/formal sources present.

Watching for a receipt is not the remaining work; executing this progression is.
