#!/usr/bin/env python3
"""Callable test sets: a manifest, a diff-driven selector, and the inputs each set needs (E0, stdlib only).

StegVerse-org/.github#166. Rigel's rule (relayed by Coordination, Oct 23): every selected test runs on the exact
head with 0 skipped, and the skip rule never stops unrelated work. So a repository's suite is split into callable
test sets, each declaring the paths it verifies (its surfaces) and the inputs it needs, and a pull request runs:

  * the core set, always;
  * every set one of whose surfaces a diff path matches - the receipt names the path and the surface;
  * EVERY set when selection cannot be shown complete: the diff is unavailable, a diff path matches no surface,
    a path that shapes selection itself changed (the spec, the manifest, a shared fixture), or the committed
    manifest is not what the spec generates at this head.

A set that is not selected is not run and is not reported as skipped: the receipt counts it, nothing more. A selected
set whose input is unavailable is not run either; it gets a six-field REQUIRED_VERIFICATION_INPUT_UNAVAILABLE item
routed to that input's owner, which blocks this change (and only changes that select the set). A skip inside a
selected set is REQUIRED_VERIFICATION_SKIPPED (scripts/test_suite_baseline_drift.py adjudicates the run).

  generate  --spec .stegverse/test-set-spec.json            -> the manifest (sets, surfaces, inputs), deterministic
  select    --manifest .stegverse/test-sets.json --base B --head H --out selection.json
  set       --manifest ... --id ID                          -> one set's runnable test arguments ("callable")

Surfaces are found statically and conservatively: the test file, every repository path a string literal or a
`ROOT / "a" / "b"` chain names, and the local modules it imports, closed transitively over the Python files found.
A path the analysis cannot attribute to any set selects every set, so an incomplete analysis widens, never narrows.
No clock, no network, nothing published; the selection is sealed (receipt_sha256 over canonical JSON).
"""
from __future__ import annotations

import argparse
import ast
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

SPEC_SCHEMA = "stegverse.test-set-spec/v1"
MANIFEST_SCHEMA = "stegverse.test-sets/v1"
SELECTION_SCHEMA = "stegverse.test-set-selection/v1"
SEAL = "receipt_sha256"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
RVS = "REQUIRED_VERIFICATION_SKIPPED"
INPUT_UNAVAILABLE = "REQUIRED_VERIFICATION_INPUT_UNAVAILABLE"
DEFAULT_GOAL = "StegVerse-org/.github#166 ENTERPRISE-HOST-PROVIDER-ERADICATION-001"
PATHLIKE = re.compile(r"^[A-Za-z0-9_.@+-][A-Za-z0-9_.@+/-]*$")
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def seal(body: Mapping[str, Any]) -> dict:
    clean = {k: v for k, v in body.items() if k != SEAL}
    return {**clean, SEAL: "sha256:" + hashlib.sha256(canonical(clean)).hexdigest()}


def seal_verifies(record: Mapping[str, Any]) -> bool:
    return isinstance(record, Mapping) and seal(record).get(SEAL) == record.get(SEAL)


def six(code: str, predicate: str, repair: str, retry: str, goal: str, nxt: str, **detail: Any) -> dict:
    return {"failure_code": code, "failed_predicate": predicate, "required_evidence_or_repair": repair,
            "retry_entrypoint": retry, "owning_existing_goal": goal, "next_attempt": nxt, **detail}


def glob_match(pattern: str, path: str) -> bool:
    """`dir/**` matches everything under dir; otherwise fnmatch on the whole path (`*` may cross `/`)."""
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-2])
    return path == pattern or fnmatch.fnmatchcase(path, pattern)


# -- static surfaces -----------------------------------------------------------------------------------------

def repo_files(root: Path) -> set[str]:
    done = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root, capture_output=True, text=True)
    if done.returncode == 0:
        return {p for p in done.stdout.split("\0") if p}
    out = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            out.add(str(Path(dirpath, f).relative_to(root)))
    return out


def _chain(node: ast.AST) -> list[str] | None:
    """`X / "a" / "b"` -> ["a", "b"] (the string parts at the right of a `/` chain)."""
    parts: list[str] = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
            parts.insert(0, node.right.value)
        else:
            return parts or None
        node = node.left
    return parts or None


class Surfaces:
    """Per-file direct references, closed transitively over local Python files."""

    def __init__(self, root: Path, files: set[str], search_dirs: Iterable[str]):
        self.root, self.files = root, files
        self.dirs = {str(Path(f).parent) for f in files}
        self.search = ["."] + sorted(search_dirs)
        self._direct: dict[str, set[str]] = {}

    def _resolve(self, text: str) -> set[str]:
        text = text.strip()
        text = text[2:] if text.startswith("./") else text
        if not text or not PATHLIKE.match(text) or text in (".", "..") or ".." in text.split("/"):
            return set()
        text = text.rstrip("/")
        if text in self.files:
            return {text}
        if text in self.dirs and "/" in text:      # a named sub-directory (a top-level one is an import root)
            return {text + "/**"}
        return set()

    def _module(self, name: str, here: str) -> set[str]:
        rel = name.replace(".", "/")
        out = set()
        for base in [str(Path(here).parent)] + self.search:
            for cand in (f"{rel}.py", f"{rel}/__init__.py"):
                p = os.path.normpath(os.path.join(base, cand))
                if p in self.files:
                    out.add(p)
        return out

    def direct(self, path: str) -> set[str]:
        if path in self._direct:
            return self._direct[path]
        refs: set[str] = set()
        try:
            tree = ast.parse((self.root / path).read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
            self._direct[path] = refs
            return refs
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) < 300:
                for token in node.value.split():
                    refs |= self._resolve(token.strip("`'\",;:()[]"))
            elif isinstance(node, ast.BinOp):
                parts = _chain(node)
                if parts:
                    refs |= self._resolve("/".join(parts))
            elif isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "join":
                parts = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                if parts:
                    refs |= self._resolve("/".join(parts))
            elif isinstance(node, ast.Import):
                for a in node.names:
                    refs |= self._module(a.name, path)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                refs |= self._module(node.module, path)
                for a in node.names:
                    refs |= self._module(f"{node.module}.{a.name}", path)
        refs.discard(path)
        self._direct[path] = refs
        return refs

    def closure(self, start: str) -> list[str]:
        seen, todo = {start}, [start]
        while todo:
            cur = todo.pop()
            for ref in self.direct(cur):
                if ref not in seen:
                    seen.add(ref)
                    if ref.endswith(".py"):
                        todo.append(ref)
        return sorted(seen)


# -- the manifest --------------------------------------------------------------------------------------------

def test_files(root: Path, files: set[str], globs: list[str]) -> list[str]:
    return sorted(f for f in files if any(glob_match(g, f) for g in globs) and Path(f).name.startswith("test_")
                  and f.endswith(".py"))


def unittest_names(root: Path, path: str) -> dict[str, list[str]]:
    """{Class: [test methods, own and inherited from classes of the same module]} for the TestCase-style classes
    of a module that hold at least one test, read statically. A base class with no test of its own or inherited
    (a fixture base) and a mixin that is not a TestCase are not runnable units and are not listed."""
    out: dict[str, list[str]] = {}
    try:
        tree = ast.parse((root / path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return out
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

    def methods(name: str, seen: frozenset = frozenset()) -> list[str]:
        node = classes[name]
        own = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name.startswith("test")]
        inherited = [m for b in node.bases if isinstance(b, ast.Name) and b.id in classes and b.id not in seen
                     for m in methods(b.id, seen | {name})]
        return own + [m for m in dict.fromkeys(inherited) if m not in own]

    def is_case(name: str, seen: frozenset = frozenset()) -> bool:
        return any(getattr(b, "attr", getattr(b, "id", "")).endswith("TestCase") or
                   (isinstance(b, ast.Name) and b.id in classes and b.id not in seen and is_case(b.id, seen | {name}))
                   for b in classes[name].bases)

    for name in classes:
        names = methods(name)
        if names and is_case(name):
            out[name] = names
    return out


def dotted(path: str) -> str:
    return path[:-3].replace("/", ".")


def generate(root: Path, spec: Mapping[str, Any], spec_path: str) -> dict:
    root = Path(root)
    files = repo_files(root)
    runner = spec["runner"]
    surf = Surfaces(root, files, spec.get("import_roots", []))
    core_files = sorted(spec["core"]["tests"])
    splits: dict[str, list[dict]] = {}
    for s in spec.get("splits", []):
        splits.setdefault(s["file"], []).append(s)
    sets: list[dict] = []
    core_surfaces: set[str] = set(spec["core"].get("surfaces", [])) | set(core_files)
    sets.append({"id": "core", "always": True, "tests": [f if runner == "pytest" else dotted(f) for f in core_files],
                 "exclude": [], "inputs": sorted(spec["core"].get("inputs", [])), "surfaces": sorted(core_surfaces)})
    for f in test_files(root, files, spec["test_globs"]):
        if f in core_files:
            continue
        closure = sorted({f} | set(spec.get("extra_surfaces", {}).get(f, [])))
        module_inputs = sorted(spec.get("module_inputs", {}).get(f, []))
        carved = splits.get(f, [])
        if runner == "pytest":
            carved_nodes = sorted(n for s in carved for n in s["tests"])
            sets.append({"id": f, "always": False, "tests": [f], "exclude": carved_nodes, "inputs": module_inputs,
                         "surfaces": closure})
        else:
            if carved:
                names = unittest_names(root, f)
                taken = {n for s in carved for n in s["tests"]}
                rest = []
                for cls, methods in sorted(names.items()):
                    cid = f"{dotted(f)}.{cls}"
                    if cid in taken:
                        continue
                    picked = [m for m in methods if f"{cid}.{m}" in taken]
                    rest += [f"{cid}.{m}" for m in methods if m not in picked] if picked else [cid]
                tests = rest
            else:
                tests = [dotted(f)]
            if tests:
                sets.append({"id": f, "always": False, "tests": tests, "exclude": [], "inputs": module_inputs,
                             "surfaces": closure})
        for s in carved:
            sets.append({"id": s["id"], "always": False, "tests": sorted(s["tests"]), "exclude": [],
                         "inputs": sorted(set(module_inputs) | set(s["inputs"])), "surfaces": closure})
    graph: dict[str, list[str]] = {}
    todo = sorted({g for st in sets for g in st["surfaces"] if g.endswith(".py")})
    while todo:
        cur = todo.pop()
        if cur in graph:
            continue
        graph[cur] = sorted(surf.direct(cur))
        todo += [r for r in graph[cur] if r.endswith(".py") and r not in graph]
    graph = {k: v for k, v in sorted(graph.items()) if v}
    spec_bytes = (root / spec_path).read_bytes()
    return {"schema": MANIFEST_SCHEMA, "runner": runner, "repository": spec["repository"],
            "generated_from": {"spec": spec_path, "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
                               "generator": "scripts/test_set_selection.py (StegVerse-Labs/.github)"},
            "selects_all": sorted(set(spec.get("selects_all", [])) | {spec_path, spec["manifest"]}),
            "inputs": spec.get("inputs", {}), "sets": sets, "surface_graph": graph,
            "surface_rule": "a set verifies its surfaces and everything they reach in surface_graph (a file's direct "
                            "repository references: string-literal paths, path chains, local imports)",
            "authority_effect": "NONE"}


def closure(graph: Mapping[str, list[str]], roots: Iterable[str]) -> dict[str, str]:
    """{reached path or glob: the root it was reached from}."""
    seen: dict[str, str] = {}
    for r in sorted(roots):
        todo = [r]
        while todo:
            cur = todo.pop()
            if cur in seen:
                continue
            seen[cur] = r
            todo += graph.get(cur, [])
    return seen


# -- inputs --------------------------------------------------------------------------------------------------

def input_available(root: Path, decl: Mapping[str, Any], python: str, env: Mapping[str, str]) -> tuple[bool, str]:
    check = decl.get("check", {})
    kind = check.get("kind")
    if kind == "python_module":
        code = "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec(sys.argv[1]) else 1)"
        ok = subprocess.run([python, "-c", code, check["module"]], cwd=root, capture_output=True).returncode == 0
        return ok, f"python module {check['module']!r} {'importable' if ok else 'not importable'} by {python}"
    if kind == "env_path":
        value = env.get(check["env"], "")
        ok = bool(value) and Path(value).exists()
        return ok, f"{check['env']}={'set to an existing path' if ok else 'unset or not an existing path'}"
    if kind == "git_ref":
        where = Path(env.get(check["env"], "")) if check.get("env") else root
        if check.get("env") and not (env.get(check["env"]) and where.exists()):
            return False, f"{check['env']} unset or not an existing path"
        ok = subprocess.run(["git", "rev-parse", "--verify", "--quiet", check["ref"] + "^{commit}"], cwd=where,
                            capture_output=True).returncode == 0
        if ok and check.get("contains"):
            ok = subprocess.run(["git", "merge-base", "--is-ancestor", check["contains"], check["ref"]], cwd=where,
                                capture_output=True).returncode == 0
        return ok, f"{check['ref']} {'present' if ok else 'absent'}" + (
            f" (must contain {check['contains'][:12]})" if check.get("contains") else "")
    if kind == "unavailable":
        return False, check.get("reason", "declared unavailable")
    return False, f"unknown input check {kind!r}: an input that cannot be checked is unavailable"


# -- selection -----------------------------------------------------------------------------------------------

def resolve(root: Path, rev: str | None) -> str | None:
    """The exact commit a revision names here, or None."""
    if not rev:
        return None
    done = subprocess.run(["git", "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"], cwd=root,
                          capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else None


def parents(root: Path, sha: str | None) -> list[str]:
    if not sha:
        return []
    done = subprocess.run(["git", "rev-list", "--parents", "-n", "1", sha], cwd=root, capture_output=True, text=True)
    return done.stdout.split()[1:] if done.returncode == 0 else []


def changed(root: Path, base: str, head: str) -> list[str] | None:
    done = subprocess.run(["git", "diff", "--name-only", "--no-renames", f"{base}...{head}"], cwd=root,
                          capture_output=True, text=True)
    if done.returncode != 0:
        return None
    return sorted(p for p in done.stdout.splitlines() if p)


def select(root: Path, manifest: Mapping[str, Any], diff: list[str] | None, *, manifest_path: str,
           spec: Mapping[str, Any] | None, spec_path: str | None, base: str | None, head: str | None,
           python: str = sys.executable, env: Mapping[str, str] | None = None, retry: str = "",
           goal: str = DEFAULT_GOAL, pr_head: str | None = None) -> dict:
    env = os.environ if env is None else env
    nxt = "the next run of this job at the exact head"
    rows: list[dict] = []
    # The record binds the exact commits it was computed for: the head the suite runs on (for a pull request,
    # GitHub's merge ref), its parents, the base, and the pull request head the merge ref was built from.
    head_sha = resolve(root, head or "HEAD")
    base_sha = resolve(root, base)
    head_parents = parents(root, head_sha)
    if head_sha is None:
        rows.append(six("TEST_SET_SELECTION_HEAD_UNRESOLVED", "SELECTION_IS_BOUND_TO_AN_EXACT_HEAD_COMMIT",
                        f"--head {head or 'HEAD'} names no commit in this checkout; select on the exact head",
                        retry, goal, nxt, blocking=True))
    if base and base_sha is None:
        rows.append(six("TEST_SET_SELECTION_BASE_UNRESOLVED", "SELECTION_IS_BOUND_TO_AN_EXACT_BASE_COMMIT",
                        f"--base {base} names no commit in this checkout; fetch the base (fetch-depth: 0)",
                        retry, goal, nxt, blocking=True))
    if pr_head is not None and head_sha is not None and pr_head not in ([head_sha] + head_parents[1:]):
        rows.append(six("TEST_SET_SELECTION_HEAD_IS_NOT_THE_PULL_REQUEST_HEAD",
                        "SELECTION_HEAD_IS_THE_PULL_REQUEST_HEAD_OR_ITS_MERGE_REF",
                        f"the selected head {head_sha} is neither the pull request head {pr_head} nor a merge ref "
                        "built from it; check out the exact pull request head or its merge ref", retry, goal, nxt,
                        blocking=True))
    all_reasons: list[dict] = []
    fresh = None
    if spec is not None and spec_path:
        regenerated = generate(root, spec, spec_path)
        fresh = canonical(regenerated) == canonical(manifest)
        if not fresh:
            all_reasons.append({"reason": "MANIFEST_NOT_GENERATED_FROM_SPEC", "detail": f"{manifest_path} is not "
                                "what the spec generates at this head"})
            rows.append(six("TEST_SET_MANIFEST_STALE", "MANIFEST_IS_GENERATED_FROM_THE_SPEC_AT_THIS_HEAD",
                            f"regenerate it: python3 scripts/test_set_selection.py generate --spec {spec_path} "
                            f"--out {manifest_path}, and commit the result", retry, goal, nxt, blocking=True))
            manifest = regenerated
    sets = manifest["sets"]
    listed = {t for s in sets for t in s["tests"]}
    selected: dict[str, list[dict]] = {s["id"]: [{"reason": "ALWAYS_RUN_CORE"}] for s in sets if s.get("always")}
    unmapped: list[str] = []
    graph = manifest.get("surface_graph", {})
    reached: dict[str, dict[str, str]] = {}
    if diff is None:
        all_reasons.append({"reason": "DIFF_UNAVAILABLE", "detail": f"git diff {base}...{head} could not be read"})
    else:
        for p in diff:
            hit = [g for g in manifest.get("selects_all", []) if glob_match(g, p)]
            if hit:
                all_reasons.append({"reason": "PATH_SHAPES_SELECTION", "path": p, "surface": hit[0]})
                continue
            matched = False
            for s in sets:
                reach = reached.setdefault(s["id"], closure(graph, s["surfaces"]))
                g = p if p in reach else next((g for g in reach if g.endswith("/**") and glob_match(g, p)), None)
                if g:
                    matched = True
                    selected.setdefault(s["id"], []).append({"reason": "DIFF_PATH_MATCHES_SURFACE", "path": p,
                                                             "surface": g, "declared_surface": reach[g]})
            if not matched:
                unmapped.append(p)
                all_reasons.append({"reason": "DIFF_PATH_MAPS_TO_NO_SET", "path": p})
    mode = "ALL" if all_reasons else "DIFF"
    if mode == "ALL":
        for s in sets:
            selected.setdefault(s["id"], []).append({"reason": "ALL_SETS_SELECTED"})
    decls = manifest.get("inputs", {})
    status: dict[str, tuple[bool, str]] = {}
    out_sets: list[dict] = []
    run_tests: list[str] = []
    excludes: set[str] = set()
    included: set[str] = set()
    unavailable: list[dict] = []
    for s in sets:
        if s["id"] not in selected:
            continue
        inputs = []
        for name in s["inputs"]:
            if name not in status:
                decl = decls.get(name)
                status[name] = input_available(root, decl, python, env) if decl else \
                    (False, f"input {name!r} is not declared in the manifest")
            inputs.append({"id": name, "available": status[name][0], "detail": status[name][1]})
        runnable = all(i["available"] for i in inputs)
        out_sets.append({"id": s["id"], "reasons": selected[s["id"]], "inputs": inputs, "runnable": runnable,
                         "tests": s["tests"]})
        if runnable:
            run_tests += s["tests"]
            included |= set(s["tests"])
            excludes |= set(s.get("exclude", []))
        else:
            for i in inputs:
                if not i["available"]:
                    decl = decls.get(i["id"], {})
                    unavailable.append(six(
                        INPUT_UNAVAILABLE, "SELECTED_TEST_SET_INPUT_IS_AVAILABLE",
                        f"test set {s['id']} is selected by this change and needs input {i['id']} ({i['detail']}); "
                        f"{decl.get('repair', 'supply the input to the job that runs this set')}",
                        retry, decl.get("owner", goal), decl.get("finish_point", nxt),
                        set=s["id"], input=i["id"], tests=s["tests"], blocking=True))
    stale_listing = []
    if spec is not None:
        present = set(test_files(root, repo_files(root), spec["test_globs"]))
        known = {t.split("::")[0] if manifest["runner"] == "pytest" else t for t in listed}
        for f in sorted(present):
            key = f if manifest["runner"] == "pytest" else dotted(f)
            if not any(k == key or k.startswith(key + ".") for k in known):
                stale_listing.append(f)
    body = {"schema": SELECTION_SCHEMA, "repository": manifest.get("repository"), "base": base, "head": head,
            "base_sha": base_sha, "head_sha": head_sha, "head_parents": head_parents, "pr_head_sha": pr_head,
            "runner": manifest["runner"], "lowest_supported_mode": "E0", "derived_from_clock": False,
            "authority_effect": "NONE", "diff_available": diff is not None, "diff": diff,
            "manifest": {"path": manifest_path, "sha256": hashlib.sha256(canonical(manifest)).hexdigest(),
                         "generated_from_spec_at_this_head": fresh},
            "mode": mode, "all_reasons": all_reasons, "unmapped_paths": unmapped,
            "sets_total": len(sets), "selected_count": len(out_sets), "not_selected_count": len(sets) - len(out_sets),
            "not_selected_note": "not selected means not run by this change and not reported as skipped",
            "selected": out_sets,
            "run": {"tests": run_tests, "deselect": sorted(excludes - included)},
            "input_unavailable": unavailable, "rows": rows,
            "unlisted_test_files": stale_listing}
    blocking = rows + unavailable
    body["disposition"] = "FAIL_CLOSED" if blocking else "SELECTED"
    if blocking:
        body.update({k: blocking[0][k] for k in SIX})
    return seal(body)


def run_args(selection: Mapping[str, Any]) -> list[str]:
    """The runner arguments for the runnable selected sets: pytest node/file args plus --deselect, or unittest
    names."""
    args = list(selection["run"]["tests"])
    if selection["runner"] == "pytest":
        for node in selection["run"]["deselect"]:
            args += ["--deselect", node]
    return args


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--root", default=".")
    g.add_argument("--spec", required=True)
    g.add_argument("--out")
    s = sub.add_parser("select")
    s.add_argument("--root", default=".")
    s.add_argument("--manifest", required=True)
    s.add_argument("--spec", help="the spec the manifest is generated from: a stale manifest selects every set")
    s.add_argument("--base")
    s.add_argument("--head", default="HEAD")
    s.add_argument("--pr-head", help="the pull request head sha: the selected head must be it or a merge ref built "
                   "from it (its second parent)")
    s.add_argument("--retry-entrypoint", default="the job that runs this selection")
    s.add_argument("--owning-goal", default=DEFAULT_GOAL)
    s.add_argument("--out", required=True)
    s.add_argument("--args-out", help="write the runner arguments, one per line")
    c = sub.add_parser("set")
    c.add_argument("--root", default=".")
    c.add_argument("--manifest", required=True)
    c.add_argument("--id", required=True)
    a = parser.parse_args(argv)
    root = Path(a.root).resolve()
    if a.command == "generate":
        spec = json.loads((root / a.spec).read_text(encoding="utf-8"))
        if spec.get("schema") != SPEC_SCHEMA:
            raise SystemExit(f"{a.spec}: schema must be {SPEC_SCHEMA}")
        text = json.dumps(generate(root, spec, a.spec), indent=1, sort_keys=True) + "\n"
        if a.out:
            (root / a.out).write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    manifest = json.loads((root / a.manifest).read_text(encoding="utf-8"))
    if a.command == "set":
        hit = [s for s in manifest["sets"] if s["id"] == a.id]
        if not hit:
            raise SystemExit(f"no test set {a.id!r}")
        sel = {"runner": manifest["runner"], "run": {"tests": hit[0]["tests"], "deselect": hit[0]["exclude"]}}
        print("\n".join(run_args(sel)))
        return 0
    spec = json.loads((root / a.spec).read_text(encoding="utf-8")) if a.spec else None
    diff = changed(root, a.base, a.head) if a.base else None
    record = select(root, manifest, diff, manifest_path=a.manifest, spec=spec, spec_path=a.spec, base=a.base,
                    head=a.head, retry=a.retry_entrypoint, goal=a.owning_goal, pr_head=a.pr_head)
    Path(a.out).write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if a.args_out:
        Path(a.args_out).write_text("\n".join(run_args(record)) + "\n", encoding="utf-8")
    print(f"SELECTION head_sha={record['head_sha']} base_sha={record['base_sha']} pr_head_sha={record['pr_head_sha']}")
    print(f"SELECTION mode={record['mode']} selected={record['selected_count']}/{record['sets_total']} "
          f"runnable={sum(1 for x in record['selected'] if x['runnable'])} "
          f"input_unavailable={len(record['input_unavailable'])} {SEAL}={record[SEAL]}")
    for r in record["all_reasons"][:20]:
        print("ALL", json.dumps(r, sort_keys=True))
    for x in record["selected"]:
        if record["mode"] == "DIFF" or not x["runnable"] or x["id"] == "core":
            print(f"SET {x['id']} runnable={x['runnable']} reasons={json.dumps(x['reasons'][:3], sort_keys=True)}")
    for u in record["input_unavailable"] + record["rows"]:
        print(f"FAIL_CLOSED {u['failure_code']} {u.get('set', '')} input={u.get('input', '')} "
              f"owner={u['owning_existing_goal']}")
    return 1 if record["disposition"] == "FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
