#!/usr/bin/env python3
"""Prepare exact production source roots for the first SV-DN-1 canonical round."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import tempfile
from typing import Any, Mapping
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

TASK_ID = "SV-DN1-PRODUCTION-SOURCE-PREP-001"
WORKER_ID = "sv-dn1-production-source-prep-worker"
BOUND_STATE_ENV = "STEGVERSE_BOUND_STATE_ROOT"
SOURCE_ROOT_ENV = "STEGVERSE_SOURCE_MATERIALIZATION_ROOT"
TVC_SPOOL_ROOT_ENV = "STEGVERSE_FORMALISM_TVC_SPOOL_ROOT"

DEFAULT_BOUND_ROOT = Path.home() / ".stegverse" / "state" / "sv-dn1-production-source-prep"
DEFAULT_SOURCE_ROOT = Path("/var/lib/stegverse/source")
DEFAULT_TVC_SPOOL = Path.home() / ".stegverse" / "transport" / "formalism-tvc-repository"

HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_CREDENTIAL_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "GITHUB_PERSONAL_ACCESS_TOKEN",
    "ACTIONS_RUNTIME_TOKEN", "ACTIONS_ID_TOKEN_REQUEST_TOKEN",
    "HF_TOKEN", "HUGGINGFACE_TOKEN", "HUGGING_FACE_HUB_TOKEN",
    "TVC_EPHEMERAL_GITHUB_TOKEN",
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
    "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AZURE_CLIENT_SECRET",
    "OAUTH_TOKEN",
)
NODE_MARKERS = (Path("/etc/stegverse/node.json"), Path.home() / ".stegverse" / "node.json")
PUBLIC_HOSTS = {"github.com", "codeload.github.com"}
MAX_PUBLIC_ARCHIVE_BYTES = 64 * 1024 * 1024

COMMITS = {
    "StegVerse-org/StegVerse-SDK": "4461a1edf83549c51189ca4217dd75752caf604e",
    "Data-Continuation/core-lite": "284ddc21a352ee9c7decdd40dd499b7286710bc8",
    "StegVerse-Labs/StegCore": "eb2ef110d09328aa90bf1ed91c18b47a3ba32a71",
    "master-records/orchestration": "baf9272f89ebe515fc4c2413b5d951d28f1e4485",
}
PUBLIC_REPOS = {"StegVerse-org/StegVerse-SDK", "Data-Continuation/core-lite"}
PRIVATE_REPOS = {"StegVerse-Labs/StegCore", "master-records/orchestration"}
ANCHORS = {
    "StegVerse-org/StegVerse-SDK": {
        "stegverse/governance_ingress_runtime.py": "62c5ae4799ae018f6b100766215c3c68078c5b2e",
        "stegverse/sovereign_validation_runtime.py": "814d4cb607cc2cb4c7a605474fe845e13540898d",
    },
    "Data-Continuation/core-lite": {
        "core_lite/transaction_route.py": "734923a86bfcd4d41d07e0fb8797de50f0fb9408",
    },
    "StegVerse-Labs/StegCore": {
        "src/stegcore/transaction_lifecycle.py": "81935669846fedd2867272810b090226b05780ab",
    },
    "master-records/orchestration": {
        "services/manifest_receipt_custody.py": "26a4c1e082ee91128648b2b9bd13cc32ce915f82",
    },
}
ROOT_ENV_OUTPUT = {
    "StegVerse-org/StegVerse-SDK": "STEGVERSE_SDK_SOURCE_ROOT",
    "StegVerse-Labs/StegCore": "STEGVERSE_STEGCORE_SOURCE_ROOT",
    "Data-Continuation/core-lite": "STEGVERSE_CORE_LITE_SOURCE_ROOT",
    "master-records/orchestration": "STEGVERSE_MASTER_RECORDS_SOURCE_ROOT",
}
WARRANT_SCHEMA = "stegverse.tvc-github-repository-operation-warrant/v0.1"
RECEIPT_SCHEMA = "stegverse.tvc-github-repository-operation-receipt/v0.1"


class PrivateSourcePending(RuntimeError):
    pass


class SourcePinDrift(RuntimeError):
    pass


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def source_root() -> Path:
    raw = str(os.getenv(SOURCE_ROOT_ENV) or "").strip()
    root = Path(raw).expanduser().resolve() if raw else DEFAULT_SOURCE_ROOT.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def bound_root() -> Path:
    raw = str(os.getenv(BOUND_STATE_ENV) or "").strip()
    root = Path(raw).expanduser().resolve() if raw else DEFAULT_BOUND_ROOT.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def spool_root() -> Path:
    raw = str(os.getenv(TVC_SPOOL_ROOT_ENV) or "").strip()
    root = Path(raw).expanduser().resolve() if raw else DEFAULT_TVC_SPOOL.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def repo_root(base: Path, repo: str) -> Path:
    owner, name = repo.split("/", 1)
    return base / owner / name


def find_node() -> tuple[Path, dict[str, Any]]:
    for path in NODE_MARKERS:
        if not path.is_file():
            continue
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise RuntimeError("sovereign node marker must be object")
        if value.get("declared") is not True:
            raise RuntimeError("sovereign node is not declared")
        if value.get("credential_authority") != "TV/TVC":
            raise RuntimeError("credential authority must be TV/TVC")
        if value.get("github_token_required") is not False:
            raise RuntimeError("source preparation may not require GitHub token")
        return path, value
    raise RuntimeError("no declared sovereign StegVerse node marker is available")


def validate_invocation(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if invocation.get("schema") != "stegverse.worker-invocation/v0.1":
        raise RuntimeError("unexpected invocation schema")
    task = invocation.get("task") or {}
    if task.get("task_id") != TASK_ID:
        raise RuntimeError("unexpected task_id")
    if task.get("worker_id") != WORKER_ID:
        raise RuntimeError("unexpected worker_id")
    if not task.get("claim_id"):
        raise RuntimeError("canonical scheduler claim is required")
    timing = task.get("heartbeat_timing") or {}
    if not isinstance(timing.get("fencing_token"), int) or timing["fencing_token"] <= 22:
        raise RuntimeError("fresh fencing token above admitted floor is required")

    handoff = invocation.get("handoff") or {}
    authority = handoff.get("authority") or {}
    if authority.get("credential_authority") != "TV/TVC":
        raise RuntimeError("credential authority drift")
    if authority.get("github_token_required") is not False:
        raise RuntimeError("GitHub token may not be required")
    if authority.get("repository_writeback_authority") is not False:
        raise RuntimeError("source preparation may not write repositories")
    if authority.get("private_repository_transport_authority") is not False:
        raise RuntimeError("private transport authority must remain in TVC")
    if authority.get("heartbeat_grants_execution_authority") is not False:
        raise RuntimeError("heartbeat may not grant source preparation authority")

    contract = handoff.get("input_contract") or {}
    if contract.get("pinned_commits") != COMMITS:
        raise RuntimeError("source commit contract drift")
    if set(contract.get("public_repositories") or []) != PUBLIC_REPOS:
        raise RuntimeError("public repository set drift")
    if set(contract.get("private_repositories") or []) != PRIVATE_REPOS:
        raise RuntimeError("private repository set drift")
    if contract.get("tvc_operation_class") != "MATERIALIZE_SOURCE_ARCHIVE":
        raise RuntimeError("TVC operation class drift")
    return dict(task)


def verify_anchors(root: Path, repo: str) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for rel, expected in ANCHORS[repo].items():
        path = root / rel
        if not path.is_file():
            raise SourcePinDrift(f"{repo}: anchor missing: {rel}")
        actual = git_blob_sha1(path.read_bytes())
        if actual != expected:
            raise SourcePinDrift(f"{repo}: anchor drift {rel}: expected {expected}, observed {actual}")
        results[rel] = actual
    return results


def _public_archive_url(repo: str, commit: str) -> str:
    return f"https://github.com/{repo}/archive/{quote(commit, safe='')}.tar.gz"


def fetch_public_archive(repo: str, commit: str) -> bytes:
    request = Request(
        _public_archive_url(repo, commit),
        method="GET",
        headers={
            "Accept": "application/octet-stream",
            "User-Agent": "StegVerse-SV-DN1-Production-Source-Prep/1",
        },
    )
    with urlopen(request, timeout=60) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.hostname not in PUBLIC_HOSTS:
            raise RuntimeError(f"public archive redirect left admitted hosts: {response.geturl()}")
        data = response.read(MAX_PUBLIC_ARCHIVE_BYTES + 1)
    if len(data) > MAX_PUBLIC_ARCHIVE_BYTES:
        raise RuntimeError(f"{repo}: public source archive exceeds limit")
    return data


def safe_extract_archive(data: bytes, destination: Path) -> dict[str, Any]:
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    stage: Path | None = Path(tempfile.mkdtemp(prefix=f".{destination.name}.sv-dn1-", dir=parent))
    previous: Path | None = None
    files = 0
    total = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as archive:
            members = archive.getmembers()
            top_names = {
                PurePosixPath(member.name).parts[0]
                for member in members if PurePosixPath(member.name).parts
            }
            if len(top_names) != 1:
                raise RuntimeError("public archive root ambiguous")
            top = next(iter(top_names))
            for member in members:
                pure = PurePosixPath(member.name)
                if not pure.parts or pure.parts[0] != top:
                    raise RuntimeError("public archive member outside root")
                relative = PurePosixPath(*pure.parts[1:])
                if not relative.parts:
                    continue
                if ".." in relative.parts or member.issym() or member.islnk() or member.isdev():
                    raise RuntimeError("unsafe public archive member")
                assert stage is not None
                target = (stage / relative.as_posix()).resolve()
                if stage.resolve() != target and stage.resolve() not in target.parents:
                    raise RuntimeError("public archive path escape")
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    continue
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError("public archive member unreadable")
                payload = source.read()
                total += len(payload)
                if total > MAX_PUBLIC_ARCHIVE_BYTES:
                    raise RuntimeError("public archive extracted bytes exceed limit")
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
                files += 1

        if destination.exists() or destination.is_symlink():
            previous = parent / f".{destination.name}.previous-sv-dn1"
            if previous.exists() or previous.is_symlink():
                if previous.is_dir() and not previous.is_symlink():
                    shutil.rmtree(previous)
                else:
                    previous.unlink()
            os.replace(destination, previous)
        assert stage is not None
        os.replace(stage, destination)
        stage = None
        if previous is not None:
            if previous.is_dir() and not previous.is_symlink():
                shutil.rmtree(previous)
            elif previous.exists() or previous.is_symlink():
                previous.unlink()
        return {"extracted_files": files, "extracted_bytes": total}
    except Exception:
        if previous is not None and previous.exists() and not destination.exists():
            os.replace(previous, destination)
        raise
    finally:
        if stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def ensure_public_repo(base: Path, repo: str) -> dict[str, Any]:
    root = repo_root(base, repo)
    if root.is_dir():
        try:
            anchors = verify_anchors(root, repo)
            return {
                "repository": repo,
                "commit_sha": COMMITS[repo],
                "root": str(root),
                "state": "PRESENT_VERIFIED",
                "archive_fetched": False,
                "anchors": anchors,
            }
        except SourcePinDrift:
            pass

    data = fetch_public_archive(repo, COMMITS[repo])
    extraction = safe_extract_archive(data, root)
    anchors = verify_anchors(root, repo)
    return {
        "repository": repo,
        "commit_sha": COMMITS[repo],
        "root": str(root),
        "state": "MATERIALIZED_VERIFIED",
        "archive_fetched": True,
        "archive_sha256": hashlib.sha256(data).hexdigest(),
        "anchors": anchors,
        **extraction,
    }


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def operation_id(repo: str) -> str:
    slug = repo.lower().replace("/", "-").replace("_", "-").replace(".", "-")
    return f"sv-dn1-source-{slug}-{COMMITS[repo][:12]}"


def build_private_warrant(base: Path, repo: str, now: datetime) -> dict[str, Any]:
    op = operation_id(repo)
    return {
        "schema": WARRANT_SCHEMA,
        "operation_id": op,
        "operation_class": "MATERIALIZE_SOURCE_ARCHIVE",
        "repository": repo,
        "base_ref": "main",
        "expected_base_sha": COMMITS[repo],
        "destination_identity": str(repo_root(base, repo).resolve()),
        "maximum_total_bytes": MAX_PUBLIC_ARCHIVE_BYTES,
        "credential_authority": "TV/TVC",
        "consumer_credential_present": False,
        "secret_values_present": False,
        "single_use": True,
        "issued_at": iso(now),
        "expires_at": iso(now + timedelta(minutes=30)),
        "nonce": hashlib.sha256(f"{op}:{iso(now)}".encode("utf-8")).hexdigest()[:24],
        "authorization_ref": f"tvc://spool/{op}",
    }


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return value if isinstance(value, dict) else None


def validate_private_receipt(receipt: Mapping[str, Any], repo: str) -> None:
    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise RuntimeError(f"{repo}: wrong TVC receipt schema")
    if receipt.get("operation_class") != "MATERIALIZE_SOURCE_ARCHIVE":
        raise RuntimeError(f"{repo}: wrong TVC operation class")
    if receipt.get("repository") != repo:
        raise RuntimeError(f"{repo}: TVC receipt repository mismatch")
    result = receipt.get("result") or {}
    if result.get("status") != "MATERIALIZED":
        raise RuntimeError(f"{repo}: TVC materialization did not complete")
    if result.get("commit_sha") != COMMITS[repo]:
        raise SourcePinDrift(f"{repo}: TVC materialization commit mismatch")
    if receipt.get("credential_authority") != "TV/TVC":
        raise RuntimeError(f"{repo}: TVC receipt authority mismatch")
    if receipt.get("credential_value_exposed") is not False:
        raise RuntimeError(f"{repo}: TVC receipt indicates credential exposure")
    if receipt.get("non_tv_tvc_secret_or_token_used") is not False:
        raise RuntimeError(f"{repo}: TVC receipt indicates non-TV/TVC credential use")
    if receipt.get("scope_expanded") is not False:
        raise RuntimeError(f"{repo}: TVC materialization scope expanded")
    if receipt.get("merge_performed") is not False:
        raise RuntimeError(f"{repo}: TVC materialization unexpectedly performed merge")


def request_or_verify_private(base: Path, spool: Path, repo: str, now: datetime) -> dict[str, Any]:
    root = repo_root(base, repo)
    op = operation_id(repo)
    inbox = spool / "inbox" / f"{op}.json"
    outbox = spool / "outbox" / f"{op}.json"
    processed = spool / "processed" / f"{op}.json"

    if root.is_dir():
        try:
            anchors = verify_anchors(root, repo)
            receipt = _load_json(inbox)
            if receipt is not None:
                validate_private_receipt(receipt, repo)
                return {
                    "repository": repo,
                    "commit_sha": COMMITS[repo],
                    "root": str(root),
                    "state": "PRESENT_VERIFIED_WITH_TVC_RECEIPT",
                    "operation_id": op,
                    "anchors": anchors,
                    "receipt_path": str(inbox),
                }
        except SourcePinDrift:
            pass

    receipt = _load_json(inbox)
    if receipt is not None:
        validate_private_receipt(receipt, repo)
        if not root.is_dir():
            raise RuntimeError(f"{repo}: TVC receipt exists but destination root is absent")
        anchors = verify_anchors(root, repo)
        return {
            "repository": repo,
            "commit_sha": COMMITS[repo],
            "root": str(root),
            "state": "MATERIALIZED_VERIFIED_WITH_TVC_RECEIPT",
            "operation_id": op,
            "anchors": anchors,
            "receipt_path": str(inbox),
        }

    warrant = build_private_warrant(base, repo, now)
    outbox.parent.mkdir(parents=True, exist_ok=True)
    outbox.write_text(json.dumps(warrant, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "repository": repo,
        "commit_sha": COMMITS[repo],
        "root": str(root),
        "state": "TVC_MATERIALIZATION_REQUESTED",
        "operation_id": op,
        "request_path": str(outbox),
        "processed_path": str(processed),
        "receipt_path": str(inbox),
    }


def atomic_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(dict(value), handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def execute(invocation: Mapping[str, Any]) -> dict[str, Any]:
    if any(truthy(os.getenv(name)) for name in HOSTED_ENV):
        raise RuntimeError("hosted environments cannot execute sovereign production source preparation")
    present = [name for name in FORBIDDEN_CREDENTIAL_ENV if truthy(os.getenv(name))]
    if present:
        raise RuntimeError("credential-bearing environment forbidden for production source preparation: " + ",".join(sorted(present)))

    node_path, _ = find_node()
    task = validate_invocation(invocation)
    base = source_root()
    spool = spool_root()
    bound = bound_root()
    now = datetime.now(timezone.utc)

    public = [ensure_public_repo(base, repo) for repo in sorted(PUBLIC_REPOS)]
    private = [request_or_verify_private(base, spool, repo, now) for repo in sorted(PRIVATE_REPOS)]

    source_roots = {row["repository"]: row for row in public + private}
    atomic_json(bound / "observed" / "source-roots.json", {
        "schema": "stegverse.sv-dn1.production-source-roots/v1",
        "roots": source_roots,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    })
    atomic_json(bound / "requests" / "private-source-requests.json", {
        "schema": "stegverse.sv-dn1.private-source-request-state/v1",
        "requests": {row["repository"]: row for row in private},
        "credential_authority": "TV/TVC",
        "consumer_credential_present": False,
        "authority_effect": "NONE_REQUEST_ONLY",
    })

    pending = [row for row in private if "VERIFIED" not in row["state"]]
    if pending:
        raise PrivateSourcePending(
            "private canonical source pending TVC materialization: "
            + ",".join(row["repository"] for row in pending)
        )

    roots = {repo: str(repo_root(base, repo)) for repo in COMMITS}
    receipt = {
        "schema": "stegverse.sv-dn1.production-source-prep-receipt/v1",
        "task_id": TASK_ID,
        "worker_id": WORKER_ID,
        "state": "COMPLETE",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "claim_id": task.get("claim_id"),
        "fencing_token": (task.get("heartbeat_timing") or {}).get("fencing_token"),
        "node_declaration_ref": str(node_path),
        "source_roots": roots,
        "source_root_env": {
            ROOT_ENV_OUTPUT[repo]: path for repo, path in roots.items()
        },
        "pinned_commits": COMMITS,
        "public_source_roots_verified": True,
        "private_source_roots_verified": True,
        "runtime_anchor_blobs_verified": True,
        "credential_authority": "TV/TVC",
        "credential_used": False,
        "github_token_used": False,
        "private_transport_performed_by_consumer": False,
        "repository_writeback_performed": False,
        "sdk_admitted": False,
        "authority_effect": "SOURCE_PREPARATION_ONLY_NO_NEW_AUTHORITY",
    }
    atomic_json(bound / "receipts" / "latest.json", receipt)
    return receipt


def completed_response(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "COMPLETED",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_FIRST_PRODUCTION_ROUND_ANALYZED",
        "checkpoint_ref": "receipts/latest.json",
        "evidence_refs": [
            "observed/source-roots.json",
            "requests/private-source-requests.json",
            "receipts/latest.json",
        ],
        "source_root_env": receipt.get("source_root_env"),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def wait_response(exc: Exception, transition: str, dependency: str) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "HANDOFF_READY",
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
        "blocker": {
            "dependency_class": dependency,
            "problem_statement": str(exc),
            "solution_required": True,
            "may_remain_blocked": False,
            "next_solution_action": "Use the existing TV/TVC repository-operation broker for private source or reconcile the exact canonical source pin; do not introduce consumer credentials or a second broker.",
            "machine_observable_release_condition": "all four canonical source roots exist and required runtime anchor Git blob identities verify",
            "physical_additional_machine_required": False,
            "third_party_runtime_required": False,
            "github_token_required": False,
            "non_tv_tvc_secret_or_token_required": False,
            "human_action_required": False,
        },
    }


def blocked_response(exc: Exception) -> dict[str, Any]:
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": "BLOCKED",
        "transition_id": "SV_DN1_PRODUCTION_SOURCE_PREP_BLOCKED",
        "transition_sequence": 1,
        "expected_next_transition": "SV_DN1_PRODUCTION_SOURCE_PREPARATION_COMPLETE",
        "error": str(exc),
        "credential_authority": "TV/TVC",
        "github_token_used": False,
        "repository_writeback_performed": False,
    }


def main() -> int:
    try:
        raw = sys.stdin.readline()
        invocation = json.loads(raw)
        if not isinstance(invocation, dict):
            raise RuntimeError("worker invocation must be JSON object")
        receipt = execute(invocation)
        print(json.dumps(completed_response(receipt), sort_keys=True))
        return 0
    except PrivateSourcePending as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_PRIVATE_SOURCE_TVC_MATERIALIZATION_PENDING", "TVC_REPOSITORY_BROKER"), sort_keys=True))
        return 0
    except SourcePinDrift as exc:
        print(json.dumps(wait_response(exc, "SV_DN1_PRODUCTION_SOURCE_PIN_RECONCILIATION_REQUIRED", "SOURCE_IDENTITY"), sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps(blocked_response(exc), sort_keys=True))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
