"""Candidate targets.components derived from observed evidence only (scripts/derive_candidate_components.py), E0.

Both ways: a surface that was actually read becomes a component with derived_from_observation, source refs and
sha256 digests; nothing read -> six-field FAIL_CLOSED, never an assumed or invented component. No network.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "data" / "registry-record-data" / "adjacency-candidate-components.draft.json"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
M1 = "a" * 40
M2 = "b" * 40


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


D = _load("derive_candidate_components_under_test", "scripts/derive_candidate_components.py")
A = _load("adjacency_ruling_for_derivation", "scripts/adjacency_ruling.py")


def digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def pr_record() -> dict:
    return {"schema": "stegverse.canonical-task-record/v1", "task_id": "PR-GOAL-001", "goal": "g",
            "implementation_pr": "Org/Impl#7", "implementation_repository": "Org/Impl"}


def pr_observation(record: dict, files=None, merged=True) -> dict:
    files = files if files is not None else ["scripts/impl_payment_observer.py", "config/read_profiles.json",
                                             "tests/test_impl_payment_observer.py", "docs/HANDOFF.md",
                                             ".github/workflows/impl-ingress.yml"]
    return {"schema": D.OBSERVATION_SCHEMA, "task_id": record["task_id"], "record_sha256": D.sha(D.canon(record)),
            "source_commits": {}, "task_file_paths": {},
            "pull_requests": [{"ref": "Org/Impl#7", "merged": merged, "merge_commit": M1, "files": sorted(files),
                               "files_sha256": D.sha(D.canon(sorted(files)))}],
            "files": [{"ref": f"Org/Impl:{f}@{M1}", "observed": True, "sha256": digest(f)} for f in files]}


def ref_record() -> dict:
    return {"schema": "stegverse.canonical-task-record/v1", "task_id": "REF-GOAL-001", "goal": "g",
            "repository": "Org/Health",
            "source_refs": ["Org/Health:tasks/REF-GOAL-001.json", "Org/Health:tools/consume_failure_map.py",
                            "Org/Health:docs/HANDOFF.md", "docs/LOCAL.md"]}


def ref_observation(record: dict, declared=None, unobserved=()) -> dict:
    declared = declared if declared is not None else ["registries/failure-registry.json", "tools/validate_registry.py",
                                                      "receipts/r.json", "Org/Other/x.json", "schemas/failure.schema.json"]
    paths = ["tasks/REF-GOAL-001.json", "tools/consume_failure_map.py", "docs/HANDOFF.md", *declared]
    files = [{"ref": f"Org/Health:{p}@{M2}", "observed": p not in unobserved and not p.startswith("Org/"),
              "sha256": None if (p in unobserved or p.startswith("Org/")) else digest(p)} for p in paths]
    return {"schema": D.OBSERVATION_SCHEMA, "task_id": record["task_id"], "record_sha256": D.sha(D.canon(record)),
            "source_commits": {"Org/Health": M2}, "pull_requests": [],
            "task_file_paths": {f"Org/Health:tasks/REF-GOAL-001.json@{M2}": sorted(declared)},
            "files": sorted(files, key=lambda f: f["ref"])}


def make_base(records: list[dict], generation: int = 320) -> Path:
    base = Path(tempfile.mkdtemp())
    (base / D.RECORDS).mkdir(parents=True)
    for r in records:
        (base / D.RECORDS / f"{r['task_id']}.json").write_text(json.dumps(r, indent=2) + "\n")
    (base / D.REGISTRY).write_text(json.dumps({"generation": generation, "tasks": records}))
    return base


class DeriveFromObservation(unittest.TestCase):
    def test_record_named_pr_surfaces_become_components_with_sources(self):
        rec = pr_record()
        out = D.derive(rec, pr_observation(rec))
        after = out["edit"]["after"]
        self.assertEqual(after["components"], ["impl-ingress", "impl-payment-observer", "read-profiles"])
        self.assertEqual(after["repositories"], ["Org/Impl"])
        self.assertEqual(after["organizations"], ["Org"])
        self.assertEqual(out["edit"]["path"], ["targets"])
        self.assertEqual(out["edit"]["before"], {"$absent": True})
        for c in out["derivation"]["components"]:
            self.assertIs(c["derived_from_observation"], True)
            self.assertEqual(c["rules"], ["R2_RECORD_NAMED_PR"])
            refs = [s["ref"] for s in c["sources"]]
            self.assertIn("Org/Impl#7 files", refs)
            self.assertIn("StegVerse-Labs/.github:data/canonical-task-records/PR-GOAL-001.json", refs)
            self.assertTrue(all(D.HEX64.match(s["sha256"]) for s in c["sources"]))

    def test_source_refs_and_own_task_file_paths_only_when_read(self):
        rec = ref_record()
        out = D.derive(rec, ref_observation(rec, unobserved=("tools/validate_registry.py",)))
        comps = {c["component"]: c for c in out["derivation"]["components"]}
        self.assertEqual(sorted(comps), ["consume-failure-map", "failure", "failure-registry"])
        self.assertEqual(comps["consume-failure-map"]["rules"], ["R1_SOURCE_REF"])
        self.assertEqual(comps["failure-registry"]["rules"], ["R3_OWN_TASK_FILE_PATH"])
        self.assertNotIn("validate-registry", comps)  # declared but not read -> not a component
        self.assertNotIn("r", comps)                  # receipts are evidence, not components
        self.assertIn(f"Org/Health:tasks/REF-GOAL-001.json@{M2}", [s["ref"] for s in comps["failure"]["sources"]])

    def test_nothing_observed_is_six_field_fail_closed(self):
        rec = pr_record()
        with self.assertRaises(D.NotDerivable) as ctx:
            D.derive(rec, pr_observation(rec, files=["tests/test_x.py", "docs/A.md", "pkg/__init__.py"]))
        six = ctx.exception.six()
        self.assertEqual(six["failure_code"], "CANDIDATE_COMPONENTS_NOT_DERIVABLE_FROM_OBSERVATION")
        self.assertEqual(six["disposition"], "FAIL_CLOSED")
        self.assertTrue(all(six[k] for k in SIX))

    def test_unmerged_pr_is_not_evidence(self):
        rec = pr_record()
        with self.assertRaises(D.NotDerivable) as ctx:
            D.derive(rec, pr_observation(rec, merged=False))
        self.assertEqual(ctx.exception.code, "CANDIDATE_COMPONENTS_NOT_DERIVABLE_FROM_OBSERVATION")

    def test_record_without_any_source_is_not_derivable(self):
        rec = {"schema": "stegverse.canonical-task-record/v1", "task_id": "BARE-001", "goal": "g"}
        obs = {"schema": D.OBSERVATION_SCHEMA, "task_id": "BARE-001", "record_sha256": D.sha(D.canon(rec)),
               "source_commits": {}, "task_file_paths": {}, "pull_requests": [], "files": []}
        with self.assertRaises(D.NotDerivable):
            D.derive(rec, obs)

    def test_stale_observation_refused(self):
        rec = pr_record()
        obs = pr_observation(rec)
        rec["goal"] = "changed after observation"
        with self.assertRaises(D.NotDerivable) as ctx:
            D.derive(rec, obs)
        self.assertEqual(ctx.exception.code, "CANDIDATE_OBSERVATION_STALE")

    def test_tampered_listing_refused(self):
        rec = pr_record()
        obs = pr_observation(rec)
        obs["pull_requests"][0]["files"].append("scripts/invented_component.py")
        obs["files"].append({"ref": f"Org/Impl:scripts/invented_component.py@{M1}", "observed": True,
                             "sha256": digest("x")})
        with self.assertRaises(D.NotDerivable) as ctx:
            D.derive(rec, obs)
        self.assertEqual(ctx.exception.code, "CANDIDATE_OBSERVATION_TAMPERED")

    def test_declared_components_are_not_rederived(self):
        rec = pr_record()
        rec["targets"] = {"organizations": ["Org"], "repositories": ["Org/Impl"], "components": ["x"]}
        with self.assertRaises(D.NotDerivable) as ctx:
            D.derive(rec, pr_observation(rec))
        self.assertEqual(ctx.exception.code, "CANDIDATE_COMPONENTS_ALREADY_DECLARED")

    def test_naming_and_surface_rules(self):
        self.assertEqual(D.component_name("schemas/ecosystem-failure-registry.schema.json"), "ecosystem-failure-registry")
        self.assertEqual(D.component_name("tvc_payment_provider_read_profile.py"), "tvc-payment-provider-read-profile")
        self.assertFalse(D.is_surface("tests/test_a.py"))
        self.assertFalse(D.is_surface("payment_ingress/README.md"))
        self.assertFalse(D.is_surface("tasks/X.json"))
        self.assertTrue(D.is_surface(".github/workflows/payment-provider-authentic-ingress.yml"))


class ProposalAndCheck(unittest.TestCase):
    def setUp(self):
        self.pr, self.ref = pr_record(), ref_record()
        self.bare = {"schema": "stegverse.canonical-task-record/v1", "task_id": "BARE-001", "goal": "g"}
        self.base = make_base([self.pr, self.ref, self.bare])
        self.bare_obs = {"schema": D.OBSERVATION_SCHEMA, "task_id": "BARE-001", "record_sha256": D.sha(D.canon(self.bare)),
                         "source_commits": {}, "task_file_paths": {}, "pull_requests": [], "files": []}
        self.prop = D.propose(self.base, [pr_observation(self.pr), ref_observation(self.ref), self.bare_obs])

    def test_proposal_is_a_row_fields_draft_without_generation_bump_or_record_edit(self):
        before = {p.name: p.read_bytes() for p in (self.base / D.RECORDS).iterdir()}
        self.assertEqual(self.prop["schema"], "stegverse.registry-record-data-proposal/v1")
        self.assertEqual(self.prop["registry_generation_base"], 320)
        self.assertEqual([e["task_id"] for e in self.prop["row_fields"]], ["PR-GOAL-001", "REF-GOAL-001"])
        self.assertEqual([r["task_id"] for r in self.prop["not_derivable"]], ["BARE-001"])
        self.assertTrue(all(self.prop["not_derivable"][0][k] for k in SIX))
        self.assertEqual(D.check(self.prop, self.base), [])
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.base / D.RECORDS).iterdir()})
        self.assertEqual(json.loads((self.base / D.REGISTRY).read_text())["generation"], 320)

    def test_check_refuses_invented_component(self):
        bad = copy.deepcopy(self.prop)
        bad["row_fields"][0]["after"]["components"].append("invented")
        self.assertTrue(any("re-derivation" in e for e in D.check(bad, self.base)))

    def test_check_refuses_missing_digest_and_flag(self):
        bad = copy.deepcopy(self.prop)
        bad["derivations"][0]["components"][0]["derived_from_observation"] = False
        bad["derivations"][0]["components"][1]["sources"][0]["sha256"] = "sha256:short"
        errors = D.check(bad, self.base)
        self.assertTrue(any("lacks derived_from_observation" in e for e in errors))

    def test_check_refuses_generation_drift_and_changed_record(self):
        drift = make_base([self.pr, self.ref, self.bare], generation=321)
        self.assertTrue(any("registry_generation_base" in e for e in D.check(self.prop, drift)))
        changed = dict(self.pr, goal="edited")
        self.assertTrue(any("CANDIDATE_OBSERVATION_STALE" in e
                            for e in D.check(self.prop, make_base([changed, self.ref, self.bare]))))

    def test_applied_components_feed_the_adjacency_touch_check(self):
        rec = dict(self.pr, targets=self.prop["row_fields"][0]["after"])
        hits = A.touches(["impl/payment/impl_payment_observer.py", "sdk/unrelated.py"], rec, "Org/Sdk")
        self.assertEqual([h["component"] for h in hits], ["impl-payment-observer"])
        self.assertEqual(A.touches(["sdk/unrelated.py"], rec, "Org/Sdk"), [])


class CommittedDraft(unittest.TestCase):
    def test_committed_draft_rederives_on_this_tree(self):
        prop = json.loads(DRAFT.read_text(encoding="utf-8"))
        self.assertEqual(D.check(prop, ROOT), [])
        self.assertEqual(sorted(e["task_id"] for e in prop["row_fields"]),
                         ["PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001", "STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001"])
        for task_id in ("PAYMENT-PROVIDER-AUTHENTIC-INGRESS-001", "STEGHEALTH-ECOSYSTEM-FAILURE-REMEDIATION-001"):
            self.assertNotIn("targets", json.loads((ROOT / D.RECORDS / f"{task_id}.json").read_text()))


if __name__ == "__main__":
    unittest.main()
