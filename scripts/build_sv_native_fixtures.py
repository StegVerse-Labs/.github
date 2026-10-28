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
ss = _load("schema_subset", "resident-runtime/schema_subset.py")

# Commit 5: the epoch the shared #3266 readback fixture observed at ledger head a5bb54d8 (receipt 35810b65), so the corpus
# and the positive controls carry the observed epoch, not a fixture value
FIXTURE_HB_EPOCH = "469411750"
# The shared base-state readback fixture TVC#519 and P4 org#192 adopt, byte-for-byte (blob cfaaec20; TVC#519 @fe768899
# tests/fixtures/base-state-readback/, = P4 org#192 @be38e05c labs-main-978b8880-producer-9c9b9f51.json): the unmodified
# Labs#3266 producer's omitted-flag ALLOW at Labs main 978b8880 / ledger a5bb54d8 (result_sha256 0653c219)
SHARED_READBACK_DIR = ROOT / "tests/fixtures/base-state-readback"
SHARED_READBACK = SHARED_READBACK_DIR / "labs-main-978b8880-producer-7ad6d81f.json"
SHARED_READBACK_BLOB = "cfaaec20bbf05e12826be99a89b3befa1c3e30a7"
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


def shared_readback() -> dict:
    """The shared fixture (SHARED_READBACK), parsed from its exact bytes; refuses if the bytes are not blob cfaaec20."""
    data = SHARED_READBACK.read_bytes()
    if git_blob_sha(data) != SHARED_READBACK_BLOB:
        raise SystemExit("shared readback fixture drifted from blob " + SHARED_READBACK_BLOB)
    return json.loads(data)


def fixture_base_state_readback(base: dict = LABS_BASE, hb_epoch: str = FIXTURE_HB_EPOCH) -> dict:
    """The base-state readback for the positive controls and the corpus. With the defaults (LABS_BASE, the observed epoch)
    this is the SHARED fixture, the unmodified Labs#3266 producer's sealed omitted-flag ALLOW at ledger head a5bb54d8 that
    TVC#519 and P4 org#192 adopt (commit 5), byte-for-byte. Any other base or epoch is a FIXTURE ONLY synthetic receipt in
    the producer's shape: fixture_only true, unobserved values UNKNOWN and listed, counted only in fixture_mode."""
    if dict(base) == LABS_BASE and hb_epoch == FIXTURE_HB_EPOCH:
        return shared_readback()
    return wi.seal({"schema": wi.BASE_STATE_READBACK_SCHEMA, "component_id": "RTC-SV-CHANGE-BASE-STATE-READBACK-014",
                    "repository": "StegVerse-Labs/.github", "base_ref": dict(base), "bound_main_commit": wi.UNKNOWN,
                    "sources": [], "hb_epoch": hb_epoch,
                    "hb_epoch_source": {"ledger_head": base["ledger_head"], "receipt": wi.UNKNOWN, "field": wi.HB_EPOCH_SOURCE_FIELD},
                    "disposition": "ALLOW", "authority_effect": "NONE_READBACK_ONLY", "readback_writes": False, "fixture_only": True,
                    # ruling ~17:15Z: the producer always emits cross_checked; the fixture is the omitted-flag ALLOW
                    "cross_checked": False, "detail": wi.NOT_CROSS_CHECKED_DETAIL,
                    "unobserved_fields": ["bound_main_commit", "hb_epoch", "hb_epoch_source/receipt", "sources"]}, "result_sha256")


FIXTURE_GATE_RECEIPT_HEX = "0" * 64  # fixture: no receipt was read; every value below is fixture_only
FIXTURE_LEDGER_COMMIT = "0" * 40


def fixture_resolved_issues(ch: dict) -> list[dict]:
    """Fixture facts for the issue each known-good change cites, in the shape sv_work_items.resolved_issue_facts emits
    for a stage-gate-derived issue (STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE): emitted by the NWI-S1 verifier, appended by
    the org writer, not touched by the change, the receipt's only issue, unresolved. Nothing was read: fixture_only is
    true and the ledger values are listed in unobserved_fields; counted only in fixture_mode."""
    return [{"issue_id": i, "record_mode": "NATIVE", "source_kind": "ORGANIZATION_LEDGER_RECEIPT", "lifecycle_state": "CLAIMED",
             "resolved_by": None, "fixture_only": True, "check_id": "nwi-s0-exit-gate",
             "ledger_ref": wi.LEDGER_REF + "@" + FIXTURE_LEDGER_COMMIT + ":receipts/" + FIXTURE_GATE_RECEIPT_HEX + ".json",
             "receipt_sha256": "sha256:" + FIXTURE_GATE_RECEIPT_HEX,
             "receipt_ledger_paths": ["receipts/" + FIXTURE_GATE_RECEIPT_HEX + ".json", "source-receipts/" + FIXTURE_GATE_RECEIPT_HEX + ".json"],
             "receipt_file_sha256": ["sha256:" + FIXTURE_GATE_RECEIPT_HEX], "verifier_ref": wi.S1_VERIFIER_REF,
             "emitter_session": wi.S1_VERIFIER_REF, "derived_issue_ids_from_receipt": [i],
             "unobserved_fields": ["ledger_ref", "receipt_file_sha256", "receipt_ledger_paths", "receipt_sha256"]}
            for i in ch["resolves"]]


# GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE (commit 4): the pair Lane B (SV-LLM/.github#46 @9fbc2e92) is producing for #3264:
# the gate ran at the change's head 7898cedb (ALLOW, evaluation af569561) and a base-side evaluation at the change's base 978b8880
# (expected to fail: the head's NWI-S0 gate applied to a tree without its evidence producers). The commits and the manifest blob
# are observed in git (git rev-parse 7898cedb:data/sv-work-items/stages/NWI-S0.json); no receipt was read, so every receipt
# value is a fixture (fixture_only, unobserved_fields) and the pair counts only in fixture_mode, never on the real path.
LANE_B_BASE_COMMIT = "978b8880d238dc3e3a8b690c0675d8bb0e9d6985"
LANE_B_HEAD_COMMIT = "7898cedba1400c8545cebcb463fd26deb25f7d5a"
LANE_B_MANIFEST_BLOB = "20b37917e1454ec788e8f1b8c75d1562ba76d1b3"
FIXTURE_HEAD_GATE_RECEIPT_HEX = "1" * 64
LANE_B_CONTRACT_PINS_SHA256 = "sha256:317aef68d7a875b84633361a25b000810457fbc89b96f735dde3259008b897d7"  # contract-pins.json @7898cedb
LANE_B_MANIFEST_SHA256 = "sha256:f92387e4cd2af861411da101f694eda9cd306833f9857d577573fae3eeace56a"  # NWI-S0.json @7898cedb


def fixture_pair_side(commit: str, disposition: str, receipt_hex: str) -> dict:
    subject = wi.stage_evaluation_subject("StegVerse-Labs/.github", "NWI-S0", LANE_B_MANIFEST_BLOB, commit, LABS_BASE)
    digest = wi.stage_evaluation_digest(subject)
    return {"subject": subject, "subject_digest": digest,
            "receipt": {"receipt_ledger_ref": wi.LEDGER_REF + "@" + FIXTURE_LEDGER_COMMIT + ":receipts/" + receipt_hex + ".json",
                        "check_id": "nwi-s0-exit-gate", "disposition": disposition, "change_digest": digest, "head_sha": commit,
                        "verifier_ref": wi.S1_VERIFIER_REF, "ledgered_at_base": True,
                        "receipt_ledger_paths": ["receipts/" + receipt_hex + ".json", "source-receipts/" + receipt_hex + ".json"],
                        "receipt_file_sha256": ["sha256:" + receipt_hex]}}


def fixture_resolution_pair(ch: dict) -> dict:
    """FIXTURE ONLY: the resolution_pair derive_resolved_issue_facts builds, for the Lane B pair above."""
    return {"rule": wi.GATE_PAIR_PREDICATE, "ledger_head": ch["base_ref"]["ledger_head"], "target_repository": ch["target_repository"],
            "change_commits": {"base_commit": LANE_B_BASE_COMMIT, "head_commit": LANE_B_HEAD_COMMIT}, "manifest_source": wi.MANIFEST_SOURCE,
            # contract-pins.json at 7898cedb pins NWI-S0.json at this blob (manifest sha256 317aef68..., observed in git)
            "pinned_manifest": {"file": "data/sv-work-items/stages/NWI-S0.json", "blob": LANE_B_MANIFEST_BLOB,
                                "sha256": LANE_B_MANIFEST_SHA256, "contract_pins_sha256": LANE_B_CONTRACT_PINS_SHA256},
            "base": fixture_pair_side(LANE_B_BASE_COMMIT, "FAIL_CLOSED", FIXTURE_GATE_RECEIPT_HEX),
            "head": fixture_pair_side(LANE_B_HEAD_COMMIT, "ALLOW", FIXTURE_HEAD_GATE_RECEIPT_HEX)}


def known_good_paired(kind_path: str) -> dict:
    """known_good() whose cited gate-derived issue also carries its fixture resolution_pair (the commit-4 positive control)."""
    obs = known_good(kind_path)
    ch = known_good_change(kind_path)
    obs["resolved_issues"] = [{**f, "resolution_pair": fixture_resolution_pair(ch),
                               "unobserved_fields": sorted(set(f["unobserved_fields"]) | {"resolution_pair/base/receipt",
                                                                                           "resolution_pair/head/receipt"})}
                              for f in obs["resolved_issues"]]
    return obs


# FIXTURE ONLY: the change's commits and the sv-push-receipt.v1 chain (Labs#3267 shape, sealed) its push left; the branch
# writer is derived from it (sv_work_items.derive_branch_writer). Two pushes by SESSION: base -> c1 -> head.
FIXTURE_PUSH_REF = "refs/heads/p1/fixture-sv-change"
FIXTURE_CHANGE_COMMITS = {"base_commit": LANE_B_BASE_COMMIT, "head_commit": LANE_B_HEAD_COMMIT}  # the gate pair's commits
FIXTURE_MID_COMMIT = "c1" * 20


def push_receipt(ch: dict, old_sha: str, new_sha: str, commits: list[str], session: str = SESSION,
                 repository: str | None = None, ref: str = FIXTURE_PUSH_REF, change_id: str | None = None) -> dict:
    """A sealed sv-push-receipt.v1 (the shape resident-runtime/sv_push_receipt.py::emit seals). change_id is optional in
    sv-push-receipt.v1 (a push precedes the record that cites it), so the fixture chain omits it unless one is given."""
    return wi.push_receipt.seal({"schema": wi.push_receipt.RECEIPT_SCHEMA, "repository": repository or ch["target_repository"], "ref": ref,
                                 "old_sha": old_sha, "new_sha": new_sha, "pusher_session": session,
                                 **({"change_id": change_id} if change_id else {}),
                                 "pushed_commits": list(commits), "hb_epoch": FIXTURE_HB_EPOCH})


def fixture_push_receipts(ch: dict, change_commits: dict | None = None, session: str = SESSION) -> list[dict]:
    cc = change_commits or FIXTURE_CHANGE_COMMITS
    if cc == FIXTURE_CHANGE_COMMITS:
        return [push_receipt(ch, cc["base_commit"], FIXTURE_MID_COMMIT, [FIXTURE_MID_COMMIT], session),
                push_receipt(ch, FIXTURE_MID_COMMIT, cc["head_commit"], [cc["head_commit"]], session)]
    return [push_receipt(ch, cc["base_commit"], cc["head_commit"], [cc["head_commit"]], session)]


_DEFAULT = object()


def writer_context(ch: dict, change_commits: dict | None = None, session: str = SESSION) -> dict:
    """transition() context naming the change's fixture push-receipt chain and commits (FIXTURE ONLY)."""
    cc = change_commits or FIXTURE_CHANGE_COMMITS
    return {"push_receipts": fixture_push_receipts(ch, cc, session), "change_commits": cc}


def observe(ch: dict, *args, push_receipts=_DEFAULT, change_commits=_DEFAULT, **kw) -> dict:
    """wi.admission_inputs with the change's fixture push-receipt chain (FIXTURE ONLY) unless push_receipts is supplied.
    With ledger bytes the commits are the caller's (as admission_inputs takes them once), else FIXTURE_CHANGE_COMMITS."""
    if change_commits is _DEFAULT:
        change_commits = None if kw.get("ledger_objects") is not None else FIXTURE_CHANGE_COMMITS
    rs = fixture_push_receipts(ch, change_commits or FIXTURE_CHANGE_COMMITS) if push_receipts is _DEFAULT else push_receipts
    return wi.admission_inputs(ch, *args, push_receipts=rs, change_commits=change_commits, **kw)


def known_good(kind_path: str) -> dict:
    """A known-good SV_CHANGE observation touching one surface kind (positive control)."""
    ch = known_good_change(kind_path)
    return observe(ch, LABS_BASE, signoff_receipts_for(ch), fixture_base_state_readback(), fixture_resolved_issues(ch))


# (d) TVC#519 replay: which SV_CHANGE field (or replay input) each mutation axis changes
AXIS_TARGET = {
    "writer_sessions": ("SV_CHANGE", "/content/0/writer_session",
                        "the content entry's writer is a session other than the one derived from the sv-push-receipt chain"),
    "current_base.registry_generation": ("REPLAY_INPUT", "/current_base/registry_generation", "current base moved; the SV_CHANGE is unchanged"),
    "current_base.ledger_head": ("REPLAY_INPUT", "/current_base/ledger_head", "current base moved; the SV_CHANGE is unchanged"),
    "validation_receipts[required_check_ids[0]]": ("SV_CHANGE", "/validation_receipts", "drop the receipt of the first required check id"),
    "validation_receipts[*].ref": ("SV_CHANGE", "/validation_receipts/*/ref", "set every ref to the empty string"),
    "validation_receipts[*].evidence_class": ("SV_CHANGE", "/validation_receipts/*/evidence_class", "set every evidence_class to OBSERVED_ARTIFACT"),
    "validation_receipts[*].change_digest": ("SV_CHANGE", "/validation_receipts/*/change_digest", "bind every receipt to another digest"),
    "bound_request_digest": ("SV_CHANGE", "/request_digest", "bind the decision to a different request digest"),
    "declared_session": ("REPLAY_INPUT", "/push_receipts", "the SV_CHANGE keeps its declared_session; the replay input push_receipts is null"),
    "signoffs": ("SV_CHANGE", "/signoffs", "drop every sign-off"),
    "signoffs[*].receipt_ref": ("SV_CHANGE", "/signoffs/*/receipt_ref", "set every sign-off receipt_ref to the empty string"),
    "validation_receipts[0].disposition": ("SV_CHANGE", "/validation_receipts/0/disposition", "the first receipt is not ALLOW"),
    "content[*].writer_session.evidence_class": ("SV_CHANGE", "/content/*/writer_session",
                                                 "every writer_session -> {session: null, evidence_class: UNKNOWN_NOT_AUTHENTICALLY_OBSERVED}; "
                                                 "the replay input push_receipts is null (no chain survived)"),
    "hb_epoch_readback": ("REPLAY_INPUT", "/hb_epoch_readback", "no base-state readback receipt (null)"),
    "hb_epoch_readback.result_sha256": ("REPLAY_INPUT", "/hb_epoch_readback/result_sha256", "break the readback's seal"),
    "hb_epoch_readback.hb_epoch_source.derived_from_clock": ("REPLAY_INPUT", "/hb_epoch_readback/hb_epoch_source/derived_from_clock",
                                                             "the sealed epoch's source reference is derived from a clock (resealed)"),
    "hb_epoch_readback.hb_epoch": ("REPLAY_INPUT", "/hb_epoch_readback/hb_epoch", "the sealed epoch slot is a JSON float (resealed)"),
    "supplied_hb_epoch": ("SV_CHANGE", "/hb_epoch", "the SV_CHANGE's hb_epoch is the sealed epoch + 1"),
    "supplied_hb_epoch[UNKNOWN]": ("SV_CHANGE", "/hb_epoch", "the SV_CHANGE's hb_epoch is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"),
    "resolves": ("SV_CHANGE", "/resolves", "the SV_CHANGE cites no SV_ISSUE"),
    "resolved_issues": ("REPLAY_INPUT", "/resolved_issues", "no issue facts: the receipt is not on the ledger, nothing was derived"),
    "resolves[+unobserved]": ("SV_CHANGE", "/resolves", "also cite svi:fff...f, which no observed issue carries"),
    "resolved_issues[0].receipt_ledger_paths": ("REPLAY_INPUT", "/resolved_issues/0/receipt_ledger_paths", "the receipt's ledger paths include a path the change touches"),
    "resolved_issues[0].receipt_file_sha256": ("REPLAY_INPUT", "/resolved_issues/0/receipt_file_sha256", "the receipt's bytes are a blob the change carries"),
    "resolved_issues[0].emitter_session": ("REPLAY_INPUT", "/resolved_issues/0/emitter_session", "the receipt's emitter is the change's branch writer (derived from the push receipts)"),
    "resolved_issues[0].verifier_ref": ("REPLAY_INPUT", "/resolved_issues/0/verifier_ref", "the receipt's verifier_ref is SV-LLM/.github#460"),
    "resolved_issues[0].derived_issue_ids_from_receipt": ("REPLAY_INPUT", "/resolved_issues/0/derived_issue_ids_from_receipt", "a second issue names the receipt"),
    "resolved_issues[0].resolved_by": ("REPLAY_INPUT", "/resolved_issues/0/resolved_by", "another change (svc:eee...e) resolved the issue"),
    "record_mode": ("SV_CHANGE", "/record_mode", "the SV_CHANGE is MIGRATED_HISTORICAL"),
    "owning_goal[UNKNOWN]": ("SV_CHANGE", "/owning_goal", "the NATIVE SV_CHANGE's owning_goal is UNKNOWN_NOT_AUTHENTICALLY_OBSERVED"),
    "resolved_issues[0].record_mode": ("REPLAY_INPUT", "/resolved_issues/0/record_mode", "the cited issue is MIGRATED_HISTORICAL"),
    "supplied_hb_epoch[int]": ("SV_CHANGE", "/hb_epoch", "the SV_CHANGE's hb_epoch is the sealed epoch as a JSON integer"),
    "hb_epoch_readback.hb_epoch_cross_check": ("REPLAY_INPUT", "/hb_epoch_readback/hb_epoch_cross_check",
                                                "the readback carries hb_epoch_cross_check (void 2ba0e329 shape), resealed"),
    "hb_epoch_readback.cross_checked[stripped]": ("REPLAY_INPUT", "/hb_epoch_readback/cross_checked",
                                                  "the readback's cross_checked and marker stripped, resealed"),
    **{"resolved_issues[0].resolution_pair." + f: ("REPLAY_INPUT", "/resolved_issues/0/resolution_pair/" + f.replace(".", "/"), why)
       for f, why in (("head", "no head-side ALLOW gate receipt"), ("base.receipt.ledgered_at_base", "the base receipt is not at the base ledger head"),
                      ("head.receipt.change_digest", "the head receipt binds another digest"),
                      ("head.receipt.disposition", "the head gate receipt is FAIL_CLOSED"),
                      ("head.subject.repository", "the head subject is StegVerse-org/.github's"),
                      ("head.subject.manifest_blob", "the head subject binds another manifest blob"),
                      ("pinned_manifest", "the gate declaration's contract-pins.json is not supplied"),
                      ("*.subject.manifest_blob", "both subjects' manifest was read from the subject, not contract-pins"),
                      ("base.subject.evaluated_commit", "the base subject is at the change's head commit"),
                      ("change_commits", "the change's commits are unobserved"))},
}
FOREIGN_SESSION = "FOREIGN-SESSION"  # fixture: the session admission_learning._foreign adds


def axis_value(axis: str, expected_code: str | None):
    """The concrete value each replay mutation writes (the same values admission_learning's mutations use)."""
    return {"writer_sessions": {"session": FOREIGN_SESSION, "evidence_class": "DECLARED"},
            "validation_receipts[*].ref": "", "validation_receipts[*].evidence_class": "OBSERVED_ARTIFACT",
            "validation_receipts[*].change_digest": "sha256:" + "0" * 64, "bound_request_digest": "sha256:" + "1" * 64,
            "declared_session": None, "signoffs": [], "signoffs[*].receipt_ref": "",
            "content[*].writer_session.evidence_class": {"session": None, "evidence_class": wi.UNKNOWN},
            "validation_receipts[0].disposition": "DENY" if expected_code == "REQUIRED_CHECK_DENIED" else "FAIL_CLOSED",
            "supplied_hb_epoch": str(int(FIXTURE_HB_EPOCH) + 1), "resolves": [], "resolves[+unobserved]": ["svi:" + "f" * 64],
            "record_mode": "MIGRATED_HISTORICAL", "supplied_hb_epoch[UNKNOWN]": wi.UNKNOWN, "owning_goal[UNKNOWN]": wi.UNKNOWN,
            "supplied_hb_epoch[int]": int(FIXTURE_HB_EPOCH)}.get(axis)


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
    elif axis == "signoffs":
        ch["signoffs"] = list(v)
    elif axis == "signoffs[*].receipt_ref":
        ch["signoffs"] = [{**s, "receipt_ref": v} for s in ch["signoffs"]]
    elif axis in ("supplied_hb_epoch", "supplied_hb_epoch[UNKNOWN]", "supplied_hb_epoch[int]"):
        ch["hb_epoch"] = v
    elif axis == "resolves":
        ch["resolves"] = list(v)
    elif axis == "resolves[+unobserved]":
        ch["resolves"] = sorted(ch["resolves"] + list(v))
    elif axis == "record_mode":
        ch["record_mode"] = v
    elif axis == "owning_goal[UNKNOWN]":
        ch["owning_goal"] = v
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
                     "resolved_issues": sc["observed_inputs"]["resolved_issues"],
                     "push_receipts": sc["observed_inputs"]["push_receipts"], "change_commits": sc["observed_inputs"]["change_commits"],
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
    # ASC-PR_AUTHOR_SESSION_DECLARED@schema keeps its id (append-only); its axis is re-derived (Lane C alignment, TVC#531):
    # the declaration is not writer evidence, the branch writer is derived from the sv-push-receipt chain.
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


# Q-SV-NATIVE-BOOTSTRAP, decided by invariant STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE (orchestrator 2026-10-18T15:47Z):
# appended through SCENARIO_CORPUS_APPEND after the epoch class v2 (so the epoch commit's ids do not move). Class rule (failed predicate + surface kind): the stage
# gate is an admitted transition (resident-runtime/stage_gate.py, kind transition), so each predicate is a class @transition.
# None of these predicates has a class yet, so each is a new class (v1); no existing scenario id moves.
BOOTSTRAP_ORIGINS = ["orchestrator 2026-10-18T15:47Z Q-SV-NATIVE-BOOTSTRAP decided by invariant STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE",
                     "StegVerse-Labs/.github#3264 own SV_CHANGE: DENY SV_CHANGE_RESOLVES_NOTHING until its gate receipt is ledgered"]
BOOTSTRAP_SEEDS = [("CHANGE_RESOLVES_CLAIMED_SV_ISSUES", "c"), ("RESOLVING_CHANGE_DID_NOT_SOURCE_ITS_ISSUE", "a"),
                   ("ONE_RECEIPT_DERIVES_ONE_ISSUE", "b"), ("RECEIPT_DERIVED_ISSUE_IS_RESOLVED_ONCE", "b"),
                   ("ADMITTED_RECORDS_ARE_NATIVE", "d")]
BOOTSTRAP_RULE_REFS = [{"file": "data/sv-work-items/invariants.json#STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE", "blob_sha": None,
                        "rule_id": "STAGE_GATE_RECEIPT_DERIVES_NATIVE_ISSUE"}]


def bootstrap_append(classes: list[dict], scenarios: list[dict]) -> list[dict]:
    out_receipts = []
    for pred, cond in BOOTSTRAP_SEEDS:
        origins = BOOTSTRAP_ORIGINS + ["condition (" + cond + ")"]
        prior = al.latest_classes(classes).get(al.class_id_for(pred, "transition"))
        if prior is not None:
            raise SystemExit(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "CLASS_EXISTS", "class_id": prior["class_id"]}))
        cls = al.generalize({"failed_predicate": pred}, surface="transition", origin_scenarios=origins, rule_refs=BOOTSTRAP_RULE_REFS,
                            declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH)
        gen = al.generate(cls, known_good(SURFACE_PATH["transition"]), hb_epoch=FIXTURE_HB_EPOCH)
        gen = [s if s["expected_disposition"] == "ALLOW" else wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
               "source": {**s["source"], "origin_scenarios": origins}}, "scenario_sha256") for s in gen]
        out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
        if out["disposition"] != "ALLOW":
            raise SystemExit(json.dumps(out, sort_keys=True))
        classes += out["append_classes"]; scenarios += out["append_scenarios"]
        out_receipts.append({k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cls["class_id"]})
    return out_receipts


# Orchestrator decision UNKNOWN_IN_NATIVE_RECORD (2026-10-18T16:07Z): a NATIVE record field holding the sentinel is FAIL_CLOSED,
# never DENY. A new class (the predicate had no class), appended after the bootstrap classes so no existing id moves. Surface
# kind transition: admission of the record is an admitted transition (as for the bootstrap classes).
NATIVE_UNKNOWN_SEED = ("NATIVE_RECORD_FIELDS_ARE_OBSERVED", "transition",
                       ["orchestrator 2026-10-18T16:07Z decided UNKNOWN_IN_NATIVE_RECORD: a NATIVE record field holding "
                        "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED is FAIL_CLOSED UNKNOWN_IN_NATIVE_RECORD; DENY only for observed, wrong values"])
NATIVE_UNKNOWN_RULE_REFS = [{"file": "data/sv-work-items/invariants.json#NATIVE_RECORD_FIELDS_ARE_OBSERVED", "blob_sha": None,
                             "rule_id": "NATIVE_RECORD_FIELDS_ARE_OBSERVED"}]


def native_unknown_append(classes: list[dict], scenarios: list[dict]) -> list[dict]:
    pred, surface, origins = NATIVE_UNKNOWN_SEED
    prior = al.latest_classes(classes).get(al.class_id_for(pred, surface))
    if prior is not None:
        raise SystemExit(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "CLASS_EXISTS", "class_id": prior["class_id"]}))
    cls = al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=origins, rule_refs=NATIVE_UNKNOWN_RULE_REFS,
                        declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH)
    gen = al.generate(cls, known_good(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH)
    gen = [s if s["expected_disposition"] == "ALLOW" else wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
           "source": {**s["source"], "origin_scenarios": origins}}, "scenario_sha256") for s in gen]
    out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
    if out["disposition"] != "ALLOW":
        raise SystemExit(json.dumps(out, sort_keys=True))
    classes += out["append_classes"]; scenarios += out["append_scenarios"]
    return [{k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cls["class_id"]}]


# Contract invariant (orchestrator 2026-10-18T15:59Z, narrowed 16:03Z): anything not observed is
# UNKNOWN_NOT_AUTHENTICALLY_OBSERVED, which is FAIL_CLOSED, never DENY. The epoch class gains the sentinel axis as version 2
# (supersedes v1) through SCENARIO_CORPUS_APPEND, appended last so no existing scenario id moves; only the new scenario is appended.
EPOCH_UNKNOWN_RULING = "UNKNOWN_IS_FAIL_CLOSED_NEVER_DENY"
EPOCH_UNKNOWN_ORIGINS = ["orchestrator 2026-10-18T15:59Z contract invariant (narrowed 16:03Z): UNKNOWN_NOT_AUTHENTICALLY_OBSERVED is "
                         "FAIL_CLOSED, never DENY (the SV_CHANGE's hb_epoch null, '', 'null' or the sentinel -> FAIL_CLOSED "
                         "HB_EPOCH_SOURCE_UNOBSERVED, before c9192134)"]


def epoch_unknown_append(classes: list[dict], scenarios: list[dict]) -> list[dict]:
    pred, surface, origins = EPOCH_BINDING_SEED
    prior = al.latest_classes(classes)[al.class_id_for(pred, surface)]
    cls = al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=origins + EPOCH_UNKNOWN_ORIGINS,
                        rule_refs=EPOCH_RULE_REFS, declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH,
                        prior=prior, class_version=prior["class_version"] + 1, supersedes=prior["class_sha256"], ruling=EPOCH_UNKNOWN_RULING)
    have = {s["scenario_id"] for s in scenarios}
    gen = [s for s in al.generate(cls, known_good(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH) if s["scenario_id"] not in have]
    gen = [wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
                    "source": {**s["source"], "origin_scenarios": EPOCH_UNKNOWN_ORIGINS}}, "scenario_sha256") for s in gen]
    out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
    if out["disposition"] != "ALLOW":
        raise SystemExit(json.dumps(out, sort_keys=True))
    classes += out["append_classes"]; scenarios += out["append_scenarios"]
    return [{k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cls["class_id"]}]


# Orchestrator 16:55Z: an integer hb_epoch on a NATIVE SV_CHANGE is an observed, malformed value (sv-change 6b43b6ec requires the
# string) -> DENY HB_EPOCH_MISMATCH. The epoch class gains the axis as version 3 (supersedes v2), appended last; no id moves.
EPOCH_INT_RULING = "NATIVE_RECORD_HB_EPOCH_IS_A_STRING"
EPOCH_INT_ORIGINS = ["orchestrator 2026-10-18T16:55Z: validate_change accepted an integer hb_epoch that the sv-change schema (6b43b6ec) "
                     "and admission reject; an integer is a malformed native value: DENY HB_EPOCH_MISMATCH"]


def epoch_int_append(classes: list[dict], scenarios: list[dict], ruling: str = EPOCH_INT_RULING,
                     ruling_origins: list[str] = EPOCH_INT_ORIGINS) -> list[dict]:
    pred, surface, origins = EPOCH_BINDING_SEED
    prior = al.latest_classes(classes)[al.class_id_for(pred, surface)]
    cls = al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=origins + ruling_origins,
                        rule_refs=EPOCH_RULE_REFS, declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH,
                        prior=prior, class_version=prior["class_version"] + 1, supersedes=prior["class_sha256"], ruling=ruling)
    have = {s["scenario_id"] for s in scenarios}
    gen = [s for s in al.generate(cls, known_good(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH) if s["scenario_id"] not in have]
    gen = [wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
                    "source": {**s["source"], "origin_scenarios": ruling_origins}}, "scenario_sha256") for s in gen]
    out = al.corpus_append(classes, scenarios, cls, gen, hb_epoch=FIXTURE_HB_EPOCH)
    if out["disposition"] != "ALLOW":
        raise SystemExit(json.dumps(out, sort_keys=True))
    classes += out["append_classes"]; scenarios += out["append_scenarios"]
    return [{k: out[k] for k in ("disposition", "transition_class", "corpus_head")} | {"class_id": cls["class_id"]}]


# Ruling ~17:05Z (decided by invariant, NOT_CROSS_CHECKED_MARKER + the 9c9b9f51 pin): a readback carrying hb_epoch_cross_check
# (the 2ba0e329 shape) was not produced by the pinned readback -> FAIL_CLOSED HB_EPOCH_SOURCE_UNOBSERVED. Epoch class v4, last.
READBACK_SHAPE_RULING = "READBACK_SHAPE_MATCHES_PINNED_PRODUCER"
READBACK_SHAPE_ORIGINS = ["orchestrator ruling 2026-10-18 ~17:05Z: the Labs#3266 2ba0e329-shaped readback (hb_epoch_cross_check) is void "
                          "under NOT_CROSS_CHECKED_MARKER and the 9c9b9f51 pin; not authentically observed: FAIL_CLOSED "
                          "HB_EPOCH_SOURCE_UNOBSERVED (READBACK_SHAPE_MATCHES_PINNED_PRODUCER), never DENY"]


# Orchestrator 16:58Z GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE: a new class @transition (the predicate had none), appended
# last; its positive control is the Lane B pair (known_good_paired); each axis carries its own six-field code.
GATE_PAIR_ORIGINS = ["orchestrator 2026-10-18T16:58Z: the BASE-side failing nwi-s0-exit-gate receipt sources the native issue, the "
                     "HEAD-side ALLOW gate receipt resolves it; same manifest (or equivalent gate declaration), same repository, both "
                     "ledgered at the change's base ledger_head",
                     "SV-LLM/.github#46 @9fbc2e92: gate ALLOW at 7898cedb (evaluation af569561); base-side evaluation at 978b8880"]
GATE_PAIR_RULE_REFS = [{"file": "data/sv-work-items/invariants.json#GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE", "blob_sha": None,
                        "rule_id": "GATE_RECEIPT_PAIR_RESOLVES_GATE_DERIVED_ISSUE"}]


def gate_pair_append(classes: list[dict], scenarios: list[dict]) -> list[dict]:
    pred, surface = wi.GATE_PAIR_PREDICATE, "transition"
    prior = al.latest_classes(classes).get(al.class_id_for(pred, surface))
    if prior is not None:
        raise SystemExit(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "CLASS_EXISTS", "class_id": prior["class_id"]}))
    cls = al.generalize({"failed_predicate": pred}, surface=surface, origin_scenarios=GATE_PAIR_ORIGINS, rule_refs=GATE_PAIR_RULE_REFS,
                        declared_by_session=SESSION, harvest_receipt_ref=None, hb_epoch=FIXTURE_HB_EPOCH)
    gen = al.generate(cls, known_good_paired(SURFACE_PATH[surface]), hb_epoch=FIXTURE_HB_EPOCH)
    gen = [s if s["expected_disposition"] == "ALLOW" else wi.seal({**{k: v for k, v in s.items() if k != "scenario_sha256"},
           "source": {**s["source"], "origin_scenarios": GATE_PAIR_ORIGINS}}, "scenario_sha256") for s in gen]
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
    receipts += epoch_unknown_append(classes, scenarios)
    receipts += bootstrap_append(classes, scenarios)
    receipts += native_unknown_append(classes, scenarios)
    receipts += epoch_int_append(classes, scenarios)
    receipts += gate_pair_append(classes, scenarios)
    receipts += epoch_int_append(classes, scenarios, READBACK_SHAPE_RULING, READBACK_SHAPE_ORIGINS)
    return classes, scenarios, receipts


def _jsonl(rows): return "".join(json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows)


# CONTRACT_PINS_MANIFEST_IS_THE_CONSUMER_PIN (orchestrator 16:30Z): every canonical contract file a consumer (Lane B #46,
# Lane C TVC#519, Lane D, P4) pins, with its git blob sha and sha256. Consumers pin the manifest's own digest and re-pin a
# file only when its entry changes. The manifest never lists itself.
CONTRACT_PINS = ROOT / "data/sv-work-items/contract-pins.json"
# The repo-local import closure of the pinned Python files (CONTRACT_PINS_MANIFEST_IS_THE_CONSUMER_PIN.import_closure).
# Loaded when sv_work_items is imported: org-kernel/kernel.py (its supplied_epoch_failure / hb_reference; reached by
# derive_resolved_issue_facts through epoch_check), org-kernel/node_store.py (kernel, at import) and
# scripts/project_worker_claim_into_canonical_task.py (claim_projection). Loaded by kernel.py's _own_module (its own
# repository, on a crossing) and transitively: the rest. tests/test_nwi_gate_declaration.py recomputes the closure.
IMPORT_CLOSURE_FILES = [
    "org-kernel/kernel.py", "org-kernel/node_store.py", "scripts/project_worker_claim_into_canonical_task.py",
    ".stegverse/transition-ledger/emit.py", "resident-runtime/aggregate_repo_transition.py", "resident-runtime/ledger_store.py",
    "resident-runtime/organization_batch_custody.py", "workers/canonical_state_transition_custody.py",
    "heartbeat_runtime/independent_oscillator.py"]
# Loaded by kernel.py from a caller-supplied dispatch root (root/"org-boundary/runtime/<m>.py"), never from this repository's
# own path: not repo-local by construction, so outside the closure; declared so a new unresolved load fails the test.
DISPATCH_ROOT_LOADS = {"org-kernel/kernel.py": ["capability_ingress", "manifest_selection", "node_standing"]}
CONTRACT_FILES = sorted([
    "schemas/admission-corpus.v1.schema.json", "schemas/canonical-task-work-items.v1.schema.json",
    "schemas/sv-change-signoff-receipt.v0.1.schema.json", "schemas/sv-change.v1.schema.json", "schemas/sv-check-receipt.v1.schema.json",
    "schemas/sv-issue.v1.schema.json", "schemas/sv-surface-aliases.v1.schema.json",
    "data/sv-work-items/invariants.json", "data/sv-work-items/required-checks.json", "data/sv-work-items/lifecycle-transitions.json",
    "data/sv-work-items/surface-aliases.json", *["data/sv-work-items/stages/NWI-S%d.json" % i for i in range(5)],
    "data/sv-work-items/migration/sv-issues.jsonl", "data/sv-work-items/migration/sv-changes.jsonl",
    "data/admission-scenarios/classes.jsonl", "data/admission-scenarios/corpus.jsonl", "data/admission-scenarios/seed-append-outcomes.jsonl",
    "data/admission-scenarios/tvc-replay/replay-map.jsonl", "data/admission-scenarios/tvc-replay/sv-changes.jsonl",
    "data/admission-scenarios/tvc-replay/signoff-receipts.jsonl",
    "resident-runtime/sv_work_items.py", "resident-runtime/admission_learning.py", "resident-runtime/stage_gate.py",
    "resident-runtime/sv_migration.py", "resident-runtime/schema_subset.py", "scripts/build_sv_native_fixtures.py",
    "resident-runtime/sv_push_receipt.py", "schemas/sv-push-receipt.v1.schema.json",  # the branch writer's evidence (Labs#3267)
    "tests/sv_ledger_fixtures.py",  # orchestrator 16:58Z: Lane D pins it (blob 30a9fe89)
    "tests/fixtures/base-state-readback/labs-main-978b8880-producer-7ad6d81f.json",  # commit 5: shared readback (blob cfaaec20)
    *IMPORT_CLOSURE_FILES])


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def contract_pins(generated: dict[Path, str]) -> str:
    """The manifest over the files as they will be committed: generated text for derived files, the tree for the rest."""
    files = {}
    for rel in CONTRACT_FILES:
        p = ROOT / rel
        data = generated[p].encode("utf-8") if p in generated else p.read_bytes()
        files[rel] = {"blob": git_blob_sha(data), "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}
    body = {"schema": "stegverse.sv-contract-pins/v1", "repository": "StegVerse-Labs/.github",
            "invariant": "data/sv-work-items/invariants.json#CONTRACT_PINS_MANIFEST_IS_THE_CONSUMER_PIN",
            "digest_rule": {"blob": "git blob sha1 of the file bytes (git hash-object)", "sha256": "sha256:<hex> of the file bytes"},
            "excludes": ["data/sv-work-items/contract-pins.json (the manifest never lists itself)"],
            "import_closure": {"rule": "every repo-local module the listed Python files load (import, import_module, "
                                       "importlib spec_from_file_location with a statically resolvable path, eagerly or on call), "
                                       "transitively, is listed", "members": sorted(IMPORT_CLOSURE_FILES),
                               "dispatch_root_loads_excluded": DISPATCH_ROOT_LOADS},
            "consumer_contract": "pin this manifest's own blob and sha256; re-pin a listed file only when its entry changes",
            "generated_by": "scripts/build_sv_native_fixtures.py (--check flags a stale manifest)", "files": files}
    return json.dumps(body, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def schema_errors(generated: dict[Path, str]) -> list[dict]:
    """SV_WORK_ITEM_SCHEMAS_VALIDATE (NWI-S0 exit gate, check schema-validate): every derived migration record validates
    against its pinned schema (resident-runtime/schema_subset.py)."""
    bad = []
    for name, schema_file in (("sv-issues.jsonl", "schemas/sv-issue.v1.schema.json"), ("sv-changes.jsonl", "schemas/sv-change.v1.schema.json")):
        schema = json.loads((ROOT / schema_file).read_text())
        for n, line in enumerate(generated[MIG / name].splitlines()):
            errs = ss.validate(json.loads(line), schema)
            if errs:
                bad.append({"file": "data/sv-work-items/migration/" + name, "line": n + 1, "schema": schema_file, "errors": errs[:5]})
    return bad


def build() -> dict[Path, str]:
    c, s, r = corpus()
    iss = issues()
    out = {MIG / "sv-issues.jsonl": _jsonl(iss), MIG / "sv-changes.jsonl": _jsonl(changes(iss)), SCN / "classes.jsonl": _jsonl(c), SCN / "corpus.jsonl": _jsonl(s),
           SCN / "seed-append-outcomes.jsonl": _jsonl(r),
           **dict(zip((SCN / "tvc-replay/sv-changes.jsonl", SCN / "tvc-replay/replay-map.jsonl", SCN / "tvc-replay/signoff-receipts.jsonl"),
                      map(_jsonl, replay(s))))}
    out.update(readback_pin_sync())
    out[CONTRACT_PINS] = contract_pins(out)
    return out


READBACK_PIN_TARGETS = {  # where the single #3266 pin (sv_work_items.BASE_STATE_READBACK_PIN) is copied
    ROOT / "data/sv-work-items/invariants.json": None,
    ROOT / "data/sv-work-items/stages/NWI-S0.json": ("repository", "pull_request", "head", "file", "blob", "sha256")}


def readback_pin_sync() -> dict[Path, str]:
    """Copy wi.BASE_STATE_READBACK_PIN into invariants.json (ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH.readback_pin,
    all fields) and NWI-S0.json (exit_gate_check.hb_epoch.readback_pin, the six it carries). Drop new values into the
    constant only; history and prose entries are edited by hand."""
    out = {}
    for p, keys in READBACK_PIN_TARGETS.items():
        d = json.loads(p.read_text())
        pin = {k: wi.BASE_STATE_READBACK_PIN[k] for k in (keys or wi.BASE_STATE_READBACK_PIN)}
        if keys is None:
            next(i for i in d["invariants"] if i["invariant_id"] == "ADMISSION_HB_EPOCH_IS_THE_BOUND_LEDGER_HEAD_EPOCH")["readback_pin"] = pin
        else:
            d["exit_gate_check"]["hb_epoch"]["readback_pin"] = pin
        out[p] = json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return out


def pin_violations(out: dict[Path, str]) -> list[dict]:
    """Every emitted required_checks_ref.blob_sha is a 40-hex git blob (UNKNOWN only in a MIGRATED_HISTORICAL record);
    no placeholder such as WORKTREE is ever written."""
    bad = []
    for p, text in out.items():
        if p == CONTRACT_PINS or p in READBACK_PIN_TARGETS:
            continue  # not a record file (hashes only / pin sync)
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
    invalid = schema_errors(out)
    if invalid:  # FAIL_CLOSED in both modes: a record that does not validate is never written
        print(json.dumps({"disposition": "FAIL_CLOSED", "failure_code": "SV_WORK_ITEM_SCHEMA_INVALID", "violations": invalid}, sort_keys=True))
        return 1
    if args.check:
        print(json.dumps({"disposition": "ALLOW" if not stale else "FAIL_CLOSED", "stale": stale,
                          "schemas_validated": ["schemas/sv-change.v1.schema.json", "schemas/sv-issue.v1.schema.json"]}, sort_keys=True))
        return 1 if stale else 0
    for p, t in out.items():
        p.parent.mkdir(parents=True, exist_ok=True); p.write_text(t)
    print(json.dumps({"written": sorted(str(p.relative_to(ROOT)) for p in out)})); return 0


if __name__ == "__main__":
    sys.exit(main())
