#!/usr/bin/env python3
"""Deterministically derive the S0 migration fixtures and the seed scenario corpus.

  SV_ISSUEs  <- every six-field non-ALLOW entry in data/sv-work-items/migration/sources/*.md
  corpus     <- SCENARIO_CORPUS_APPEND of each seed class (A6), in order
  SV_CHANGEs <- the observed fields (target_repository, base_ref, content, projection) of the committed
                sv-changes.jsonl; identity, digests, resolves and migration fields are re-derived
Migration records are MIGRATED_HISTORICAL: their history carries no supplied epoch, so hb_epoch is
UNKNOWN (never a fixture value), and resolution_class is UNKNOWN unless the source table states it.
FIXTURE_HB_EPOCH is used only for the NATIVE known-good controls and the corpus. `--check` exits 1 if
the committed files differ from a fresh derivation.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def _load(n, p):
    if n in sys.modules:
        return sys.modules[n]
    s = importlib.util.spec_from_file_location(n, ROOT / p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
wi = _load("sv_work_items", "resident-runtime/sv_work_items.py")
al = _load("admission_learning", "resident-runtime/admission_learning.py")
mg = _load("sv_migration", "resident-runtime/sv_migration.py")

FIXTURE_HB_EPOCH = "1024"
SESSION = "P1 Ecosystem AI Lane (d8cbc58c)"
LABS_BASE = {"registry_generation": 319, "ledger_head": "a5bb54d81893b392a3ce28182986fc39857807e1"}
MIG = ROOT / "data/sv-work-items/migration"
SCN = ROOT / "data/admission-scenarios"
INVARIANT_FILES = {  # rule_id -> (repository, file, blob_sha); others stay invariant_declared false
    "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH": ("StegVerse-Labs/.github", "org-kernel/kernel.py#supplied_epoch_failure", "ffec5d648d7fa4aead1f44f76df936a2da21bb96"),
    "H28_COMPONENT_AVAILABLE_AT_PINNED_COMMIT": ("StegVerse-Labs/.github", "data/reusable-task-component-model.json", "87688679d07e0c2b4bc9b6b885ac489f0dc3a09a"),
    "ECOSYSTEM_CAPABILITY_PERFORMS_STEP": ("StegVerse-Labs/.github", "data/reusable-task-component-model.json", "87688679d07e0c2b4bc9b6b885ac489f0dc3a09a"),
}
FIELD = re.compile(r"^\s*- (?:\*\*)?(failure_code|failed_predicate|required_evidence_or_repair|retry_entrypoint|owning_existing_goal|next_attempt):(?:\*\*)?\s*(.*)$")


def _clean(v: str) -> str:
    v = v.strip()
    m = re.match(r"^`([^`]+)`(.*)$", v)
    return (m.group(1) + m.group(2)).strip() if m else v


def parse_six(text: str) -> list[dict]:
    """Six-field entries; a field whose value continues as indented sub-bullets is joined with '; '."""
    out, cur, last = [], {}, None
    for line in text.splitlines():
        m = FIELD.match(line)
        if not m:
            cont = re.match(r"^\s+- (.*)$", line)
            if cur and last and cont:
                cur[last] = (cur[last] + "; " if cur[last] else "") + cont.group(1).strip()
                continue
            if cur and all(f in cur and cur[f] for f in wi.SIX_FIELDS):
                out.append(cur); cur = {}
            last = None
            continue
        k, v = m.group(1), _clean(m.group(2))
        if k == "failure_code":
            if cur and all(f in cur and cur[f] for f in wi.SIX_FIELDS):
                out.append(cur)
            cur = {"failure_code": v.split()[0].rstrip(".`")}
        elif cur:
            cur[k] = v
        last = k if cur else None
    if cur and all(f in cur and cur[f] for f in wi.SIX_FIELDS):
        out.append(cur)
    return out


def resolution_class(text: str, code: str) -> str:
    """The class the source table states for this failure code; UNKNOWN when it states none (SF-3: no default)."""
    for line in text.splitlines():
        if line.startswith("|") and code in line:
            m = re.search(r"\*\*([ABCD])\*\*", line)
            if m:
                return m.group(1)
    return wi.UNKNOWN


def issues() -> list[dict]:
    recs = []
    for src in sorted((MIG / "sources").glob("*.md")):
        raw = src.read_bytes(); text = raw.decode("utf-8")
        for six in parse_six(text):
            inv = INVARIANT_FILES.get(six["failed_predicate"])
            body = {"schema": wi.ISSUE_SCHEMA,
                    "disposition": {"disposition": "FAIL_CLOSED", **six},
                    "violated_invariant": ({"rule_id": six["failed_predicate"], "repository": inv[0], "file": inv[1], "blob_sha": inv[2], "invariant_declared": True}
                                           if inv else {"rule_id": six["failed_predicate"], "repository": "StegVerse-Labs/.github",
                                                        "file": str(src.relative_to(ROOT)), "blob_sha": None, "invariant_declared": False}),
                    "source_receipt": {"kind": "MIGRATION_EVIDENCE", "evidence_path": str(src.relative_to(ROOT)),
                                       "evidence_sha256": "sha256:" + hashlib.sha256(raw).hexdigest()},
                    "resolution_class": resolution_class(text, six["failure_code"]),
                    "surface": mg.derive_surface(six["retry_entrypoint"]),
                    "lifecycle_state": "OPENED", "observed_base": dict(LABS_BASE),
                    "migration_provenance": mg.provenance(LABS_BASE),
                    "owning_goal": six["owning_existing_goal"], "opened_by_session": SESSION, "hb_epoch": wi.UNKNOWN}
            recs.append(mg.finish_issue(body))
    return mg.merge_issues(recs)[0]


# which migrated issues each P1 change resolves: (failure_code, retry_entrypoint substring), as cited in the change
CHANGE_RESOLVES = {3225: [("SHARED_LEDGER_COMPONENT_NOT_PUBLISHED", "")], 3226: [("SHARED_LEDGER_COMPONENT_NOT_PUBLISHED", "")],
                   3234: [("ECOSYSTEM_CAPABILITY_ABSENT", "")],
                   None: [("CLOCK_DERIVED_EPOCH_ADMITTED_BY_ORG_APPEND", "kernel.py"), ("HB_EPOCH_REFUSAL_NOT_SIX_FIELD_AT_CLI", ""),
                          ("HB_EPOCH_CLI_COERCED", "")]}
OBSERVED_CHANGE_FIELDS = ("schema", "target_repository", "base_ref", "content", "projection", "declared_session", "owning_goal",
                          "lifecycle_state", "required_checks_ref", "signoffs", "validation_receipts", "admission_order_slot",
                          "supersedes", "governance_decision_ref")


def changes(issue_rows: list[dict]) -> list[dict]:
    rows = [json.loads(l) for l in (MIG / "sv-changes.jsonl").read_text().splitlines() if l.strip()]
    out = []
    for r in rows:
        body = {k: r[k] for k in OBSERVED_CHANGE_FIELDS if k in r}
        body["content"] = [{**c, "writer_session": mg._writer(c["writer_session"])} for c in r["content"]]
        body["resolves"] = sorted({i["issue_id"] for code, sub in CHANGE_RESOLVES[r["projection"]["pr"]] for i in issue_rows
                                   if i["disposition"]["failure_code"] == code and sub in i["disposition"]["retry_entrypoint"]})
        body["hb_epoch"] = wi.UNKNOWN
        body["migration_provenance"] = mg.provenance(r["base_ref"])
        out.append(mg.finish_change(body))
    return out


def known_good(kind_path: str) -> dict:
    """A known-good SV_CHANGE observation touching one surface kind (positive control)."""
    content = [{"path": kind_path, "blob_digest": "sha256:" + "a" * 64, "writer_session": {"session": SESSION, "evidence_class": "DECLARED"}}]
    digest = wi.change_digest(content)
    checks, signoffs = wi.required_for([kind_path])
    ch = {"schema": wi.CHANGE_SCHEMA, "record_mode": "NATIVE", "target_repository": "StegVerse-Labs/.github", "resolves": ["svi:" + "0" * 64],
          "owning_goal": "StegVerse-org/.github#163", "declared_session": SESSION, "base_ref": dict(LABS_BASE),
          "head": {"change_digest": digest}, "content": content, "touched_paths": [kind_path], "lifecycle_state": "VERIFIED",
          "required_checks_ref": {"file": "data/sv-work-items/required-checks.json", "blob_sha": "WORKTREE", "row_id": "SV-CHANGE-REQUIRED-CHECKS-001"},
          "validation_receipts": [ledger_receipt(c, digest) for c in checks],
          "signoffs": [{"role": r, "session": "fixture-owner", "receipt_ref": "fixture:signoff:" + r} for r in signoffs],
          "hb_epoch": FIXTURE_HB_EPOCH}
    ch["change_id"] = wi.change_identity(ch)
    ch["request_digest"] = wi.request_digest(ch)
    return wi.admission_inputs(wi.validate_change(ch), LABS_BASE)


def ledger_receipt(check_id: str, digest: str, disposition: str = "ALLOW") -> dict:
    """A fixture LEDGER_RECEIPT reference (positive controls only; not a real receipt)."""
    body = {"check_id": check_id, "disposition": disposition, "change_digest": digest}
    return {**body, "evidence_class": "LEDGER_RECEIPT", "ref": wi.LEDGER_REF + "#fixture:" + check_id, "digest": wi.sha(body)}


SURFACE_PATH = {"transition": "resident-runtime/example_transition.py", "ledger_writer": "resident-runtime/aggregate_repo_transition.py",
                "workflow": ".github/workflows/example.yml", "schema": "schemas/example.schema.json", "registry": "data/canonical-task-registry.json"}
REFS = {"MERGE_AUTHORITY": {"file": "KV INDEX.md#MERGE AUTHORITY", "blob_sha": None, "rule_id": None},
        "ST019": {"file": "StegVerse-Labs/repo-standards:config/repository-protection-policy.json#merge_admission", "blob_sha": "ce3d413d62022ef60c9bfc8dda516dc56fb0eefb", "rule_id": "ST019-MERGE-ADMISSION-001"}}
# (predicate, surface, origin scenarios) -- A6 plus Lane C's minimal seed (#3241, #3245) extended
SEEDS = [
    ("MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "workflow", ["StegVerse-Labs/.github#3241 CHECK_SKIPPED_OR_UNOBSERVED"]),
    ("MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "transition", ["StegVerse-Labs/.github#3244 SPPA fail-open (correction #167 c6249647656)"]),
    ("BRANCH_WRITER_IS_BRANCH_OWNER", "transition", ["StegVerse-Labs/.github#3245 foreign writer", "StegVerse-org/StegVerse-SDK#533 cross-branch pushes"]),
    ("BASE_IS_CURRENT", "transition", ["StegVerse-org/StegVerse-SDK#546 stale-base merge"]),
    ("AUTHORIZATION_BINDS_FULL_REQUEST", "transition", ["StegVerse-Labs/TVC#526 RELEASE_POLICY_FIELDS_NOT_BOUND_TO_GOVERNANCE_SUBJECT (repair TVC#527)"]),
    ("VALIDATION_RECEIPT_BINDS_EXACT_HEAD", "transition", ["StegVerse-Labs/.github#3246 SDK_ENTRYPOINT_RESOLVED_FROM_PROCESS_MODULE_CACHE"]),
    ("REQUIRED_SIGNOFF_RECORDED", "ledger_writer", ["StegVerse-org/.github#189 merged without ledger-component-owner sign-off (merge 40a5d235)"]),
    ("MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "ledger_writer", ["StegVerse-org/.github#189 epoch binder gaps (189-binder-check rows 1, 5b, 6, 8, 13, 15)"]),
    ("PR_AUTHOR_SESSION_DECLARED", "schema", ["KV INDEX MERGE AUTHORITY PR_AUTHOR_SESSION_DECLARED (12:47Z)"]),
    ("MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "registry", ["Labs registry gen 319 fence (ST019 generation_fenced_files)"]),
]


def corpus() -> tuple[list[dict], list[dict], list[dict]]:
    classes, scenarios, receipts = [], [], []
    for pred, surface, origins in SEEDS:
        cls = al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=origins,
                            rule_refs=[REFS["MERGE_AUTHORITY"], REFS["ST019"]], declared_by_session=SESSION,
                            harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH)
        gen = al.generate(cls, known_good(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH)
        gen = [s if s["expected_disposition"] == "ALLOW" or not origins else wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
               "source": {**s["source"], "origin_scenarios": origins}}, "scenario_sha256") for s in gen]
        out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
        if out["disposition"] != "ALLOW":
            raise SystemExit(json.dumps(out, sort_keys=True))
        classes += out["append_classes"]; scenarios += out["append_scenarios"]
        receipts.append({k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cls["class_id"]})
    return classes, scenarios, receipts


def _jsonl(rows): return "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows)


def build() -> dict[Path, str]:
    c, s, r = corpus()
    iss = issues()
    return {MIG / "sv-issues.jsonl": _jsonl(iss), MIG / "sv-changes.jsonl": _jsonl(changes(iss)), SCN / "classes.jsonl": _jsonl(c), SCN / "corpus.jsonl": _jsonl(s),
            SCN / "seed-append-outcomes.jsonl": _jsonl(r)}


def main(argv=None) -> int:
    a = argparse.ArgumentParser(); a.add_argument("--check", action="store_true"); args = a.parse_args(argv)
    out = build(); stale = [str(p.relative_to(ROOT)) for p, t in out.items() if not p.exists() or p.read_text() != t]
    if args.check:
        print(json.dumps({"disposition": "ALLOW" if not stale else "FAIL_CLOSED", "stale": stale}, sort_keys=True)); return 1 if stale else 0
    for p, t in out.items():
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    print(json.dumps({"written": sorted(str(p.relative_to(ROOT)) for p in out)})); return 0


if __name__ == "__main__":
    sys.exit(main())
