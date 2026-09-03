#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADOPTION = ROOT / "control" / "worker-blocker-fallback-adoption.json"

ALLOWED = {
    "ADOPTED",
    "ADOPTED_REFERENCE_IMPLEMENTATION",
    "ALREADY_CONFORMANT",
    "ALREADY_PARTIALLY_CONFORMANT",
    "FOLLOWUP_TASK_CREATED",
    "FOLLOWUP_TASK_REQUIRED",
    "NOT_APPLICABLE",
}

def fail(message: str):
    raise SystemExit(f"WORKER_BLOCKER_FALLBACK_ADOPTION_FAIL: {message}")

def main():
    doc = json.loads(ADOPTION.read_text(encoding="utf-8"))
    families = doc.get("worker_families")
    if not isinstance(families, list) or not families:
        fail("worker_families missing")

    seen = set()
    for row in families:
        family = row.get("family")
        state = row.get("state")
        if not family:
            fail("family missing")
        if family in seen:
            fail(f"duplicate family {family}")
        seen.add(family)
        if state not in ALLOWED:
            fail(f"{family}: invalid state {state}")
        if state == "FOLLOWUP_TASK_REQUIRED":
            fail(f"{family}: vague FOLLOWUP_TASK_REQUIRED is prohibited; create a durable owner")
        if not row.get("owner"):
            fail(f"{family}: owner missing")
        if state in {"ADOPTED","ADOPTED_REFERENCE_IMPLEMENTATION","ALREADY_CONFORMANT"}:
            if not row.get("evidence") and family == "validation_reconciliation":
                fail(f"{family}: adopted state requires evidence")

    target = next((r for r in families if r.get("family") == "validation_reconciliation"), None)
    if target is None:
        fail("validation_reconciliation family missing")
    if target.get("state") != "ADOPTED":
        fail("validation_reconciliation must remain ADOPTED unless its evidence is explicitly superseded")
    evidence = target.get("evidence") or []
    required_fragments = [
        "StegVerse-Labs/StegIndex#3",
        "StegVerse-Labs/.github#881",
        "StegVerse-Labs/.github#885",
        "33713433913 SUCCESS",
        "33713434257 SUCCESS",
    ]
    joined = "\n".join(evidence)
    for fragment in required_fragments:
        if fragment not in joined:
            fail(f"validation_reconciliation missing evidence fragment: {fragment}")
    if target.get("authority_effect") != "NONE":
        fail("validation_reconciliation adoption must grant no authority")

    propagation = next((r for r in families if r.get("family") == "site_publisher_propagation"), None)
    if propagation is None:
        fail("site_publisher_propagation family missing")
    if propagation.get("state") != "ALREADY_CONFORMANT":
        fail("site_publisher_propagation must remain ALREADY_CONFORMANT unless evidence is superseded")
    p_evidence = "\n".join(propagation.get("evidence") or [])
    for fragment in [
        "StegVerse-Labs/Site:docs/SITE_MIRROR_HANDOFF.md",
        "GCAT-BCAT-Engine/Publisher:docs/PUBLISHER_MIRROR_HANDOFF.md",
        "PENDING_SITE_ACTIVATION",
        "release_condition",
    ]:
        if fragment not in p_evidence:
            fail(f"site_publisher_propagation missing evidence fragment: {fragment}")
    if propagation.get("authority_effect") != "NONE":
        fail("site_publisher_propagation conformance must grant no authority")

    authority = next((r for r in families if r.get("family") == "tv_tvc_authority_bound_invocation"), None)
    if authority is None:
        fail("tv_tvc_authority_bound_invocation family missing")
    if authority.get("state") != "ALREADY_CONFORMANT":
        fail("tv_tvc_authority_bound_invocation must remain ALREADY_CONFORMANT unless evidence is superseded")
    a_evidence = "\n".join(authority.get("evidence") or [])
    for fragment in [
        "StegVerse-Labs/TV:docs/TV_MIRROR_HANDOFF.md",
        "StegVerse-Labs/TVC:TVC_MIRROR_HANDOFF.md",
        "BLOCKED_CREDENTIAL_NOT_OBSERVED",
        "another_physical_machine_required=false",
    ]:
        if fragment not in a_evidence:
            fail(f"tv_tvc_authority_bound_invocation missing evidence fragment: {fragment}")
    if authority.get("authority_effect") != "NONE":
        fail("tv_tvc_authority_bound_invocation conformance must grant no authority")

    mailbox = next((r for r in families if r.get("family") == "mailbox_failure_remediation"), None)
    if mailbox is None:
        fail("mailbox_failure_remediation family missing")
    if mailbox.get("state") != "ALREADY_CONFORMANT":
        fail("mailbox_failure_remediation must remain ALREADY_CONFORMANT unless evidence is superseded")
    m_evidence = "\n".join(mailbox.get("evidence") or [])
    for fragment in [
        "StegVerse-Labs/StegVerse-Healer:failure_mailbox/FAILURE_MAILBOX_MIRROR_HANDOFF.md",
        "failure_mailbox/backfill.py",
        "quarantines parse/ingest failures",
        "incident_engine preserves independent",
    ]:
        if fragment not in m_evidence:
            fail(f"mailbox_failure_remediation missing evidence fragment: {fragment}")
    if mailbox.get("authority_effect") != "NONE":
        fail("mailbox_failure_remediation conformance must grant no authority")

    observers = next((r for r in families if r.get("family") == "publication_release_observers"), None)
    if observers is None:
        fail("publication_release_observers family missing")
    if observers.get("state") != "ALREADY_CONFORMANT":
        fail("publication_release_observers must remain ALREADY_CONFORMANT unless evidence is superseded")
    o_evidence = "\n".join(observers.get("evidence") or [])
    for fragment in [
        "GCAT-BCAT-Engine/Publisher:docs/STEGCLAW_RELEASE_AWARENESS_MIRROR_HANDOFF.md",
        "PARALLEL_SAFE_NON_AUTHORIZING_RELEASE_AWARENESS",
        "unrelated RTG-001/stegdb-sync failures remain separate",
        "authority remain false",
    ]:
        if fragment not in o_evidence:
            fail(f"publication_release_observers missing evidence fragment: {fragment}")
    if observers.get("authority_effect") != "NONE":
        fail("publication_release_observers conformance must grant no authority")

    for row in families:
        if row.get("state") == "FOLLOWUP_TASK_CREATED":
            if not row.get("owner") or not row.get("evidence_required"):
                fail(f"{row.get('family')}: follow-up task lacks durable owner/evidence requirements")

    if doc.get("state") == "ADOPTION_COMPLETE_EVIDENCE_BACKED":
        nonterminal = [
            row.get("family") for row in families
            if row.get("state") not in {"ADOPTED","ALREADY_CONFORMANT","ADOPTED_REFERENCE_IMPLEMENTATION","NOT_APPLICABLE"}
        ]
        if nonterminal:
            fail(f"complete adoption contains nonterminal families: {nonterminal}")

    for family in ("heartbeat_runtime", "deployment_runtime_activation"):
        runtime = next((r for r in families if r.get("family") == family), None)
        if runtime is None:
            fail(f"{family}: missing")
        if runtime.get("state") != "ADOPTED":
            fail(f"{family}: must remain ADOPTED unless proof is explicitly superseded")
        evidence = "\n".join(runtime.get("evidence") or [])
        for fragment in [
            "StegVerse-Labs/.github#903",
            "33718097701 SUCCESS",
            "100531416166 SUCCESS",
            "33718097665 SUCCESS",
            "test_runtime_blocker_continuation_proof.py",
        ]:
            if fragment not in evidence:
                fail(f"{family}: missing proof fragment {fragment}")
        if runtime.get("authority_effect") != "NONE":
            fail(f"{family}: adoption must grant no authority")

    org_completion = next((r for r in families if r.get("family") == "organization_repository_completion"), None)
    if org_completion is None:
        fail("organization_repository_completion family missing")
    if org_completion.get("state") != "ADOPTED":
        fail("organization_repository_completion must remain ADOPTED unless proof is superseded")
    oc_evidence = "\n".join(org_completion.get("evidence") or [])
    for fragment in [
        "Admissible-Existence/.github#25",
        "0d6f1ff24f511005815abc14af3dd12fe3030af9",
        "33718570347 SUCCESS",
        "100532820290 SUCCESS",
        "test_principle_worker_blocker_fallback.py",
        "archive_permitted=false",
    ]:
        if fragment not in oc_evidence:
            fail(f"organization_repository_completion missing proof fragment: {fragment}")
    if org_completion.get("authority_effect") != "NONE":
        fail("organization_repository_completion adoption must grant no authority")

    print(f"WORKER_BLOCKER_FALLBACK_ADOPTION_PASS families={len(families)}")

if __name__ == "__main__":
    main()
