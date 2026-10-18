#!/usr/bin/env python3
"""Apply Task Registry record data (work items, owner questions) at exactly tip + 1.

Until now every record-data change to data/canonical-task-registry.json was a
hand-made edit with a hand-set generation. This entrypoint applies a data file of
schema ``stegverse.registry-record-data-proposal/v1``:

* ``work_items``: {task_id: [work item, ...]} set on Registry rows, validated by the
  handoff projection's own ``project_work_items`` (no item may be rejected);
* ``human_actions``: owner questions merged by ``id`` into the top-level list, each
  with ``question``, ``default_until_answered``, ``source_ref``, ``state`` and a
  ``task_id`` that is null or resolves in the Registry;
* ``register_from_record``: task ids whose standalone record
  (data/canonical-task-records/<id>.json) is projected unchanged into a new aggregate
  row; a task already registered with different content is refused;
* ``row_fields``: exact ``before`` -> ``after`` edits of a field path
  (``["field"]`` or ``["field", index]``) on a Registry row and, when it exists, the same
  path in the task's standalone record; refused unless the current value equals
  ``before`` (a value already equal to ``after`` is a no-op).

A record-derived row is admissible only if the seven validators accept it after the
write; otherwise every file is restored and the refusal names the validator.

Task identity resolves through ``find_source`` of
apply_admitted_canonical_work_projection.py; a task that exists only as a shard is
refused, because only the aggregate Registry carries the generation. The new
generation is checked with ``evaluate_pull_request`` of check_registry_generation_fence.py
against the live tip (``--tip-ref``), the same gate CI runs. With ``--apply`` the file is
written (indent 2, UTF-8 preserved), the Cross-Task Coordination validators and the
handoff projection of every task run, and on any failure the file is restored.

Deterministic and idempotent: data already present is a NO_CHANGE with no bump.
Every refusal carries the standard six fields and changes nothing. Read-only toward
every other surface; it grants no admission, claim, fence or runtime authority.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_SCHEMA = "stegverse.registry-record-data-proposal/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = "python scripts/apply_task_record_data.py <data.json> --apply"
VALIDATORS = (
    "scripts/audit_canonical_task_projections.py",
    "scripts/audit_execution_substrate_resolution.py",
    "scripts/validate_four_missing_cosv_tracking.py",
    "scripts/validate_org_control_plane.py",
    "scripts/validate_task_record_actionable_disposition.py",
    "scripts/validate_task_registration_substrate_resolution.py",
    "scripts/validate_task_registry_global_invariants.py",
)
QUESTION_FIELDS = ("id", "question", "default_until_answered", "source_ref", "state")
PROTECTED_FIELDS = {"task_id", "schema", "correlation_id", "root_correlation_id"}
_MISSING = object()


def _module(name: str, root: Path = ROOT):
    spec = importlib.util.spec_from_file_location(f"_apply_record_data_{name}", root / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


fence = _module("check_registry_generation_fence")
admitted = _module("apply_admitted_canonical_work_projection")
projection = _module("render_task_handoff_projection")


class Refused(Exception):
    def __init__(self, code: str, predicate: str, repair: str, next_attempt: str, **evidence: Any) -> None:
        super().__init__(code)
        self.result = {"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
                       "required_evidence_or_repair": repair, "retry_entrypoint": RETRY_ENTRYPOINT,
                       "owning_existing_goal": OWNING_GOAL, "next_attempt": next_attempt,
                       "evidence": evidence, "files_changed": False}


def _schema(predicate: str, repair: str, **evidence: Any) -> Refused:
    return Refused("RECORD_DATA_SCHEMA_MISMATCH", predicate, repair, "after the data file is corrected", **evidence)


def validate_data(data: Any) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    if not isinstance(data, dict) or data.get("schema") != DATA_SCHEMA:
        raise _schema(f"data schema == {DATA_SCHEMA}", "supply a record-data file of the declared schema")
    work_items = data.get("work_items", {})
    actions = data.get("human_actions", [])
    register = data.get("register_from_record", [])
    row_fields = data.get("row_fields", [])
    if (not isinstance(work_items, dict) or not isinstance(actions, list) or not isinstance(register, list)
            or not isinstance(row_fields, list)):
        raise _schema("work_items is an object; human_actions, register_from_record and row_fields are lists",
                      "fix the container types")
    for task_id in register:
        if not isinstance(task_id, str) or not projection._SAFE_TASK_ID.match(task_id):
            raise _schema("register_from_record lists task ids", "list safe task ids", value=task_id)
    for edit in row_fields:
        path = edit.get("path") if isinstance(edit, dict) else None
        if (not isinstance(edit, dict) or not isinstance(edit.get("task_id"), str) or "before" not in edit or "after" not in edit
                or not isinstance(path, list) or not 1 <= len(path) <= 2 or not isinstance(path[0], str)
                or path[0] in PROTECTED_FIELDS or (len(path) == 2 and (isinstance(path[1], bool) or not isinstance(path[1], int)))):
            raise _schema("every row_fields edit has task_id, path ([field] or [field, index]), before and after; "
                          "task_id and identity fields are not editable", "fix the row_fields edit", edit=edit)
    clean_items: dict[str, list[dict[str, Any]]] = {}
    for task_id, items in work_items.items():
        kept, rejected = projection.project_work_items(items)
        if rejected or not isinstance(items, list) or len(kept) != len(items):
            raise _schema("every work item is well formed (kind, repo, number, state, owner_approved)",
                          "correct or remove the malformed work items", task_id=task_id, rejected=rejected)
        clean_items[task_id] = kept
    seen: set[str] = set()
    for action in actions:
        if not isinstance(action, dict) or any(not isinstance(action.get(k), str) or not action[k] for k in QUESTION_FIELDS):
            raise _schema("every human action has non-empty " + ", ".join(QUESTION_FIELDS),
                          "complete the owner question fields", action=action)
        if action["id"] in seen:
            raise _schema("human action ids are unique", "remove the duplicate id", id=action["id"])
        seen.add(action["id"])
        if action.get("task_id") is not None and not isinstance(action["task_id"], str):
            raise _schema("human action task_id is null or a task id", "fix task_id", id=action["id"])
    return clean_items, actions, register, row_fields


def _resolve_in_registry(registry: dict[str, Any], task_id: str, task_shards: Path) -> None:
    try:
        source_kind, _task, _shard = admitted.find_source(registry=registry, task_id=task_id, task_shards=task_shards)
    except SystemExit:
        raise Refused("RECORD_DATA_UNKNOWN_TASK_ID", f"{task_id} resolves exactly once in the canonical Task Registry",
                      "register the task first, or drop its rows from the data file",
                      "after the task is registered", task_id=task_id) from None
    if source_kind != "MONOLITHIC_REGISTRY":
        raise Refused("RECORD_DATA_TASK_NOT_IN_AGGREGATE_REGISTRY",
                      f"{task_id} is a row of data/canonical-task-registry.json (the only generation-bearing surface)",
                      "promote the task into the aggregate Registry, or drop its rows",
                      "after the task is in the aggregate Registry", task_id=task_id)


def _get(container: Any, path: list[Any]) -> Any:
    value = container.get(path[0], _MISSING) if isinstance(container, dict) else _MISSING
    if len(path) == 2:
        value = value[path[1]] if isinstance(value, list) and 0 <= path[1] < len(value) else _MISSING
    return value


def _set(container: dict[str, Any], path: list[Any], value: Any) -> None:
    if len(path) == 1:
        container[path[0]] = copy.deepcopy(value)
    else:
        container[path[0]][path[1]] = copy.deepcopy(value)


def _edit(target: dict[str, Any], edit: dict[str, Any], where: str) -> bool:
    """Apply one exact before -> after edit; True when it changed something."""
    current = _get(target, edit["path"])
    if current == edit["after"]:
        return False
    if current is _MISSING or current != edit["before"]:
        raise Refused("RECORD_DATA_ROW_FIELD_BEFORE_MISMATCH",
                      f"{where} {edit['task_id']}{edit['path']} == the declared before value",
                      "re-read the current value and restate the edit against it", "after the edit is restated",
                      task_id=edit["task_id"], path=edit["path"], current=None if current is _MISSING else current)
    _set(target, edit["path"], edit["after"])
    return True


def merge(registry: dict[str, Any], data: Any, task_shards: Path) -> tuple[dict[str, Any], dict[Path, dict[str, Any]]]:
    """Return the registry and the standalone records with the data applied; generation untouched."""
    work_items, actions, register, row_fields = validate_data(data)
    merged = copy.deepcopy(registry)
    records: dict[Path, dict[str, Any]] = {}
    for task_id in register:
        path = task_shards / f"{task_id}.json"
        if not path.is_file():
            raise Refused("RECORD_DATA_RECORD_ABSENT", f"{path.name} exists in the canonical task records",
                          "write the standalone canonical record first", "after the record exists", task_id=task_id)
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("task_id") != task_id:
            raise Refused("RECORD_DATA_RECORD_IDENTITY", f"{path.name} carries task_id {task_id}",
                          "correct the record identity", "after the record is corrected", task_id=task_id)
        existing = [row for row in merged.get("tasks", []) if row.get("task_id") == task_id]
        # A row this same data registered earlier also carries this data's work items for it.
        expected = dict(record, work_items=work_items[task_id]) if task_id in work_items else record
        if existing and existing[0] not in (record, expected):
            raise Refused("RECORD_DATA_ALREADY_REGISTERED", f"{task_id} is not yet a different aggregate row",
                          "edit the existing row with row_fields instead of re-registering it", "after the data is restated",
                          task_id=task_id)
        if not existing:
            merged.setdefault("tasks", []).append(copy.deepcopy(record))
    for task_id in sorted(work_items):
        _resolve_in_registry(merged, task_id, task_shards)
    for action in actions:
        if action.get("task_id") is not None:
            _resolve_in_registry(merged, action["task_id"], task_shards)
    rows = {row.get("task_id"): row for row in merged.get("tasks", [])}
    for task_id, items in work_items.items():
        rows[task_id]["work_items"] = items
    existing_actions = merged.get("human_actions")
    if not isinstance(existing_actions, list):
        raise _schema("registry human_actions is a list", "restore the Registry human_actions list")
    by_id = {a.get("id"): i for i, a in enumerate(existing_actions) if isinstance(a, dict) and a.get("id")}
    for action in actions:
        if action["id"] in by_id:
            existing_actions[by_id[action["id"]]] = action
        else:
            by_id[action["id"]] = len(existing_actions)
            existing_actions.append(action)
    for edit in row_fields:
        _resolve_in_registry(merged, edit["task_id"], task_shards)
        _edit(rows[edit["task_id"]], edit, "registry row")
        record_path = task_shards / f"{edit['task_id']}.json"
        if record_path.is_file():
            record = records.get(record_path) or json.loads(record_path.read_text(encoding="utf-8"))
            if _edit(record, edit, "standalone record") or record_path in records:
                records[record_path] = record
    return merged, records


def plan(registry: dict[str, Any], data: Any, tip_generation: int, task_shards: Path) -> dict[str, Any]:
    merged, records = merge(registry, data, task_shards)
    if merged == registry and not records:
        return {"disposition": "NO_CHANGE", "generation": registry.get("generation"), "registry": registry, "records": {}}
    current = fence.parse_generation(json.dumps(registry), "working tree")
    merged["generation"] = current + 1
    gate = fence.evaluate_pull_request(merged["generation"], tip_generation)
    if gate.get("disposition") != fence.ALLOW:
        raise Refused(gate.get("failure_code", "REGISTRY_GENERATION_FENCE"), gate.get("failed_predicate", ""),
                      gate.get("required_evidence_or_repair", ""), gate.get("next_attempt", ""),
                      head_generation=merged["generation"], tip_generation=tip_generation)
    return {"disposition": "ALLOW", "generation": merged["generation"], "tip_generation": tip_generation,
            "registry": merged, "records": records}


def render(registry: dict[str, Any]) -> str:
    return json.dumps(registry, indent=2, ensure_ascii=False) + "\n"


def verify(root: Path, registry_path: Path, validators: tuple[str, ...]) -> None:
    for validator in validators:
        done = subprocess.run([sys.executable, str(root / validator)], cwd=root, capture_output=True, text=True)
        if done.returncode != 0:
            raise Refused("RECORD_DATA_POST_APPLY_VALIDATION", f"{validator} passes on the applied Registry",
                          "fix the data so the validator passes", "after the validator passes",
                          output=(done.stdout + done.stderr).strip()[-600:])
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for task in registry.get("tasks", []):
        try:
            projection.build_projection(task, None, registry)
        except Exception as exc:  # the INDEX projection must render every task
            raise Refused("RECORD_DATA_POST_APPLY_PROJECTION", "the handoff projection renders every Registry task",
                          "fix the data so every task renders", "after every task renders",
                          task_id=task.get("task_id"), detail=f"{type(exc).__name__}: {exc}") from None


def apply(data: Any, *, registry_path: Path, task_shards: Path, tip_generation: int, write: bool,
          root: Path = ROOT, validators: tuple[str, ...] = VALIDATORS) -> dict[str, Any]:
    original = registry_path.read_text(encoding="utf-8")
    result = plan(json.loads(original), data, tip_generation, task_shards)
    report = {k: v for k, v in result.items() if k not in ("registry", "records")}
    report["records_changed"] = sorted(path.name for path in result["records"])
    if result["disposition"] == "NO_CHANGE" or not write:
        report["files_changed"] = False
        return report
    originals = {registry_path: original, **{path: path.read_text(encoding="utf-8") for path in result["records"]}}
    try:
        registry_path.write_text(render(result["registry"]), encoding="utf-8")
        for path, record in result["records"].items():
            path.write_text(render(record), encoding="utf-8")
        verify(root, registry_path, validators)
    except BaseException:
        for path, text in originals.items():
            path.write_text(text, encoding="utf-8")
        raise
    report["files_changed"] = True
    return report


def tip_generation_from(repo: Path, tip_ref: str) -> int:
    try:
        return fence.generation_at(repo, fence.rev(repo, tip_ref))
    except fence.GenerationUnreadable as exc:
        raise Refused(fence.UNREADABLE, f"live tip {tip_ref} generation is readable",
                      "fetch the live base tip (git fetch origin main), then rerun", "after the tip is fetched",
                      detail=str(exc)) from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("data", type=Path)
    parser.add_argument("--registry", type=Path, default=ROOT / "data" / "canonical-task-registry.json")
    parser.add_argument("--task-shards", type=Path, default=ROOT / "data" / "canonical-task-records")
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--tip-ref", default="origin/main", help="live base tip the new generation must sit on")
    parser.add_argument("--apply", action="store_true", help="write, validate and project; otherwise plan only")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.data.read_text(encoding="utf-8"))
        report = apply(data, registry_path=args.registry, task_shards=args.task_shards,
                       tip_generation=tip_generation_from(args.repo, args.tip_ref), write=args.apply)
    except Refused as refusal:
        print(json.dumps(refusal.result, indent=2, ensure_ascii=False))
        return 1
    except (OSError, ValueError) as exc:
        print(json.dumps(_schema("data file is readable JSON", "supply a readable data file",
                                 detail=f"{type(exc).__name__}: {exc}").result, indent=2))
        return 1
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
