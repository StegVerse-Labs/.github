# Repository Ledger Genesis Readback: reusable component mirror handoff

Organization: `StegVerse-Labs`
Component: `RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013`
Family: `evidence_validation` (`data/reusable-evidence-validation-component-contract.json`)
Evidence class: `SOURCE_IMPLEMENTED`. Tests run on temporary git refs written by the real writer. No production runtime observation is claimed by this source change.

## Where it lives

The Task Registry Library is the Reusable Task Component Model:

- `data/reusable-task-component-model.json` (`component_families`, `component_interface_minimum`)
- the family contract each family points to

A component is declared as an entry in its family contract. `RTC-EVIDENCE-CURRENT-SELECTOR-010` was added the same way (674d4577, contract only). Goal Tasks compose components in `data/canonical-task-registry.json` under `reusable_task_component_composition.selected_components`.

## What it answers

Input: `organization`, `repository`, `expected_organization_ledger_head` and `owning_existing_goal`, in a `stegverse.repository-ledger-genesis-readback-request/v1` manifest.

It fresh-fetches `refs/stegverse/organization-ledger` anonymously from `https://github.com/<organization>/.github.git` into a temporary bare repository. A request cannot choose the source. It then reads the chain back with the existing `resident-runtime/organization_ledger_readback.py` (`readback` and `repository_readback`), so there is no second verifier.

| disposition | when |
|---|---|
| `ALLOW` | `repository-ledger/<organization>/<repository>/HEAD.json` is present, the chain verifies, every receipt is retained in the organization ledger, and the bound head equals the fetched head or is an ancestor of it. Applying a genesis appends to the ref, so a moved head never hides a retained genesis. |
| `FAIL_CLOSED REPOSITORY_LEDGER_HEAD_PRESENT` | no repository HEAD, and the ref is still at the bound head |
| `FAIL_CLOSED EXPECTED_ORG_LEDGER_HEAD_MOVED` | no repository HEAD, and the ref moved. `observed_organization_ledger_head` is the head to re-bind to. |
| other `FAIL_CLOSED` | the ref was not fetched, the bound head is not in the ledger's history, the existing readback refused the chain, or the request is malformed |

Every non-ALLOW carries `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` and `next_attempt`. `authority_effect` is `NONE_READBACK_ONLY`, and `consequence_committed` is false. The readback writes nothing outside its temporary directory, reads no clock, and has no loop, retry, credential or new dependency.

## How it is invoked

By manifest, through flows that already exist:

1. A request is committed as `control/resident-execution-request.d/repository-ledger-genesis-readback-<org>-<repo>-NNN.json`. This change adds the one for `StegVerse-org/StegVerse-SDK`, bound to `2acec0e1cfd158a6a3313ad422737caf41badda3` (the head its `initialization-manifest.v1.json` declares).
2. The existing source refresh carries `control/resident-execution-request.d/` and the consumer `scripts/consume_repository_ledger_genesis_readback_request.py` (added to `STATIC_FILES`) to the resident runtime.
3. The existing resident request dispatcher visits consumer `repository_ledger_genesis_readback`, which:
   - returns `NO_REQUEST` when there is no such manifest;
   - otherwise retains each answer once, under `receipts/sovereign-host/repository-ledger-genesis-readback/<request digest>-<observed head>.json`, as `RECORDED_LOCAL_READBACK`, then `ALREADY_RECORDED` for the same request and head.

   A malformed manifest is a `BOUNDARY` and is not retained.

Nothing here schedules anything. When the readback runs is decided by the ecosystem's existing refresh and dispatch transitions.

## Composition into a Goal Task: prepared, not applied

Composing the component into `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` is a `data/canonical-task-registry.json` mutation. Main is at generation 319, and `scripts/check_registry_generation_fence.py` requires exactly 320 for it. G-8 excludes a generation bump, so the composition is prepared here and left out of this change:

```json
"reusable_task_component_composition": {
  "model": "data/reusable-task-component-model.json",
  "selected_components": ["RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013"],
  "readback_requests": ["control/resident-execution-request.d/repository-ledger-genesis-readback-stegverse-org-stegverse-sdk-001.json"],
  "new_reusable_component_required": false
}
```

| field | value |
|---|---|
| class | A |
| failure_code | `GOAL_TASK_COMPOSITION_REQUIRES_REGISTRY_GENERATION` |
| failed_predicate | `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` composes `RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013` in `data/canonical-task-registry.json` at generation 320 = main 319 + 1 |
| required_evidence_or_repair | the canonical Task Registry generation mutation (319 → 320) applying the block above, admitted under `data/task-coordination-policy.json#session_mutation_generation_fence` and passing `scripts/check_registry_generation_fence.py` |
| retry_entrypoint | the registry generation admission transition (`scripts/check_registry_generation_fence.py --mode pull_request` on the mutation PR), then TVC#519 `MERGE_ADMITTED_PULL_REQUEST` with a governance-decision ALLOW |
| owning_existing_goal | `ORGANIZATION-BATCH-CUSTODY-REPLAY-001` |
| next_attempt | after this component is on main, in the next registry generation, re-based on the live tip |
