#!/usr/bin/env python3
"""RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013: is a repository's ledger genesis on its organization ledger?

A reusable, non-authorizing readback transition, generic over the repository
namespace. Given an organization, a repository and the organization-ledger
head that repository's genesis manifest is bound to, it:

1. fresh-fetches ``refs/stegverse/organization-ledger`` into a new, empty,
   temporary bare repository (anonymous; no credential helper, no prompt);
2. verifies the organization chain and the repository chain kept in
   ``repository-ledger/<organization>/<repository>`` of that same ref with the
   existing ``organization_ledger_readback.readback`` and
   ``organization_ledger_readback.repository_readback`` (no second verifier);
3. answers one disposition:

   * ``ALLOW``: the repository HEAD is present, the chain verifies, every
     repository receipt is retained in the organization ledger, and the bound
     head is the fetched head or an ancestor of it. Applying the genesis
     appends to the ref, so a moved head is expected once it is applied.
   * ``FAIL_CLOSED REPOSITORY_LEDGER_HEAD_PRESENT``: no repository HEAD, and
     the ref is still at the bound head.
   * ``FAIL_CLOSED EXPECTED_ORG_LEDGER_HEAD_MOVED``: no repository HEAD, and
     the ref moved off the bound head. ``observed_organization_ledger_head``
     is the head the genesis manifest must be re-bound to.
   * any other ``FAIL_CLOSED`` names the predicate the existing readback or
     the fetch refused.

Every non-ALLOW carries the six fields. ``authority_effect`` is always
``NONE_READBACK_ONLY``: nothing is written to any ledger or ref outside the
temporary directory, which is removed before returning. No clock is read, and
there is no loop or retry; the caller's manifest transition decides when this
runs. Stdlib and ``git`` only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

COMPONENT_ID = "RTC-REPOSITORY-LEDGER-GENESIS-READBACK-013"
REQUEST_SCHEMA = "stegverse.repository-ledger-genesis-readback-request/v1"
RESULT_SCHEMA = "stegverse.repository-ledger-genesis-readback-result/v1"
LEDGER_REF = "refs/stegverse/organization-ledger"
AUTHORITY_EFFECT = "NONE_READBACK_ONLY"
RETRY = "resident-runtime/repository_ledger_genesis_readback.py::evaluate"
HERE = Path(__file__).resolve().parent

_ORG = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}\Z")
# Repository names may begin with a dot (".github"); "." and ".." are refused below.
_REPO = re.compile(r"[A-Za-z0-9_.-]{1,100}\Z")
_GOAL = re.compile(r"[A-Z0-9][A-Z0-9_.-]{2,149}\Z")
_OID = re.compile(r"[0-9a-f]{40}\Z")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_ledger_source(organization: str) -> str:
    """The organization's own public ledger repository; never caller-chosen in a request."""
    return f"https://github.com/{organization}/.github.git"


def repository_namespace(organization: str, repository: str) -> str:
    return f"repository-ledger/{organization}/{repository}"


def _load_readback():
    path = HERE / "organization_ledger_readback.py"
    spec = importlib.util.spec_from_file_location("rtc013_organization_ledger_readback", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("organization_ledger_readback not loadable at " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RequestInvalid(ValueError):
    def __init__(self, failed_predicate: str, detail: str) -> None:
        super().__init__(failed_predicate + ": " + detail)
        self.failed_predicate = failed_predicate
        self.detail = detail


def validate_request(request: Any) -> dict[str, str]:
    if not isinstance(request, dict):
        raise RequestInvalid("REQUEST_IS_OBJECT", "the readback request must be a JSON object")
    if request.get("schema") != REQUEST_SCHEMA:
        raise RequestInvalid("REQUEST_SCHEMA_ADMITTED", f"schema must be {REQUEST_SCHEMA}")
    if request.get("component_id") != COMPONENT_ID:
        raise RequestInvalid("REQUEST_NAMES_THIS_COMPONENT", f"component_id must be {COMPONENT_ID}")
    organization, repository = request.get("organization"), request.get("repository")
    expected, goal = request.get("expected_organization_ledger_head"), request.get("owning_existing_goal")
    for field, value, pattern in (("organization", organization, _ORG), ("repository", repository, _REPO),
                                  ("expected_organization_ledger_head", expected, _OID),
                                  ("owning_existing_goal", goal, _GOAL)):
        if not isinstance(value, str) or not pattern.match(value) or value in (".", ".."):
            raise RequestInvalid("REQUEST_FIELD_WELL_FORMED", f"{field} is missing or malformed")
    if request.get("authority_effect", AUTHORITY_EFFECT) != AUTHORITY_EFFECT:
        raise RequestInvalid("REQUEST_AUTHORITY_EFFECT_IS_READBACK_ONLY", f"authority_effect must be {AUTHORITY_EFFECT}")
    return {"organization": organization, "repository": repository,
            "expected_organization_ledger_head": expected, "owning_existing_goal": goal}


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    return subprocess.run(["git", "-c", "credential.helper=", "-c", "core.askPass=", *args], cwd=cwd, env=env, capture_output=True, text=True, check=False)


def _refusal(base: dict[str, Any], code: str, predicate: str, required: str, next_attempt: str,
             goal: str, **extra: Any) -> dict[str, Any]:
    result = dict(base)
    result.update(extra)
    result.update({
        "disposition": "FAIL_CLOSED",
        "failure_code": code,
        "failed_predicate": predicate,
        "required_evidence_or_repair": required,
        "retry_entrypoint": RETRY,
        "owning_existing_goal": goal,
        "next_attempt": next_attempt,
    })
    return _seal(result)


def _seal(result: dict[str, Any]) -> dict[str, Any]:
    result["authority_effect"] = AUTHORITY_EFFECT
    result["consequence_committed"] = False
    result.pop("decision_sha256", None)
    result["decision_sha256"] = "sha256:" + hashlib.sha256(canon(result)).hexdigest()
    return result


def evaluate(request: Any, *, ledger_source: str | None = None) -> dict[str, Any]:
    """Run the readback for one request. ``ledger_source`` overrides the fetch source (tests only)."""
    base: dict[str, Any] = {"schema": RESULT_SCHEMA, "component_id": COMPONENT_ID, "ledger_ref": LEDGER_REF}
    try:
        fields = validate_request(request)
    except RequestInvalid as exc:
        goal = request.get("owning_existing_goal") if isinstance(request, dict) else None
        return _refusal(base, "READBACK_REQUEST_INVALID", exc.failed_predicate,
                        exc.detail, "with a request that satisfies " + REQUEST_SCHEMA,
                        goal if isinstance(goal, str) and _GOAL.match(goal) else "UNKNOWN_NOT_AUTHENTICALLY_OBSERVED")
    organization, repository = fields["organization"], fields["repository"]
    expected, goal = fields["expected_organization_ledger_head"], fields["owning_existing_goal"]
    namespace = repository_namespace(organization, repository)
    source = ledger_source if ledger_source is not None else canonical_ledger_source(organization)
    base.update({
        "organization": organization, "repository": repository, "repository_namespace": namespace,
        "expected_organization_ledger_head": expected,
        "ledger_source": source, "ledger_source_is_canonical": source == canonical_ledger_source(organization),
        "request_sha256": "sha256:" + hashlib.sha256(canon(request)).hexdigest(),
    })
    with tempfile.TemporaryDirectory(prefix="rtc013-") as work:
        repo = Path(work) / "ledger.git"
        init = _git(["init", "--quiet", "--bare", str(repo)], Path(work))
        fetched = init.returncode == 0 and _git(
            ["fetch", "--quiet", "--no-tags", "--no-write-fetch-head", source, f"+{LEDGER_REF}:{LEDGER_REF}"], repo
        ).returncode == 0
        head = _git(["rev-parse", "--verify", "--quiet", LEDGER_REF + "^{commit}"], repo) if fetched else None
        observed = head.stdout.strip() if head is not None and head.returncode == 0 else None
        if not observed or not _OID.match(observed):
            return _refusal(base, "ORGANIZATION_LEDGER_REF_NOT_FETCHED", "ORGANIZATION_LEDGER_REF_FRESH_FETCHED",
                            f"{source} must publish {LEDGER_REF}, readable anonymously",
                            "after the organization ledger ref is readable", goal)
        base["observed_organization_ledger_head"] = observed
        base["observed_head_equals_expected"] = observed == expected
        readback = _load_readback()
        location = f"git+{repo}#{LEDGER_REF}"
        try:
            readback.readback(location)
            repository_result = readback.repository_readback(location, namespace)
        except readback.ReadbackRefused as exc:
            if exc.failed_predicate == "REPOSITORY_LEDGER_HEAD_PRESENT":
                if observed != expected:
                    return _refusal(
                        base, "EXPECTED_ORG_LEDGER_HEAD_MOVED", "EXPECTED_ORG_LEDGER_HEAD_MOVED",
                        f"no genesis under {namespace}, and {LEDGER_REF} moved from {expected} to {observed}: "
                        "re-bind the genesis manifest's expected_organization_ledger_head to the observed head",
                        "after the genesis manifest is re-bound to observed_organization_ledger_head", goal)
                return _refusal(
                    base, "REPOSITORY_LEDGER_GENESIS_NOT_RETAINED", "REPOSITORY_LEDGER_HEAD_PRESENT",
                    f"the organization ledger writer applies the {organization}/{repository} genesis at {expected} "
                    "and fast-forwards the ref; the retained receipt under this namespace is the evidence",
                    "after the organization ledger writer appends the genesis", goal)
            return _refusal(base, "ORGANIZATION_LEDGER_READBACK_REFUSED", exc.failed_predicate, exc.detail,
                            "after the refused chain is repaired by its writer; nothing is written by this readback",
                            goal)
        except (ValueError, RuntimeError, OSError, KeyError) as exc:
            return _refusal(base, "ORGANIZATION_LEDGER_READBACK_REFUSED", "ORGANIZATION_LEDGER_READS_BACK",
                            type(exc).__name__ + ": " + str(exc),
                            "after the ledger reads back; nothing is written by this readback", goal)
        if observed != expected and _git(["merge-base", "--is-ancestor", expected, observed], repo).returncode != 0:
            return _refusal(base, "EXPECTED_ORG_LEDGER_HEAD_NOT_AN_ANCESTOR",
                            "EXPECTED_ORG_LEDGER_HEAD_IS_ANCESTOR_OF_OBSERVED",
                            f"{expected} is not in the history of {observed}; the ledger was not extended from the "
                            "head the genesis was bound to", "after the bound head is reconciled with the ledger", goal)
    result = dict(base)
    result.update({
        "disposition": "ALLOW",
        "expected_head_relation": "EQUAL" if observed == expected else "ANCESTOR",
        "repository_head_receipt_sha256": repository_result["head_receipt_sha256"],
        "genesis_receipt_sha256": repository_result["genesis_receipt_sha256"],
        "repository_chain_length": repository_result["chain_length"],
        "every_receipt_verifies_against_its_body": repository_result["every_receipt_verifies_against_its_body"],
        "every_receipt_retained_in_organization_ledger": repository_result["every_receipt_retained_in_organization_ledger"],
    })
    return _seal(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--request", type=Path, required=True, help="a " + REQUEST_SCHEMA + " manifest")
    args = parser.parse_args(argv)
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        request = {"_unreadable": type(exc).__name__}
    result = evaluate(request)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["disposition"] == "ALLOW" else 1


if __name__ == "__main__":
    raise SystemExit(main())
