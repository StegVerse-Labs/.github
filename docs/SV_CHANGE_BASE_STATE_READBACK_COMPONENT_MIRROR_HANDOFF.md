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
             {"file": "refs/stegverse/organization-ledger:HEAD.json", "blob_sha": "<git blob>"},
             {"file": "refs/stegverse/organization-ledger:receipts/<hex>.json", "blob_sha": "<git blob>"}],
 "disposition": "ALLOW",
 "hb_epoch": "469411750",
 "hb_epoch_source": {"ledger_head": "<40-hex>", "receipt": "receipts/<hex>.json", "field": "$.hb_reference.epoch"},
 "ledger_head_receipt_sha256": "sha256:<hex>",
 "result_sha256": "sha256:<seal over the canonical receipt>"}
```

`hb_epoch_source` has exactly three fields, and Lane B #46 (@64b90721) consumes these names: `ledger_head` (the ledger ref commit
the epoch was read at), `receipt` (the head receipt's ledger_store key `receipts/<hex>.json`, relative to
`refs/stegverse/organization-ledger`; the same path appears in `sources`), and `field` (`$.hb_reference.epoch`). It is sealed
with `hb_epoch` on ALLOW and on DENY HB_EPOCH_MISMATCH, where the epoch was observed. **On every FAIL_CLOSED, `hb_epoch` is
null and `hb_epoch_source` is present and null.** It is never omitted, so a consumer can tell an unobserved epoch from an older
receipt format. The rule citation is not in this slot: it is in `EPOCH_RULE_SOURCE` / `EPOCH_RULE_FUNCTION`
(kernel.py:68-74; supplied_epoch_failure 726248a5).

Known answer (live, `RTC014_LIVE_LABS_REPO`): Labs ledger head `a5bb54d81893b392a3ce28182986fc39857807e1`, receipt
`receipts/35810b6598e99cef32d9a0f1f97d07394d9f21c540ed7d3a395d9d78b753db3d.json`, hb_epoch `"469411750"`.

`hb_epoch` is **observed state**. JD-P4-3 is part-decided by invariant ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH, with Labs#3236 as precedent.

- **What it is.** The epoch is the one recorded on the org-ledger head receipt that the base is bound to.
- **How it is read.** The read follows the real Labs#3255 layout:
  1. `HEAD.json` at the bound ledger head (`ledger_store.HEAD_KEY`).
  2. `ledger_store.receipt_key(receipt_sha256)`, i.e. `receipts/<hex>.json`, which gives the sealed `stegverse.organization-transition-receipt/v1` (`aggregate_repo_transition.py:1073-1092`).
  3. `$.hb_reference.epoch` (`kernel.hb_reference`).

  The files are blobs `7660d2bc` (aggregate_repo_transition.py), `43d36e6a` (ledger_store.py) and `ffec5d64` (kernel.py), identical on main 978b8880 and #3255 75fc4ddd.
- **Validation.** The value is `str($.hb_reference.epoch)`, and only when three things hold: the epoch is an int (not a bool, no coercion), it is >= 32, and `$.hb_reference.derived_from_clock` is exactly false. The rule source is `org-kernel/kernel.py:68-74` (`hb_reference`, blob `ffec5d64`). This is the same rule as P1 #3264 @fc19b532 `base_ledger_head_epoch`. The seal is `receipt_sha256` = sha256 of the canonical body without it, using the #3255/#3270 `canon`/`sha`. There is no top-level hb_epoch, and the receipt format is unchanged.
- **Sealing.** The epoch is sealed with the rest of the receipt.
- **Refusals.**
  - A head receipt without a valid epoch gives FAIL_CLOSED `HB_EPOCH_SOURCE_UNOBSERVED`.
  - `--hb-epoch` is never a source, only a cross-check. If a verified sealed epoch contradicts it, that is an observed contradiction: DENY `HB_EPOCH_MISMATCH` with six fields. P4's name `HB_EPOCH_FLAG_MISMATCH` is kept in the detail (`flag_failure_code`). FAIL_CLOSED `HB_EPOCH_SOURCE_UNOBSERVED` is only for an epoch that is absent, unsealed, clock-derived (derived_from_clock not exactly false), not an int, a bool, or under 32.
  - Rule sources, both cited: `org-kernel/kernel.py` lines 68-74 (`hb_reference`) and P1's citation, sha256 `726248a585904b52cfe2eec1754e7ce582f67d6b501bd664bb7bee80bce9b7ef` of the source segment of `kernel.py::supplied_epoch_failure` (lines 236-269), both in blob `ffec5d648d7fa4aead1f44f76df936a2da21bb96`. The sha256 was verified against those bytes (the test checks it).
- **No minting.** No epoch is ever minted here. Minting an epoch for new ledger appends is still undecided.

| disposition | when |
|---|---|
| `ALLOW` | the registry generation was read at the bound commit, the ledger chain verified, and the head was stable |
| `FAIL_CLOSED REGISTRY_GENERATION_UNREADABLE` | the registry file is absent, unparseable, or lacks an integer `generation` at the bound commit |
| `FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED` | the head receipt is absent, unsealed, not an organization-transition receipt, or its `hb_reference` epoch is missing, not an int, below 32, or derived from a clock (failed_predicate `ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH`) |
| `DENY HB_EPOCH_MISMATCH` | `--hb-epoch` was given and is malformed (not ASCII digits >= 32) or differs from the verified observed epoch. `hb_epoch` and `hb_epoch_source` stay sealed, because the ledger epoch was observed. Detail: `expected_hb_epoch` (the supplied value), `supplied_hb_epoch_well_formed`, `flag_failure_code: HB_EPOCH_FLAG_MISMATCH`, and `supplied_epoch_failure_code: HB_EPOCH_INVALID` when malformed |
| `FAIL_CLOSED BASE_STATE_NOT_OBSERVED` | the bound commit is malformed, absent or not on main; the repository is unreadable; the ledger ref is absent; the existing readback refused (its `failed_predicate` is carried); or the head moved during the read. A supplied hb_epoch never causes this code: it is judged only against the observed epoch |

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

## Epoch slot filled from the head receipt (local runs, not CI evidence)

These are read-only box runs; the refs were unchanged.

**Labs main 978b8880, ledger head a5bb54d8: ALLOW.**
- `base_ref {319, a5bb54d81893b392a3ce28182986fc39857807e1}`
- `hb_epoch "469411750"`, read from receipt `sha256:35810b65…db3d`
- seal `sha256:318c47a6d36c6df7cc04fef8f076cc45de44ac81525bddd55c3dc5b6554a62ec`

**Org main 40a5d235: FAIL_CLOSED `REGISTRY_GENERATION_NOT_DECLARED`.**
- It refuses before the ledger is read, so the epoch slot stays unset.
- Seal: `sha256:5b9eda6c4f036318a1577dc6cb3f092377c2c5b465d48667cfdd03ded14106e3`.
- Diagnostic only: `ledger_head_epoch` on the org ledger head 2acec0e1 reads epoch 446655631 from receipt `sha256:51a48225…5a64`.
- The known-answer test (`RTC014_LIVE_LABS_REPO`) runs against the live head a5bb54d8. It reads receipt 35810b65, verifies its seal, and gets `"469411750"`.
- `--hb-epoch 469411751` against the same head gives DENY `HB_EPOCH_MISMATCH` (detail `HB_EPOCH_FLAG_MISMATCH`), seal `sha256:7791f0567770553eed10a9d203ed3dfffa471f2badc84aecc2cf2049cf0c7e57`. `--hb-epoch 469411750` gives the same ALLOW receipt as no flag (seal `sha256:318c47a6…`).

## 15:41Z ruling: a malformed --hb-epoch is DENY HB_EPOCH_MISMATCH

A malformed or differing supplied epoch is DENY `HB_EPOCH_MISMATCH` with the six fields. This matches P1 `verify_admission_hb_epoch`, Lane B #46, P4 #192 and Lane D #3270.
Before this change, a malformed value was FAIL_CLOSED `BASE_STATE_NOT_OBSERVED` (`HB_EPOCH_SUPPLIED_WELL_FORMED`), which is now removed.

**Sealing decision.** The supplied value is judged only after the ledger-head epoch is observed.
- When the epoch was observed, `hb_epoch` and `hb_epoch_source` are sealed exactly as on ALLOW, and the supplied value is carried as `expected_hb_epoch`.
  - It is copied verbatim if it is a JSON scalar, and as its `repr` otherwise.
  - Two further fields go with it: `supplied_hb_epoch_well_formed` and, when malformed, `supplied_epoch_failure_code: HB_EPOCH_INVALID`, the kernel's name.
- An earlier refusal keeps its own code, for example a bound commit that is not on main, or a registry failure.
- An unobservable ledger-head epoch is FAIL_CLOSED `HB_EPOCH_SOURCE_UNOBSERVED` whatever was supplied, with `hb_epoch` and `hb_epoch_source` sealed null.

## 16:00Z refinement: supplied-epoch classes (contract invariant = P1's next verify_admission_hb_epoch)

| `--hb-epoch` | result |
|---|---|
| omitted entirely | no cross-check runs; the ledger-derived ALLOW stands (**deliberate**, see below) and carries the canonical not-cross-checked marker (New Bot ruling 16:30Z, P1 invariants.json `NOT_CROSS_CHECKED_MARKER`): top-level `cross_checked: false` plus top-level `detail: "HB_EPOCH_NOT_CROSS_CHECKED"` (= P1 #3264 @7898cedb `verify_admission_hb_epoch`, sv_work_items.py blob 4c2aa6ef); see the table below for the other dispositions |
| given explicitly as `""`, the string `"null"` or `UNKNOWN_NOT_AUTHENTICALLY_OBSERVED` (or `None` through the Python API) (16:03Z narrowing) | FAIL_CLOSED `HB_EPOCH_SOURCE_UNOBSERVED`. `hb_epoch` and `hb_epoch_source` are sealed null, as on every FAIL_CLOSED, and the detail carries `supplied_hb_epoch` |
| any other malformed value (bool, negative, non-numeric, < 32, ...) | DENY `HB_EPOCH_MISMATCH`, slots sealed, `supplied_hb_epoch_well_formed: false` |
| well-formed and differing | DENY `HB_EPOCH_MISMATCH`, slots sealed, `supplied_hb_epoch_well_formed: true` |
| equal | ALLOW |

**`cross_checked` is always emitted** (P1 `NOT_CROSS_CHECKED_MARKER`, amended 17:15Z). All fields are top level, and no `hb_epoch_cross_check` key is ever emitted.

| Receipt | `cross_checked` | `supplied_hb_epoch` | `detail` |
|---|---|---|---|
| ALLOW, `--hb-epoch` omitted | `false` | absent | `"HB_EPOCH_NOT_CROSS_CHECKED"` |
| ALLOW, cross-check held | `true` | the value given | absent |
| DENY `HB_EPOCH_MISMATCH` | `true`: the cross-check ran against the observed sealed epoch and disagreed | the value given | absent |
| FAIL_CLOSED, any code | `false`: no comparison with a sealed epoch was made | the value given, when the flag was given (including `""`, `"null"` and the sentinel) | absent |

- **The `supplied_hb_epoch` name** is P1 @7898cedb's own name for the supplied epoch, used in `sv_work_items.admission_inputs` and `evaluate_admission`. P1 has no producer-side field of its own, so this name was used instead of `hb_epoch_supplied`.
- **Its value** is the supplied value verbatim when it is a JSON scalar, and its `repr` otherwise.
- **The DENY receipt still carries its earlier detail fields:** `expected_hb_epoch`, `supplied_hb_epoch_well_formed`, `flag_failure_code` and `supplied_epoch_failure_code`.


These classes apply only once the ledger-head epoch is observed. An earlier refusal keeps its own code, and an unobservable ledger-head epoch is FAIL_CLOSED `HB_EPOCH_SOURCE_UNOBSERVED` whatever was supplied.

**Deliberate choice for the omitted flag.** `--hb-epoch` is this readback's optional cross-check, not the admission's supplied epoch. With no flag there is nothing to cross-check, so the readback returns the observed ledger epoch.
An admission whose supplied epoch is absent, "", "null" or the sentinel fails closed in the admission (TVC#519 `admit()`, P1 `verify_admission_hb_epoch`), not here.
The Python API marks the omitted case with the `OMITTED` default; an explicit `hb_epoch=None` is null.
