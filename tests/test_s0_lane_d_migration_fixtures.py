"""Lane D NWI-S0 migration fixtures, checked with P1's in-repo schemas and validators (p1/sv-native-work-items).

The schemas are the in-repo files under schemas/; FIXTURE_MANIFEST.json pins their git blobs and sha256 at P1 head
725d0f65. Records are MIGRATED_HISTORICAL and are never admissible. There are two independent checks: a stdlib
JSON Schema subset validator (it refuses any keyword it does not implement) and P1's
sv_work_items.validate_issue / validate_change. Branch writers evidence is UNKNOWN (JDQ Q-WRITER-IDENTITY).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data/sv-work-items/migration/lane-d"
UNKNOWN = "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"
SUPPORTED = {"$id", "$schema", "title", "description", "type", "properties", "required", "additionalProperties",
             "items", "enum", "const", "pattern", "minLength", "minItems", "minimum", "uniqueItems",
             "allOf", "anyOf", "not", "if", "then"}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _type_ok(v, t):
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, TYPES[t])


def validate(inst, schema, path=""):
    """Yield (json_pointer, keyword) for every violation."""
    unknown_kw = {k for k in schema if not k.startswith("x-")} - SUPPORTED
    if unknown_kw:
        raise AssertionError(f"unsupported schema keywords at {path or '/'}: {sorted(unknown_kw)}")
    for sub in schema.get("allOf", []):
        yield from validate(inst, sub, path)
    if "anyOf" in schema and not any(not list(validate(inst, sub, path)) for sub in schema["anyOf"]):
        yield path or "/", "anyOf"
    if "not" in schema and not list(validate(inst, schema["not"], path)):
        yield path or "/", "not"
    if "if" in schema and not list(validate(inst, schema["if"], path)) and "then" in schema:
        yield from validate(inst, schema["then"], path)
    if "type" in schema:
        ts = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_type_ok(inst, t) for t in ts):
            yield path or "/", "type"
            return
    if "const" in schema and inst != schema["const"]:
        yield path or "/", "const"
    if "enum" in schema and inst not in schema["enum"]:
        yield path or "/", "enum"
    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            yield path or "/", "minLength"
        if "pattern" in schema and re.search(schema["pattern"], inst) is None:
            yield path or "/", "pattern"
    if isinstance(inst, (int, float)) and not isinstance(inst, bool) and "minimum" in schema and inst < schema["minimum"]:
        yield path or "/", "minimum"
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            yield path or "/", "minItems"
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in inst}) != len(inst):
            yield path or "/", "uniqueItems"
        if "items" in schema:
            for i, x in enumerate(inst):
                yield from validate(x, schema["items"], f"{path}/{i}")
    if isinstance(inst, dict):
        for r in schema.get("required", []):
            if r not in inst:
                yield f"{path}/{r}", "required"
        props = schema.get("properties", {})
        for k, v in inst.items():
            if k in props:
                yield from validate(v, props[k], f"{path}/{k}")
            elif schema.get("additionalProperties") is False:
                yield f"{path}/{k}", "additionalProperties"
            elif isinstance(schema.get("additionalProperties"), dict):
                yield from validate(v, schema["additionalProperties"], f"{path}/{k}")


def _resolve(inst, pointer):
    for part in [p for p in pointer.split("/") if p]:
        inst = inst[int(part)] if isinstance(inst, list) else inst[part]
    return inst


def _git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def _load_mod(name, rel):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _schema(name):
    return json.loads((ROOT / "schemas" / name).read_text())


def _jsonl(name):
    return [json.loads(l) for l in (FIX / name).read_text().splitlines() if l.strip()]


def all_gaps():
    gaps = []
    for f, s in (("sv-issues.jsonl", "sv-issue.v1.schema.json"), ("sv-changes.jsonl", "sv-change.v1.schema.json")):
        sch = _schema(s)
        for i, r in enumerate(_jsonl(f)):
            gaps += [{"file": f, "record": i, "pointer": p, "keyword": k} for p, k in validate(r, sch)]
    rec = json.loads((FIX / "work-items.json").read_text())
    gaps += [{"file": "work-items.json", "record": 0, "pointer": p, "keyword": k}
             for p, k in validate(rec, _schema("canonical-task-work-items.v1.schema.json"))]
    return gaps


class LaneDS0MigrationFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((FIX / "FIXTURE_MANIFEST.json").read_text())
        cls.issues = _jsonl("sv-issues.jsonl")
        cls.changes = _jsonl("sv-changes.jsonl")
        cls.items = json.loads((FIX / "work-items.json").read_text())
        cls.wi = _load_mod("sv_work_items", "resident-runtime/sv_work_items.py")
        cls.mg = _load_mod("sv_migration", "resident-runtime/sv_migration.py")
        cls.b = _load_mod("lane_d_s0_builder", "scripts/build_lane_d_s0_migration_fixtures.py")

    def test_pinned_sources_match_repository_files(self):
        for pin in self.manifest["pinned_sources"]:
            raw = (ROOT / pin["path"]).read_bytes()
            self.assertEqual(_git_blob(raw), pin["git_blob"], pin["path"])
            self.assertEqual("sha256:" + hashlib.sha256(raw).hexdigest(), pin["sha256"], pin["path"])
        self.assertEqual(self.mg.SURFACE_ALIASES_BLOB, next(p["git_blob"] for p in self.manifest["pinned_sources"]
                                                            if p["path"] == "data/sv-work-items/surface-aliases.json"))

    def test_outputs_reproduce_from_frozen_inputs(self):
        for path, text in self.b.outputs().items():
            self.assertEqual(path.read_text(), text, str(path))
        for inp in self.manifest["inputs"]:
            raw = (ROOT / inp["path"]).read_bytes()
            self.assertEqual("sha256:" + hashlib.sha256(raw).hexdigest(), inp["sha256"], inp["path"])

    def test_zero_schema_gaps(self):
        self.assertEqual(all_gaps(), [])
        self.assertEqual(json.loads((FIX / "expected-schema-gaps.json").read_text())["gaps"], [])

    def test_p1_validators_accept_every_record(self):
        for r in self.issues:
            self.wi.validate_issue(r)
        for c in self.changes:
            self.wi.validate_change(c)
        self.assertEqual(self.wi.work_items_record(self.issues + self.changes), self.items)

    def test_every_record_is_migrated_historical_and_never_admissible(self):
        for r in self.issues + self.changes:
            self.assertEqual(r["record_mode"], "MIGRATED_HISTORICAL")
            self.assertEqual(sorted(r["unknown_fields"]), sorted(self.wi.sentinel_pointers(r)))
            self.assertEqual(r["hb_epoch"], UNKNOWN)  # never from a clock
        base = self.issues[0]["observed_base"]
        for c in self.changes:
            out = self.wi.admit(self.wi.admission_inputs(c, base))
            self.assertEqual((out["disposition"], out["failure_code"]), ("FAIL_CLOSED", "HISTORICAL_RECORD_NOT_ADMISSIBLE"))

    def test_identities(self):
        for r in self.issues:
            self.assertEqual(r["issue_id"], self.wi.issue_identity(r))
        for c in self.changes:
            self.assertEqual(c["change_id"], self.wi.change_identity(c))
            self.assertEqual(c["head"]["change_digest"][7:], c["change_id"][4:])
            self.assertTrue(all(e["writer_session"] == {"session": None, "evidence_class": UNKNOWN} for e in c["content"]))
        # change_ids are pinned: RF-1 moved issue ids, never change ids
        self.assertEqual({str(c["projection"]["pr"]): c["change_id"] for c in self.changes}, self.manifest["pinned_change_ids"])

    def test_counts(self):
        self.assertEqual(len(self.issues), self.manifest["counts"]["sv_issue"])
        self.assertEqual(len(self.changes), self.manifest["counts"]["sv_change"])
        self.assertEqual(len(self.items["work_items"]), len(self.issues) + len(self.changes))
        self.assertEqual(sorted(c["projection"]["pr"] for c in self.changes),
                         [3231, 3232, 3235, 3241, 3243, 3245, 3251, 3253, 3255, 3258, 3261])

    def test_3245_records_branch_writer_is_branch_owner_fail(self):
        c = next(c for c in self.changes if c["projection"]["pr"] == 3245)
        self.assertEqual(c["lifecycle_state"], "FAIL_CLOSED")
        (v,) = c["validation_receipts"]
        self.assertEqual((v["check_id"], v["disposition"], v["evidence_class"]), ("BRANCH_WRITER_IS_BRANCH_OWNER", "FAIL_CLOSED", "OBSERVED_ARTIFACT"))
        self.assertEqual(v["change_digest"], c["head"]["change_digest"])
        path, line = v["ref"].split("#L")
        raw = (ROOT / path).read_bytes()
        self.assertEqual(v["digest"], "sha256:" + hashlib.sha256(raw).hexdigest())
        cited = raw.decode("utf-8").splitlines()[int(line) - 1]
        self.assertTrue(cited.startswith("| #3245 |") and "BRANCH_WRITER_IS_BRANCH_OWNER" in cited)
        self.assertTrue(any(i["disposition"]["failure_code"] == "BRANCH_HAS_FOREIGN_WRITER" for i in self.issues))
        self.assertFalse([c for c in self.changes if c["projection"]["pr"] != 3245 and c["validation_receipts"]])

    def test_rf1_split_and_line_587(self):
        by_line = {i["projection"]["source_line"]: i for i in self.issues}
        self.assertNotEqual(by_line[591]["issue_id"], by_line[592]["issue_id"])
        self.assertEqual((by_line[591]["owning_goal"], by_line[592]["owning_goal"]),
                         ("STEGVERSE-WORKSPACE-ANY-DEVICE-KV-SURFACE-001", "STEGOPS-CAMPAIGN-CRM-PROJECTION-001"))
        self.assertEqual(by_line[587]["surface"]["path"], "scripts/apply_admitted_canonical_work_projection.py")
        self.assertEqual(by_line[584]["surface"]["path"], "scripts/consume_org_claim_allocator_request.py")
        self.assertNotEqual(by_line[19]["issue_id"], by_line[20]["issue_id"])  # WU1 vs WU2/WU3

    def test_s26_4_excluded_and_no_owner_flag(self):
        self.assertFalse(any(i["disposition"]["failure_code"] == "S0_RECORD_FORMAT_NOT_PUBLISHED" for i in self.issues))
        for w in self.items["work_items"]:
            self.assertFalse({k for k in w if "approv" in k.lower() or "owner" in k.lower()})

    def test_proposed_aliases_are_proposals_only(self):
        prop = json.loads((FIX / "PROPOSED_SURFACE_ALIASES.json").read_text())
        table = json.loads((ROOT / "data/sv-work-items/surface-aliases.json").read_text())
        declared = {e["alias"] for e in table["lane_aliases"]}
        self.assertEqual(prop["status"], "PROPOSED_NOT_APPLIED")
        src = (FIX / "sources/LANE_D_S14_S26.md").read_text().splitlines()
        for e in prop["proposals"]:
            self.assertIn(e["evidence_text"], src[e["evidence_line"] - 1])
        self.assertTrue(declared)

    def test_validator_rejects_known_bad(self):
        s = _schema("sv-issue.v1.schema.json")
        bad = dict(self.issues[0], extra=1, lifecycle_state="DONE")
        self.assertTrue({"additionalProperties", "enum"} <= {k for _, k in validate(bad, s)})
        native = {k: v for k, v in self.issues[0].items() if k not in ("unknown_fields", "migration_provenance")}
        self.assertTrue(list(validate(dict(native, record_mode="NATIVE"), s)))
        with self.assertRaises(AssertionError):
            list(validate({}, {"oneOf": []}))


if __name__ == "__main__":
    unittest.main()
