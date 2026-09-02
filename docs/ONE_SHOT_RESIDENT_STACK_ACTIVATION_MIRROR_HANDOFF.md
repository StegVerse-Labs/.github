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

Current source state: IMPLEMENTED / VALIDATION PENDING.
Current authentic request consumption: NOT OBSERVED.
Current authentic one-shot activation COMPLETE: NOT OBSERVED.
