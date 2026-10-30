"""CONTRACT_PINS: data/sv-work-items/contract-pins.json is transitively closed. The test recomputes, by AST (import /
from-import / importlib spec_from_file_location with a statically resolvable path, eager or lazy), every repository-local
module the pinned code loads, transitively, and requires each to be pinned; the only unresolved loads are the declared
dispatch-root loads of org-kernel/kernel.py (caller-supplied root, never this repository's path). Pure; no clock, no network."""
from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve_base(node, fpath, consts):
    """Return a Path for expression node if statically resolvable, else None."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str): return node.value
    if isinstance(node, ast.Name):
        if node.id == "ROOT": return ROOT
        return consts.get(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        l = resolve_base(node.left, fpath, consts); r = resolve_base(node.right, fpath, consts)
        if isinstance(l, Path) and isinstance(r, str): return l / r
        return None
    if isinstance(node, ast.Attribute) and node.attr == "parent":
        b = resolve_base(node.value, fpath, consts); return b.parent if isinstance(b, Path) else None
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "parents":
        b = resolve_base(node.value.value, fpath, consts)
        if isinstance(b, Path) and isinstance(node.slice, ast.Constant): return b.parents[node.slice.value]
        return None
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "resolve":
        return resolve_base(node.func.value, fpath, consts)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Path" and node.args \
            and isinstance(node.args[0], ast.Name) and node.args[0].id == "__file__":
        return fpath
    return None
def edges(rel):
    f = ROOT / rel; t = ast.parse(f.read_text()); out = set(); unresolved = []
    consts = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            v = resolve_base(n.value, f, consts)
            if isinstance(v, Path): consts[n.targets[0].id] = v
    funcs = {n.name: n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)}
    def calls_with_literal(fn, idx):
        res = []
        for c in ast.walk(t):
            if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == fn and len(c.args) > idx:
                res.append(c.args[idx])
        return res
    parent_of = {}
    for fn in funcs.values():
        for n in ast.walk(fn): parent_of.setdefault(id(n), fn)
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "spec_from_file_location":
            arg = n.args[1]; fn = parent_of.get(id(n)); cands = []
            v = resolve_base(arg, f, consts)
            if isinstance(v, Path): cands = [v]
            elif fn is not None:
                params = [a.arg for a in fn.args.args]
                local = dict(consts)
                for s in ast.walk(fn):
                    if isinstance(s, ast.Assign) and len(s.targets) == 1 and isinstance(s.targets[0], ast.Name):
                        vv = resolve_base(s.value, f, local)
                        if isinstance(vv, Path): local[s.targets[0].id] = vv
                # arg built from a parameter: substitute literal call-site values
                names = [x.id for x in ast.walk(arg) if isinstance(x, ast.Name)]
                pnames = [p for p in names if p in params]
                if pnames:
                    p = pnames[0]; idx = params.index(p)
                    for lit in calls_with_literal(fn.name, idx):
                        if isinstance(lit, ast.Constant):
                            sub = ast.parse(ast.unparse(arg).replace(p, repr(lit.value)), mode="eval").body
                            vv = resolve_base(sub, f, local)
                            if isinstance(vv, Path): cands.append(vv)
                    if not cands and "root" in params: unresolved.append((fn.name, ast.unparse(arg), "dispatch-root"))
                else:
                    vv = resolve_base(arg, f, local)
                    if isinstance(vv, Path): cands = [vv]
                    else: unresolved.append((fn.name, ast.unparse(arg), "?"))
            else: unresolved.append(("<module>", ast.unparse(arg), "?"))
            for c in cands: out.add(str(c.resolve().relative_to(ROOT)))
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in n.names] if isinstance(n, ast.Import) else [n.module or ""]
            for m in mods:
                for base in (f.parent, ROOT):
                    p = base / (m.replace(".", "/") + ".py")
                    if p.is_file(): out.add(str(p.resolve().relative_to(ROOT)))
    return out, unresolved

def closure(seeds):
    seen, unresolved, st = set(), {}, sorted(seeds)
    while st:
        r = st.pop()
        if r in seen:
            continue
        seen.add(r)
        e, u = edges(r)
        if u:
            unresolved[r] = sorted(x[0] for x in u)
        st += sorted(e)
    return seen, unresolved


class ContractPinsClosureTests(unittest.TestCase):
    def setUp(self):
        self.pins = json.loads((ROOT / "data/sv-work-items/contract-pins.json").read_text())
        self.pinned = set(self.pins["files"])

    def test_closure_is_pinned(self):
        seeds = {f for f in self.pinned if f.endswith(".py")}
        seen, unresolved = closure(seeds)
        self.assertEqual(sorted(seen - self.pinned), [], "repo-local imports of the pinned code that are not pinned")
        self.assertEqual(unresolved, self.pins["import_closure"]["dispatch_root_loads_excluded"])

    def test_declared_members_are_the_computed_closure(self):
        direct = {f for f in self.pinned if f.endswith(".py")} - set(self.pins["import_closure"]["members"])
        seen, _ = closure(direct)
        self.assertEqual(sorted(seen - direct), self.pins["import_closure"]["members"])
        for f in ("org-kernel/kernel.py", "org-kernel/node_store.py", "scripts/project_worker_claim_into_canonical_task.py",
                  "tests/sv_ledger_fixtures.py"):
            self.assertIn(f, self.pinned)


if __name__ == "__main__":
    unittest.main()
