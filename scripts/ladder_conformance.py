#!/usr/bin/env python3
"""Ladder-conformance artifact for the priority goals (StegVerse-org/.github#163).

  observe   run the observation plan against local checkouts at the exact pinned commits and write
            data/sv-work-items/ladder-conformance/observations/<goal>.observations.json (+ raw/<run>.out).
            Needs the checkouts (and gh for PR-state rows); never run in CI. Refuses a checkout at another commit.
  generate  evaluate declarations + observations + scoped tasks with resident-runtime/ladder_conformance.py and write
            conformance/<goal>.conformance.json with its receipt (sha256 of every input and of the document).
  check     regenerate in memory and require the committed conformance files to be byte-identical and internally
            consistent (exit 0), else print the six-field refusal (exit 1). E0: stdlib, no clock, no network.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("ladder_conformance", ROOT / "resident-runtime/ladder_conformance.py")
lc = sys.modules.get("ladder_conformance") or importlib.util.module_from_spec(_s)
if "ladder_conformance" not in sys.modules:
    sys.modules["ladder_conformance"] = lc
    _s.loader.exec_module(lc)

BASE = lc.BASE
PLAN = BASE / "observation-plan.json"
GOAL_FILES = {g: g + ".json" for g in lc.GOALS}
RECEIPT_INPUTS = ("resident-runtime/ladder_conformance.py", "resident-runtime/sv_operating_modes.py",
                  "scripts/ladder_conformance.py")


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def dump(v: Any) -> str:
    return json.dumps(v, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


def load_inputs(base: Path = BASE) -> dict[str, Any]:
    out: dict[str, Any] = {"declarations": {}, "observations": {}, "tasks": [], "files": {}}
    for g, f in GOAL_FILES.items():
        for kind, name in (("declarations", f), ("observations", g + ".observations.json")):
            p = base / kind / name
            raw = p.read_bytes()
            out[kind][g] = json.loads(raw)
            out["files"][rel(p) if p.is_relative_to(ROOT) else str(p)] = lc.sha256_uri(raw)
    plan = base / "observation-plan.json"
    out["files"][rel(plan) if plan.is_relative_to(ROOT) else str(plan)] = lc.sha256_uri(plan.read_bytes())
    for p in sorted((base / "scoped-tasks").glob("*.json")):
        raw = p.read_bytes()
        out["tasks"].append(json.loads(raw))
        out["files"][rel(p) if p.is_relative_to(ROOT) else str(p)] = lc.sha256_uri(raw)
    return out


def build(base: Path = BASE) -> dict[str, str]:
    """goal -> conformance document text (deterministic)."""
    inp = load_inputs(base)
    code = {p: lc.sha256_uri((ROOT / p).read_bytes()) for p in RECEIPT_INPUTS}
    texts = {}
    for g in lc.GOALS:
        doc = lc.evaluate(inp["declarations"][g], inp["observations"][g], inp["tasks"])
        obs = inp["observations"][g]
        doc["inspected"] = {"roots": obs.get("roots"), "sources": obs.get("sources")}
        mine = {k: v for k, v in inp["files"].items()
                if ("/scoped-tasks/" in k and any(t.get("goal") == g and k.endswith(t["task_id"] + ".json") for t in inp["tasks"]))
                or k.endswith("/" + GOAL_FILES[g]) or k.endswith("/" + g + ".observations.json")
                or k.endswith("/observation-plan.json")}
        body = lc.canonical(doc)
        doc["receipt"] = {"schema": "stegverse.ladder-conformance-receipt/v1", "inputs": dict(sorted(mine.items())),
                          "code": code, "document_sha256": lc.sha256_uri(body),
                          "standard": "StegVerse-Labs/.github#3308 resident-runtime/sv_operating_modes.py (branch head "
                                      "5e7fc7238cf698b78dc5938f21e75133a9961d53, this branch's base)",
                          "evidence_class": "SOURCE_OBSERVED_CONFORMANCE_RECORD",
                          "runtime_completion": False,
                          "note": "not a ledger receipt: runtime counts only when a manifest-directed transition appends a "
                                  "receipt to refs/stegverse/organization-ledger"}
        texts[g] = dump(doc)
    return texts


def cmd_generate(_: argparse.Namespace) -> int:
    for g, text in build().items():
        (BASE / "conformance" / (g + ".conformance.json")).write_text(text)
        d = json.loads(text)
        print(g, d["verdict"], "gaps", d["gaps"], "consistency", d["consistency"])
    return 0


def check(base: Path = BASE) -> dict[str, Any]:
    texts = build(base)
    for g in lc.GOALS:  # every observed run's raw output is committed and matches its recorded hash
        obs = json.loads((base / "observations" / (g + ".observations.json")).read_bytes())
        for r in obs.get("runs", []):
            if "raw_sha256" not in r:
                continue
            p = base / "observations" / "raw" / (r["run_id"] + ".out")
            if not p.is_file() or lc.sha256_uri(p.read_bytes()) != r["raw_sha256"]:
                return lc.refusal("FAIL_CLOSED", "OPERATING_MODE_E0_WITNESS_UNBOUND", "OBSERVED_RUN_OUTPUT_COMMITTED",
                                  "re-run python scripts/ladder_conformance.py observe and commit raw/ with the observations",
                                  lc.CHECK_GOAL, "on the next observe run", goal=g, run_id=r["run_id"])
    for g, text in texts.items():
        p = base / "conformance" / (g + ".conformance.json")
        if not p.is_file() or p.read_text() != text:
            return lc.refusal("FAIL_CLOSED", "LADDER_ARTIFACT_STALE", "COMMITTED_ARTIFACT_REGENERATES_BYTE_IDENTICAL",
                              "run python scripts/ladder_conformance.py generate and commit the result", lc.CHECK_GOAL,
                              "on the next push", goal=g)
        d = json.loads(text)
        if d.get("consistency") != "ALLOW":
            first = d["consistency_refusals"][0]
            return dict(first, goal=g)
    return {"disposition": "ALLOW", "mode": "E0", "goals": {g: json.loads(t)["verdict"] for g, t in texts.items()}}


def cmd_check(_: argparse.Namespace) -> int:
    out = check()
    print(dump(out), end="")
    return 0 if out["disposition"] == "ALLOW" else 1


# ---------------------------------------------------------------- observe (local only) --------------------------
def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True).stdout.strip()


def _blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def _six(d: dict[str, Any]) -> dict[str, Any]:
    return {k: d.get(k) for k in ("disposition",) + lc.om.SIX[1:] if k in d}


def _parse(kind: str, run: dict[str, Any], rc: int, out: str, err: str) -> list[dict[str, Any]]:
    if kind == "finish-point":
        d = json.loads(out)
        rows = [dict(_six(p), subject=p["predicate"]) for p in d["predicates"]]
        verdict = dict(_six(d), subject="FINISH_POINT_VERDICT")
        unmet = [r for r in rows if r.get("disposition") != "ALLOW"]
        if d.get("disposition") != "ALLOW" and unmet and all(all(r.get(k) for k in lc.om.SIX) for r in unmet):
            # the verdict's six fields are carried per unmet predicate; the first one is the verdict's
            verdict.update({k: unmet[0][k] for k in lc.om.SIX}, six_fields_source="unmet_predicates[0]",
                           unmet=[r["subject"] for r in unmet])
        return rows + [verdict]
    if kind == "disposition":
        d = json.loads(out if out.strip() else err)  # a non-ALLOW plan is printed on stderr
        return [dict(_six(d), subject=run.get("subject"))]
    if kind == "rows":  # a probe printing {"rows": [{subject, disposition, ...}, ...]}
        return [dict(r) for r in json.loads(out)["rows"]]
    if kind == "unittest":
        text = err + out
        m = re.search(r"^Ran (\d+) tests?", text, re.M)
        skipped = re.search(r"skipped=(\d+)", text)
        ok = rc == 0 and re.search(r"^OK\b", text, re.M) is not None
        res = {"tests_ran": int(m.group(1)) if m else 0, "skipped": int(skipped.group(1)) if skipped else 0,
               "passed": ok}
        good = ok and res["skipped"] == 0 and res["tests_ran"] > 0
        row = {"subject": run.get("subject"), "disposition": "ALLOW" if good else "FAIL_CLOSED", **res}
        if not good:
            row.update(run["on_fail"])
        return [row]
    raise ValueError(kind)


def cmd_observe(a: argparse.Namespace) -> int:
    plan = json.loads(PLAN.read_text())
    roots = dict(x.split("=", 1) for x in a.root)
    for g, gp in plan["goals"].items():
        if a.goal and g != a.goal:
            continue
        rt: dict[str, Any] = {}
        for key, spec in gp["roots"].items():
            path = Path(roots[key]).resolve()
            if spec["kind"] == "git":
                head = _git(path, "rev-parse", "HEAD")
                if head != spec["commit"]:
                    raise SystemExit("root %s is at %s, not %s" % (key, head, spec["commit"]))
            rt[key] = (path, spec)
        sources = []
        for s in gp["sources"]:
            path, spec = rt[s["root"]]
            raw = (path / s["path"]).read_bytes()
            if spec["kind"] == "files" and _blob(raw) != s["git_blob"]:
                raise SystemExit("%s:%s blob %s != %s" % (s["root"], s["path"], _blob(raw), s["git_blob"]))
            sources.append({"root": s["root"], "repo": spec["repo"], "commit": spec["commit"], "path": s["path"],
                            "sha256": lc.sha256_uri(raw), "git_blob": _blob(raw)})
        runs = []
        rawdir = BASE / "observations" / "raw"
        rawdir.mkdir(parents=True, exist_ok=True)
        for r in gp["runs"]:
            row: dict[str, Any] = {"run_id": r["run_id"], "what": r["what"]}
            if r["kind"] == "gh_pr":
                d = json.loads(subprocess.run(["gh", "pr", "view", str(r["number"]), "-R", r["repo"], "--json",
                                               "state,isDraft,headRefOid,baseRefName"], check=True, capture_output=True,
                                              text=True).stdout)
                row.update(status="OBSERVED", pin=None, pr=r["repo"] + "#" + str(r["number"]), **d)
                runs.append(row)
                continue
            path, spec = rt[r["root"]]
            row["pin"] = spec["repo"] + "@" + spec["commit"]
            if r["kind"] == "grep":
                files = _git(path, "ls-files").splitlines() if spec["kind"] == "git" else \
                    [s["path"] for s in gp["sources"] if s["root"] == r["root"]]
                files = [f for f in files if any(fnmatch.fnmatch(f, gl) for gl in r["globs"])
                         and not any(fnmatch.fnmatch(f, ex) for ex in r.get("exclude", []))]
                hits = []
                for pat in r["patterns"]:
                    rx = re.compile(pat)
                    for f in files:
                        try:
                            lines = (path / f).read_text(errors="replace").splitlines()
                        except (IsADirectoryError, FileNotFoundError):
                            continue
                        hits += [{"pattern": pat, "path": f, "line": i + 1, "text": ln.strip()[:200]}
                                 for i, ln in enumerate(lines) if rx.search(ln)]
                row.update(status="OBSERVED", files_scanned=len(files), patterns=r["patterns"], hits=hits)
                runs.append(row)
                continue
            argv = [sys.executable if x == "{python}" else re.sub(r"\{root:(\w+)\}", lambda m: str(rt[m.group(1)][0]), x)
                    for x in r["argv"]]
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0")
            p = subprocess.run(argv, cwd=path, capture_output=True, text=True, env=env, timeout=600)
            out, err = p.stdout, p.stderr
            for key, (rp, _) in rt.items():
                out, err = out.replace(str(rp), "{root:%s}" % key), err.replace(str(rp), "{root:%s}" % key)
            out = re.sub(r"in \d+\.\d+s", "in <t>s", out)
            err = re.sub(r"in \d+\.\d+s", "in <t>s", err)
            text = "$ " + " ".join(r["argv"]) + "\n--- exit %d\n--- stdout\n%s--- stderr\n%s" % (p.returncode, out, err)
            (rawdir / (r["run_id"] + ".out")).write_text(text)
            try:
                outcomes = _parse(r["parse"], r, p.returncode, out, err)
                status = "OBSERVED"
            except Exception as exc:  # noqa: BLE001 - an unparsable run is recorded, never guessed
                outcomes, status = [], "UNPARSABLE:" + type(exc).__name__
            row.update(status=status, command=" ".join(r["argv"]), exit_code=p.returncode,
                       raw="data/sv-work-items/ladder-conformance/observations/raw/" + r["run_id"] + ".out",
                       raw_sha256=lc.sha256_uri(text.encode()), outcomes=outcomes)
            runs.append(row)
        doc = {"schema": lc.OBS_SCHEMA, "task_id": g, "observed_by": "scripts/ladder_conformance.py observe",
               "mode": "E0", "roots": {k: {"repo": s["repo"], "commit": s["commit"], "kind": s["kind"]}
                                       for k, (_, s) in rt.items()},
               "sources": sources, "runs": runs}
        (BASE / "observations" / (g + ".observations.json")).write_text(dump(doc))
        print(g, len(sources), "sources", len(runs), "runs")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="scripts/ladder_conformance.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("observe")
    o.add_argument("--root", action="append", default=[], help="key=path of a checkout named in the plan")
    o.add_argument("--goal")
    sub.add_parser("generate")
    sub.add_parser("check")
    a = ap.parse_args(argv)
    return {"observe": cmd_observe, "generate": cmd_generate, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
