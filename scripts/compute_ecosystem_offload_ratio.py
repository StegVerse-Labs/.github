#!/usr/bin/env python3
"""Ecosystem offload ratio (EOR) per lane per UTC day, from committed inputs only.

EOR is the share of a lane's work that the ecosystem's own machinery ran rather than an
LLM session: ``EOR = E / (E + L)``, where

* ``E`` is the summed wall-clock duration of the lane's completed CI runs, taken from a
  run-duration export (``stegverse.ci-run-duration-export.v1``): one entry per run with
  ``repo``, ``run_id``, ``workflow``, ``head_branch``, ``run_started_at`` and
  ``completed_at`` (UTC, ``YYYY-MM-DDTHH:MM:SSZ``);
* ``L`` is the lane's LLM session time, taken from a session-usage table (CSV with header
  ``date,lane,session_id,llm_minutes``; ``llm_minutes`` is a non-negative decimal);
* a lane map (``stegverse.lane-branch-map.v1``) assigns runs to lanes by exact
  ``repo`` and ``head_branch``;
* optionally, a lane-usage table (CSV with header
  ``date,lane,unit_id,e_minutes,l_minutes,source``) in which a lane reports both E and L
  per work unit. Its E is kept apart from CI-measured E (``E_reported_minutes``) and every
  row it touches is labelled ``LANE_REPORTED``, because a lane's own figure is not a
  measurement.

This is the RM11 method (E and L in minutes, EOR = E / (E + L)) computed from files
instead of estimated. A run is attributed to the UTC day it started. Runs without
``completed_at`` and runs on no mapped branch are reported, never counted. Arithmetic
is exact (seconds as integers, minutes as Fractions); EOR is reported as a reduced
fraction and as a percentage rounded half-even to 0.01.

Nothing is fetched: no API, network or clock is read. A missing or malformed input is a
FAIL_CLOSED refusal with the standard six fields. The result is research evidence only;
it grants no authority and claims no runtime observation.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from datetime import datetime, timezone
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
from typing import Any

RUNS_SCHEMA = "stegverse.ci-run-duration-export.v1"
LANES_SCHEMA = "stegverse.lane-branch-map.v1"
RESULT_SCHEMA = "stegverse.ecosystem-offload-ratio.v1"
SESSION_HEADER = ["date", "lane", "session_id", "llm_minutes"]
USAGE_HEADER = ["date", "lane", "unit_id", "e_minutes", "l_minutes", "source"]
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
RETRY_ENTRYPOINT = ("python scripts/compute_ecosystem_offload_ratio.py --ci-runs <export.json> "
                    "--sessions <usage.csv> --lanes <lane-map.json> [--lane-usage <lane-usage.csv>]")
TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Refused(Exception):
    def __init__(self, code: str, predicate: str, repair: str, **evidence: Any) -> None:
        super().__init__(code)
        self.result = {
            "schema": RESULT_SCHEMA,
            "disposition": "FAIL_CLOSED",
            "failure_code": code,
            "failed_predicate": predicate,
            "required_evidence_or_repair": repair,
            "retry_entrypoint": RETRY_ENTRYPOINT,
            "owning_existing_goal": OWNING_GOAL,
            "next_attempt": "after the named input is committed or corrected",
            "evidence": evidence,
        }


def _invalid(predicate: str, repair: str, **evidence: Any) -> Refused:
    return Refused("INPUT_VALUE_INVALID", predicate, repair, **evidence)


def _instant(value: Any, field: str, index: int) -> datetime:
    if not isinstance(value, str) or not TIMESTAMP.match(value):
        raise _invalid(f"runs[{index}].{field} is UTC YYYY-MM-DDTHH:MM:SSZ", "correct the run export", value=value)
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        raise _invalid(f"runs[{index}].{field} is a real instant", "correct the run export", value=value) from None


def load_lanes(lanes: Any) -> dict[tuple[str, str], str]:
    if not isinstance(lanes, dict) or lanes.get("schema") != LANES_SCHEMA or not isinstance(lanes.get("lanes"), dict):
        raise Refused("INPUT_SCHEMA", f"lane map schema == {LANES_SCHEMA} with a lanes object", "supply the lane map")
    owner: dict[tuple[str, str], str] = {}
    for lane, branches in lanes["lanes"].items():
        if not isinstance(branches, list):
            raise _invalid(f"lanes.{lane} is a list of {{repo, head_branch}}", "correct the lane map")
        for entry in branches:
            if not (isinstance(entry, dict) and isinstance(entry.get("repo"), str) and "/" in entry["repo"]
                    and isinstance(entry.get("head_branch"), str) and entry["head_branch"]):
                raise _invalid(f"lanes.{lane} entries carry repo (owner/name) and head_branch", "correct the lane map")
            key = (entry["repo"], entry["head_branch"])
            if owner.get(key, lane) != lane:
                raise Refused("RUN_LANE_AMBIGUOUS", "each repo and head_branch maps to one lane",
                              "assign the branch to exactly one lane", repo=key[0], head_branch=key[1],
                              lanes=sorted({owner[key], lane}))
            owner[key] = lane
    return owner


def load_runs(runs: Any) -> list[dict[str, Any]]:
    if not isinstance(runs, dict) or runs.get("schema") != RUNS_SCHEMA or not isinstance(runs.get("runs"), list):
        raise Refused("INPUT_SCHEMA", f"run export schema == {RUNS_SCHEMA} with a runs list", "supply the run export")
    seen: set[tuple[str, Any]] = set()
    for index, run in enumerate(runs["runs"]):
        if not (isinstance(run, dict) and isinstance(run.get("repo"), str) and isinstance(run.get("head_branch"), str)
                and isinstance(run.get("workflow"), str) and run.get("run_id") is not None):
            raise _invalid(f"runs[{index}] carries repo, run_id, workflow and head_branch", "correct the run export")
        key = (run["repo"], run["run_id"])
        if key in seen:
            raise _invalid("each repo and run_id appears once", "remove the duplicate run", repo=key[0], run_id=key[1])
        seen.add(key)
    return runs["runs"]


def load_sessions(text: str) -> list[dict[str, Any]]:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0] != SESSION_HEADER:
        raise Refused("INPUT_SCHEMA", f"session table header == {','.join(SESSION_HEADER)}", "supply the session table")
    sessions = []
    for number, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != len(SESSION_HEADER):
            raise _invalid(f"session table line {number} has {len(SESSION_HEADER)} fields", "correct the session table")
        day, lane, session_id, minutes = row
        try:
            value = Decimal(minutes)
        except InvalidOperation:
            value = Decimal(-1)
        if not DATE.match(day) or not lane or not session_id or not value.is_finite() or value < 0:
            raise _invalid(f"session table line {number} has a UTC date, lane, session_id and llm_minutes >= 0",
                           "correct the session table", line=number)
        sessions.append({"date": day, "lane": lane, "session_id": session_id, "llm_minutes": Fraction(value)})
    return sessions


def _decimal_minutes(value: str) -> Fraction | None:
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None
    return Fraction(number) if number.is_finite() and number >= 0 else None


def load_usage(text: str) -> list[dict[str, Any]]:
    rows = list(csv.reader(io.StringIO(text)))
    if not rows or rows[0] != USAGE_HEADER:
        raise Refused("INPUT_SCHEMA", f"lane-usage table header == {','.join(USAGE_HEADER)}", "supply the lane-usage table")
    usage, seen = [], set()
    for number, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != len(USAGE_HEADER):
            raise _invalid(f"lane-usage line {number} has {len(USAGE_HEADER)} fields", "correct the lane-usage table")
        day, lane, unit_id, e_text, l_text, source = row
        e, l_ = _decimal_minutes(e_text), _decimal_minutes(l_text)
        if not DATE.match(day) or not lane or not unit_id or not source or e is None or l_ is None:
            raise _invalid(f"lane-usage line {number} has a UTC date, lane, unit_id, e_minutes and l_minutes >= 0 "
                           "and a source", "correct the lane-usage table", line=number)
        if (lane, unit_id) in seen:
            raise _invalid("each lane and unit_id appears once", "remove the duplicate unit", lane=lane, unit_id=unit_id)
        seen.add((lane, unit_id))
        usage.append({"date": day, "lane": lane, "unit_id": unit_id, "e": e, "l": l_})
    return usage


def _minutes(value: Fraction) -> str:
    return str((Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal("0.01"), ROUND_HALF_EVEN))


def compute(runs_doc: Any, sessions_text: str, lanes_doc: Any, usage_text: str | None = None) -> dict[str, Any]:
    owner = load_lanes(lanes_doc)
    runs = load_runs(runs_doc)
    sessions = load_sessions(sessions_text)
    usage = load_usage(usage_text) if usage_text is not None else []
    e_seconds: dict[tuple[str, str], int] = {}
    run_ids: dict[tuple[str, str], list[str]] = {}
    unattributed, incomplete = [], []
    for index, run in enumerate(runs):
        ref = f"{run['repo']}#{run['run_id']}"
        if run.get("completed_at") is None:
            incomplete.append(ref)
            continue
        started = _instant(run.get("run_started_at"), "run_started_at", index)
        completed = _instant(run["completed_at"], "completed_at", index)
        if completed < started:
            raise _invalid(f"runs[{index}].completed_at >= run_started_at", "correct the run export", run=ref)
        lane = owner.get((run["repo"], run["head_branch"]))
        if lane is None:
            unattributed.append(ref)
            continue
        key = (lane, started.strftime("%Y-%m-%d"))
        e_seconds[key] = e_seconds.get(key, 0) + int((completed - started).total_seconds())
        run_ids.setdefault(key, []).append(ref)
    l_minutes: dict[tuple[str, str], Fraction] = {}
    for session in sessions:
        key = (session["lane"], session["date"])
        l_minutes[key] = l_minutes.get(key, Fraction(0)) + session["llm_minutes"]
    e_reported: dict[tuple[str, str], Fraction] = {}
    l_reported: dict[tuple[str, str], Fraction] = {}
    units: dict[tuple[str, str], list[str]] = {}
    for unit in usage:
        key = (unit["lane"], unit["date"])
        e_reported[key] = e_reported.get(key, Fraction(0)) + unit["e"]
        l_reported[key] = l_reported.get(key, Fraction(0)) + unit["l"]
        units.setdefault(key, []).append(unit["unit_id"])
    rows = []
    for lane, day in sorted(set(e_seconds) | set(l_minutes) | set(e_reported)):
        key = (lane, day)
        e_ci = Fraction(e_seconds.get(key, 0), 60)
        e = e_ci + e_reported.get(key, Fraction(0))
        l_ = l_minutes.get(key, Fraction(0)) + l_reported.get(key, Fraction(0))
        if key in e_reported:
            measurement = "LANE_REPORTED"
        elif key in l_minutes:
            measurement = "E_AND_L_FROM_FILES"
        else:
            measurement = "L_NOT_SUPPLIED_FOR_LANE_DAY"
        total = e + l_
        eor = e / total if total else None
        rows.append({
            "lane": lane, "date": day,
            "E_seconds": e_seconds.get(key, 0), "E_ci_minutes": _minutes(e_ci),
            "E_reported_minutes": _minutes(e_reported.get(key, Fraction(0))),
            "E_minutes": _minutes(e), "L_minutes": _minutes(l_),
            "EOR": None if eor is None else f"{eor.numerator}/{eor.denominator}",
            "EOR_percent": None if eor is None else _minutes(eor * 100),
            "runs": sorted(run_ids.get(key, [])), "units": sorted(units.get(key, [])),
            "measurement": measurement,
        })
    return {"schema": RESULT_SCHEMA, "disposition": "COMPUTED", "rows": rows,
            "unattributed_runs": sorted(unattributed), "incomplete_runs": sorted(incomplete),
            "authority": {"benchmark_completion_granted": False, "runtime_observation_claimed": False}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ci-runs", type=Path)
    parser.add_argument("--sessions", type=Path)
    parser.add_argument("--lanes", type=Path)
    parser.add_argument("--lane-usage", type=Path)
    args = parser.parse_args(argv)
    try:
        for name in ("ci_runs", "sessions", "lanes"):
            if getattr(args, name) is None and not (name == "sessions" and args.lane_usage is not None):
                flag = "--" + name.replace("_", "-")
                raise Refused("INPUT_NOT_SUPPLIED", f"{flag} names a committed input file", f"supply {flag}", input=flag)
        try:
            result = compute(json.loads(args.ci_runs.read_text(encoding="utf-8")),
                             args.sessions.read_text(encoding="utf-8") if args.sessions else ",".join(SESSION_HEADER) + "\n",
                             json.loads(args.lanes.read_text(encoding="utf-8")),
                             args.lane_usage.read_text(encoding="utf-8") if args.lane_usage else None)
        except (OSError, ValueError) as exc:
            raise Refused("INPUT_UNREADABLE", "every input file is readable UTF-8 (JSON where declared)",
                          "supply readable files", detail=f"{type(exc).__name__}: {exc}") from None
    except Refused as refusal:
        print(json.dumps(refusal.result, indent=2, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
