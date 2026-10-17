#!/usr/bin/env python3
"""Generate an organization's ledger contract pair from one parameter file.

DRAFT for candidate 1 (RTC-EVIDENCE-CUSTODY-004 organization-ledger profile).
Stdlib only. The generator is deterministic: the same parameter file always
yields byte-identical contract.json and org-contract.json (json indent=2,
template key order, trailing newline), matching how StegVerse-org@10d14104
serializes its contracts. It decides nothing. Identity strings are the only
inputs; every invariant field is fixed by the template. A parameter that
breaks an invariant is refused with the six fields, and nothing is written.

Usage:
  generate_ledger_contracts.py PARAMS.json --out-dir .stegverse/transition-ledger [--check]
--check compares the generated contracts with the existing files and exits 1 on any difference.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

LEDGER_REF = "refs/stegverse/organization-ledger"
RETRY = "org-kernel/organization-ledger/generate_ledger_contracts.py::main"
GOAL = "StegVerse-org/.github#163"
CONSUMABLE = ("stegverse.repo-transition-receipt/v1", "stegverse.canonical-state-transition-receipt/v1")

class Refused(Exception):
    def __init__(self, code, predicate, repair):
        super().__init__(code); self.code, self.predicate, self.repair = code, predicate, repair

def refusal(e):
    return {"disposition": "FAIL_CLOSED", "failure_code": e.code, "failed_predicate": e.predicate,
            "required_evidence_or_repair": e.repair, "retry_entrypoint": RETRY,
            "owning_existing_goal": GOAL, "next_attempt": "correct the parameter file and rerun; nothing was written",
            "consequence_committed": False, "authority_effect": "NONE_REFUSAL_ONLY"}

def slug(org):  # byte-for-byte the org-kernel organization_slug derivation (kernel.py L458-459)
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in org).strip("-")

def derive(p):
    org = p.get("organization")
    if not isinstance(org, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}", org):
        raise Refused("PARAMETER_ORGANIZATION_INVALID", "ORGANIZATION_IS_A_GITHUB_ORG_LOGIN", "supply organization as the exact GitHub org login")
    owner_repository = p.get("owner_repository", org + "/.github")
    ledger_repo = p.get("organization_ledger_repository", org + "/.github")
    ref = p.get("organization_ledger_ref", LEDGER_REF)
    if ref != LEDGER_REF:
        raise Refused("PARAMETER_LEDGER_REF_NOT_DESIGNATED", "ORGANIZATION_LEDGER_REF_IS_THE_DESIGNATED_REF", "use " + LEDGER_REF)
    if not owner_repository.startswith(org + "/") or not ledger_repo.startswith(org + "/"):
        raise Refused("PARAMETER_REPOSITORY_OUTSIDE_ORGANIZATION", "LEDGER_REPOSITORIES_ARE_INSIDE_THE_ORGANIZATION", "name repositories under " + org + "/")
    consumes = p.get("consumes", [CONSUMABLE[0]])
    if not consumes or any(c not in CONSUMABLE for c in consumes):
        raise Refused("PARAMETER_CONSUMES_UNSUPPORTED", "CONSUMES_IS_A_SUBSET_OF_COMPONENT_RECEIPT_SCHEMAS", "consumes must be a non-empty subset of " + ", ".join(CONSUMABLE))
    designation = p.get("designation_source")
    if not isinstance(designation, str) or not designation:
        raise Refused("PARAMETER_DESIGNATION_SOURCE_ABSENT", "LEDGER_REF_DESIGNATION_IS_RECORDED", "cite the #163 comment or request_id that adopts this organization")
    target = p.get("propagation_target", "master-records/.github")
    if p.get("slug_override") is not None:
        raise Refused("PARAMETER_SLUG_TYPED", "ORGANIZATION_SLUG_IS_DERIVED_NEVER_TYPED", "remove slug_override; the slug is derived")
    namespace = "repository-ledger/" + owner_repository
    return org, owner_repository, ledger_repo, ref, consumes, designation, target, namespace, p.get("repository_ledger_designation_source", designation)

def contracts(p):
    org, owner_repository, ledger_repo, ref, consumes, designation, target, namespace, repo_designation = derive(p)
    repo = {
      "schema": "stegverse.repo-transition-ledger-contract/v1",
      "repository": owner_repository,
      "ledger_level": "REPOSITORY",
      "receipt_schema": "stegverse.repo-transition-receipt/v1",
      "append_only_receipts": True,
      "required_fields": ["repository","transition_id","transition_class","predecessor_state_sha256","successor_state_sha256","evidence","authority_effect","hb_reference","previous_receipt_sha256"],
      "replay_rule": "REPOSITORY_REPLAY_MUST_NOT_REQUIRE_ORGANIZATION_OR_ECOSYSTEM_REPLAY",
      "repository_ledger_location": {
        "repository": ledger_repo,
        "ref": ref,
        "namespace": namespace,
        "locator_form": "git+<checkout>#" + ref + ":" + namespace,
        "new_ledger_root": False,
        "designation_source": repo_designation,
        "rule": p.get("repository_ledger_rule", "The repository chain is kept in its own subtree of the designated organization ledger ref, published by the same fast-forward push under ORGANIZATION_LEDGER_LOCK. Repository replay walks repository-ledger/<repository>/HEAD.json back through its own receipts and never reads an organization receipt. Repository receipts minted before this location was bound (previous_receipt_sha256 null, retained under source-receipts/) are history, not the head of this chain."),
      },
      "propagation_rule": "PROPAGATE_ONLY_EVIDENCE_NEEDED_BY_NEXT_HIGHER_LEVEL",
      "authority_effect": "NONE_CONTRACT_ONLY",
    }
    orgc = {
      "schema": "stegverse.organization-transition-ledger-contract/v1",
      "organization": org,
      "ledger_level": "ORGANIZATION",
      "consumes": list(consumes),
      "emits": "stegverse.organization-transition-receipt/v1",
      "replay_rule": "ORGANIZATION_REPLAY_MUST_REQUIRE_ONLY_VERIFIED_REPO_RECEIPTS_AND_ORG_RECEIPTS_NOT_ECOSYSTEM_REPLAY",
      "preserves_repo_receipt": True,
      "preserves_source_transition_receipt": True,
      "append_only_receipts": True,
      "propagation_target": target,
      "authority_effect": "NONE_CONTRACT_ONLY",
      "organization_scope_rule": "EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT",
      "ledger_root_is_organization_runtime_reality_locus": True,
      "runtime_reality_authority": "Organization",
      "ledger_lock": "ORGANIZATION_LEDGER_LOCK",
      "write_mode": "MANIFEST_DIRECTED_APPEND",
      "propagation_role": "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER",
      "propagation_gates_organization_runtime_reality": False,
      "propagation_receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
      "always_on_receiver_required": False,
      "declaration": "ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001",
      "organization_ledger_ref": ref,
      "organization_ledger_repository": ledger_repo,
      "organization_ledger_ref_designation_source": designation,
    }
    if "organization_record_service_declared" in p:
        orgc["organization_record_service_declared"] = bool(p["organization_record_service_declared"])
        if not p["organization_record_service_declared"]:
            orgc["propagation_submission_disposition"] = "DENY_ORGANIZATION_RECORD_SERVICE_NOT_DECLARED_FOR_THE_PROPAGATION_TARGET"
    return {"contract.json": repo, "org-contract.json": orgc}

def render(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("params", type=Path); ap.add_argument("--out-dir", type=Path, required=True); ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    try:
        out = contracts(json.loads(a.params.read_text()))
    except Refused as e:
        print(json.dumps(refusal(e), sort_keys=True)); return 1
    status = 0
    for name, doc in out.items():
        path = a.out_dir / name
        if a.check:
            same = path.exists() and path.read_text() == render(doc)
            print(("IDENTICAL " if same else "DIFFERS ") + str(path)); status |= 0 if same else 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True); path.write_text(render(doc))
    if status:
        print(json.dumps(refusal(Refused("CONTRACT_NOT_GENERATED_FROM_PARAMETERS", "COMMITTED_CONTRACTS_EQUAL_GENERATED_CONTRACTS",
              "regenerate the contracts from the parameter file and commit them unedited")), sort_keys=True))
    return status

if __name__ == "__main__":
    sys.exit(main())
