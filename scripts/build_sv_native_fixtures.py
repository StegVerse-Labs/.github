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
REQUIRED_CHECKS_FILE = "data/sv-work-items/required-checks.json"
REQUIRED_CHECKS_BLOB = mg.git_blob((ROOT / REQUIRED_CHECKS_FILE).read_bytes())  # the row file's git blob as committed
FIXTURE_SIGNOFF_SESSION = "fixture-owner"
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


def known_good_change(kind_path: str) -> dict:
    """The full known-good NATIVE SV_CHANGE touching one surface kind (valid under the tightened sv-change.v1)."""
    content = [{"path": kind_path, "blob_digest": "sha256:" + "a" * 64, "deleted": False, "writer_session": {"session": SESSION, "evidence_class": "DECLARED"}}]
    digest = wi.change_digest({"target_repository": "StegVerse-Labs/.github", "base_ref": dict(LABS_BASE), "content": content})
    checks, signoffs = wi.required_for([kind_path])
    change_id = wi.change_identity({"target_repository": "StegVerse-Labs/.github", "base_ref": dict(LABS_BASE), "content": content})
    ch = {"schema": wi.CHANGE_SCHEMA, "record_mode": "NATIVE", "target_repository": "StegVerse-Labs/.github", "resolves": ["svi:" + "0" * 64],
          "owning_goal": "StegVerse-org/.github#163", "declared_session": SESSION, "base_ref": dict(LABS_BASE),
          "head": {"change_digest": digest}, "content": content, "touched_paths": [kind_path], "lifecycle_state": "VERIFIED",
          "required_checks_ref": {"file": REQUIRED_CHECKS_FILE, "blob_sha": REQUIRED_CHECKS_BLOB, "row_id": "SV-CHANGE-REQUIRED-CHECKS-001"},
          "validation_receipts": [ledger_receipt(c, digest) for c in checks],
          "signoffs": [{"role": r, "session": FIXTURE_SIGNOFF_SESSION, "receipt_ref": fixture_signoff_receipt(r, change_id, digest)["receipt_sha256"]}
                       for r in signoffs],
          "hb_epoch": FIXTURE_HB_EPOCH}
    ch["change_id"] = wi.change_identity(ch)
    ch["request_digest"] = wi.request_digest(ch)
    return wi.validate_change(ch)


def fixture_signoff_receipt(role: str, change_id: str, change_digest: str) -> dict:
    """FIXTURE ONLY (TVC#519 seed convention): a sealed sign-off receipt for a positive control. No owner signed
    anything: session and disposition are fixture pins listed in unobserved_fields, fixture_only is true, and
    sv_work_items.signoff_resolves counts it only in fixture_mode, never on the real admission path."""
    return wi.seal({"schema": wi.SIGNOFF_RECEIPT_SCHEMA, "role": role, "session": FIXTURE_SIGNOFF_SESSION, "change_id": change_id,
                    "change_digest": change_digest, "disposition": "ALLOW", "fixture_only": True,
                    "unobserved_fields": ["session", "disposition"]}, "receipt_sha256")


def signoff_receipts_for(ch: dict) -> list[dict]:
    return [fixture_signoff_receipt(s["role"], ch["change_id"], ch["head"]["change_digest"]) for s in ch.get("signoffs") or []]


def fixture_base_state_readback(base: dict = LABS_BASE, hb_epoch: str = FIXTURE_HB_EPOCH) -> dict:
    """FIXTURE ONLY: a sealed ALLOW base-state readback receipt in the shape of Lane C's RTC-SV-CHANGE-BASE-STATE-
    READBACK-014 (Labs#3266; the epoch slot as in its working tree after JD-P4-3) for the positive controls. Nothing
    was read: fixture_only is true, the values no readback observed are UNKNOWN and listed in unobserved_fields, and
    sv_work_items.verify_admission_hb_epoch counts it only in fixture_mode."""
    return wi.seal({"schema": wi.BASE_STATE_READBACK_SCHEMA, "component_id": "RTC-SV-CHANGE-BASE-STATE-READBACK-014",
                    "repository": "StegVerse-Labs/.github", "base_ref": dict(base), "bound_main_commit": wi.UNKNOWN,
                    "sources": [], "hb_epoch": hb_epoch,
                    "hb_epoch_source": {"ledger_head": base["ledger_head"], "receipt_sha256": wi.UNKNOWN, "field": wi.HB_EPOCH_SOURCE_FIELD,
                                        "validated_by": "org-kernel/kernel.py::supplied_epoch_failure sha256:" + wi.SUPPLIED_EPOCH_RULE_SHA256},
                    "disposition": "ALLOW", "authority_effect": "NONE_READBACK_ONLY", "readback_writes": False, "fixture_only": True,
                    "unobserved_fields": ["bound_main_commit", "hb_epoch", "hb_epoch_source/receipt_sha256", "sources"]}, "result_sha256")


def known_good(kind_path: str) -> dict:
    """A known-good SV_CHANGE observation touching one surface kind (positive control)."""
    ch = known_good_change(kind_path)
    return wi.admission_inputs(ch, LABS_BASE, signoff_receipts_for(ch), fixture_base_state_readback())


# (d) TVC#519 replay: which SV_CHANGE field (or replay input) each mutation axis changes
AXIS_TARGET = {
    "writer_sessions": ("SV_CHANGE", "/content/0/writer_session", "the content entry's writer is a session other than declared_session"),
    "current_base.registry_generation": ("REPLAY_INPUT", "/current_base/registry_generation", "current base moved; the SV_CHANGE is unchanged"),
    "current_base.ledger_head": ("REPLAY_INPUT", "/current_base/ledger_head", "current base moved; the SV_CHANGE is unchanged"),
    "validation_receipts[required_check_ids[0]]": ("SV_CHANGE", "/validation_receipts", "drop the receipt of the first required check id"),
    "validation_receipts[*].ref": ("SV_CHANGE", "/validation_receipts/*/ref", "set every ref to the empty string"),
    "validation_receipts[*].evidence_class": ("SV_CHANGE", "/validation_receipts/*/evidence_class", "set every evidence_class to OBSERVED_ARTIFACT"),
    "validation_receipts[*].change_digest": ("SV_CHANGE", "/validation_receipts/*/change_digest", "bind every receipt to another digest"),
    "bound_request_digest": ("SV_CHANGE", "/request_digest", "bind the decision to a different request digest"),
    "declared_session": ("SV_CHANGE", "/declared_session", "empty the declared session"),
    "signoffs": ("SV_CHANGE", "/signoffs", "drop every sign-off"),
    "signoffs[*].receipt_ref": ("SV_CHANGE", "/signoffs/*/receipt_ref", "set every sign-off receipt_ref to the empty string"),
    "validation_receipts[0].disposition": ("SV_CHANGE", "/validation_receipts/0/disposition", "the first receipt is not ALLOW"),
    "content[*].writer_session.evidence_class": ("SV_CHANGE", "/content/*/writer_session",
                                                 "every writer_session -> {session: null, evidence_class: UNKNOWN_NOT_AUTHENTICALLY_OBSERVED}"),
    "hb_epoch_readback": ("REPLAY_INPUT", "/hb_epoch_readback", "no base-state readback receipt (null)"),
    "hb_epoch_readback.result_sha256": ("REPLAY_INPUT", "/hb_epoch_readback/result_sha256", "break the readback's seal"),
    "hb_epoch_readback.hb_epoch_source.derived_from_clock": ("REPLAY_INPUT", "/hb_epoch_readback/hb_epoch_source/derived_from_clock",
                                                             "the sealed epoch's source reference is derived from a clock (resealed)"),
    "hb_epoch_readback.hb_epoch": ("REPLAY_INPUT", "/hb_epoch_readback/hb_epoch", "the sealed epoch slot is a JSON float (resealed)"),
    "supplied_hb_epoch": ("SV_CHANGE", "/hb_epoch", "the SV_CHANGE's hb_epoch is the sealed epoch + 1"),
}
FOREIGN_SESSION = "FOREIGN-SESSION"  # fixture: the session admission_learning._foreign adds


def axis_value(axis: str, expected_code: str | None):
    """The concrete value each replay mutation writes (the same values admission_learning's mutations use)."""
    return {"writer_sessions": {"session": FOREIGN_SESSION, "evidence_class": "DECLARED"},
            "validation_receipts[*].ref": "", "validation_receipts[*].evidence_class": "OBSERVED_ARTIFACT",
            "validation_receipts[*].change_digest": "sha256:" + "0" * 64, "bound_request_digest": "sha256:" + "1" * 64,
            "declared_session": "", "signoffs": [], "signoffs[*].receipt_ref": "",
            "content[*].writer_session.evidence_class": {"session": None, "evidence_class": wi.UNKNOWN},
            "validation_receipts[0].disposition": "DENY" if expected_code == "REQUIRED_CHECK_DENIED" else "FAIL_CLOSED",
            "supplied_hb_epoch": str(int(FIXTURE_HB_EPOCH) + 1)}.get(axis)


def apply_replay_mutation(ch: dict, m: dict | None) -> dict:
    """Apply one replay-map mutation to a full SV_CHANGE. Unless the mutation targets request_digest itself, the
    request digest is re-bound afterwards (rebind_request_digest), so the scenario fires its own predicate."""
    ch = json.loads(json.dumps(ch))
    if m is None or m["applies_to"] == "REPLAY_INPUT":
        return ch
    axis, v = m["axis"], m["value"]
    if axis == "writer_sessions":
        ch["content"][0]["writer_session"] = dict(v)
    elif axis == "content[*].writer_session.evidence_class":
        ch["content"] = [{**c, "writer_session": dict(v)} for c in ch["content"]]
    elif axis == "validation_receipts[required_check_ids[0]]":
        first = wi.required_for(ch["touched_paths"])[0][0]
        ch["validation_receipts"] = [r for r in ch["validation_receipts"] if r["check_id"] != first]
    elif axis.startswith("validation_receipts[*]."):
        f = axis.split(".", 1)[1]
        ch["validation_receipts"] = [{**r, f: v} for r in ch["validation_receipts"]]
    elif axis == "validation_receipts[0].disposition":
        ch["validation_receipts"][0] = {**ch["validation_receipts"][0], "disposition": v}
    elif axis == "bound_request_digest":
        ch["request_digest"] = v
    elif axis == "declared_session":
        ch["declared_session"] = v
    elif axis == "signoffs":
        ch["signoffs"] = list(v)
    elif axis == "signoffs[*].receipt_ref":
        ch["signoffs"] = [{**s, "receipt_ref": v} for s in ch["signoffs"]]
    elif axis == "supplied_hb_epoch":
        ch["hb_epoch"] = v
    else:
        raise SystemExit(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "REPLAY_AXIS_UNDECLARED", "axis": axis}))
    if m["rebind_request_digest"]:
        ch["request_digest"] = wi.request_digest(ch)
    return ch


def replay(scenarios: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    """Each corpus scenario references the full known-good SV_CHANGE of its class's surface plus the one mutation
    (an SV_CHANGE pointer or a replay input) its axis applies; positive controls apply none."""
    changes, rows = {}, []
    for sc in scenarios:
        path = sc["observed_inputs"]["touched_paths"][0]
        ch = changes.setdefault(path, known_good_change(path))
        axis = sc["generated_from"]["axis"]
        tgt = AXIS_TARGET[axis] if axis is not None else None
        mut = None if tgt is None else {"axis": axis, "applies_to": tgt[0], "pointer": tgt[1], "operation": tgt[2],
                                        "value": None if tgt[0] == "REPLAY_INPUT" else axis_value(axis, sc["expected_failure_code"]),
                                        "rebind_request_digest": tgt[0] == "SV_CHANGE" and tgt[1] != "/request_digest"}
        rows.append({"scenario_id": sc["scenario_id"], "scenario_sha256": sc["scenario_sha256"], "sv_change_id": ch["change_id"],
                     "current_base": sc["observed_inputs"]["current_base"] if tgt and tgt[0] == "REPLAY_INPUT" else dict(LABS_BASE),
                     "signoff_receipts": [r["receipt_sha256"] for r in signoff_receipts_for(ch)],
                     "hb_epoch_readback": sc["observed_inputs"]["hb_epoch_readback"],
                     "mutation": mut, "expected_disposition": sc["expected_disposition"], "expected_failure_code": sc["expected_failure_code"]})
    signoffs = {r["receipt_sha256"]: r for ch in changes.values() for r in signoff_receipts_for(ch)}
    return sorted(changes.values(), key=lambda c: c["change_id"]), rows, [signoffs[k] for k in sorted(signoffs)]


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
    ("RECEIPT_CHANGE_DIGEST_EQUALS_HEAD", "transition", ["StegVerse-Labs/.github#3246 SDK_ENTRYPOINT_RESOLVED_FROM_PROCESS_MODULE_CACHE"]),
    ("REQUIRED_SIGNOFF_RECORDED", "ledger_writer", ["StegVerse-org/.github#189 merged without ledger-component-owner sign-off (merge 40a5d235)"]),
    ("MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "ledger_writer", ["StegVerse-org/.github#189 epoch binder gaps (189-binder-check rows 1, 5b, 6, 8, 13, 15)"]),
    ("PR_AUTHOR_SESSION_DECLARED", "schema", ["KV INDEX MERGE AUTHORITY PR_AUTHOR_SESSION_DECLARED (12:47Z)"]),
    ("MERGE_READY_REQUIRES_EVERY_JOB_RAN_AND_PASSED", "registry", ["Labs registry gen 319 fence (ST019 generation_fenced_files)"]),
]


# Harvested through SCENARIO_CORPUS_APPEND (not hand-edited). Observed locally: the commit was re-fetched by sha and
# its tree verified (commit, parent, tree, touched paths below). The push time, the restore time and the lost reflog
# entry come from the orchestrator's report, for which no ledger receipt is held: flagged in unobserved_fields.
HARVEST_LOCATOR = "orchestrator:2026-10-18T14:31Z:org#192@f108ed0a"
HARVESTED = [{
    "disposition": "FAIL_CLOSED", "failure_code": "BRANCH_WRITER_UNOBSERVED", "failed_predicate": "BRANCH_WRITER_IS_BRANCH_OWNER",
    "required_evidence_or_repair": "a durable push-time writer receipt (sv-push-receipt, being built by Lane C) for the push of "
                                   "f108ed0a to StegVerse-org/.github#192; a re-fetched, tree-verified commit is not writer evidence "
                                   "and no reflog is reconstructed",
    "retry_entrypoint": "resident-runtime/sv_work_items.py::evaluate_admission",
    "owning_existing_goal": "StegVerse-org/.github#163",
    "next_attempt": "after Lane C's sv-push-receipt exists and a push-time writer receipt for the org#192 push is on the ledger; "
                    "until then the writer stays UNKNOWN_NOT_AUTHENTICALLY_OBSERVED and the range base never overrides it",
    "touched_surface_kinds": ["transition"], "class_name": "WRITER_EVIDENCE_LOST_BY_SNAPSHOT_RESTORE",
    "source_receipt_ref": HARVEST_LOCATOR,
    "observed_case": {"repository": "StegVerse-org/.github", "pull_request": "StegVerse-org/.github#192",
                      "commit": "f108ed0a7b85b80ca91af5664011115bcb7d34f1", "parent": "af556c9dfecf0a68edf3547e84586af0f7d23bfe",
                      "tree": "32a4e47ace8726706c7d30017e18476faf4f79fd",
                      "touched_paths": ["resident-runtime/admission_predicate.py", "tests/test_admission_predicate.py"],
                      "commit_refetched_by_sha_and_tree_verified": True, "reflog_reconstructed": False,
                      "push_time": "2026-10-18T13:54:46Z", "snapshot_restore_time": "about 2026-10-18T13:55Z",
                      "writer_session": {"session": None, "evidence_class": wi.UNKNOWN}},
    "unobserved_fields": ["source_receipt_ref", "observed_case/push_time", "observed_case/snapshot_restore_time",
                          "observed_case/writer_session"],
}]


def harvest_append(classes: list[dict], scenarios: list[dict]) -> list[dict]:
    """harvest -> generalize (class rule) -> generate -> corpus_append for each HARVESTED outcome."""
    receipts = []
    for cand in al.harvest(HARVESTED):
        surface = cand["surfaces"][0]
        cid = al.class_id_for(cand["failed_predicate"], surface)
        prior = al.latest_classes(classes).get(cid)
        name = cand["source"]["class_name"]
        cls = al.generalize({**cand, "class_name": name}, surface=surface,
                            origin_scenarios=["%s %s (%s)" % (cand["source"]["observed_case"]["pull_request"], name, HARVEST_LOCATOR)],
                            rule_refs=[REFS["MERGE_AUTHORITY"], REFS["ST019"]], declared_by_session=SESSION,
                            harvest_receipt_ref=HARVEST_LOCATOR, hb_epoch=FIXTURE_HB_EPOCH, prior=prior,
                            class_version=(prior or {}).get("class_version", 0) + 1,
                            supersedes=(prior or {}).get("class_sha256"), provenance_unobserved=["harvest_receipt_ref"])
        have = {s["scenario_id"] for s in scenarios}
        gen = [s for s in al.generate(cls, known_good(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH) if s["scenario_id"] not in have]
        axis = next(a["field"] for a in cls["mutation_axes"] if a.get("expected_failure_code") == cand["failure_code"])
        neg = next(s for s in gen if s["generated_from"]["axis"] == axis)
        body = {k: v for k, v in neg.items() if k != "scenario_sha256"}
        gen.append(wi.seal({**body, "scenario_id": "%s/harvested/%s@%s@%s" % (cid, name, cand["source"]["observed_case"]["pull_request"],
                                                                            cand["source"]["observed_case"]["commit"][:8]),
                            "origin": "HARVESTED", "source": {**cand["source"], "class_sha256": cls["class_sha256"]}}, "scenario_sha256"))
        out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
        if out["disposition"] != "ALLOW":
            raise SystemExit(json.dumps(out, sort_keys=True))
        classes += out["append_classes"]; scenarios += out["append_scenarios"]
        receipts.append({k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cid})
    return receipts


# JD-P4-3, part-decided by invariant (orchestrator 15:09Z): appended through SCENARIO_CORPUS_APPEND after the harvest.
# Class rule: (ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH, ledger_writer) -- the surface whose row requires the
# supplied-epoch-binder-check. No existing class has this predicate, so it is a new class (v1).
EPOCH_BINDING_SEED = ("ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH", "ledger_writer",
                      ["orchestrator 2026-10-18T15:09Z JD-P4-3 part-decided: ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH "
                       "(Labs#3266 readback seals the bound ledger head's epoch)",
                       "StegVerse-org/.github#189 epoch binder gaps (189-binder-check rows)"])
EPOCH_RULE_REFS = [{"file": "data/sv-work-items/invariants.json#ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH", "blob_sha": None,
                    "rule_id": "ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH"},
                   {"file": "StegVerse-Labs/.github:org-kernel/kernel.py#supplied_epoch_failure", "blob_sha": INVARIANT_FILES[wi.EPOCH_PREDICATE][2],
                    "rule_id": "SUBMISSION_CARRIES_THE_SUPPLIED_HB_EPOCH"}]


def epoch_binding_append(classes: list[dict], scenarios: list[dict]) -> list[dict]:
    pred, surface, origins = EPOCH_BINDING_SEED
    prior = al.latest_classes(classes).get(al.class_id_for(pred, surface))
    if prior is not None:  # the class rule maps onto an existing class: never a duplicate
        raise SystemExit(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "CLASS_EXISTS", "class_id": prior["class_id"]}))
    cls = al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=origins, rule_refs=EPOCH_RULE_REFS,
                        declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH)
    gen = al.generate(cls, known_good(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH)
    gen = [s if s["expected_disposition"] == "ALLOW" else wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
           "source": {**s["source"], "origin_scenarios": origins}}, "scenario_sha256") for s in gen]
    out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
    if out["disposition"] != "ALLOW":
        raise SystemExit(json.dumps(out, sort_keys=True))
    classes += out["append_classes"]; scenarios += out["append_scenarios"]
    return [{k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cls["class_id"]}]


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
    receipts += harvest_append(classes, scenarios)
    receipts += epoch_binding_append(classes, scenarios)
    return classes, scenarios, receipts


def _jsonl(rows): return "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows)


def build() -> dict[Path, str]:
    c, s, r = corpus()
    iss = issues()
    return {MIG / "sv-issues.jsonl": _jsonl(iss), MIG / "sv-changes.jsonl": _jsonl(changes(iss)), SCN / "classes.jsonl": _jsonl(c), SCN / "corpus.jsonl": _jsonl(s),
            SCN / "seed-append-outcomes.jsonl": _jsonl(r),
            **dict(zip((SCN / "tvc-replay/sv-changes.jsonl", SCN / "tvc-replay/replay-map.jsonl", SCN / "tvc-replay/signoff-receipts.jsonl"),
                       map(_jsonl, replay(s))))}


def pin_violations(out: dict[Path, str]) -> list[dict]:
    """Every emitted required_checks_ref.blob_sha is a 40-hex git blob (UNKNOWN only in a MIGRATED_HISTORICAL record);
    no placeholder such as WORKTREE is ever written."""
    bad = []
    for p, text in out.items():
        for n, line in enumerate(text.splitlines()):
            if "WORKTREE" in line:
                bad.append({"file": str(p.relative_to(ROOT)), "line": n + 1, "found": "WORKTREE"})
            rec = json.loads(line)
            ref = rec.get("required_checks_ref") if isinstance(rec, dict) else None
            if isinstance(ref, dict):
                b = ref.get("blob_sha")
                ok = isinstance(b, str) and re.fullmatch(r"[0-9a-f]{40}", b) is not None
                if not ok and not (b == wi.UNKNOWN and rec.get("record_mode") == "MIGRATED_HISTORICAL"):
                    bad.append({"file": str(p.relative_to(ROOT)), "line": n + 1, "blob_sha": b})
    return bad


def main(argv=None) -> int:
    a = argparse.ArgumentParser(); a.add_argument("--check", action="store_true"); args = a.parse_args(argv)
    out = build(); stale = [str(p.relative_to(ROOT)) for p, t in out.items() if not p.exists() or p.read_text() != t]
    bad = pin_violations(out)
    if bad:  # FAIL_CLOSED in both modes: nothing with an unpinned row is written
        print(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "REQUIRED_CHECKS_ROW_NOT_PINNED", "violations": bad}, sort_keys=True))
        return 1
    if args.check:
        print(json.dumps({"disposition": "ALLOW" if not stale else "FAIL_CLOSED", "stale": stale}, sort_keys=True)); return 1 if stale else 0
    for p, t in out.items():
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    print(json.dumps({"written": sorted(str(p.relative_to(ROOT)) for p in out)})); return 0


if __name__ == "__main__":
    sys.exit(main())
