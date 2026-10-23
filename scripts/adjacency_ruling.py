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


# --- (b) dynamic loads in the closure: resolved from literals / static constants, or FAIL_CLOSED ---------------
# A static import closure misses modules loaded by name at run time (e.g. a gate that loads
# stegverse.structural_validator_candidate through importlib.import_module(f"stegverse.{name}")). Every by-name
# load in a closure file is detected; its target is resolved only from literals and statically determinable
# constants (module/function constants, constant tables and loops over them, f-strings and path expressions
# over __file__, and the arguments of every call site of a module-private loader function). A load whose target
# cannot be determined fails closed: it is never treated as disjoint.
LOADERS = {  # qualified callee -> (kind, positional index, keyword)
    "importlib.import_module": ("module", 0, "name"),
    "importlib.__import__": ("module", 0, "name"),
    "__import__": ("module", 0, "name"),
    "importlib.util.spec_from_file_location": ("path", 1, "location"),
    "importlib.machinery.SourceFileLoader": ("path", 1, "path"),
    "imp.load_source": ("path", 1, "pathname"),
    "runpy.run_module": ("module", 0, "mod_name"),
    "runpy.run_path": ("path", 0, "path_name"),
    "exec": ("code", 0, "source"),
    "builtins.exec": ("code", 0, "source"),
}
_MAX_DEPTH = 4


class _Unknown(Exception):
    pass


class _Table(tuple):
    """A constant container (tuple/list/set/dict values): subscripting or iterating it yields any member."""


def _qual(node: ast.AST, aliases: dict[str, str]) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    parts.append(aliases.get(node.id, node.id))
    return ".".join(reversed(parts))


def _aliases(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for a in node.names:
                out[a.asname or a.name] = f"{node.module}.{a.name}"
    return out


class _Module:
    def __init__(self, root: Path, path: Path, tree: ast.Module):
        self.root, self.path, self.tree = root, path, tree
        self.aliases = _aliases(tree)
        self.functions: dict[str, ast.AST] = {}
        self.owner: dict[int, ast.AST | None] = {}
        self._index(tree, None)
        self.private_loaders: set[str] = set()

    def _index(self, node: ast.AST, fn: ast.AST | None) -> None:
        for child in ast.iter_child_nodes(node):
            self.owner[id(child)] = fn
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if fn is None:
                    self.functions.setdefault(child.name, child)
                self._index(child, child)
            else:
                self._index(child, fn)

    # value environment ----------------------------------------------------------------------------------------
    def _assigned(self, scope: ast.AST, name: str) -> list[ast.AST] | None:
        """Every expression bound to `name` directly in `scope` (plain assignments, for-loops over an iterable);
        None if the name is bound any other way there (so its value is not statically determinable)."""
        mine = None if scope is self.tree else scope
        found: list[ast.AST] = []
        allowed: set[int] = set()
        for node in ast.walk(scope):
            if self.owner.get(id(node)) is not mine and node is not scope:
                continue
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == name:
                        found.append(node.value)
                        allowed.add(id(t))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name \
                    and node.value is not None:
                found.append(node.value)
                allowed.add(id(node.target))
            elif isinstance(node, (ast.For, ast.comprehension)) and isinstance(node.target, ast.Name) \
                    and node.target.id == name:
                found.append(ast.Starred(value=node.iter))
                allowed.add(id(node.target))
        for node in ast.walk(scope):
            if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, (ast.Store, ast.Del)) \
                    and id(node) not in allowed and (self.owner.get(id(node)) is mine):
                return None
            if isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names:
                return None
        return found

    def name_values(self, name: str, fn: ast.AST | None, depth: int) -> set:
        if name == "__file__":
            return {self.path}
        if name == "__name__":
            return {".".join(self.path.relative_to(self.root).with_suffix("").parts)}
        if fn is not None:
            args = fn.args
            params = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
            if name in params:
                return self.param_values(fn, name, depth)
            bound = self._assigned(fn, name)
            if bound is None:
                raise _Unknown(f"{name} is not bound to a static constant")
            if bound:
                return self._union(bound, fn, depth)
        bound = self._assigned(self.tree, name)
        if not bound:
            raise _Unknown(f"{name} is not bound to a static constant")
        return self._union(bound, None, depth)

    def _union(self, exprs: list[ast.AST], fn: ast.AST | None, depth: int) -> set:
        out: set = set()
        for e in exprs:
            if isinstance(e, ast.Starred):
                out |= self.members(e.value, fn, depth)
            else:
                out |= self.values(e, fn, depth)
        return out

    def members(self, expr: ast.AST, fn: ast.AST | None, depth: int) -> set:
        out: set = set()
        for v in self.values(expr, fn, depth):
            if not isinstance(v, _Table):
                raise _Unknown("iteration over a non-constant")
            out |= set(v)
        return out

    def param_values(self, fn: ast.AST, name: str, depth: int) -> set:
        """Values a module-private function's parameter takes at every call site in this module."""
        if depth >= _MAX_DEPTH or not fn.name.startswith("_") or self.owner.get(id(fn)) is not None:
            raise _Unknown(f"parameter {name} of {getattr(fn, 'name', '?')}")
        args = fn.args
        positional = [a.arg for a in args.posonlyargs + args.args]
        defaults = dict(zip(positional[len(positional) - len(args.defaults):], args.defaults))
        defaults.update({a.arg: d for a, d in zip(args.kwonlyargs, args.kw_defaults) if d is not None})
        out: set = set()
        calls = 0
        callees = {id(c.func) for c in ast.walk(self.tree) if isinstance(c, ast.Call)}
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name) and node.id == fn.name and id(node) not in callees:
                raise _Unknown(f"{fn.name} is referenced, not only called")
        for call in [c for c in ast.walk(self.tree) if isinstance(c, ast.Call)
                     and isinstance(c.func, ast.Name) and c.func.id == fn.name]:
            calls += 1
            if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
                raise _Unknown(f"*args/**kwargs call of {fn.name}")
            caller = self.owner.get(id(call))
            expr = None
            if name in positional and positional.index(name) < len(call.args):
                expr = call.args[positional.index(name)]
            for k in call.keywords:
                if k.arg == name:
                    expr = k.value
            if expr is None:
                expr = defaults.get(name)
            if expr is None:
                raise _Unknown(f"no value for {name}")
            out |= self.values(expr, caller, depth + 1)
        if not calls:
            raise _Unknown(f"{fn.name} has no call site in its module")
        self.private_loaders.add(fn.name)
        return out

    def values(self, e: ast.AST, fn: ast.AST | None, depth: int = 0) -> set:
        if isinstance(e, ast.Constant) and isinstance(e.value, (str, int)) and not isinstance(e.value, bool):
            return {e.value}
        if isinstance(e, ast.Name):
            return self.name_values(e.id, fn, depth)
        if isinstance(e, (ast.Tuple, ast.List, ast.Set)):
            return {_Table(v for x in e.elts for v in self.values(x, fn, depth))}
        if isinstance(e, ast.Dict):
            return {_Table(v for x in e.values for v in self.values(x, fn, depth))}
        if isinstance(e, ast.JoinedStr):
            acc = {""}
            for part in e.values:
                if isinstance(part, ast.FormattedValue):
                    if part.format_spec is not None or part.conversion not in (-1, 115):
                        raise _Unknown("formatted value")
                    vals = {str(v) for v in self.values(part.value, fn, depth) if isinstance(v, (str, int, Path))}
                else:
                    vals = self.values(part, fn, depth)
                acc = {a + str(b) for a in acc for b in vals}
            return acc
        if isinstance(e, ast.BinOp) and isinstance(e.op, (ast.Add, ast.Div)):
            left, right = self.values(e.left, fn, depth), self.values(e.right, fn, depth)
            out = set()
            for a in left:
                for b in right:
                    if isinstance(e.op, ast.Add) and isinstance(a, str) and isinstance(b, str):
                        out.add(a + b)
                    elif isinstance(e.op, ast.Div) and isinstance(a, Path) and isinstance(b, (str, Path)):
                        out.add(a / b)
                    else:
                        raise _Unknown("operand types")
            return out
        if isinstance(e, ast.Subscript):
            if isinstance(e.value, ast.Attribute) and e.value.attr == "parents":
                paths = self._paths(e.value.value, fn, depth)
                return {p.parents[i] for p in paths for i in self.values(e.slice, fn, depth) if isinstance(i, int)}
            base = self.values(e.value, fn, depth)
            out = set()
            for b in base:
                if isinstance(b, _Table):
                    out |= set(b)
                else:
                    raise _Unknown("subscript")
            return out
        if isinstance(e, ast.Attribute):
            if e.attr == "parent":
                return {p.parent for p in self._paths(e.value, fn, depth)}
            raise _Unknown(f"attribute {e.attr}")
        if isinstance(e, ast.Call):
            return self._call_values(e, fn, depth)
        raise _Unknown(type(e).__name__)

    def _paths(self, e: ast.AST, fn: ast.AST | None, depth: int) -> set[Path]:
        vals = self.values(e, fn, depth)
        if not all(isinstance(v, Path) for v in vals):
            raise _Unknown("not a path")
        return vals

    def _call_values(self, e: ast.Call, fn: ast.AST | None, depth: int) -> set:
        q = _qual(e.func, self.aliases)
        args = e.args
        if q in ("pathlib.Path", "pathlib.PurePath", "pathlib.PosixPath", "Path") and len(args) >= 1:
            acc: set = {None}
            for a in args:
                vals = self.values(a, fn, depth)
                acc = {(Path(v) if x is None else x / v) for x in acc for v in vals if isinstance(v, (str, Path))}
            return acc
        if q in ("str", "os.fspath") and len(args) == 1:
            return {str(v) for v in self.values(args[0], fn, depth)}
        if q == "os.path.join" and args:
            acc = {Path(v) for v in self.values(args[0], fn, depth)}
            for a in args[1:]:
                acc = {x / v for x in acc for v in self.values(a, fn, depth)}
            return {str(p) for p in acc}
        if q in ("os.path.dirname", "os.path.abspath", "os.path.realpath") and len(args) == 1:
            vals = {Path(v) for v in self.values(args[0], fn, depth)}
            return {str(p.parent) if q.endswith("dirname") else str(p) for p in vals}
        if isinstance(e.func, ast.Attribute):
            method, target = e.func.attr, e.func.value
            if method in ("resolve", "absolute", "expanduser") and not args:
                return self._paths(target, fn, depth)
            if method == "with_name" and len(args) == 1:
                return {p.with_name(str(v)) for p in self._paths(target, fn, depth) for v in self.values(args[0], fn, depth)}
            if method == "joinpath":
                acc = self._paths(target, fn, depth)
                for a in args:
                    acc = {p / str(v) for p in acc for v in self.values(a, fn, depth)}
                return acc
            if method in ("read_text", "read_bytes", "read") and not args:
                return {_Source(p) for p in self._file_refs(target, fn, depth)}
        raise _Unknown(f"call {q}")

    def _file_refs(self, e: ast.AST, fn: ast.AST | None, depth: int) -> set[Path]:
        if isinstance(e, ast.Call) and _qual(e.func, self.aliases) in ("open", "io.open") and e.args:
            return {Path(str(v)) for v in self.values(e.args[0], fn, depth)}
        return {Path(str(v)) for v in self.values(e, fn, depth)}


class _Source(str):
    """The text of a file (open(p).read(), Path(p).read_text()) - an exec of it loads that file."""
    def __new__(cls, path: Path):
        obj = super().__new__(cls, str(path))
        obj.file = path
        return obj


def _abs(module: _Module, p: Any) -> Path:
    p = Path(p)
    return p if p.is_absolute() else (module.path.parent / p)


def dynamic_loads(root: Path, path: Path, tree: ast.Module) -> tuple[list[str], list[Path], list[dict[str, Any]], set[str]]:
    """(module names, files, unresolved sites, module-private loader functions) of the by-name loads in one file."""
    module = _Module(root, path, tree)
    rel = path.relative_to(root).as_posix()
    names: list[str] = []
    files: list[Path] = []
    unresolved: list[dict[str, Any]] = []
    for call in [n for n in ast.walk(tree) if isinstance(n, ast.Call)]:
        q = _qual(call.func, module.aliases)
        if q not in LOADERS:
            continue
        kind, index, keyword = LOADERS[q]
        expr = call.args[index] if len(call.args) > index else next(
            (k.value for k in call.keywords if k.arg == keyword), None)
        fn = module.owner.get(id(call))
        site = {"path": rel, "line": call.lineno, "call": q}
        try:
            if expr is None:
                raise _Unknown("no target argument")
            if kind == "code" and isinstance(expr, ast.Call) and _qual(expr.func, module.aliases) == "compile" and expr.args:
                expr = expr.args[0]
            vals = module.values(expr, fn)
            if kind == "module":
                package = next((k.value for k in call.keywords if k.arg == "package"), None)
                if package is None and q.endswith("import_module") and len(call.args) > 1:
                    package = call.args[1]
                pkgs = module.values(package, fn) if package is not None else {None}
                for v in vals:
                    if not isinstance(v, str):
                        raise _Unknown("module name is not a string")
                    if v.startswith("."):
                        for pkg in pkgs:
                            if not isinstance(pkg, str):
                                raise _Unknown("relative module without a constant package")
                            up = len(v) - len(v.lstrip("."))
                            base = pkg.split(".")[: len(pkg.split(".")) - (up - 1)]
                            names.append(".".join(base + ([v.lstrip(".")] if v.lstrip(".") else [])))
                    else:
                        names.append(v)
            elif kind == "path":
                for v in vals:
                    if not isinstance(v, (str, Path)) or isinstance(v, _Table):
                        raise _Unknown("location is not a path")
                    files.append(_abs(module, v))
            else:  # exec
                for v in vals:
                    if isinstance(v, _Source):
                        files.append(_abs(module, v.file))
                    elif isinstance(v, str):
                        inner = ast.parse(v)
                        n2, f2, u2, _ = dynamic_loads(root, path, inner)
                        for node in ast.walk(inner):
                            if isinstance(node, ast.Import):
                                n2 += [a.name for a in node.names]
                            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                                n2 += [node.module] + [f"{node.module}.{a.name}" for a in node.names]
                        names += n2
                        files += f2
                        unresolved += u2
                    else:
                        raise _Unknown("exec of a non-source value")
        except (_Unknown, SyntaxError, ValueError, TypeError) as exc:
            unresolved.append({**site, "reason": str(exc) or type(exc).__name__})
    return names, files, unresolved, module.private_loaders


def static_closure(root: Path, test_rel: str) -> dict[str, str]:
    """{repository path: sha256} of the test file and every repository file it reaches statically."""
    root = root.resolve()
    start = (root / test_rel).resolve()
    _require(start.is_file() and root in start.parents, "ADJACENCY_RULING_FINISH_POINT_SOURCE_UNAVAILABLE",
             "FINISH_POINT_TEST_PRESENT_AT_PINNED_COMMIT",
             f"the finish-point test {test_rel} must exist at the pinned commit of the finish-point repository")
    seen: dict[str, str] = {}
    trees: dict[str, ast.Module] = {}
    private_loaders: dict[str, set[str]] = {}
    unresolved: list[dict[str, Any]] = []
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
        dyn_names, dyn_files, dyn_unresolved, loaders = dynamic_loads(root, path, tree)
        names += dyn_names
        unresolved += dyn_unresolved
        if loaders:
            private_loaders[rel] = loaders
        trees[rel] = tree
        for target in dyn_files:
            try:
                target = target.resolve()
            except OSError:
                continue
            if target.is_file() and root in target.parents:
                queue.append(target)
        for name in names:
            parts = name.split(".")
            for i in range(1, len(parts) + 1):  # a package's __init__ runs on import of anything below it
                queue += _module_files(root, ".".join(parts[:i]))
    # a module-private loader resolved from its own call sites must not be reachable from another closure file
    for owner_rel, loaders in private_loaders.items():
        for rel, tree in trees.items():
            if rel == owner_rel:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute):
                    used = node.attr
                elif isinstance(node, ast.ImportFrom):
                    used = next((a.name for a in node.names if a.name in loaders), None)
                else:
                    continue
                if used in loaders:
                    unresolved.append({"path": rel, "line": getattr(node, "lineno", 0), "call": f"{owner_rel}:{used}",
                                       "reason": "a module-private loader is reached from another module"})
    _require(not unresolved, "ADJACENCY_RULING_FINISH_POINT_CLOSURE_UNRESOLVED",
             "FINISH_POINT_CLOSURE_DYNAMIC_LOADS_RESOLVED",
             "every by-name load reachable from the finish-point test (importlib.import_module, __import__, "
             "spec_from_file_location, runpy, exec of a file) must name its target by a literal or a statically "
             "determinable constant; an unresolved load is never treated as disjoint - pin a finish-point test whose "
             "closure resolves, or make the load's target a constant",
             sorted(unresolved, key=lambda u: (u["path"], u["line"]))[:50])
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
        _require(bool(comps), "ADJACENCY_RULING_CANDIDATE_COMPONENTS_UNDECLARED", "CANDIDATE_DECLARES_COMPONENTS",
                 f"{cid}'s observed record declares no targets.components, so (a) and (b) would hold vacuously; "
                 f"{cid}'s owner records its components (a record change through its own Goal), or the overlap is "
                 "resolved by Coordination without this input", {"candidate": cid})
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
