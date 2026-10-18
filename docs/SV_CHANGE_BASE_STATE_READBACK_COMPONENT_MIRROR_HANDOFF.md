# SV_CHANGE Base-State Readback (B1): reusable component mirror handoff

Organization: `StegVerse-Labs`
Component: `RTC-SV-CHANGE-BASE-STATE-READBACK-014`
Family: `evidence_validation` (`data/reusable-evidence-validation-component-contract.json`)
Class: B capability, decided from the invariant `SV_CHANGE_BASE_UNBOUND`.
Evidence class: `SOURCE_IMPLEMENTED`. Tests run on temporary git repositories whose ledger ref is written by the real writer. No production runtime observation is claimed by this source change.

## Why

SV_CHANGE admission binds a base `{registry_generation, ledger_head}` (TVC `sv_change_admission` B1, P4 `StegVerse-org/.github#192` `admission_predicate.py`). Nothing gave admission callers those two values, so admission failed closed (`SV_CHANGE_BASE_UNBOUND` / `BASE_STATE_NOT_OBSERVED`). Both are observed state, so this is a readback. No issuer is involved.

## What it answers

`resident-runtime/sv_change_base_state_readback.py::evaluate(repository, bound_main_commit, *, hb_epoch=None, main_ref="refs/heads/main")`

- **registry_generation**: `generation` of the repository's own registry file at exactly `bound_main_commit`, read with `git cat-file`. It never reads a working tree. The commit must be `main_ref` or in its history. The path comes from the pinned `REGISTRY_PATHS` map, keyed by the caller's `repository_name`:

  | repository | registry path |
  |---|---|
  | StegVerse-Labs/.github | `data/canonical-task-registry.json` (integer `generation`) |
  | StegVerse-org/.github | `orchestration/task-registry.json` (`orchestration_task_registry`; declares no `generation` at main 40a5d235) |

  There is no default path. An unmapped repository is FAIL_CLOSED `REGISTRY_PATH_NOT_DECLARED`. A registry that declares no `generation` is FAIL_CLOSED `REGISTRY_GENERATION_NOT_DECLARED` (failed_predicate `REGISTRY_DECLARES_GENERATION`, `joint_item` and next_attempt naming joint item **Q-ORG-REGISTRY-GENERATION**, owning_existing_goal #164). A declared but malformed generation, or a missing file, stays `REGISTRY_GENERATION_UNREADABLE`. The component proposes and makes no registry edit.
- **ledger_head**: the commit of `refs/stegverse/organization-ledger` in the same local repository. The chain is verified first by the existing `resident-runtime/organization_ledger_readback.py::readback`, so there is no second verifier. The ref must not move during the read.

Sealed receipt `stegverse.sv-change-base-state-readback/v1`:

```json
{"schema": "stegverse.sv-change-base-state-readback/v1",
 "base_ref": {"registry_generation": 319, "ledger_head": "<40-hex>"},
 "bound_main_commit": "<40-hex>",
 "sources": [{"file": "data/canonical-task-registry.json", "blob_sha": "<git blob>"},
             {"file": "refs/stegverse/organization-ledger:HEAD.json", "blob_sha": "<git blob>"}],
 "disposition": "ALLOW",
 "hb_epoch": null,
 "open_questions": [{"id": "JD-P4-3", "slot": "hb_epoch", "status": "OPEN: ..."}],
 "result_sha256": "sha256:<seal over the canonical receipt>"}
```

`hb_epoch` is an explicit slot. It holds the caller's supplied epoch (ASCII digits >= 32). If none is supplied it is `null` and marked open as JD-P4-3. It is never derived.

| disposition | when |
|---|---|
| `ALLOW` | the registry generation was read at the bound commit, the ledger chain verified, and the head was stable |
| `FAIL_CLOSED REGISTRY_GENERATION_UNREADABLE` | the registry file is absent, unparseable, or lacks an integer `generation` at the bound commit |
| `FAIL_CLOSED BASE_STATE_NOT_OBSERVED` | the bound commit is malformed, absent or not on main; the repository is unreadable; the ledger ref is absent; the existing readback refused (its `failed_predicate` is carried); the head moved during the read; or a supplied hb_epoch is malformed |

Every non-ALLOW carries `failure_code`, `failed_predicate`, `required_evidence_or_repair`, `retry_entrypoint`, `owning_existing_goal` (`StegVerse-org/.github#164`) and `next_attempt`. `authority_effect` is `NONE_READBACK_ONLY`.

The readback writes nothing. It runs only read git verbs (`rev-parse`, `cat-file`, `merge-base`, which a test pins), and reads no clock. It uses no network, credential or new dependency: the caller's existing transport supplies the local clone, as for `organization_ledger_readback.py`.

CLI: `python resident-runtime/sv_change_base_state_readback.py --repository <clone> --bound-main-commit <sha> [--main-ref <ref>] [--hb-epoch <n>]`

## Consumers

- StegVerse-Labs/TVC#519 `sv_change_admission`: the base-state input accepts this receipt. It checks the schema and the seal, pins this script by git blob, and fills the observed `registry_generation`/`ledger_head`. An SV_CHANGE whose own `base_ref` is unbound is still DENY `SV_CHANGE_BASE_UNBOUND`.
- StegVerse-org/.github#192 (P4): the base gen/ledger head inputs that it otherwise fails closed on (`BASE_STATE_NOT_OBSERVED`).

## Composition into a Goal Task: prepared, not applied

Composing the component is a `data/canonical-task-registry.json` mutation. Main is at generation 319, and `scripts/check_registry_generation_fence.py` requires exactly 320. G-8 excludes a generation bump, so the composition is prepared here and left out of this change. No task in the Labs registry currently names `StegVerse-org/.github#164`. The owning Goal Task id is therefore `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` until the registry generation that registers it.

```json
"reusable_task_component_composition": {
  "model": "data/reusable-task-component-model.json",
  "selected_components": ["RTC-SV-CHANGE-BASE-STATE-READBACK-014"],
  "new_reusable_component_required": false
}
```

| field | value |
|---|---|
| class | A |
| failure_code | `GOAL_TASK_COMPOSITION_REQUIRES_REGISTRY_GENERATION` |
| failed_predicate | the Goal Task owning StegVerse-org/.github#164 composes `RTC-SV-CHANGE-BASE-STATE-READBACK-014` in `data/canonical-task-registry.json` at generation 320 = main 319 + 1 |
| required_evidence_or_repair | the canonical Task Registry generation mutation (319 → 320) applying the block above to that Goal Task, admitted under `data/task-coordination-policy.json#session_mutation_generation_fence` and passing `scripts/check_registry_generation_fence.py` |
| retry_entrypoint | the registry generation admission transition (`scripts/check_registry_generation_fence.py --mode pull_request` on the mutation PR) |
| owning_existing_goal | `StegVerse-org/.github#164` |
| next_attempt | after this component is on main, in the next registry generation, re-based on the live tip |

## Local observation (not CI evidence)

On 2026-10-18, run on the box against a local clone (main `978b8880`, ref fetched read-only), the readback returned ALLOW with `base_ref {registry_generation: 319, ledger_head: a5bb54d81893b392a3ce28182986fc39857807e1}`, a ledger chain of 7, and `hb_epoch` null (JD-P4-3 open). This is a local run only.

## Run against StegVerse-org/.github main 40a5d235 (read-only, local bare clone)

Before this fix the producer hard-coded `data/canonical-task-registry.json`, which org/.github does not have, so it returned FAIL_CLOSED `REGISTRY_GENERATION_UNREADABLE`. With `--repository-name StegVerse-org/.github` it reads `orchestration/task-registry.json` (blob `de0f66b1`) and returns FAIL_CLOSED `REGISTRY_GENERATION_NOT_DECLARED`, failed_predicate `REGISTRY_DECLARES_GENERATION`, next_attempt "after joint item Q-ORG-REGISTRY-GENERATION decides how this registry declares its generation", `hb_epoch` null (JD-P4-3), sealed `sha256:6324f1bb432b21de3a357faf902b0ff437fb0c51dd1a0a019600d03382094913`. The clone's refs were unchanged. Local run only, not CI evidence.
