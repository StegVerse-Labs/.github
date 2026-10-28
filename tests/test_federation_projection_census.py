"""H61: the projection census of the canonical federation directory (StegVerse-org/.github#162).

Known answers from the committed anonymous observations: StegVerse-org and SV-LLM hold current declared projections;
nine organizations hold an undeclared generation-1 copy without SV-LLM and SV-011; four rows are not anonymously
readable. Every refusal carries the six fields. Clock-free and network-free.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "org-boundary" / "runtime" / "federation_projection_census.py"
CENSUS = ROOT / "data" / "federation-projection-census" / "census.json"
CANONICAL = ROOT / "org-boundary" / "registry" / "federation.json"
REFERENCE = ROOT / "data" / "federation-projection-census" / "reference" / "federation_projection.py"

spec = importlib.util.spec_from_file_location("federation_projection_census", MODULE_PATH)
census_module = importlib.util.module_from_spec(spec)
sys.modules["federation_projection_census"] = census_module
spec.loader.exec_module(census_module)

STALE = ["AaCT-E", "Admissible-Existence", "AdmittedCode", "Data-Continuation", "ECAT-ICAT-Formal",
         "GCAT-BCAT-Engine", "StegGhost", "StegVerse-002", "Triad-Test"]
UNOBSERVED = ["formalism-tests", "Infrastructure-Continuity-Ventures", "master-records", "SV-011"]
SKAP = ("SKAP Vault inside KV is the only PII and credential store for every user, the ecosystem's own included; "
        "the ecosystem holds none")


class FederationProjectionCensusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = census_module.census_result(CENSUS, CANONICAL)
        self.rows = {r["organization"]: r for r in self.result["organizations"]}

    def test_census_covers_exactly_the_canonical_directory(self) -> None:
        canonical = json.loads(CANONICAL.read_text(encoding="utf-8"))
        self.assertEqual([r["organization"] for r in self.result["organizations"]],
                         [o["organization"] for o in canonical["organizations"]])
        self.assertEqual(self.result["denominator"], len(canonical["organizations"]))
        self.assertEqual(self.result["canonical_generation"], canonical["generation"])

    def test_known_answer_states(self) -> None:
        self.assertEqual(self.rows["StegVerse-Labs"]["state"], "CANONICAL")
        for org in ("StegVerse-org", "SV-LLM"):
            self.assertEqual(self.rows[org]["state"], "CURRENT")
            self.assertEqual(self.rows[org]["disposition"], "ALLOW")
        for org in STALE:
            row = self.rows[org]
            self.assertEqual((row["state"], row["failure_code"]), ("STALE", "FEDERATION_PROJECTION_STALE"))
            self.assertFalse(row["declared_projection"])
            self.assertEqual(row["observed_generation"], 1)
            self.assertEqual(row["missing_organizations"], ["SV-LLM", "SV-011"])
            self.assertEqual(row["local_additions"], [])
        for org in UNOBSERVED:
            self.assertEqual(self.rows[org]["failure_code"], "FEDERATION_PROJECTION_UNOBSERVED")
        self.assertEqual(self.result["counts"], {"CANONICAL": 1, "CURRENT": 2, "STALE": 9, "UNOBSERVED": 4})
        self.assertEqual(self.result["disposition"], "FAIL_CLOSED")

    def test_every_refusal_carries_six_fields(self) -> None:
        for row in self.result["organizations"]:
            if row["disposition"] != "ALLOW":
                for field in census_module.SIX:
                    self.assertTrue(row.get(field), (row["organization"], field))
                self.assertEqual(row["owning_existing_goal"], census_module.GOAL)

    def test_result_is_sealed_and_deterministic(self) -> None:
        body = {k: v for k, v in self.result.items() if k != "receipt_sha256"}
        self.assertEqual(self.result["receipt_sha256"], census_module.sha(census_module.canon(body)))
        self.assertEqual(census_module.census_result(CENSUS, CANONICAL), self.result)

    def test_observations_and_reference_are_pinned(self) -> None:
        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        self.assertEqual(census["reference_tool"]["sha256"],
                         "sha256:" + hashlib.sha256(REFERENCE.read_bytes()).hexdigest())
        for row in census["organizations"]:
            if row.get("observation"):
                self.assertEqual(row["observation_sha256"],
                                 "sha256:" + hashlib.sha256((ROOT / row["observation"]).read_bytes()).hexdigest())
                self.assertRegex(row["observed_commit"], r"^[0-9a-f]{40}$")

    def test_reprojection_is_what_current_organizations_already_hold(self) -> None:
        projected = census_module.reprojection("AaCT-E", CENSUS, CANONICAL)
        for org in ("StegVerse-org", "SV-LLM"):
            observed = json.loads((ROOT / "data/federation-projection-census/observed" / f"{org}.json").read_text())
            self.assertEqual(observed, projected)
        ref = census_module.reference(json.loads(CENSUS.read_text(encoding="utf-8")))
        self.assertTrue(ref.verify(projected, CANONICAL.read_bytes())["valid"])

    def test_a_local_addition_or_altered_observation_is_refused(self) -> None:
        census = json.loads(CENSUS.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            projected = census_module.reprojection("AaCT-E", CENSUS, CANONICAL)
            added = copy.deepcopy(projected)
            added["organizations"].append({"organization": "Local-Addition", "repository": "Local-Addition/.github"})
            path = Path(tmp) / "added.json"
            path.write_bytes(json.dumps(added).encode())
            row = dict(next(r for r in census["organizations"] if r["organization"] == "StegVerse-org"))
            row.update(observation=str(path), observation_sha256=census_module.sha(path.read_bytes()))
            judged = census_module.judge(row, CANONICAL.read_bytes(), census)
            self.assertEqual(judged["failure_code"], "FEDERATION_PROJECTION_STALE")
            self.assertEqual(judged["local_additions"], ["Local-Addition"])
            row["observation_sha256"] = "sha256:" + "0" * 64
            self.assertEqual(census_module.judge(row, CANONICAL.read_bytes(), census)["failure_code"],
                             "FEDERATION_PROJECTION_OBSERVATION_ALTERED")

    def test_census_is_clock_free_network_free_and_holds_no_credential(self) -> None:
        tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
        imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(imported & {"socket", "urllib", "http", "requests", "time", "datetime", "subprocess", "os"})
        self.assertIn(SKAP, MODULE_PATH.read_text(encoding="utf-8"))
        self.assertIn(SKAP, (ROOT / "docs" / "FEDERATION_DIRECTORY.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
