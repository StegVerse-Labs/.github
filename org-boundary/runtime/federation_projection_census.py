#!/usr/bin/env python3
"""Projection census of the canonical federation directory (H61; StegVerse-org/.github#162).

SKAP Vault inside KV is the only PII and credential store for every user, the ecosystem's own included; the ecosystem holds none (HST citation pending P1 #163).
This module reads and writes no credential: every observation it judges was read anonymously.

The canonical directory is this repository's org-boundary/registry/federation.json. Every other organization holds
org-boundary/registry/federation.json as a declared projection of it (its projection_rule): the canonical entries
unchanged plus their provenance, updated only by re-projection. This census judges, for each directory row, the
copy that organization actually published, from the exact bytes committed under
data/federation-projection-census/observed/ (taken anonymously at a pinned commit, never fetched here):

  CANONICAL   the canonical file itself (StegVerse-Labs)
  CURRENT     a declared projection whose entries equal the canonical entries       -> ALLOW
  STALE       a copy that is not a declared projection of the canonical entries,
              or whose entries differ (an older generation or a local addition)    -> FAIL_CLOSED, six fields
  UNOBSERVED  no anonymous observation exists (repository not publicly readable)   -> FAIL_CLOSED, six fields

Projection is judged with the reference tool's own verify/project (SV-LLM/.github
org-boundary/runtime/federation_projection.py, vendored byte-identical and pinned by sha256 in the census). No clock,
no network, no git invocation; the result is sealed (receipt_sha256 over canonical JSON). The census grants no
routing, admission or transition authority, and it never edits the directory or any organization's copy.

  verify     [--census PATH]                                     -> the sealed census result (exit 1 unless every row ALLOWs)
  reproject  --organization ORG                                  -> the projection that organization should commit
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_PATH = ROOT / "org-boundary/registry/federation.json"
CENSUS_PATH = ROOT / "data/federation-projection-census/census.json"
SCHEMA = "stegverse.federation-projection-census/v1"
RESULT_SCHEMA = "stegverse.federation-projection-census-result/v1"
GOAL = "StegVerse-org/.github#162 (Lane B, canonical federation directory H61)"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_census(path: Path | str = CENSUS_PATH) -> dict[str, Any]:
    census = json.loads(Path(path).read_text(encoding="utf-8"))
    if census.get("schema") != SCHEMA:
        raise SystemExit("census schema mismatch")
    return census


def reference(census: dict[str, Any]):
    """The vendored reference tool, loaded only after its bytes match the pinned sha256."""
    tool = census["reference_tool"]
    path = ROOT / tool["vendored_at"]
    if sha(path.read_bytes()) != tool["sha256"]:
        raise SystemExit("reference projection tool bytes differ from the pinned sha256")
    name = "federation_projection_reference"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _hold(row: dict[str, Any], code: str, predicate: str, repair: str, next_attempt: str, **detail: Any) -> dict[str, Any]:
    return {"organization": row["organization"], "repository": row["repository"], "state": detail.pop("state"),
            "disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
            "required_evidence_or_repair": repair,
            "retry_entrypoint": "python org-boundary/runtime/federation_projection_census.py verify (after the census "
                                "row is re-observed at a milestone)",
            "owning_existing_goal": GOAL, "next_attempt": next_attempt, "authority_effect": "NONE_REFUSAL_ONLY", **detail}


def judge(row: dict[str, Any], canonical_bytes: bytes, census: dict[str, Any]) -> dict[str, Any]:
    ref = reference(census)
    canonical = json.loads(canonical_bytes)
    names = [o["organization"] for o in canonical["organizations"]]
    source_commit = census["canonical"]["generation_commit"]
    repair = ("the owner of " + row["repository"] + " commits org-boundary/registry/federation.json exactly as "
              "`python org-boundary/runtime/federation_projection_census.py reproject --organization "
              + row["organization"] + "` prints it (canonical generation " + str(canonical["generation"])
              + ", source_commit " + source_commit + "); no row is added or changed locally")
    if row.get("role") == "CANONICAL":
        return {"organization": row["organization"], "repository": row["repository"], "state": "CANONICAL",
                "disposition": "ALLOW", "generation": canonical["generation"], "source_sha256": sha(canonical_bytes)}
    if not row.get("observation"):
        return _hold(row, "FEDERATION_PROJECTION_UNOBSERVED", "PROJECTION_IS_ANONYMOUSLY_OBSERVED",
                     "an anonymous read of " + row["repository"] + ":org-boundary/registry/federation.json at a pinned "
                     "commit (" + row.get("unobserved_reason", "not observed") + ")",
                     "at the milestone after " + row["repository"] + " is publicly readable", state="UNOBSERVED")
    data = (ROOT / row["observation"]).read_bytes()
    if sha(data) != row.get("observation_sha256"):
        return _hold(row, "FEDERATION_PROJECTION_OBSERVATION_ALTERED", "OBSERVATION_BYTES_MATCH_THE_CENSUS",
                     "the observed bytes exactly as read at " + str(row.get("observed_commit")),
                     "re-observe at the next milestone", state="STALE")
    copy = json.loads(data)
    held = [o.get("organization") for o in copy.get("organizations") or []]
    detail = {"observed_commit": row["observed_commit"], "observed_generation": copy.get("generation"),
              "observed_denominator": copy.get("denominator"),
              "missing_organizations": [n for n in names if n not in held],
              "local_additions": [n for n in held if n not in names]}
    if not isinstance(copy.get("projection"), dict):
        return _hold(row, "FEDERATION_PROJECTION_STALE", "COPY_IS_A_DECLARED_PROJECTION_OF_THE_CANONICAL_ENTRIES",
                     repair, "the milestone after that commit lands on " + row["repository"] + " main",
                     state="STALE", declared_projection=False, **detail)
    verdict = ref.verify(copy, canonical_bytes)
    if not verdict["valid"]:
        return _hold(row, "FEDERATION_PROJECTION_STALE", "COPY_IS_A_DECLARED_PROJECTION_OF_THE_CANONICAL_ENTRIES",
                     repair, "the milestone after that commit lands on " + row["repository"] + " main",
                     state="STALE", declared_projection=True, checks=verdict["checks"], **detail)
    return {"organization": row["organization"], "repository": row["repository"], "state": "CURRENT",
            "disposition": "ALLOW", "observed_commit": row["observed_commit"],
            "projection_source_commit": verdict["source_commit"], "generation": copy.get("generation")}


def census_result(census_path: Path | str = CENSUS_PATH, canonical_path: Path | str = CANONICAL_PATH) -> dict[str, Any]:
    census = load_census(census_path)
    canonical_bytes = Path(canonical_path).read_bytes()
    canonical = json.loads(canonical_bytes)
    names = [o["organization"] for o in canonical["organizations"]]
    rows = census["organizations"]
    if [r["organization"] for r in rows] != names or canonical.get("denominator") != len(names):
        raise SystemExit("census rows must be exactly the canonical directory's organizations, in order")
    judged = [judge(r, canonical_bytes, census) for r in rows]
    counts: dict[str, int] = {}
    for j in judged:
        counts[j["state"]] = counts.get(j["state"], 0) + 1
    body = {"schema": RESULT_SCHEMA, "canonical_generation": canonical["generation"],
            "denominator": canonical["denominator"], "canonical_source_sha256": sha(canonical_bytes),
            "counts": dict(sorted(counts.items())),
            "disposition": "ALLOW" if all(j["disposition"] == "ALLOW" for j in judged) else "FAIL_CLOSED",
            "organizations": judged, "authority_effect": "NONE_OBSERVATION_ONLY"}
    return {**body, "receipt_sha256": sha(canon(body))}


def reprojection(organization: str, census_path: Path | str = CENSUS_PATH,
                 canonical_path: Path | str = CANONICAL_PATH) -> dict[str, Any]:
    census = load_census(census_path)
    canonical_bytes = Path(canonical_path).read_bytes()
    if organization not in [o["organization"] for o in json.loads(canonical_bytes)["organizations"]]:
        raise SystemExit("organization is not in the canonical directory: add it there first")
    return reference(census).project(canonical_bytes, source_commit=census["canonical"]["generation_commit"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--census", default=str(CENSUS_PATH))
    r = sub.add_parser("reproject")
    r.add_argument("--organization", required=True)
    args = parser.parse_args(argv)
    if args.command == "reproject":
        sys.stdout.write(json.dumps(reprojection(args.organization), indent=2, ensure_ascii=False) + "\n")
        return 0
    result = census_result(args.census)
    print(json.dumps(result, indent=1, sort_keys=True))
    return 0 if result["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
