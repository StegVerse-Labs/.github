#!/usr/bin/env python3
"""Report an organization's Organization Role deployment state as an actionable disposition.

ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001 deploys per organization, in each
organization's own `.github`. This verifier runs against one such checkout and says
exactly what is missing, in the non-ALLOW vocabulary the ecosystem disposition
invariant requires: failure_code, failed_predicate, required_evidence_or_repair,
retry_entrypoint, owning_existing_goal, next_attempt.

It reads source only. It opens no connection, contacts no receiver, consults no
device inventory, and grants no authority. A gap it reports is a source defect
repairable in the organization's own repository - never a machine dependency.

    python3 scripts/verify_organization_role_deployment.py --org-root <checkout>

Exit status is 0 when the organization is deployed, 1 when any check fails. The
disposition is printed as JSON either way, so a non-ALLOW is a finding with a
repair rather than a silent stop.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "stegverse.organization-role-deployment-disposition/v1"
OWNING_GOAL = "ORGANIZATION-ROLE-RUNTIME-REALITY-DEPLOYMENT-001"
RETRY_ENTRYPOINT = "scripts/verify_organization_role_deployment.py"

CONTRACT_PATH = ".stegverse/transition-ledger/org-contract.json"
AGGREGATOR_PATH = "resident-runtime/aggregate_repo_transition.py"
DECLARATION_PATH = "data/organization-role-runtime-reality-deployment.json"
REGISTER_PATH = "data/organization-role-exemption-register.json"

REPO_RECEIPT = "stegverse.repo-transition-receipt/v1"
CANONICAL_RECEIPT = "stegverse.canonical-state-transition-receipt/v1"
ORGANIZATION_SCOPE_RULE = (
    "EVERY_STATE_TRANSITION_OCCURRING_WITHIN_THE_ORGANIZATION_EMITS_AN_ORGANIZATION_RECEIPT"
)
MASTER_RECORDS_ROLE = "RELEASED_ORGANIZATION_BATCH_RECEIPT_RECORDER"

# Contract fields the role change adds, and the value each must carry.
ROLE_FIELDS: dict[str, Any] = {
    "runtime_reality_authority": "Organization",
    "ledger_root_is_organization_runtime_reality_locus": True,
    "ledger_lock": "ORGANIZATION_LEDGER_LOCK",
    "write_mode": "MANIFEST_DIRECTED_APPEND",
    "propagation_role": MASTER_RECORDS_ROLE,
    "propagation_gates_organization_runtime_reality": False,
    "propagation_receiver_unavailable_disposition": "DURABLE_QUEUE_OR_EVENT_EPHEMERAL_MATERIALIZATION",
    "always_on_receiver_required": False,
}


def finding(
    failure_code: str,
    failed_predicate: str,
    repair: str,
    next_attempt: str,
    **detail: Any,
) -> dict[str, Any]:
    return {
        "failure_code": failure_code,
        "failed_predicate": failed_predicate,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "owning_existing_goal": OWNING_GOAL,
        "next_attempt": next_attempt,
        **detail,
    }


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def check_contract(root: Path, findings: list[dict[str, Any]]) -> dict[str, Any] | None:
    path = root / CONTRACT_PATH
    if not path.is_file():
        findings.append(finding(
            "ORGANIZATION_LEDGER_CONTRACT_ABSENT",
            "ORGANIZATION_DECLARES_A_TRANSITION_LEDGER_CONTRACT",
            f"Add {CONTRACT_PATH}, copying the reference organization's contract and "
            "replacing the organization name.",
            "ADD_THE_ORGANIZATION_LEDGER_CONTRACT",
            path=CONTRACT_PATH,
        ))
        return None
    contract = load_json(path)
    if contract is None:
        findings.append(finding(
            "ORGANIZATION_LEDGER_CONTRACT_UNREADABLE",
            "ORGANIZATION_LEDGER_CONTRACT_IS_A_JSON_OBJECT",
            f"Repair {CONTRACT_PATH} so it parses as a JSON object.",
            "REPAIR_THE_ORGANIZATION_LEDGER_CONTRACT",
            path=CONTRACT_PATH,
        ))
        return None

    consumes = contract.get("consumes")
    if isinstance(consumes, str):
        consumes = [consumes]
    consumes = list(consumes or [])
    missing = [s for s in (REPO_RECEIPT, CANONICAL_RECEIPT) if s not in consumes]
    if missing:
        findings.append(finding(
            "ORGANIZATION_CONTRACT_CONSUMES_INCOMPLETE",
            "ORGANIZATION_CONTRACT_CONSUMES_REPOSITORY_AND_CANONICAL_STATE_TRANSITION_RECEIPTS",
            "Set consumes to an array holding both receipt schemas. A canonical governed "
            "transition that is not a repository transition otherwise has no path to an "
            "organization receipt and is dropped.",
            "GENERALIZE_THE_CONTRACT_CONSUMES_LIST",
            path=CONTRACT_PATH,
            observed_consumes=consumes,
            missing_schemas=missing,
        ))

    if contract.get("organization_scope_rule") != ORGANIZATION_SCOPE_RULE:
        findings.append(finding(
            "ORGANIZATION_SCOPE_RULE_NOT_DECLARED",
            "ORGANIZATION_CONTRACT_DECLARES_THE_ORGANIZATION_SCOPE_RULE",
            f"Set organization_scope_rule to {ORGANIZATION_SCOPE_RULE}.",
            "DECLARE_THE_ORGANIZATION_SCOPE_RULE",
            path=CONTRACT_PATH,
            observed=contract.get("organization_scope_rule"),
        ))

    if contract.get("preserves_source_transition_receipt") is not True:
        findings.append(finding(
            "SOURCE_TRANSITION_RECEIPT_NOT_PRESERVED",
            "ORGANIZATION_CONTRACT_PRESERVES_THE_SOURCE_TRANSITION_RECEIPT",
            "Set preserves_source_transition_receipt to true so the organization receipt "
            "retains its exact source receipt schema and digest.",
            "PRESERVE_THE_SOURCE_TRANSITION_RECEIPT",
            path=CONTRACT_PATH,
        ))

    role_missing = {k: v for k, v in ROLE_FIELDS.items() if contract.get(k) != v}
    if role_missing:
        findings.append(finding(
            "ORGANIZATION_ROLE_NOT_DECLARED_IN_CONTRACT",
            "ORGANIZATION_CONTRACT_DECLARES_THE_ORGANIZATION_AS_RUNTIME_REALITY_AUTHORITY",
            "Add the Organization Role fields to the contract: the organization holds "
            "runtime reality at its ledger root under the ledger lock by manifest-directed "
            "append, and master-records records released organization batch receipts "
            "without gating that reality.",
            "DECLARE_THE_ORGANIZATION_ROLE_IN_THE_CONTRACT",
            path=CONTRACT_PATH,
            missing_or_wrong={k: {"required": v, "observed": contract.get(k)}
                              for k, v in role_missing.items()},
        ))
    return contract


def check_aggregator(root: Path, findings: list[dict[str, Any]]) -> None:
    path = root / AGGREGATOR_PATH
    if not path.is_file():
        findings.append(finding(
            "ORGANIZATION_AGGREGATOR_ABSENT",
            "ORGANIZATION_HAS_A_RECEIPT_AGGREGATOR",
            f"Add {AGGREGATOR_PATH}, copying the reference organization's aggregator.",
            "ADD_THE_ORGANIZATION_AGGREGATOR",
            path=AGGREGATOR_PATH,
        ))
        return
    source = path.read_text(encoding="utf-8")
    # Admission must be driven by the contract's consumes list. Naming the canonical
    # schema literally is NOT the test: an aggregator that reads the contract never
    # needs to, and testing for the literal would reward the hard-coding this check
    # exists to remove.
    contract_driven = re.search(
        r'consumes["\']?\s*\)?.{0,200}?\bnot\s+in\b', source, re.DOTALL
    ) or re.search(
        r'\bin\b.{0,80}?consumes', source, re.DOTALL
    )
    if contract_driven:
        return
    # A source verifier that compares against one hard-coded schema rejects every
    # canonical governed transition, whatever the contract says it consumes.
    hard_reject = re.search(
        r'schema.{0,40}!=\s*["\']' + re.escape(REPO_RECEIPT) + r'["\']', source
    )
    findings.append(finding(
        "AGGREGATOR_REJECTS_NON_REPOSITORY_SOURCE",
        "AGGREGATOR_ADMITS_BY_THE_CONTRACT_CONSUMES_LIST",
        "Gate admission on the contract's consumes list rather than a hard-coded "
        "schema comparison, and bind a canonical state transition by its own digest "
        "rather than relabelling it as a repository transition. The reference "
        "organization's verify_source is the implementation to copy.",
        "GENERALIZE_THE_AGGREGATOR_SOURCE_VERIFIER",
        path=AGGREGATOR_PATH,
        observed_contract_driven_admission=False,
        observed_hard_reject=bool(hard_reject),
        observed_line=source[:hard_reject.start()].count("\n") + 1 if hard_reject else None,
    ))


def check_declaration(root: Path, findings: list[dict[str, Any]]) -> None:
    for path_str, schema, label in (
        (DECLARATION_PATH, "stegverse.organization-role-runtime-reality-deployment/v1", "declaration"),
        (REGISTER_PATH, "stegverse.organization-role-exemption-register/v1", "exemption register"),
    ):
        path = root / path_str
        document = load_json(path) if path.is_file() else None
        if document is None:
            findings.append(finding(
                f"ORGANIZATION_ROLE_{label.upper().replace(' ', '_')}_ABSENT",
                f"ORGANIZATION_HOLDS_ITS_OWN_ORGANIZATION_ROLE_{label.upper().replace(' ', '_')}",
                f"Add {path_str}, copying the reference organization's {label} and setting "
                "the organization name and deployment scope to this organization's own.",
                f"ADD_THE_ORGANIZATION_ROLE_{label.upper().replace(' ', '_')}",
                path=path_str,
            ))
            continue
        if document.get("schema") != schema:
            findings.append(finding(
                f"ORGANIZATION_ROLE_{label.upper().replace(' ', '_')}_SCHEMA_MISMATCH",
                f"ORGANIZATION_ROLE_{label.upper().replace(' ', '_')}_DECLARES_ITS_SCHEMA",
                f"Set schema in {path_str} to {schema}.",
                f"REPAIR_THE_ORGANIZATION_ROLE_{label.upper().replace(' ', '_')}",
                path=path_str,
                observed=document.get("schema"),
            ))


def evaluate(org_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    contract = check_contract(org_root, findings)
    check_aggregator(org_root, findings)
    check_declaration(org_root, findings)
    organization = (contract or {}).get("organization")
    disposition = "ALLOW" if not findings else "FAIL_CLOSED"
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "organization": organization,
        "org_root": str(org_root),
        "disposition": disposition,
        "state": "DEPLOYED" if disposition == "ALLOW" else "NOT_DEPLOYED",
        "evaluation_boundary": "ORGANIZATION_ROLE_SOURCE_VERIFICATION",
        "owning_existing_goal": OWNING_GOAL,
        "finding_count": len(findings),
        "findings": findings,
        # This verifier reads files. It observes no runtime and needs no receiver.
        "evidence_class": "SOURCE_IMPLEMENTED",
        "runtime_observed": False,
        "receiver_contacted": False,
        "external_machine_required": False,
        "consequence_committed": False,
        "authority_effect": "NONE_VERIFICATION_ONLY",
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="verify_organization_role_deployment",
        description="Report one organization's Organization Role deployment state.",
    )
    parser.add_argument(
        "--org-root", required=True,
        help="path to the organization's .github checkout",
    )
    parser.add_argument("--output", help="write the disposition JSON here; default stdout")
    args = parser.parse_args(argv)

    org_root = Path(args.org_root).expanduser().resolve()
    if not org_root.is_dir():
        parser.error(f"org root is not a directory: {org_root}")
    result = evaluate(org_root)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if result["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
