#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "control" / "archive-readiness.json"
REGISTRY = ROOT / "control" / "worker-registry.json"

TERMINAL = {"COMPLETED", "COMPLETE", "CLOSED", "CANCELLED", "SUPERSEDED"}
PROGRESSING = "PROGRESSING"


def load(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    gate = load(GATE)
    registry = load(REGISTRY)
    tasks = {t["task_id"]: t for t in registry.get("tasks", [])}
    errors = []

    unfinished = gate.get("unfinished_production_tasks", [])
    progressing = 0
    for entry in unfinished:
        task_id = entry["task_id"]
        task = tasks.get(task_id)
        if task is None:
            errors.append(f"missing-registry-task:{task_id}")
            continue
        if task.get("state") in TERMINAL:
            continue
        if entry.get("progress_class") == PROGRESSING:
            progressing += 1

    all_terminal = all(
        (tasks.get(e["task_id"]) or {}).get("state") in TERMINAL
        for e in unfinished
    ) if unfinished else True

    claimed_archive_ready = bool(gate.get("thread_archive_ready"))
    if claimed_archive_ready and not (all_terminal or progressing == len(unfinished)):
        errors.append("premature-archive-ready")

    if unfinished and progressing == 0 and claimed_archive_ready:
        errors.append("archive-ready-with-zero-progressing-workers")

    for entry in unfinished:
        if entry.get("progress_class") == "MONITORING_BLOCKED" and claimed_archive_ready:
            errors.append(f"archive-ready-with-monitoring-blocked:{entry['task_id']}")

    summary = gate.get("summary", {})
    if summary.get("progressing") != progressing:
        errors.append("progressing-summary-mismatch")

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        raise SystemExit(1)

    print(json.dumps({
        "ok": True,
        "thread_archive_ready": claimed_archive_ready,
        "unfinished_count": len(unfinished),
        "progressing_count": progressing,
        "all_terminal": all_terminal
    }, indent=2))


if __name__ == "__main__":
    main()
