#!/usr/bin/env python3
"""Adjacency-ruling input to the registry collision check-in (E0: stdlib + local git, no clock, no network, no LLM).

STEGVERSE-CANONICAL-WORK-COORDINATION-001. The collision check-in (scripts/check_registry_collision_checkin.py)
returns COORDINATE_CONVERGENCE for any declared adjacency, and until now nothing could clear it short of removing
the adjacency. A Coordination adjacency ruling (class D, ADJACENT_NOT_DUPLICATE) is that missing input. A ruling
is never trusted: its digest is re-derived, and its conditions are re-computed from observed state:

  (a) component disjointness - the evaluator's own overlap() over the subject record and each candidate's observed
      record (data/canonical-task-records/<id>.json on the predecessor tree): no shared component, no lineage, no
      shared execution substrate, no conflicting user-action surface. The ruling's component lists must equal the
      observed ones.
  (b) the subject's finish-point test touches none of the candidates' components - the test file is read at the
      commit the ruling pins (a local checkout of the finish-point repository, `git rev-parse HEAD` must equal the
      pin), its static import closure is computed (AST imports, dotted-module and path string literals, closed
      transitively over the repository's Python files), and no file in it may be (i) a path a candidate record
      names in that repository (source_refs, existing_evidence_refs, handoff_projection_refs) or (ii) a module whose
      underscore-split name contains a candidate component name (hyphens -> underscores) as a contiguous run.
  (c) every consumes-dependency the ruling names is a candidate and a TASK dependency of the subject record.

A ruling only ever clears COORDINATE_CONVERGENCE for exactly the subject task, over candidates it covers; a
STOP_COLLISION (hard collision) is never cleared. Everything else is a six-field FAIL_CLOSED.

  digest  --ruling R                                   -> the evidence_digest R must carry
  verify  --ruling R --request Q [--base DIR] --finish-point-root DIR [--receipt-out F]
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import re
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "stegverse.adjacency-ruling/v1"
RECEIPT_SCHEMA = "stegverse.adjacency-ruling-verification/v1"
OWNING_GOAL = "STEGVERSE-CANONICAL-WORK-COORDINATION-001"
ENTRYPOINT = "python scripts/adjacency_ruling.py verify (or canonical_task_registration_transition.py plan --adjacency-ruling)"
NEXT_ATTEMPT = "on the next registration plan after the ruling or the finish-point source is repaired"
EVALUATOR = "scripts/evaluate_task_registry_collision_checkin.py"
RECORDS = "data/canonical-task-records"
ADDRESSABLE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+:[A-Za-z0-9_./-]+\.py(::[A-Za-z0-9_]+)*$")
REQUIRED = ("schema", "task_id", "ruling_class", "ruling", "ruled_by", "subject", "candidates",
            "consumes_dependencies", "evidence_digest")


class RulingRefusal(Exception):
    def __init__(self, code: str, predicate: str, repair: str, detail: Any = None):
        super().__init__(code)
        self.code, self.predicate, self.repair, self.detail = code, predicate, repair, detail

    def six(self) -> dict[str, Any]:
        return {"disposition": "FAIL_CLOSED", "failure_code": self.code, "failed_predicate": self.predicate,
                "required_evidence_or_repair": self.repair, "retry_entrypoint": ENTRYPOINT,
                "owning_existing_goal": OWNING_GOAL, "next_attempt": NEXT_ATTEMPT, "detail": self.detail}


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def ruling_digest(ruling: dict[str, Any]) -> str:
    return sha(canon({k: v for k, v in ruling.items() if k != "evidence_digest"}))


def _require(ok: bool, code: str, predicate: str, repair: str, detail: Any = None) -> None:
    if not ok:
        raise RulingRefusal(code, predicate, repair, detail)


# --- (b) static closure of the finish-point test ---------------------------------------------------------------
def _module_files(root: Path, dotted: str) -> list[Path]:
    parts = [p for p in dotted.split(".") if p]
    if not parts:
        return []
    base = root.joinpath(*parts)
    return [p for p in (base.with_suffix(".py"), base / "__init__.py") if p.is_file()]


def _resolve_from(root: Path, here: Path, node: ast.ImportFrom) -> list[str]:
    if node.level:
        pkg = here.parent
        for _ in range(node.level - 1):
            pkg = pkg.parent
        prefix = ".".join(pkg.relative_to(root).parts)
        mod = ".".join(p for p in (prefix, node.module or "") if p)
    else:
        mod = node.module or ""
    return [mod] + [f"{mod}.{a.name}" if mod else a.name for a in node.names]


def static_closure(root: Path, test_rel: str) -> dict[str, str]:
    """{repository path: sha256} of the test file and every repository file it reaches statically."""
    root = root.resolve()
    start = (root / test_rel).resolve()
    _require(start.is_file() and root in start.parents, "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE",
             "FINISH_POINT_TEST_PRESENT_AT_PINNED_COMMIT",
             f"the finish-point test {test_rel} must exist at the pinned commit of the finish-point repository")
    seen: dict[str, str] = {}
    queue = [start]
    while queue:
        path = queue.pop()
        rel = path.relative_to(root).as_posix()
        if rel in seen:
            continue
        data = path.read_bytes()
        seen[rel] = sha(data)
        if path.suffix != ".py":
            continue
        try:
            tree = ast.parse(data.decode("utf-8"), filename=rel)
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise RulingRefusal("ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE", "FINISH_POINT_CLOSURE_PARSES",
                                f"{rel} must parse so its closure can be computed", str(exc))
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names += [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                names += _resolve_from(root, path, node)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                text = node.value.strip()
                if text and len(text) < 300 and "\n" not in text:
                    candidate = (root / text)
                    try:
                        if candidate.resolve().is_file() and root in candidate.resolve().parents:
                            queue.append(candidate.resolve())
                    except OSError:
                        pass
                    if all(part.isidentifier() for part in text.split(".")):
                        names.append(text)
        for name in names:
            parts = name.split(".")
            for i in range(1, len(parts) + 1):  # a package's __init__ runs on import of anything below it
                queue += _module_files(root, ".".join(parts[:i]))
    return dict(sorted(seen.items()))


def _component_tokens(components: Iterable[str]) -> dict[str, list[str]]:
    return {c: c.lower().replace("-", "_").split("_") for c in components if isinstance(c, str) and c.strip()}


def _contains_run(parts: list[str], run: list[str]) -> bool:
    n = len(run)
    return n > 0 and any(parts[i:i + n] == run for i in range(len(parts) - n + 1))


def _footprint(record: dict[str, Any], repository: str) -> set[str]:
    refs: list[str] = []
    for key in ("source_refs", "existing_evidence_refs", "handoff_projection_refs"):
        value = record.get(key)
        if isinstance(value, list):
            refs += [v for v in value if isinstance(v, str)]
    out = set()
    for ref in refs:
        for sep in ("/", ":"):
            if ref.startswith(repository + sep):
                out.add(ref[len(repository) + 1:].split("#")[0].split("@")[0])
    return out


def touches(closure: Iterable[str], record: dict[str, Any], repository: str) -> list[dict[str, str]]:
    hits = []
    footprint = _footprint(record, repository)
    tokens = _component_tokens((record.get("targets") or {}).get("components") or [])
    for rel in closure:
        if rel in footprint:
            hits.append({"path": rel, "reason": "PATH_NAMED_BY_CANDIDATE_RECORD"})
            continue
        parts = [p for seg in Path(rel).with_suffix("").parts for p in seg.lower().split("_")]
        for component, run in tokens.items():
            if _contains_run(parts, run):
                hits.append({"path": rel, "reason": "MODULE_NAMES_CANDIDATE_COMPONENT", "component": component})
                break
    return hits


# --- verification ---------------------------------------------------------------------------------------------
def _load_evaluator(base: Path) -> Any:
    script = base / EVALUATOR
    _require(script.is_file(), "ADJACENCY_RULING_EVALUATOR_ABSENT", "COLLISION_EVALUATOR_PRESENT_ON_BASE",
             f"run on a predecessor tree that carries {EVALUATOR}")
    spec = importlib.util.spec_from_file_location("adjacency_ruling_overlap_evaluator", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _observed_record(base: Path, task_id: str) -> dict[str, Any]:
    path = base / RECORDS / f"{task_id}.json"
    _require(path.is_file(), "ADJACENCY_RULING_CANDIDATE_NOT_OBSERVED", "CANDIDATE_RECORD_OBSERVED_ON_BASE",
             f"{task_id} must have an observed record at {RECORDS}/{task_id}.json on the predecessor tree")
    return json.loads(path.read_text(encoding="utf-8"))


def _git_head(root: Path) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                             check=False, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _acceptance(request: dict[str, Any]) -> str | None:
    scope = ((request.get("sealed_scope") or {}).get("scope") or {})
    return (scope.get("finish_point") or {}).get("acceptance_test")


def verify(ruling: Any, request: dict[str, Any], base: Path, finish_point_root: Path | None,
           checkin_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """ALLOW receipt, or a six-field FAIL_CLOSED receipt. Never raises for a bad ruling."""
    body: dict[str, Any] = {"schema": RECEIPT_SCHEMA, "authority_effect": "NONE_REGISTRATION_ONLY",
                            "clock_read": False, "network_used": False, "llm_used": False, "lowest_supported_mode": "E0"}
    try:
        body.update(_verify(ruling, request, base, finish_point_root, checkin_rows))
        body["disposition"] = "ALLOW"
    except RulingRefusal as refusal:
        body.update(refusal.six())
    return body


def _verify(ruling: Any, request: dict[str, Any], base: Path, finish_point_root: Path | None,
            checkin_rows: list[dict[str, Any]] | None) -> dict[str, Any]:
    _require(isinstance(ruling, dict) and all(k in ruling for k in REQUIRED) and ruling.get("schema") == SCHEMA,
             "ADJACENCY_RULING_SCHEMA_INVALID", "ADJACENCY_RULING_IS_WELL_FORMED",
             f"a {SCHEMA} object with {', '.join(REQUIRED)}")
    record = request.get("record") or {}
    task_id = request.get("task_id")
    _require(ruling["task_id"] == task_id == record.get("task_id"), "ADJACENCY_RULING_SUBJECT_MISMATCH",
             "RULING_NAMES_THE_REQUESTED_TASK", "the ruling's task_id must be the request's task_id")
    _require(ruling["ruling_class"] == "D" and ruling["ruling"] == "ADJACENT_NOT_DUPLICATE",
             "ADJACENCY_RULING_NOT_CLASS_D_ADJACENT", "RULING_IS_CLASS_D_ADJACENT_NOT_DUPLICATE",
             "only a class D ADJACENT_NOT_DUPLICATE ruling is an input here; a duplicate folds into the existing Goal")
    digest = ruling_digest(ruling)
    _require(ruling["evidence_digest"] == digest, "ADJACENCY_RULING_DIGEST_MISMATCH", "RULING_EVIDENCE_DIGEST_MATCHES",
             f"evidence_digest must be {digest} (python scripts/adjacency_ruling.py digest --ruling <file>)")
    subject = ruling["subject"] if isinstance(ruling["subject"], dict) else {}
    fp = subject.get("finish_point") if isinstance(subject.get("finish_point"), dict) else {}
    sealed_test = _acceptance(request)
    _require(bool(sealed_test) and fp.get("acceptance_test") == sealed_test, "ADJACENCY_RULING_FINISH_POINT_DIVERGES",
             "RULING_FINISH_POINT_IS_THE_SEALED_ONE",
             "subject.finish_point.acceptance_test must equal the request's sealed_scope finish_point.acceptance_test")
    repository, _, rest = sealed_test.partition(":")
    test_rel = rest.split("::")[0]
    _require(ADDRESSABLE.match(sealed_test) is not None, "ADJACENCY_RULING_FINISH_POINT_NOT_ADDRESSABLE",
             "FINISH_POINT_ACCEPTANCE_TEST_IS_ONE_ADDRESSABLE_TEST_FILE",
             "the sealed acceptance_test must read '<org>/<repo>:<path/to/test.py>[::<Class>::<test>]' so condition (b) "
             "can be recomputed from that one file (a new sealed_scope before apply; nothing is applied yet)",
             sealed_test[:300])
    _require(fp.get("repository") == repository and isinstance(fp.get("source_commit"), str)
             and len(fp["source_commit"]) == 40, "ADJACENCY_RULING_SCHEMA_INVALID", "RULING_PINS_FINISH_POINT_SOURCE",
             "subject.finish_point names the repository of the acceptance test and its full 40-hex source_commit")
    observed_subject = sorted((record.get("targets") or {}).get("components") or [])
    _require(sorted(subject.get("components") or []) == observed_subject, "ADJACENCY_RULING_COMPONENTS_DIVERGE",
             "RULING_COMPONENTS_EQUAL_OBSERVED", "subject.components must equal the request record's components",
             {"ruling": sorted(subject.get("components") or []), "observed": observed_subject})

    candidates = ruling["candidates"] if isinstance(ruling["candidates"], list) else []
    cand_ids = [c.get("task_id") for c in candidates if isinstance(c, dict)]
    _require(bool(cand_ids) and len(set(cand_ids)) == len(cand_ids) and task_id not in cand_ids,
             "ADJACENCY_RULING_SCHEMA_INVALID", "RULING_NAMES_DISTINCT_CANDIDATES", "list each candidate Goal once")
    if checkin_rows is not None:
        for row in checkin_rows:
            evidence = row.get("evidence") or {}
            _require(row.get("task_id") == task_id, "ADJACENCY_RULING_DOES_NOT_COVER_CHECKIN",
                     "CHECKIN_FAILURE_IS_THE_RULED_TASK", "a ruling clears only its own task's check-in row", row)
            _require(row.get("head_disposition") == "COORDINATE_CONVERGENCE"
                     and not evidence.get("hard_collision_task_ids") and not evidence.get("new_hard_collision_task_ids"),
                     "ADJACENCY_RULING_CANNOT_CLEAR_HARD_COLLISION", "CHECKIN_IS_COORDINATE_CONVERGENCE_ONLY",
                     "a STOP_COLLISION is never cleared by a ruling; resolve it with the collision owner", row)
            missing = sorted(set(evidence.get("collision_candidate_ids") or []) - set(cand_ids))
            _require(not missing, "ADJACENCY_RULING_DOES_NOT_COVER_CHECKIN", "RULING_COVERS_EVERY_CHECKIN_CANDIDATE",
                     f"the ruling must cover every check-in candidate; missing {missing}", missing)

    evaluator = _load_evaluator(base)
    if finish_point_root is None or not finish_point_root.is_dir():
        raise RulingRefusal("ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE", "FINISH_POINT_SOURCE_AT_PINNED_COMMIT",
                            f"supply --finish-point-root: a checkout of {repository} at {fp['source_commit']}")
    head = _git_head(finish_point_root)
    _require(head == fp["source_commit"], "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE",
             "FINISH_POINT_SOURCE_AT_PINNED_COMMIT",
             f"the finish-point root must be {repository} checked out at {fp['source_commit']}", {"observed_head": head})
    closure = static_closure(finish_point_root, test_rel)

    rows = []
    for cand in candidates:
        cid = cand["task_id"]
        observed = _observed_record(base, cid)
        comps = sorted((observed.get("targets") or {}).get("components") or [])
        _require(sorted(cand.get("components") or []) == comps, "ADJACENCY_RULING_COMPONENTS_DIVERGE",
                 "RULING_COMPONENTS_EQUAL_OBSERVED", f"candidates[{cid}].components must equal its observed record",
                 {"ruling": sorted(cand.get("components") or []), "observed": comps})
        footprint = sorted(_footprint(observed, repository))
        listed = cand.get("finish_point_paths")
        _require(isinstance(listed, list), "ADJACENCY_RULING_SCHEMA_INVALID", "RULING_LISTS_FINISH_POINT_PATHS",
                 f"candidates[{cid}].finish_point_paths must list the paths it relies on (may be empty)")
        repos, shared, lineage, adjacent, substrates, conflicts, _shareable = evaluator.overlap(record, observed, None)
        a_ok = not shared and not lineage and not substrates and not conflicts and not (set(observed_subject) & set(comps))
        _require(a_ok, "ADJACENCY_CONDITION_A_NOT_HELD", "COMPONENTS_DISJOINT_RECOMPUTED",
                 f"{task_id} and {cid} overlap beyond adjacency; this is a duplicate - fold the overlap into {cid}",
                 {"components": shared, "lineage": lineage, "execution_substrates": substrates,
                  "user_action_surface_conflicts": conflicts})
        hits = touches(closure, observed, repository)
        _require(not hits, "ADJACENCY_CONDITION_B_NOT_HELD", "FINISH_POINT_TEST_TOUCHES_NO_CANDIDATE_COMPONENT_RECOMPUTED",
                 f"the finish-point test reaches {cid}'s components; this is a duplicate - fold the overlap into {cid}",
                 hits)
        rows.append({"task_id": cid, "components": comps, "footprint_in_finish_point_repository": footprint,
                     "overlap": {"repositories": repos, "components": shared, "lineage": lineage, "adjacent": adjacent,
                                 "execution_substrates": substrates, "user_action_surface_conflicts": conflicts},
                     "condition_a": "HELD", "condition_b": "HELD"})

    deps = {d.get("ref") for d in record.get("dependencies") or [] if isinstance(d, dict) and d.get("kind") == "TASK"}
    consumes = ruling["consumes_dependencies"] if isinstance(ruling["consumes_dependencies"], list) else None
    _require(consumes is not None, "ADJACENCY_RULING_SCHEMA_INVALID", "RULING_LISTS_CONSUMES_DEPENDENCIES",
             "consumes_dependencies must be a list (may be empty)")
    for dep in consumes:
        did = dep.get("task_id") if isinstance(dep, dict) else None
        _require(did in cand_ids and did in deps, "ADJACENCY_CONDITION_C_NOT_HELD",
                 "CONSUMES_DEPENDENCY_RECORDED_ON_SUBJECT",
                 f"{did} must be a ruled candidate and a TASK dependency of {task_id}'s record", dep)
    return {"task_id": task_id, "ruling_digest": digest, "ruled_by": ruling["ruled_by"],
            "finish_point": {"repository": repository, "source_commit": head, "test": test_rel,
                             "closure": closure, "closure_digest": sha(canon(closure))},
            "candidates": rows, "consumes_dependencies": consumes, "condition_c": "HELD",
            "clears": "COORDINATE_CONVERGENCE"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("digest")
    d.add_argument("--ruling", required=True, type=Path)
    v = sub.add_parser("verify")
    v.add_argument("--ruling", required=True, type=Path)
    v.add_argument("--request", required=True, type=Path)
    v.add_argument("--base", type=Path, default=ROOT)
    v.add_argument("--finish-point-root", type=Path)
    v.add_argument("--receipt-out", type=Path)
    args = parser.parse_args(argv)
    ruling = json.loads(args.ruling.read_text(encoding="utf-8"))
    if args.cmd == "digest":
        print(ruling_digest(ruling))
        return 0
    request = json.loads(args.request.read_text(encoding="utf-8"))
    body = verify(ruling, request, args.base.resolve(), args.finish_point_root.resolve() if args.finish_point_root else None)
    text = json.dumps(body, indent=2, sort_keys=True) + "\n"
    if args.receipt_out:
        args.receipt_out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if body["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
