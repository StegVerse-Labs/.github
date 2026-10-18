#!/usr/bin/env python3
"""Lane D NWI-S0 migration fixtures, built with P1's in-repo record rules (p1/sv-native-work-items @725d0f65).

Inputs, all frozen in data/sv-work-items/migration/lane-d/:
  sources/LANE_D_S14_S26.md       Lane D lane file sections 14-26 (Drive 1EmaRyhHeR5afyrMWIaz3Qt8xhz4hSjal)
  inputs/github-pr-snapshot.json  one GitHub read of the open Lane D PRs (heads, files, blob digests, CI)

Lane D owns only the extraction of six-field rows from its lane file. Everything else comes from P1's modules,
unmodified: surfaces from resident-runtime/sv_migration.py resolve_surface with the pinned
data/sv-work-items/surface-aliases.json; ids, digests, sealing, restatement merging, change finishing and the
work-items record from sv_work_items / sv_migration. Every record is MIGRATED_HISTORICAL. Deterministic: stdlib,
no clock, no network. `--check` exits 1 if the committed outputs differ from a fresh derivation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


wi = _load("sv_work_items", "resident-runtime/sv_work_items.py")
mg = _load("sv_migration", "resident-runtime/sv_migration.py")

FIX = ROOT / "data/sv-work-items/migration/lane-d"
SRC = FIX / "sources/LANE_D_S14_S26.md"
SNAP = FIX / "inputs/github-pr-snapshot.json"
UNKNOWN = wi.UNKNOWN
SESSION = 'Lane D "KV and WorkSpace" Grok bot, agent b699e0c0-3b4e-4a24-945f-6f521c282268'
LANE_FILE = "drive:1EmaRyhHeR5afyrMWIaz3Qt8xhz4hSjal"
KV_GOAL = "STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001"
REQUIRED_CHECKS_REF = {"file": "data/sv-work-items/required-checks.json", "blob_sha": "473862673e0327c4907d5c83c51c89fd30c77f3a",
                       "row_id": "SV-CHANGE-REQUIRED-CHECKS-001"}
SIX = wi.SIX_FIELDS
GOAL_ID = re.compile(r"\b([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+-\d{3})\b")


def surface_for(retry_entrypoint: str, class_cell: str | None):
    """P1 resolve_surface on retry_entrypoint (pinned alias table, prefix rules, no repo_paths). For a section 16
    table row whose entrypoint stays UNKNOWN, the same resolver runs on the row's Class column (the table-column
    rule that the alias table's bare_names entry cites). Nothing else is resolved."""
    s = mg.resolve_surface(retry_entrypoint)
    if s == UNKNOWN and class_cell:
        s = mg.resolve_surface(class_cell)
    return s


def _clean(v: str) -> str:
    v = v.strip()
    return v.replace("`", "").strip()


def _section_of(lines: list[str], idx: int) -> str:
    for j in range(idx, -1, -1):
        m = re.match(r"^## (\d+)\.", lines[j])
        if m:
            return "§" + m.group(1)
    return UNKNOWN


def _goal(text: str) -> str:
    m = GOAL_ID.search(text or "")
    return m.group(1) if m else UNKNOWN


# ---------------------------------------------------------------- extraction
def table_six(lines):
    """§14 table: | Item | failure_code | ... | next_attempt |, with 'same' meaning the previous row's value."""
    out, prev, on = [], None, False
    for i, line in enumerate(lines):
        if line.startswith("| Item | failure_code | failed_predicate |"):
            on = True
            continue
        if on and line.startswith("|---"):
            continue
        if on and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            item, vals = cells[0], cells[1:8]
            res = []
            for k, v in enumerate(vals):
                if prev and v.startswith("same"):
                    v = prev[k] + v[4:]
                res.append(v)
            prev = res
            six = dict(zip(SIX, (_clean(x) for x in res)))
            disp = "DENY" if "(DENY)" in six["failure_code"] else "FAIL_CLOSED"
            six["failure_code"] = six["failure_code"].split()[0]
            cls = "B" if six["required_evidence_or_repair"].startswith("B:") else ("A" if "r10: A" in six["required_evidence_or_repair"] else UNKNOWN)
            out.append({"line": i + 1, "item": item, "disposition": disp, "six": six, "resolution_class": cls, "form": "S14_TABLE"})
            continue
        if on:
            break
    return out


def abcd_table(lines):
    """§16 A/B/C/D table rows written as 'fc X / fp Y / rep ... / re ... / goal ... / next ...'."""
    out = []
    for i, line in enumerate(lines):
        if not line.startswith("|") or " fc " not in line or " / fp " not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        item, klass, text = cells[0], cells[1], cells[3]
        m = re.search(r"\b(FAIL_CLOSED|DENY)\b.*?\bfc (.+?) / fp (.+?) / rep (.+?) / re (.+?) / goal (.+?) / next (.+?)\s*$", text)
        if not m:
            continue
        goal = m.group(6).strip()
        goal = KV_GOAL if goal == "KV" else goal  # table legend: KV = STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001
        fp = m.group(3).strip()
        six = {"failure_code": _clean(m.group(2)), "failed_predicate": _clean(fp), "required_evidence_or_repair": _clean(m.group(4)),
               "retry_entrypoint": _clean(m.group(5)), "owning_existing_goal": _clean(goal), "next_attempt": _clean(m.group(7))}
        kc = re.match(r"^\*\*([ABCD])\*\*", klass) or re.match(r"^\*\*B, built", klass)
        cls = (kc.group(1) if kc and kc.groups() else "B") if kc else UNKNOWN
        out.append({"line": i + 1, "item": item, "disposition": m.group(1), "six": six, "resolution_class": cls, "form": "S16_ABCD_TABLE",
                    "class_cell": klass})
    # 'fp as above' / 're as above' refer to the previous row
    for a, b in zip(out, out[1:]):
        for k in SIX:
            if b["six"][k] == "as above":
                b["six"][k] = a["six"][k]
    return out


FIELD = re.compile(r"^(\s*)- (?:\*\*)?(failure_code / failed_predicate|failure_code/failed_predicate|failure_code|failed_predicate|"
                   r"required_evidence_or_repair|retry_entrypoint|owning_existing_goal|next_attempt):(?:\*\*)?\s*(.*)$")


def bullet_six(lines):
    out, cur, last, start, indent = [], {}, None, 0, ""

    def flush():
        if cur and all(cur.get(f) for f in SIX):
            out.append({"line": start + 1, "item": None, "disposition": "FAIL_CLOSED",
                        "six": {k: _clean(cur[k]) for k in SIX}, "resolution_class": UNKNOWN, "form": "BULLETS"})

    for i, line in enumerate(lines):
        m = FIELD.match(line)
        if m:
            ind, k, v = m.group(1), m.group(2), m.group(3).strip()
            if k.startswith("failure_code"):
                flush()
                cur, start, indent = {}, i, ind
                if "/" in k:
                    parts = [p.strip() for p in v.split(" / ")]
                    cur["failure_code"] = _clean(parts[0])
                    cur["failed_predicate"] = _clean(parts[1] if len(parts) > 1 else parts[0])
                else:
                    cur["failure_code"] = _clean(v).split()[0] if v else ""
                last = "failed_predicate" if "/" in k else "failure_code"
            elif cur:
                cur[k] = v
                last = k
            continue
        cont = re.match(r"^(\s+)- (.*)$", line)
        if cur and last and cont and len(cont.group(1)) > len(indent):
            cur[last] = (cur[last] + "; " if cur[last] else "") + cont.group(2).strip()
            continue
        if cur:
            flush()
            cur, last = {}, None
    flush()
    return out


def foreign_writer(lines):
    """#3245 BRANCH_WRITER_IS_BRANCH_OWNER (lane file §23-25 PR table; predicate and code from INDEX MERGE AUTHORITY)."""
    for i, line in enumerate(lines):
        if line.startswith("| #3245 |") and "BRANCH_WRITER_IS_BRANCH_OWNER" in line:
            six = {"failure_code": "BRANCH_HAS_FOREIGN_WRITER", "failed_predicate": "BRANCH_WRITER_IS_BRANCH_OWNER",
                   "required_evidence_or_repair": "a superseding laned/ draft by the branch owner that carries the foreign commits dd317bd3, 8e08e467, 88a2067a openly",
                   "retry_entrypoint": "superseding laned/ draft for StegVerse-Labs/.github#3245",
                   "owning_existing_goal": UNKNOWN, "next_attempt": "once StegVerse-Labs/.github#3253 is on main"}
            return [{"line": i + 1, "item": "#3245 branch writers", "disposition": "FAIL_CLOSED", "six": six,
                     "resolution_class": UNKNOWN, "form": "S2X_PR_TABLE_PLUS_INDEX_MERGE_AUTHORITY"}]
    return []


def foreign_line(text: str) -> int:
    return next(i + 1 for i, l in enumerate(text.splitlines()) if l.startswith("| #3245 |") and "BRANCH_WRITER_IS_BRANCH_OWNER" in l)


def issues(text: str, raw: bytes, base: dict) -> list[dict]:
    lines = text.splitlines()
    # §26.4 (S0_RECORD_FORMAT_NOT_PUBLISHED) is left out: the lane file records no failed_predicate for it, and the
    # predicate is an identity input that may not be UNKNOWN. See FIXTURE_MANIFEST.json#excluded_records.
    found = sorted(table_six(lines) + abcd_table(lines) + bullet_six(lines) + foreign_writer(lines), key=lambda r: r["line"])
    ev = {"kind": "MIGRATION_EVIDENCE", "evidence_path": str(SRC.relative_to(ROOT)), "evidence_sha256": wi.sha(raw)}
    finished, lines_by_id = [], {}
    for f in found:
        six = f["six"]
        body = {"schema": wi.ISSUE_SCHEMA,
                "disposition": {"disposition": f["disposition"], **six},
                "violated_invariant": {"rule_id": six["failed_predicate"], "file": LANE_FILE + "#" + _section_of(lines, f["line"] - 1),
                                       "blob_sha": None, "invariant_declared": False},
                "surface": surface_for(six["retry_entrypoint"], f.get("class_cell")),
                "source_receipt": dict(ev), "resolution_class": f["resolution_class"], "lifecycle_state": "OPENED",
                "observed_base": dict(base), "migration_provenance": mg.provenance(base),
                "owning_goal": _goal(six["owning_existing_goal"]), "opened_by_session": SESSION, "hb_epoch": UNKNOWN,
                "projection": {"lane_file_section": _section_of(lines, f["line"] - 1), "source_line": f["line"],
                               "source_form": f["form"], "item": f["item"]}}
        rec = mg.finish_issue(body)
        lines_by_id.setdefault(rec["issue_id"], []).append(f["line"])
        finished.append(rec)
    merged, _ = mg.merge_issues(finished)
    # The source lines of merged restatements live in the projection (a non-authority view), then the record is resealed.
    out = []
    for r in merged:
        r = {k: v for k, v in r.items() if k != "issue_sha256"}
        r["projection"] = {**r["projection"], "restatement_source_lines": lines_by_id[r["issue_id"]][1:]}
        out.append(wi.seal(r, "issue_sha256"))
    return sorted(out, key=lambda r: r["issue_id"])


def build():
    raw = SRC.read_bytes()
    text = raw.decode("utf-8")
    snap = json.loads(SNAP.read_text())
    base_main = {"registry_generation": snap["registry_generation_observed"]["value"],
                 "ledger_head": snap["organization_ledger_head_observed"]["value"], "tree_sha": snap["main_tree_sha"]}
    out_issues = issues(text, raw, base_main)
    out_changes = []
    for p in snap["prs"]:
        n = p["pr"]
        ref = re.compile(r"#%d(?!\d)" % n)
        res = [i for i in out_issues if any(ref.search(i["disposition"][k]) for k in ("required_evidence_or_repair", "retry_entrypoint"))
               and i["disposition"]["failed_predicate"] != "BRANCH_WRITER_IS_BRANCH_OWNER"]
        goals = sorted({i["owning_goal"] for i in res} - {UNKNOWN})
        base_ref = {"registry_generation": base_main["registry_generation"], "ledger_head": base_main["ledger_head"],
                    "tree_sha": p["base_tree_sha"]}
        # Branch writers evidence is UNKNOWN (JDQ Q-WRITER-IDENTITY): session null, evidence_class UNKNOWN.
        content = [{"path": f["path"], "blob_digest": f["blob_digest"], "writer_session": {"session": None, "evidence_class": UNKNOWN}}
                   for f in p["files"]]
        foreign = n == 3245
        body = {"schema": wi.CHANGE_SCHEMA, "target_repository": p["repo"], "resolves": sorted(i["issue_id"] for i in res),
                "owning_goal": goals[0] if len(goals) == 1 else UNKNOWN, "declared_session": p["declared_authoring_session"],
                "base_ref": base_ref, "content": content, "lifecycle_state": "FAIL_CLOSED" if foreign else "PROPOSED",
                "validation_receipts": [], "required_checks_ref": dict(REQUIRED_CHECKS_REF), "signoffs": [], "supersedes": None,
                "admission_order_slot": None, "governance_decision_ref": None, "hb_epoch": UNKNOWN,
                "migration_provenance": mg.provenance(base_ref),
                "projection": {"repo": p["repo"], "pr": n, "head_sha": p["head_sha"], "head_ref": p["head_ref"],
                               "base_ref": p["base_ref"], "base_sha": p["base_sha"], "github_state": "DRAFT" if p["is_draft"] else p["state"],
                               "github_ci": {"counts": p["ci_counts"], "authority": "PROJECTION_ONLY_NOT_A_VALIDATION_RECEIPT"},
                               "branch_writers_evidence": UNKNOWN + " (JDQ Q-WRITER-IDENTITY)",
                               "branch_writer_is_branch_owner": "FAIL" if foreign else UNKNOWN}}
        if foreign:
            # The observed artifact is the lane-file record of the foreign commits (frozen excerpt, line cited), bound
            # to the current head.change_digest. OBSERVED_ARTIFACT is cited evidence only and never counts toward VERIFIED.
            body["validation_receipts"] = [{"check_id": "BRANCH_WRITER_IS_BRANCH_OWNER", "disposition": "FAIL_CLOSED",
                                            "change_digest": wi.change_digest(body), "evidence_class": "OBSERVED_ARTIFACT",
                                            "ref": "%s#L%d" % (SRC.relative_to(ROOT), foreign_line(text)), "digest": wi.sha(raw)}]
        out_changes.append(mg.finish_change(body))
    record = wi.work_items_record(out_issues + out_changes)
    return out_issues, out_changes, record


def _jsonl(rows):
    return "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows)


def outputs():
    i, c, w = build()
    return {FIX / "sv-issues.jsonl": _jsonl(i), FIX / "sv-changes.jsonl": _jsonl(c),
            FIX / "work-items.json": json.dumps(w, indent=2, sort_keys=True, ensure_ascii=False) + "\n"}


def main(argv=None) -> int:
    a = argparse.ArgumentParser()
    a.add_argument("--check", action="store_true")
    args = a.parse_args(argv)
    out = outputs()
    stale = [str(p.relative_to(ROOT)) for p, t in out.items() if not p.exists() or p.read_text() != t]
    if args.check:
        print(json.dumps({"disposition": "ALLOW" if not stale else "FAIL_CLOSED", "stale": stale}, sort_keys=True))
        return 1 if stale else 0
    for p, t in out.items():
        p.write_text(t)
    print(json.dumps({"written": sorted(str(p.relative_to(ROOT)) for p in out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
