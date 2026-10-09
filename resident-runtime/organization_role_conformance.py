#!/usr/bin/env python3
"""`stegverse-labs.organization-role-conformance` -- evaluate a role-conformance request.

StegDB (`STEGDB-ORGANIZATION-ROLE-VERSION-PROPAGATION-002`) derives which
Organizations are stale against the current Organization Role version and emits
one manifest-bound conformance request to each. This organization receives its
request on its existing manifest ingress (`organization_manifest_ingress.receive`).
The admitted manifest declares `processing.capability` =
`organization_role_conformance` on its route, so the boundary selects this
adapter for it, never by who addressed the packet.

The manifest shape is the one the SDK admits: the route is declared in
`extensions.stegverse_route` (`stegverse.route.organization-role-conformance.v1`)
and the request rides in
`extensions.stegverse_organization_role_conformance_request`. The SDK refuses
the request as a top-level manifest field, so it is never read from one here.

This adapter only evaluates. It reads this organization's own source and
compares it with the target version's recorded file digests; the ingress then
appends the disposition, under the organization ledger lock, as the transition.
Nothing here re-adopts a file or writes anything except its own result: a
source change is a separate manifest-bound transition under its own owner.

The disposition is computed, never supplied by the request:

* DENY when the issuer is not the authorized owner, the destination is not this
  organization, or the manifest binding (the canonical task record at its
  commit) or the target version's own contract digest does not hold;
* ALLOW when every recorded file of the target version matches this
  organization's source byte for byte;
* FAIL_CLOSED otherwise, naming `REFERENCE_ADOPTION_PARITY_WITH_RECORDED_FILE_DIGESTS`
  and the exact files that differ.

No predicate here is about a reachable surface, a live lane or a receiver: the
request has arrived, and what is evaluated is the organization's own source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
SERVICE_ID = "stegverse-labs.organization-role-conformance"
CAPABILITY = "organization_role_conformance"
ROUTE_ID = "stegverse.route.organization-role-conformance.v1"
#: The SDK's route declaration extension, and the extension the request rides in
#: beside it (`stegverse.organization_role_conformance_processor.REQUEST_EXTENSION`).
ROUTE_DECLARATION_EXTENSION = "stegverse_route"
REQUEST_EXTENSION = "stegverse_organization_role_conformance_request"
REQUEST_SCHEMA = "stegverse.organization-role-conformance-request/v1"
RESULT_SCHEMA = "stegverse.organization-role-conformance-evaluation/v1"

#: The only issuer whose conformance requests this organization admits: the
#: canonical owner of role-version propagation, in the repository its canonical
#: task record names.
AUTHORIZED_ISSUER_TASK_ID = "STEGDB-ORGANIZATION-ROLE-VERSION-PROPAGATION-002"
AUTHORIZED_ISSUER_REPOSITORY = "StegVerse-Labs/StegDB"
#: The canonical task registry is held by this repository.
BINDING_REPOSITORY = "StegVerse-Labs/.github"
BINDING_PATH = f"data/canonical-task-records/{AUTHORIZED_ISSUER_TASK_ID}.json"

ISSUER_PREDICATE = "ISSUER_IS_THE_AUTHORIZED_ROLE_VERSION_PROPAGATION_OWNER"
DESTINATION_PREDICATE = "DESTINATION_IS_THIS_ORGANIZATION"
REQUEST_PREDICATE = "MANIFEST_DECLARES_ONE_ROLE_CONFORMANCE_REQUEST"
BINDING_PREDICATE = "MANIFEST_BINDING_MATCHES_CANONICAL_TASK_RECORD_AT_ITS_COMMIT"
BINDING_SOURCE_PREDICATE = "CANONICAL_TASK_RECORD_AT_BOUND_COMMIT_PRESENT_IN_ORGANIZATION_SOURCE"
VERSION_PREDICATE = "TARGET_ROLE_VERSION_CONTRACT_DIGEST_RECOMPUTES_FROM_ITS_FILES"
PARITY_PREDICATE = "REFERENCE_ADOPTION_PARITY_WITH_RECORDED_FILE_DIGESTS"
RETRY_ENTRYPOINT = "resident-runtime/organization_manifest_ingress.py::receive"

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_BLOB = re.compile(r"^[0-9a-f]{40}$")


def canon(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_uri(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    """The git blob id of these bytes, computed here rather than asked of git."""
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def organization_identity(root: Path = ROOT) -> str | None:
    """This organization, from its own boundary document; never from the request."""
    try:
        return json.loads((root / "org-runtime/interlock-intr.json").read_text(encoding="utf-8"))["organization"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def _safe_relative(path: Any) -> str | None:
    if not isinstance(path, str) or not path or "\\" in path:
        return None
    pure = PurePosixPath(path)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    return str(pure)


def _record_at_commit(root: Path, commit: str, path: str) -> bytes | None:
    """The record's bytes at `commit` in this checkout, or None when not present."""
    try:
        completed = subprocess.run(["git", "-C", str(root), "cat-file", "blob", f"{commit}:{path}"],
                                   capture_output=True, check=False, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _commit_present(root: Path, commit: str) -> bool:
    try:
        return subprocess.run(["git", "-C", str(root), "cat-file", "-e", commit + "^{commit}"],
                              capture_output=True, check=False, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def _verdict(disposition: str, predicate: str | None, detail: str, **extra: Any) -> dict[str, Any]:
    return {"disposition": disposition, "failed_predicate": predicate, "detail": detail, **extra}


def check_binding(binding: Any, issuer_repository: str, root: Path) -> dict[str, Any] | None:
    """None when the binding holds; otherwise the verdict it earns.

    The binding is the canonical task record's bytes, named by commit and
    digest. The record is read at that commit from this organization's own
    source. Only when the commit is not in this checkout (a shallow
    materialization) is the working-tree record compared instead, and then a
    mismatch is an actionable FAIL_CLOSED rather than a DENY: a record this
    organization cannot read at its commit has not been shown to differ.
    """
    if not isinstance(binding, Mapping):
        return _verdict("DENY", BINDING_PREDICATE, "manifest_binding absent")
    if (binding.get("repository"), binding.get("path")) != (BINDING_REPOSITORY, BINDING_PATH):
        return _verdict("DENY", BINDING_PREDICATE,
                        f"binding names {binding.get('repository')}:{binding.get('path')}, "
                        f"not {BINDING_REPOSITORY}:{BINDING_PATH}")
    commit, declared = binding.get("commit"), binding.get("sha256")
    if not isinstance(commit, str) or not _COMMIT.match(commit):
        return _verdict("DENY", BINDING_PREDICATE, "binding commit is not a full revision")
    if not isinstance(declared, str) or not _SHA256.match(declared):
        return _verdict("DENY", BINDING_PREDICATE, "binding sha256 is not a sha256 digest")
    raw = _record_at_commit(root, commit, BINDING_PATH)
    if raw is None and _commit_present(root, commit):
        return _verdict("DENY", BINDING_PREDICATE, f"no canonical task record at {commit}")
    if raw is None:
        working = root / BINDING_PATH
        raw = working.read_bytes() if working.is_file() else None
        if raw is None or sha256_uri(raw) != declared:
            return _verdict("FAIL_CLOSED", BINDING_SOURCE_PREDICATE,
                            f"commit {commit} is not in this checkout and the working-tree record "
                            "does not equal the declared digest",
                            required_evidence_or_repair=(
                                "materialize this organization's source with commit " + commit
                                + " and resubmit the same manifest"))
    elif sha256_uri(raw) != declared:
        return _verdict("DENY", BINDING_PREDICATE,
                        f"record at {commit} is {sha256_uri(raw)}, binding declares {declared}")
    try:
        record = json.loads(raw)
    except ValueError:
        return _verdict("DENY", BINDING_PREDICATE, "bound record is not JSON")
    if not isinstance(record, Mapping) or record.get("task_id") != AUTHORIZED_ISSUER_TASK_ID:
        return _verdict("DENY", BINDING_PREDICATE, "bound record is not the issuer's task record")
    if record.get("repository") != issuer_repository:
        return _verdict("DENY", BINDING_PREDICATE,
                        f"bound record names {record.get('repository')} as owner, "
                        f"the issuer declares {issuer_repository}")
    return None


def check_target_version(target: Any) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """The version's files when its contract digest recomputes from them; else the DENY."""
    if not isinstance(target, Mapping) or not isinstance(target.get("version_id"), str) \
            or not target["version_id"]:
        return _verdict("DENY", VERSION_PREDICATE, "target_role_version absent or unnamed"), []
    files = target.get("files")
    if not isinstance(files, list) or not files:
        return _verdict("DENY", VERSION_PREDICATE, "target_role_version declares no files"), []
    seen = set()
    for entry in files:
        if not isinstance(entry, Mapping) or _safe_relative(entry.get("path")) is None \
                or not isinstance(entry.get("blob_sha"), str) or not _BLOB.match(entry["blob_sha"]) \
                or type(entry.get("byte_count")) is not int or entry["byte_count"] < 0 \
                or not isinstance(entry.get("contract_digest"), str) \
                or not _SHA256.match(entry["contract_digest"]) or entry["path"] in seen:
            return _verdict("DENY", VERSION_PREDICATE, "target file entry invalid: "
                            + str(entry.get("path") if isinstance(entry, Mapping) else entry)), []
        seen.add(entry["path"])
    if target.get("contract_digest") != sha256_uri(canon(files)):
        return _verdict("DENY", VERSION_PREDICATE,
                        f"contract_digest {target.get('contract_digest')} does not recompute "
                        f"from the declared files ({sha256_uri(canon(files))})"), []
    return None, [dict(entry) for entry in files]


def compare_files(files: list[Mapping[str, Any]], root: Path) -> list[dict[str, Any]]:
    """Every recorded file whose bytes here differ from the record, with both sides."""
    differing = []
    for entry in files:
        path = root / entry["path"]
        raw = path.read_bytes() if path.is_file() else None
        observed = None if raw is None else {
            "contract_digest": sha256_uri(raw), "blob_sha": git_blob_sha(raw), "byte_count": len(raw)}
        recorded = {key: entry[key] for key in ("contract_digest", "blob_sha", "byte_count")}
        if observed != recorded:
            differing.append({"path": entry["path"], "recorded": recorded,
                              "observed": observed if observed is not None else "ABSENT"})
    return sorted(differing, key=lambda row: row["path"])


def evaluate(request: Any, *, root: Path = ROOT) -> dict[str, Any]:
    """The disposition this organization's source earns for a conformance request."""
    root = Path(root)
    organization = organization_identity(root)
    base = {"schema": RESULT_SCHEMA, "service_id": SERVICE_ID, "organization": organization,
            "source_mutated": False, "authority_effect": "NONE_EVALUATION_ONLY"}
    if not isinstance(request, Mapping) or request.get("schema") != REQUEST_SCHEMA:
        return {**base, **_verdict("DENY", REQUEST_PREDICATE,
                                   "manifest carries no " + REQUEST_SCHEMA + " request")}
    issuer = request.get("issuer") if isinstance(request.get("issuer"), Mapping) else {}
    target = request.get("target_role_version")
    base.update({
        "issuer": {"repository": issuer.get("repository"), "owner_task_id": issuer.get("owner_task_id")},
        "destination_organization": request.get("destination_organization"),
        "manifest_binding": request.get("manifest_binding"),
        "target_role_version_id": target.get("version_id") if isinstance(target, Mapping) else None,
        "target_contract_digest": target.get("contract_digest") if isinstance(target, Mapping) else None,
        "target_reference": target.get("reference") if isinstance(target, Mapping) else None,
    })
    if (issuer.get("owner_task_id"), issuer.get("repository")) != (
            AUTHORIZED_ISSUER_TASK_ID, AUTHORIZED_ISSUER_REPOSITORY):
        return {**base, **_verdict("DENY", ISSUER_PREDICATE,
                                   f"issuer {issuer.get('repository')}/{issuer.get('owner_task_id')} "
                                   "is not authorized to issue role-conformance requests")}
    if organization is None or request.get("destination_organization") != organization:
        return {**base, **_verdict("DENY", DESTINATION_PREDICATE,
                                   f"request is for {request.get('destination_organization')}, "
                                   f"this organization is {organization}")}
    refused = check_binding(request.get("manifest_binding"), issuer["repository"], root)
    if refused is not None:
        return {**base, **refused}
    refused, files = check_target_version(target)
    if refused is not None:
        return {**base, **refused}
    differing = compare_files(files, root)
    compared = sorted(entry["path"] for entry in files)
    if not differing:
        return {**base, **_verdict("ALLOW", None, "every recorded file matches this organization's source"),
                "compared_files": compared, "differing_files": []}
    return {**base, **_verdict(
        "FAIL_CLOSED", PARITY_PREDICATE,
        "differs from the recorded digests: " + ", ".join(row["path"] for row in differing)),
        "compared_files": compared, "differing_files": differing,
        "required_evidence_or_repair": (
            "adopt the recorded files of " + str(target.get("version_id"))
            + " by a separate manifest-bound source transition under the owning task, preserving "
            "this organization's own valid changes; this ingress does not mutate source"),
        "retry_entrypoint": RETRY_ENTRYPOINT,
        "next_attempt": {"entrypoint": RETRY_ENTRYPOINT,
                         "resubmit": "THE_SAME_MANIFEST_AFTER_THE_SOURCE_TRANSITION",
                         "awaits_an_external_machine": False}}


def manifest_request(manifest: Any) -> Any:
    """The request the manifest carries in its SDK-admitted extension, or None."""
    extensions = manifest.get("extensions") if isinstance(manifest, Mapping) else None
    return extensions.get(REQUEST_EXTENSION) if isinstance(extensions, Mapping) else None


def respond(packet: Mapping[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    """Evaluate the request a crossing packet carries, bound to the manifest it came in."""
    payload = packet.get("payload") if isinstance(packet.get("payload"), Mapping) else {}
    manifest = payload.get("manifest") if isinstance(payload.get("manifest"), Mapping) else {}
    result = evaluate(manifest_request(manifest), root=root)
    return {**result, "manifest_sha256": payload.get("manifest_sha256"),
            "request_packet_id": packet.get("packet_id")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # The boundary passes the packet as --envelope and the kernel as --packet.
    parser.add_argument("--packet", "--envelope", dest="packet", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = respond(json.loads(args.packet.read_text(encoding="utf-8")))
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
