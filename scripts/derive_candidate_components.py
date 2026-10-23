#!/usr/bin/env python3
"""Derive a Goal's targets.components from observed evidence only, as a registry record-data repair DRAFT.

STEGVERSE-CANONICAL-WORK-COORDINATION-001. The adjacency-ruling verifier (scripts/adjacency_ruling.py) refuses a
candidate whose observed record declares no targets.components (ADJACENCY_RULING_CANDIDATE_COMPONENTS_UNDECLARED),
because conditions (a) and (b) would otherwise hold vacuously. This entrypoint is the repair input for that
refusal. It never assumes disjointness and never invents a component: every component is the normalized file stem
of an implementation surface (code or config, never tests, docs, task files or receipts) that was actually read
from one of three observed sources, and every component carries derived_from_observation, its source refs and the
sha256 of each source read:

  R1 SOURCE_REF          - a code/config path the record itself names in source_refs, read at a pinned commit;
  R2 RECORD_NAMED_PR     - a code/config file changed by a pull request the record names (implementation_pr,
                           read_profile_pr, pr, *_pr), read at the merge commit the PR reports;
  R3 OWN_TASK_FILE_PATH  - a code/config path declared inside a task file the record names in source_refs (in the
                           record's own repository), and read at the same pinned commit.

No component -> six-field FAIL_CLOSED (CANDIDATE_COMPONENTS_NOT_DERIVABLE_FROM_OBSERVATION); the check-in keeps
refusing. The output is a ``stegverse.registry-record-data-proposal/v1`` file (the record-data successor transition,
StegVerse-Labs/.github#3257, scripts/apply_task_record_data.py): one ``row_fields`` edit per Goal, path
["targets"], before {"$absent": true}. Records are never edited here and the registry generation is never bumped;
the apply (one generation, tip + 1) is that entrypoint's job, not this one's.

  observe --task-id ID [--out F]          (network: gh api; reads the sources and writes an observation index)
  derive  --task-id ID --observation F    (offline, pure)  -> row_fields edit + derivation, or FAIL_CLOSED
  propose --observation F [...] --out P   (offline)        -> the record-data proposal draft
  check   --proposal P [--base DIR]       (offline, CI)    -> re-derives every edit from its recorded observation
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RECORDS = "data/canonical-task-records"
REGISTRY = "data/canonical-task-registry.json"
PROPOSAL_SCHEMA = "stegverse.registry-record-data-proposal/v1"
OBSERVATION_SCHEMA = "stegverse.candidate-component-observation/v1"
DERIVATION_SCHEMA = "stegverse.candidate-component-derivation/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
ENTRYPOINT = "python scripts/derive_candidate_components.py derive --task-id <ID> --observation <F>"
ABSENT = {"$absent": True}
CODE_SUFFIXES = (".py", ".json", ".yml", ".yaml", ".toml")
EXCLUDED_DIRS = {"tests", "test", "docs", "doc", "tasks", "receipts", "fixtures"}
PR_REF = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)$")
REPO_PATH = re.compile(r"^([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+):([A-Za-z0-9_./-]+)$")
REL_PATH = re.compile(r"^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$")
HEX64 = re.compile(r"^sha256:[0-9a-f]{64}$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class NotDerivable(Exception):
    def __init__(self, code: str, predicate: str, repair: str, detail: Any = None):
        super().__init__(code)
        self.code, self.predicate, self.repair, self.detail = code, predicate, repair, detail

    def six(self) -> dict[str, Any]:
        return {"disposition": "FAIL_CLOSED", "failure_code": self.code, "failed_predicate": self.predicate,
                "required_evidence_or_repair": self.repair, "retry_entrypoint": ENTRYPOINT,
                "owning_existing_goal": OWNING_GOAL,
                "next_attempt": "after the Goal's owner records an observable implementation surface (a source_ref or a "
                                "record-named PR); the adjacency check-in keeps refusing until then",
                "detail": self.detail}


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _need(ok: bool, code: str, predicate: str, repair: str, detail: Any = None) -> None:
    if not ok:
        raise NotDerivable(code, predicate, repair, detail)


# --- the derivation rule (pure) --------------------------------------------------------------------------------
def is_surface(path: str) -> bool:
    """A code/config implementation surface: not a test, doc, task file, receipt or package marker."""
    p = PurePosixPath(path)
    if not REL_PATH.match(path) or p.suffix.lower() not in CODE_SUFFIXES or p.name == "__init__.py":
        return False
    if any(part.lower() in EXCLUDED_DIRS for part in p.parts[:-1]):
        return False
    return not (p.name.startswith("test_") or p.stem.endswith("_test"))


def component_name(path: str) -> str:
    name = PurePosixPath(path).name.lower()
    for suffix in CODE_SUFFIXES:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if name.endswith(".schema"):
        name = name[: -len(".schema")]
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", name)).strip("-")


def record_prs(record: dict[str, Any]) -> list[str]:
    return sorted({v for k, v in record.items()
                   if (k == "pr" or k.endswith("_pr")) and isinstance(v, str) and PR_REF.match(v)})


def record_source_refs(record: dict[str, Any]) -> list[tuple[str, str]]:
    out = []
    for ref in record.get("source_refs") or []:
        m = REPO_PATH.match(ref) if isinstance(ref, str) else None
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def own_task_files(record: dict[str, Any]) -> list[tuple[str, str]]:
    repo = record.get("repository")
    return [(r, p) for r, p in record_source_refs(record)
            if r == repo and PurePosixPath(p).parts[0] == "tasks" and p.endswith(".json")]


def task_file_paths(value: Any) -> list[str]:
    """Every string value in a task file that is a relative code/config path."""
    out: set[str] = set()

    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and REL_PATH.match(v) and "/" in v and PurePosixPath(v).suffix.lower() in CODE_SUFFIXES:
            out.add(v)
    walk(value)
    return sorted(out)


def _file_index(observation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {f["ref"]: f for f in observation.get("files") or []}


def _ref(repo: str, path: str, commit: str) -> str:
    return f"{repo}:{path}@{commit}"


def derive(record: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    """row_fields edit + per-component derivation. Raises NotDerivable (six fields) - never guesses."""
    task_id = record.get("task_id")
    _need(observation.get("schema") == OBSERVATION_SCHEMA and observation.get("task_id") == task_id,
          "CANDIDATE_OBSERVATION_SCHEMA_MISMATCH", f"observation schema == {OBSERVATION_SCHEMA} for {task_id}",
          "re-run observe for this task id", {"task_id": task_id})
    record_digest = sha(canon(record))
    _need(observation.get("record_sha256") == record_digest, "CANDIDATE_OBSERVATION_STALE",
          "observation.record_sha256 == sha256(canonical record)",
          "the record changed after it was observed; re-run observe", {"observed": observation.get("record_sha256"),
                                                                       "current": record_digest})
    existing = (record.get("targets") or {}).get("components")
    _need(not existing, "CANDIDATE_COMPONENTS_ALREADY_DECLARED", "record declares no targets.components",
          "nothing to derive: the record already declares components", {"components": existing})
    _need("targets" not in record, "CANDIDATE_TARGETS_PRESENT_WITHOUT_COMPONENTS", "targets is absent",
          "the record carries a targets object without components; its owner repairs it through its own Goal")
    files = _file_index(observation)
    record_src = {"ref": f"StegVerse-Labs/.github:{RECORDS}/{task_id}.json", "sha256": record_digest}
    found: dict[str, dict[str, Any]] = {}

    def add(component: str, repo: str, path: str, rule: str, sources: list[dict[str, str]]) -> None:
        entry = found.setdefault(component, {"component": component, "derived_from_observation": True,
                                             "repositories": set(), "rules": set(), "paths": set(), "sources": {}})
        entry["repositories"].add(repo)
        entry["rules"].add(rule)
        entry["paths"].add(f"{repo}:{path}")
        for s in sources:
            entry["sources"][s["ref"]] = s["sha256"]

    def read(repo: str, path: str, commit: str) -> dict[str, Any] | None:
        f = files.get(_ref(repo, path, commit))
        return f if f and f.get("observed") is True and HEX64.match(str(f.get("sha256"))) else None

    commit_of = observation.get("source_commits") or {}
    # R1: code/config source_refs
    for repo, path in record_source_refs(record):
        commit = commit_of.get(repo)
        f = read(repo, path, commit) if commit else None
        if f and is_surface(path):
            add(component_name(path), repo, path, "R1_SOURCE_REF", [record_src, {"ref": f["ref"], "sha256": f["sha256"]}])
    # R2: files changed by record-named PRs, read at the reported merge commit
    prs = {p["ref"]: p for p in observation.get("pull_requests") or []}
    for pr_ref in record_prs(record):
        pr = prs.get(pr_ref)
        if not pr or pr.get("merged") is not True or not SHA40.match(str(pr.get("merge_commit"))):
            continue
        repo = PR_REF.match(pr_ref).group(1)
        listing = {"ref": f"{pr_ref} files", "sha256": pr["files_sha256"]}
        _need(sha(canon(sorted(pr["files"]))) == pr["files_sha256"], "CANDIDATE_OBSERVATION_TAMPERED",
              "files_sha256 == sha256(canonical sorted file listing)", "re-run observe", {"pr": pr_ref})
        for path in pr["files"]:
            f = read(repo, path, pr["merge_commit"])
            if f and is_surface(path):
                add(component_name(path), repo, path, "R2_RECORD_NAMED_PR", [record_src, listing,
                                                                             {"ref": f["ref"], "sha256": f["sha256"]}])
    # R3: code/config paths declared in the record's own task file
    for repo, path in own_task_files(record):
        commit = commit_of.get(repo)
        tf = read(repo, path, commit) if commit else None
        declared = (observation.get("task_file_paths") or {}).get(_ref(repo, path, commit or ""))
        if not tf or declared is None:
            continue
        for decl in declared:
            f = read(repo, decl, commit)
            if f and is_surface(decl):
                add(component_name(decl), repo, decl, "R3_OWN_TASK_FILE_PATH",
                    [record_src, {"ref": tf["ref"], "sha256": tf["sha256"]}, {"ref": f["ref"], "sha256": f["sha256"]}])
    _need(bool(found), "CANDIDATE_COMPONENTS_NOT_DERIVABLE_FROM_OBSERVATION",
          "at least one code/config surface observed through R1 (source_refs), R2 (record-named merged PR) or R3 "
          "(own task file)", "the Goal's owner records an implementation surface; disjointness is never assumed",
          {"task_id": task_id, "prs": record_prs(record), "source_refs": record.get("source_refs") or []})
    components = sorted(found)
    by_repo: dict[str, list[str]] = {}
    for c in components:
        for repo in found[c]["repositories"]:
            by_repo.setdefault(repo, []).append(c)
    repositories = sorted(by_repo)
    after = {"organizations": sorted({r.split("/")[0] for r in repositories}), "repositories": repositories,
             "components": components, "repository_components": {r: sorted(v) for r, v in sorted(by_repo.items())}}
    derivation = [{"component": c, "derived_from_observation": True, "rules": sorted(found[c]["rules"]),
                   "paths": sorted(found[c]["paths"]),
                   "sources": [{"ref": r, "sha256": d} for r, d in sorted(found[c]["sources"].items())]}
                  for c in components]
    return {"edit": {"task_id": task_id, "path": ["targets"], "before": ABSENT, "after": after},
            "derivation": {"schema": DERIVATION_SCHEMA, "task_id": task_id, "record_sha256": record_digest,
                           "observation_sha256": sha(canon(observation)), "observation": observation,
                           "components": derivation}}


# --- proposal and its CI check (offline) -----------------------------------------------------------------------
def load_record(base: Path, task_id: str) -> dict[str, Any]:
    path = base / RECORDS / f"{task_id}.json"
    _need(path.is_file(), "CANDIDATE_RECORD_UNOBSERVED", f"{RECORDS}/{task_id}.json exists on the base tree",
          "register the task first", {"task_id": task_id})
    return json.loads(path.read_text(encoding="utf-8"))


def registry_generation(base: Path) -> int | None:
    path = base / REGISTRY
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("generation", data.get("registry_generation"))


def propose(base: Path, observations: list[dict[str, Any]], note: str = "") -> dict[str, Any]:
    edits, derivations, refused = [], [], []
    for obs in observations:
        try:
            out = derive(load_record(base, obs["task_id"]), obs)
            edits.append(out["edit"])
            derivations.append(out["derivation"])
        except NotDerivable as exc:
            refused.append({"task_id": obs.get("task_id"), **exc.six()})
    return {"schema": PROPOSAL_SCHEMA, "registry_generation_base": registry_generation(base),
            "authority_effect": "NONE", "draft": True,
            "note": note or ("Record-data repair DRAFT: targets.components derived from observed evidence only "
                             "(scripts/derive_candidate_components.py). Applied, if ever, only by the record-data "
                             "successor transition (scripts/apply_task_record_data.py, StegVerse-Labs/.github#3257) "
                             "at tip + 1; this file bumps no generation and edits no record."),
            "work_items": {}, "human_actions": [], "register_from_record": [], "row_fields": edits,
            "derivations": derivations, "not_derivable": refused}


def check(proposal: dict[str, Any], base: Path) -> list[str]:
    errors: list[str] = []
    if proposal.get("schema") != PROPOSAL_SCHEMA:
        errors.append(f"schema != {PROPOSAL_SCHEMA}")
    if proposal.get("draft") is not True or proposal.get("authority_effect") != "NONE":
        errors.append("a derivation proposal is a draft with authority_effect NONE")
    if proposal.get("work_items") or proposal.get("human_actions") or proposal.get("register_from_record"):
        errors.append("a derivation proposal carries row_fields only")
    gen = registry_generation(base)
    if proposal.get("registry_generation_base") != gen:
        errors.append(f"registry_generation_base {proposal.get('registry_generation_base')} != base generation {gen}")
    derivs = {d.get("task_id"): d for d in proposal.get("derivations") or []}
    edits = proposal.get("row_fields") or []
    if len(derivs) != len(edits) or len({e.get("task_id") for e in edits}) != len(edits):
        errors.append("exactly one derivation per row_fields edit")
    for edit in edits:
        tid = edit.get("task_id")
        d = derivs.get(tid)
        if edit.get("path") != ["targets"] or edit.get("before") != ABSENT:
            errors.append(f"{tid}: edit must be path ['targets'] with before $absent")
        if d is None:
            errors.append(f"{tid}: no derivation")
            continue
        for c in d.get("components") or []:
            if c.get("derived_from_observation") is not True or not c.get("sources") or any(
                    not HEX64.match(str(s.get("sha256"))) or not s.get("ref") for s in c["sources"]):
                errors.append(f"{tid}: component {c.get('component')} lacks derived_from_observation/sources/sha256")
        if sha(canon(d.get("observation"))) != d.get("observation_sha256"):
            errors.append(f"{tid}: observation_sha256 does not match the recorded observation")
        try:
            again = derive(load_record(base, tid), d.get("observation") or {})
        except NotDerivable as exc:
            errors.append(f"{tid}: re-derivation refused {exc.code}")
            continue
        if canon(again["edit"]) != canon(edit) or canon(again["derivation"]) != canon(d):
            errors.append(f"{tid}: edit/derivation differ from the re-derivation over the recorded observation")
    for r in proposal.get("not_derivable") or []:
        if any(not r.get(k) for k in ("failure_code", "failed_predicate", "required_evidence_or_repair",
                                       "retry_entrypoint", "owning_existing_goal", "next_attempt")):
            errors.append(f"{r.get('task_id')}: not_derivable entry lacks the six fields")
    return errors


# --- observe (network, never in tests) -------------------------------------------------------------------------
def _gh(*args: str) -> Any:
    out = subprocess.run(["gh", "api", *args], capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


def _read_file(repo: str, path: str, commit: str) -> tuple[dict[str, Any], bytes | None]:
    data = _gh(f"repos/{repo}/contents/{path}?ref={commit}")
    ref = _ref(repo, path, commit)
    if not isinstance(data, dict) or data.get("type") != "file" or "content" not in data:
        return {"ref": ref, "observed": False, "sha256": None}, None
    raw = base64.b64decode(data["content"])
    return {"ref": ref, "observed": True, "sha256": sha(raw)}, raw


def observe(base: Path, task_id: str) -> dict[str, Any]:
    record = load_record(base, task_id)
    files: dict[str, dict[str, Any]] = {}
    commits: dict[str, str] = {}
    for repo, _ in record_source_refs(record):
        if repo not in commits:
            head = _gh(f"repos/{repo}/commits/HEAD")
            if isinstance(head, dict) and SHA40.match(str(head.get("sha"))):
                commits[repo] = head["sha"]
    task_paths: dict[str, list[str]] = {}
    for repo, path in record_source_refs(record):
        if repo not in commits:
            continue
        entry, raw = _read_file(repo, path, commits[repo])
        files[entry["ref"]] = entry
        if raw is not None and (repo, path) in own_task_files(record):
            declared = task_file_paths(json.loads(raw))
            task_paths[entry["ref"]] = declared
            for decl in declared:
                e, _ = _read_file(repo, decl, commits[repo])
                files[e["ref"]] = e
    prs = []
    for pr_ref in record_prs(record):
        repo, number = PR_REF.match(pr_ref).groups()
        pr = _gh(f"repos/{repo}/pulls/{number}")
        listing = _gh(f"repos/{repo}/pulls/{number}/files?per_page=100")
        if not isinstance(pr, dict) or not isinstance(listing, list):
            prs.append({"ref": pr_ref, "merged": False, "merge_commit": None, "files": [], "files_sha256": sha(canon([]))})
            continue
        names = sorted(f["filename"] for f in listing if f.get("status") != "removed")
        prs.append({"ref": pr_ref, "merged": bool(pr.get("merged")), "merge_commit": pr.get("merge_commit_sha"),
                    "files": names, "files_sha256": sha(canon(names))})
        if pr.get("merged"):
            for name in names:
                e, _ = _read_file(repo, name, pr["merge_commit_sha"])
                files[e["ref"]] = e
    return {"schema": OBSERVATION_SCHEMA, "task_id": task_id, "record_sha256": sha(canon(record)),
            "source_commits": dict(sorted(commits.items())), "pull_requests": prs,
            "task_file_paths": dict(sorted(task_paths.items())),
            "files": sorted(files.values(), key=lambda f: f["ref"])}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("observe"); o.add_argument("--task-id", required=True); o.add_argument("--out")
    d = sub.add_parser("derive"); d.add_argument("--task-id", required=True); d.add_argument("--observation", required=True)
    p = sub.add_parser("propose"); p.add_argument("--observation", action="append", required=True); p.add_argument("--out", required=True)
    c = sub.add_parser("check"); c.add_argument("--proposal", action="append", required=True)
    for s in (o, d, p, c):
        s.add_argument("--base", default=str(ROOT))
    a = ap.parse_args(argv)
    base = Path(a.base)
    if a.cmd == "observe":
        text = json.dumps(observe(base, a.task_id), indent=2, ensure_ascii=False) + "\n"
        Path(a.out).write_text(text, encoding="utf-8") if a.out else sys.stdout.write(text)
        return 0
    if a.cmd == "derive":
        try:
            out = derive(load_record(base, a.task_id), json.loads(Path(a.observation).read_text(encoding="utf-8")))
        except NotDerivable as exc:
            print(json.dumps(exc.six(), indent=2)); return 1
        print(json.dumps(out, indent=2, ensure_ascii=False)); return 0
    if a.cmd == "propose":
        obs = [json.loads(Path(f).read_text(encoding="utf-8")) for f in a.observation]
        prop = propose(base, obs)
        Path(a.out).write_text(json.dumps(prop, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"row_fields": [e["task_id"] for e in prop["row_fields"]],
                          "not_derivable": [r["task_id"] for r in prop["not_derivable"]]}))
        return 0
    status = 0
    for f in a.proposal:
        errors = check(json.loads(Path(f).read_text(encoding="utf-8")), base)
        print(json.dumps({"proposal": f, "ok": not errors, "errors": errors}))
        status |= bool(errors)
    return status


if __name__ == "__main__":
    sys.exit(main())
