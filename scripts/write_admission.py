#!/usr/bin/env python3
"""WRITE_ADMISSION: is this write to a governed StegVerse surface admitted? (E0: stdlib, local data, no clock, no network.)

STEGVERSE-CANONICAL-WORK-COORDINATION-001, class B. Rigel's design direction (Oct 23, relayed by Coordination): every
editable surface (a file, an issue, a pull request) is a governed element, not strictly blocked. A write is admitted
against the constraints (invariants, documented processes) and against whether it is necessary for, and related to,
the writer's current work. A clear relationship is never blocked; work already active on the same surface is taken
into account before the write is allowed or denied. This generalizes the adjacency ruling (scripts/adjacency_ruling.py,
Labs#3327), which already computes the relationships a finish point has to the files it reaches and consumes.

Inputs, all data (evaluation reads nothing else; `observe-stack` is the optional, local-git-only gathering step):
  --surface     {"kind": "file", "repository": "Org/repo", "path": "a/b.py"}
                | {"kind": "issue" | "pull_request", "repository": "Org/repo", "number": N}
  --work-item   stegverse.write-admission-work-item/v1 {task_id, work_id, repository, branch, head (40-hex),
                pull_request?}                       - the writer and the Goal/task its write serves
  --graph       stegverse.write-admission-graph/v1 {receipts: {"sha256:<canon digest>": body}} - the relationship
                graph as receipted evidence. Every relationship is recomputed from a body; nothing an edge claims is
                trusted. Bodies and the relationships they can establish:
                  canonical task record (task_id, targets, source_refs, ...)     -> GOAL_TARGET
                  stegverse.adjacency-ruling-verification/v1 (disposition ALLOW) -> FINISH_TEST_CLOSURE
                  stegverse.adjacency-ruling/v1 (evidence_digest re-derived)     -> CONSUMES_PIN (+ its constraints)
                  stegverse.consumes-edit-receipt/v1 (receipt_sha256 re-derived) -> CONSUMES_EDIT
                  stegverse.surface-link-observation/v1                          -> ISSUE_PR_LINK
                  stegverse.branch-stack-observation/v1                          -> STACKED_BRANCH (and coordination)
                  stegverse.write-coordination/v1                                -> coordination with active work
  --active-work stegverse.write-admission-active-work/v1 {observed {source, ...}, items [{work_id, task_id, kind,
                ref, repository, branch, head, surfaces [...]}]} - other open drafts or claims. Required: an
                unobserved active-work set is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED, never "none".
  --constraints stegverse.write-admission-constraints/v1 {rules [...]} (optional) - invariants and documented
                processes: writer_branch_glob (G-8: own laned/* branches), deny_surface (e.g. the real ledger).

Verdict (in this order):
  1. inputs well-formed                               else WRITE_ADMISSION_INPUT_INVALID
  2. constraints: each rule, then the owner routing of every receipted adjacency ruling's protected_paths
     (a non-owner edit of an owned consumed path routes to the owner with the ruling's own failure_code)
  3. relationship: at least one receipted relationship between the writer's task and the surface
                                                      else WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED
     an edit of an UNOWNED_NOT_OBSERVED consumed file needs CONSUMES_EDIT (re-pinned and receipted; a CONSUMES_PIN
     relationship alone is a read relationship)       else ADJACENCY_RULING_UNOWNED_CONSUMED_EDIT
  4. active work: every other active item touching the surface is coordinated - the writer's branch is stacked on
     or rebased onto its head (a receipted branch-stack observation), or a receipted write-coordination names both
                                                      else WRITE_ADMISSION_ACTIVE_WORK_CONFLICT
  ALLOW is a sealed stegverse.write-admission/v1 receipt (scratch: never the real ledger). Anything else is a
  six-field FAIL_CLOSED with the repair path (register the relationship, or coordinate with the active work).

  evaluate      --surface S --work-item W --graph G --active-work A [--constraints C] [--receipt-out F]
  seal-graph    --body F [--body F ...] --out G      -> a graph whose receipt keys are the bodies' digests
  observe-stack --root DIR --branch B --head H --against HEAD [--against HEAD ...] [--repository R] --out F
                                                    -> a branch-stack observation from local git only
"""
from __future__ import annotations

import argparse
import fnmatch
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ADJ_PATH = Path(__file__).resolve().with_name("adjacency_ruling.py")
_spec = importlib.util.spec_from_file_location("adjacency_ruling_for_write_admission", ADJ_PATH)
ar = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(ar)

SCHEMA = "stegverse.write-admission/v1"
WORK_ITEM_SCHEMA = "stegverse.write-admission-work-item/v1"
GRAPH_SCHEMA = "stegverse.write-admission-graph/v1"
ACTIVE_SCHEMA = "stegverse.write-admission-active-work/v1"
CONSTRAINTS_SCHEMA = "stegverse.write-admission-constraints/v1"
LINK_SCHEMA = "stegverse.surface-link-observation/v1"
STACK_SCHEMA = "stegverse.branch-stack-observation/v1"
COORDINATION_SCHEMA = "stegverse.write-coordination/v1"
RECORD_SCHEMA = "stegverse.canonical-task-record/v1"
OWNING_GOAL = ar.OWNING_GOAL
UNOWNED = ar.UNOWNED
UNKNOWN = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
ENTRYPOINT = "python scripts/write_admission.py evaluate"
NEXT_ATTEMPT = "on the writer's next write to this surface, after the relationship is registered or the active work is coordinated"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint", "owning_existing_goal",
       "next_attempt")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
E0 = {"clock_read": False, "network_used": False, "llm_used": False, "lowest_supported_mode": "E0"}


class Refusal(Exception):
    def __init__(self, code: str, predicate: str, repair: str, detail: Any = None, owner: str = OWNING_GOAL,
                 retry: str = ENTRYPOINT):
        super().__init__(code)
        self.code, self.predicate, self.repair, self.detail, self.owner, self.retry = code, predicate, repair, detail, owner, retry

    def six(self) -> dict[str, Any]:
        return {"disposition": "FAIL_CLOSED", "failure_code": self.code, "failed_predicate": self.predicate,
                "required_evidence_or_repair": self.repair, "retry_entrypoint": self.retry,
                "owning_existing_goal": self.owner, "next_attempt": NEXT_ATTEMPT, "detail": self.detail}


def _require(ok: bool, code: str, predicate: str, repair: str, detail: Any = None) -> None:
    if not ok:
        raise Refusal(code, predicate, repair, detail)


def digest(body: Any) -> str:
    return ar.sha(ar.canon(body))


# --- surfaces ------------------------------------------------------------------------------------------------------
def surface_key(surface: Any) -> str | None:
    """Canonical text of a surface: 'Org/repo:path' for a file, 'Org/repo#N' for an issue or pull request."""
    if not isinstance(surface, dict) or not REPO.match(str(surface.get("repository", ""))):
        return None
    kind, repo = surface.get("kind"), surface["repository"]
    if kind == "file":
        path = surface.get("path")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            return None
        return f"{repo}:{Path(path).as_posix()}"
    if kind in ("issue", "pull_request"):
        n = surface.get("number")
        return f"{repo}#{n}" if isinstance(n, int) and not isinstance(n, bool) and n > 0 else None
    return None


def _ref_names(ref: str, surface: dict[str, Any]) -> bool:
    """Does a record/observation ref ('Org/repo/path', 'Org/repo:path', 'Org/repo#N', with #/@ suffixes) name it?"""
    repo = surface["repository"]
    if surface["kind"] == "file":
        for sep in ("/", ":"):
            if ref.startswith(repo + sep) and ref[len(repo) + 1:].split("#")[0].split("@")[0] == surface["path"]:
                return True
        return False
    return ref.split("@")[0] in (f"{repo}#{surface['number']}", f"https://github.com/{repo}/issues/{surface['number']}",
                                 f"https://github.com/{repo}/pull/{surface['number']}")


# --- the relationship graph: every relationship recomputed from a receipted body --------------------------------
def receipts(graph: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(bodies whose key is their canonical digest, rejected keys). A body whose own seal (ruling evidence_digest,
    receipt_sha256) does not re-derive is rejected too."""
    good, bad = [], []
    for key, body in sorted((graph.get("receipts") or {}).items()):
        if not isinstance(body, dict) or digest(body) != key:
            bad.append({"receipt": key, "reason": "KEY_IS_NOT_THE_CANONICAL_SHA256_OF_THE_BODY"})
            continue
        schema = body.get("schema")
        if schema == ar.SCHEMA and body.get("evidence_digest") != ar.ruling_digest(body):
            bad.append({"receipt": key, "reason": "ADJACENCY_RULING_EVIDENCE_DIGEST_DOES_NOT_RE_DERIVE"})
            continue
        if ar.SEAL in body and body.get(ar.SEAL) != ar.seal(body).get(ar.SEAL):
            bad.append({"receipt": key, "reason": "RECEIPT_SHA256_DOES_NOT_RE_DERIVE"})
            continue
        good.append({"key": key, "body": body})
    return good, bad


def relationships(surface: dict[str, Any], work: dict[str, Any], bodies: list[dict[str, Any]],
                  active: list[dict[str, Any]]) -> list[dict[str, Any]]:
    task, repo = work["task_id"], surface["repository"]
    out: list[dict[str, Any]] = []

    def add(kind: str, key: str, why: str, **extra: Any) -> None:
        out.append({"kind": kind, "receipt": key, "why": why, **extra})

    for item in bodies:
        b, key = item["body"], item["key"]
        schema = b.get("schema")
        if schema == RECORD_SCHEMA and b.get("task_id") == task:
            refs = [r for k in ("source_refs", "existing_evidence_refs", "handoff_projection_refs")
                    for r in (b.get(k) or []) if isinstance(r, str)]
            hit = next((r for r in refs if _ref_names(r, surface)), None)
            if hit:
                add("GOAL_TARGET", key, f"{task}'s record names the surface ({hit})")
            elif surface["kind"] == "file" and repo in ((b.get("targets") or {}).get("repositories") or []):
                hits = ar.touches([surface["path"]], b, repo)
                if hits and hits[0]["reason"] == "MODULE_NAMES_CANDIDATE_COMPONENT":
                    add("GOAL_TARGET", key, f"the path names {task}'s component {hits[0]['component']}")
        elif schema == ar.RECEIPT_SCHEMA and b.get("disposition") == "ALLOW" and b.get("task_id") == task \
                and surface["kind"] == "file":
            fp = b.get("finish_point") or {}
            if fp.get("repository") == repo and surface["path"] in (fp.get("closure") or {}):
                add("FINISH_TEST_CLOSURE", key, f"{fp.get('test')} @ {fp.get('source_commit')} reaches the surface")
        elif schema == ar.SCHEMA and b.get("task_id") == task and surface["kind"] == "file":
            for dep in b.get("consumes_dependencies") or []:
                pin = dep.get("pinned_source") if isinstance(dep, dict) else None
                if isinstance(pin, dict) and pin.get("repository") == repo and surface["path"] in (pin.get("files") or {}):
                    add("CONSUMES_PIN", key, f"{task} consumes the surface pinned at {pin.get('commit')}",
                        consumed_from=dep.get("task_id"), pinned_sha256=ar._bare(pin["files"][surface["path"]]))
        elif schema == ar.CONSUMES_EDIT_SCHEMA and surface["kind"] == "file" and b.get("disposition") == "ALLOW" \
                and b.get("ledger_status") == ar.SCRATCH and (b.get("writer") or {}).get("task_id") == task \
                and b.get("repository") == repo and b.get("path") == surface["path"]:
            add("CONSUMES_EDIT", key, f"re-pinned consumes-edit {b['from'].get('sha256', '?')[:8]}->"
                f"{b['to'].get('sha256', '?')[:8]}", to_sha256=b["to"].get("sha256"),
                ruling_digest=(b.get("relationship") or {}).get("ruling_digest"))
        elif schema == LINK_SCHEMA and b.get("task_id") == task and surface_key(b.get("surface")) == surface_key(surface):
            linked = [r for r in (b.get("links") or []) if isinstance(r, str)]
            mine = [r for r in linked if r in (work.get("pull_request"), task)]
            if mine:
                add("ISSUE_PR_LINK", key, f"the surface links {mine[0]}")
        elif schema == STACK_SCHEMA and b.get("repository") == work["repository"] and b.get("branch") == work["branch"] \
                and b.get("head") == work["head"]:
            contained = {c.get("head") for c in b.get("contains") or [] if isinstance(c, dict)}
            for other in active:
                if other.get("head") in contained and surface_key(surface) in {surface_key(s) for s in other.get("surfaces") or []}:
                    add("STACKED_BRANCH", key, f"{work['branch']} is stacked on {other.get('work_id')} "
                        f"({other.get('branch')}@{str(other.get('head'))[:8]}), which writes the surface")
    return out


def _unowned_files(bodies: list[dict[str, Any]], surface: dict[str, Any]) -> list[dict[str, Any]]:
    """Receipted rulings that list the surface as an UNOWNED_NOT_OBSERVED consumed file."""
    out = []
    for item in bodies:
        b = item["body"]
        if b.get("schema") != ar.SCHEMA or surface["kind"] != "file":
            continue
        for dep in b.get("consumes_dependencies") or []:
            pin = dep.get("pinned_source") if isinstance(dep, dict) else None
            if dep.get("task_id") == UNOWNED and isinstance(pin, dict) and pin.get("repository") == surface["repository"] \
                    and surface["path"] in (pin.get("files") or {}):
                out.append({"ruling": item["key"], "ruling_digest": b.get("evidence_digest"), "task_id": b.get("task_id"),
                            "pinned_sha256": ar._bare(pin["files"][surface["path"]])})
    return out


# --- constraints ------------------------------------------------------------------------------------------------
def check_constraints(constraints: dict[str, Any] | None, surface: dict[str, Any], work: dict[str, Any],
                      bodies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    held = []
    for rule in (constraints or {}).get("rules") or []:
        kind = rule.get("kind")
        code = rule.get("failure_code") or "WRITE_ADMISSION_CONSTRAINT_VIOLATED"
        owner = rule.get("owning_existing_goal") or OWNING_GOAL
        if kind == "writer_branch_glob":
            if not any(fnmatch.fnmatchcase(work["branch"], g) for g in rule.get("globs") or []):
                raise Refusal(code, rule.get("failed_predicate") or "WRITER_BRANCH_IS_PERMITTED",
                              rule.get("repair") or f"write from a branch matching {rule.get('globs')}",
                              {"rule": rule.get("id"), "branch": work["branch"]}, owner)
        elif kind == "deny_surface":
            repo_ok = any(fnmatch.fnmatchcase(surface["repository"], g) for g in rule.get("repositories") or ["*"])
            target = surface.get("path") if surface["kind"] == "file" else f"#{surface.get('number')}"
            if repo_ok and surface["kind"] in (rule.get("surface_kinds") or ["file"]) \
                    and any(fnmatch.fnmatchcase(target, g) for g in rule.get("paths") or []):
                raise Refusal(code, rule.get("failed_predicate") or "SURFACE_IS_NOT_A_DENIED_SURFACE",
                              rule.get("repair") or "this surface is written only by its own transition",
                              {"rule": rule.get("id"), "surface": surface_key(surface)}, owner)
        else:
            raise Refusal("WRITE_ADMISSION_INPUT_INVALID", "CONSTRAINT_KIND_IS_KNOWN",
                          "constraint rules are writer_branch_glob or deny_surface; an unknown rule never passes",
                          {"rule": rule.get("id"), "kind": kind})
        held.append({"rule": rule.get("id"), "kind": kind, "condition": "HELD"})
    if surface["kind"] == "file":  # owner routing carried by every receipted adjacency ruling
        for item in bodies:
            b = item["body"]
            if b.get("schema") != ar.SCHEMA:
                continue
            for route in b.get("protected_paths") or []:
                if not isinstance(route, dict) or route.get("repository") != surface["repository"] \
                        or surface["path"] not in (route.get("paths") or []):
                    continue
                owner = route.get("owner_task_id")
                if owner != work["task_id"]:
                    mod = route.get("on_modification") or {}
                    raise Refusal(mod.get("failure_code") or "WRITE_ADMISSION_OWNED_SURFACE", "PROTECTED_PATHS_UNMODIFIED_BY_NON_OWNER",
                                  f"{surface['path']} is owned by {owner} (adjacency ruling {item['key'][:19]}): route the "
                                  f"change to {owner}; once {owner} publishes it, the consumes pin moves",
                                  {"surface": surface_key(surface), "routed_to": owner}, owner or OWNING_GOAL)
                held.append({"rule": f"protected_paths:{owner}", "kind": "owner_routing", "condition": "HELD_WRITER_IS_OWNER"})
    return held


# --- active work --------------------------------------------------------------------------------------------------
def conflicts(surface: dict[str, Any], work: dict[str, Any], active: list[dict[str, Any]],
              bodies: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """(coordinated, uncoordinated) other active items touching the surface."""
    key = surface_key(surface)
    stacked: set[str] = set()
    coordinated_ids: dict[str, str] = {}
    for item in bodies:
        b = item["body"]
        if b.get("schema") == STACK_SCHEMA and b.get("repository") == work["repository"] \
                and b.get("branch") == work["branch"] and b.get("head") == work["head"]:
            stacked |= {c.get("head") for c in b.get("contains") or [] if isinstance(c, dict) and c.get("head")}
        elif b.get("schema") == COORDINATION_SCHEMA and surface_key(b.get("surface")) == key \
                and work["work_id"] in (b.get("work_ids") or []):
            for wid in b.get("work_ids") or []:
                coordinated_ids[wid] = item["key"]
    done, open_ = [], []
    for other in active:
        if other.get("work_id") == work["work_id"] or (other.get("repository") == work["repository"]
                                                       and other.get("branch") == work["branch"]):
            continue  # the writer's own work
        if key not in {surface_key(s) for s in other.get("surfaces") or []}:
            continue
        row = {"work_id": other.get("work_id"), "task_id": other.get("task_id"), "kind": other.get("kind"),
               "ref": other.get("ref"), "branch": other.get("branch"), "head": other.get("head")}
        if other.get("head") and other.get("head") in stacked:
            done.append(dict(row, coordinated_by="STACKED_OR_REBASED_ONTO"))
        elif other.get("work_id") in coordinated_ids:
            done.append(dict(row, coordinated_by="WRITE_COORDINATION", receipt=coordinated_ids[other["work_id"]]))
        else:
            open_.append(row)
    return done, open_


# --- evaluation ---------------------------------------------------------------------------------------------------
def _well_formed(surface: Any, work: Any, graph: Any, active: Any, constraints: Any) -> None:
    _require(surface_key(surface) is not None, "WRITE_ADMISSION_INPUT_INVALID", "SURFACE_IS_ADDRESSABLE",
             "surface: {kind: file, repository: Org/repo, path} or {kind: issue|pull_request, repository, number}",
             surface)
    _require(isinstance(work, dict) and work.get("schema") == WORK_ITEM_SCHEMA
             and all(isinstance(work.get(k), str) and work[k] for k in ("task_id", "work_id", "repository", "branch", "head"))
             and REPO.match(work["repository"]) is not None and HEX40.match(work["head"]) is not None
             and work["task_id"] != UNKNOWN,
             "WRITE_ADMISSION_INPUT_INVALID", "WORK_ITEM_NAMES_AN_OBSERVED_TASK",
             f"work item: {WORK_ITEM_SCHEMA} with task_id (an existing Goal/task id, never invented), work_id, "
             "repository, branch and the 40-hex head the write is made on", work)
    _require(isinstance(graph, dict) and graph.get("schema") == GRAPH_SCHEMA and isinstance(graph.get("receipts"), dict),
             "WRITE_ADMISSION_INPUT_INVALID", "RELATIONSHIP_GRAPH_IS_WELL_FORMED",
             f"graph: {GRAPH_SCHEMA} with receipts {{sha256: body}} (python scripts/write_admission.py seal-graph)")
    _require(isinstance(active, dict) and active.get("schema") == ACTIVE_SCHEMA and isinstance(active.get("items"), list)
             and isinstance(active.get("observed"), dict) and active["observed"].get("source") not in (None, "", UNKNOWN)
             and all(isinstance(i, dict) and i.get("work_id") for i in active["items"]),
             "WRITE_ADMISSION_ACTIVE_WORK_NOT_OBSERVED", "ACTIVE_WORK_SET_OBSERVED",
             f"supply the active-work set ({ACTIVE_SCHEMA}: observed.source names where the open drafts and claims "
             f"were read; items may be empty). An unobserved set is {UNKNOWN}, never 'no active work'", active)
    _require(constraints is None or (isinstance(constraints, dict) and constraints.get("schema") == CONSTRAINTS_SCHEMA
                                     and isinstance(constraints.get("rules"), list)),
             "WRITE_ADMISSION_INPUT_INVALID", "CONSTRAINTS_ARE_WELL_FORMED", f"constraints: {CONSTRAINTS_SCHEMA} {{rules}}")


def evaluate(surface: Any, work: Any, graph: Any, active: Any, constraints: Any = None) -> dict[str, Any]:
    """The sealed ALLOW receipt, or a six-field FAIL_CLOSED. Never raises for bad input."""
    body: dict[str, Any] = {"schema": SCHEMA, "authority_effect": "NONE_ADMISSION_INPUT_ONLY",
                            "ledger_status": ar.SCRATCH, **E0}
    try:
        _well_formed(surface, work, graph, active, constraints)
        body.update({"surface": surface_key(surface), "writer": {k: work.get(k) for k in
                     ("task_id", "work_id", "repository", "branch", "head", "pull_request") if k in work}})
        bodies, rejected = receipts(graph)
        body["rejected_receipts"] = rejected
        body["constraints"] = check_constraints(constraints, surface, work, bodies)
        rels = relationships(surface, work, bodies, active["items"])
        unowned = _unowned_files(bodies, surface)
        if unowned:
            # every ruling that pins the surface as unowned must have been moved by a receipted consumes-edit:
            # one stale pin would leave that ruling's finish point consuming bytes that are no longer there
            missing = [u for u in unowned if not any(
                r["kind"] == "CONSUMES_EDIT" and u["pinned_sha256"] == r.get("to_sha256")
                and u["ruling_digest"] == r.get("ruling_digest") for r in rels)]
            if missing:
                refusal = ar._unowned_edit({UNOWNED: {"files": {surface["path"]: ""}}}, [surface["path"]])
                raise Refusal(refusal.code, refusal.predicate, refusal.repair,
                              {"surface": surface_key(surface), "unowned_pins_not_moved": missing,
                               "relationships": rels, "rejected_receipts": rejected}, OWNING_GOAL,
                              "python scripts/adjacency_ruling.py consumes-edit, then " + ENTRYPOINT)
            rels = [r for r in rels if r["kind"] != "CONSUMES_PIN" or r.get("consumed_from") != UNOWNED]
        _require(bool(rels), "WRITE_ADMISSION_RELATIONSHIP_UNRECEIPTED", "WRITE_IS_RELATED_TO_THE_WRITERS_WORK",
                 f"register the relationship between {work['task_id']} and {surface_key(surface)} as receipted evidence "
                 "in the graph: the surface in the task record's targets/source_refs, in an ALLOW adjacency-ruling "
                 "verification's finish-point closure, in a consumes pin, a surface-link observation naming the "
                 "writer's PR, or a stack on active work that writes it",
                 {"surface": surface_key(surface), "task_id": work["task_id"], "rejected_receipts": rejected})
        done, open_ = conflicts(surface, work, active["items"], bodies)
        if open_:
            raise Refusal("WRITE_ADMISSION_ACTIVE_WORK_CONFLICT", "ACTIVE_WORK_ON_THE_SURFACE_IS_COORDINATED",
                          f"{surface_key(surface)} is being written by {[o['work_id'] for o in open_]}: stack {work['branch']} "
                          "on that work (or rebase onto it) and supply the branch-stack observation "
                          "(python scripts/write_admission.py observe-stack), or record a write-coordination naming "
                          "both work items", {"active": open_, "coordinated": done, "relationships": rels},
                          OWNING_GOAL)
        body.update({"disposition": "ALLOW", "relationships": rels, "active_work_coordinated": done,
                     "active_work_observed": active["observed"]})
        return ar.seal(body)
    except Refusal as refusal:
        body.update(refusal.six())
        return body


# --- optional gathering (local git only) ----------------------------------------------------------------------
def observe_stack(root: Path, repository: str, branch: str, head: str, against: list[str]) -> dict[str, Any]:
    contains = []
    for other in against:
        try:
            rc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", other, head],
                                capture_output=True, check=False, timeout=60).returncode
        except (OSError, subprocess.SubprocessError):
            rc = 128
        contains.append({"head": other, "contained": rc == 0, "observed": rc in (0, 1)})
    return {"schema": STACK_SCHEMA, "repository": repository, "branch": branch, "head": head,
            "contains": [{"head": c["head"]} for c in contains if c["contained"]],
            "not_contained": [c["head"] for c in contains if not c["contained"] and c["observed"]],
            "unobserved": [c["head"] for c in contains if not c["observed"]], **E0}


def seal_graph(bodies: list[dict[str, Any]]) -> dict[str, Any]:
    return {"schema": GRAPH_SCHEMA, "receipts": {digest(b): b for b in bodies}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluate")
    for name in ("surface", "work-item", "graph", "active-work"):
        e.add_argument(f"--{name}", required=True, type=Path)
    e.add_argument("--constraints", type=Path)
    e.add_argument("--receipt-out", type=Path)
    g = sub.add_parser("seal-graph")
    g.add_argument("--body", type=Path, action="append", required=True)
    g.add_argument("--out", type=Path, required=True)
    o = sub.add_parser("observe-stack")
    o.add_argument("--root", type=Path, required=True)
    o.add_argument("--repository", default=UNKNOWN)
    o.add_argument("--branch", required=True)
    o.add_argument("--head", required=True)
    o.add_argument("--against", action="append", required=True)
    o.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    def read(p: Path | None) -> Any:
        return None if p is None else json.loads(p.read_text(encoding="utf-8"))

    if args.cmd == "seal-graph":
        args.out.write_text(json.dumps(seal_graph([read(p) for p in args.body]), indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
        return 0
    if args.cmd == "observe-stack":
        body = observe_stack(args.root, args.repository, args.branch, args.head, args.against)
        args.out.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    body = evaluate(read(args.surface), read(args.work_item), read(args.graph), read(args.active_work),
                    read(args.constraints))
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if body["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
