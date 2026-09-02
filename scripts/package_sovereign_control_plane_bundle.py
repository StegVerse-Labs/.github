#!/usr/bin/env python3
"""Build a portable, non-secret StegVerse sovereign control-plane bundle.

The bundle is local transport only. It grants no runtime, claim, fence,
credential, route, heartbeat, or provider authority. It is designed so
StegDeploy can materialize the exact canonical resident control-plane source
without a network fetch or an incidental adjacent checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = "stegverse-control-plane-manifest.json"
TVC_HIL_SOURCE_FLOOR = "2787eece099604a4d2aad93c575167dc73e54037"
TV_RESIDENT_PROOF_SHA = "e0d102a8c187c059754eced9ac017fdb056a0222"
TVC_RESIDENT_PROOF_MIN_SHA = "e4bef703b4d6ccad858459ec502637c598948c42"
MASTER_RECORDS_SV001_SOURCE_FLOOR = "d593c920c1630aa5da20cc2622196f8676a74afd"
MASTER_RECORDS_SV001_PROTECTED_PATHS = (
    "scripts/watch_stegverse001_autonomy_receipt.py",
    "scripts/import_stegverse001_autonomy_receipt.py",
)
SV002_MICRO_NODE_COMMIT = "410c4267b4145ed1c1f5f2d954f3926429a43c01"
SV002_MICRO_NODE_REQUIRED_PATHS = (
    "tools/run_self_characterization_principal.py",
    "tools/verify_self_characterization_runtime_identity.py",
    "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json",
    "schemas/self_characterization_runtime_identity.schema.json",
)
SV002_FORMAL_PINS = {
    "TT": "ab60b42934222a2cb5335a5a8194f258a491fc57",
    "RTG": "ca69954cb3dc4ad073c9244e003bc8f0ef3837e2",
    "GTG": "8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225",
    "AE": "53c8eedddc4e54d8fa0660039d65ab9ac63057a1",
}
TV_RESIDENT_PROOF_REQUIRED_PATHS = (
    "scripts/tv_run_resident_operational_proof.py",
    "docs/TV_OPERATIONAL_PROOF_SCHEMA.json",
)
TVC_RESIDENT_PROOF_REQUIRED_PATHS = (
    "tools/task_dispatcher.py",
    "tv_resident_operational_proof_task.py",
    "scripts/activate_tv_resident_operational_proof.py",
)
TVC_HIL_PROTECTED_PATHS = (
    "tools/hil_intr_lifecycle_intake.py",
    "tasks/hil_experiment_backend_adapter.py",
    "tasks/experiment_controlled_cycle.py",
    "config/experiment_backend.json",
    "config/package_registry.json",
)

INCLUDE_DIRS = (
    "heartbeat_runtime",
    "control",
    "handoffs",
    "authorizations",
    "workers",
    "schemas",
    "cost-basis",
    "management",
    "state_language",
    "scripts",
)
INCLUDE_FILES = (
    "README.md",
)
EXCLUDE_PARTS = {
    ".git",
    ".github",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}
EXCLUDE_PREFIXES = (
    "receipts/",
    "events/",
    "checkpoints/",
)
FORBIDDEN_NAME_FRAGMENTS = (
    ".env",
    "credential",
    "private_key",
    "private-key",
    "secret",
    "token",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", str(Path.home())),
        },
    )


def _git_bytes(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=False,
        check=False,
        timeout=60,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", str(Path.home())),
        },
    )


def _snapshot_path_allowed(relative: str) -> bool:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        return False
    if any(part in EXCLUDE_PARTS for part in path.parts):
        return False
    posix = path.as_posix()
    if any(posix.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
        return False
    lower = posix.lower()
    if any(fragment in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
        if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".js", ".html", ".css"}:
            return False
    return True


def git_snapshot_source_proof(root: Path, *, repository: str, materialized_subpath: str, commit: str) -> dict:
    root = root.expanduser().resolve()
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": repository,
        "materialized_subpath": materialized_subpath,
        "exact_commit": commit,
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    exists = _git(root, "cat-file", "-e", commit + "^{commit}")
    if exists.returncode != 0:
        return {**proof, "state": "UNVERIFIED_PINNED_COMMIT_NOT_PRESENT"}
    return {**proof, "state": "VERIFIED_LOCAL_GIT_OBJECT_SNAPSHOT", "commit_object_present": True}


def git_snapshot_entries(root: Path, *, commit: str, prefix: str) -> list[tuple[str, bytes, int]]:
    proof = git_snapshot_source_proof(root, repository="LOCAL", materialized_subpath=prefix.rstrip("/"), commit=commit)
    if proof.get("state") != "VERIFIED_LOCAL_GIT_OBJECT_SNAPSHOT":
        raise RuntimeError("pinned Git commit not locally available")
    listing = _git_bytes(root, "ls-tree", "-r", "-z", commit)
    if listing.returncode != 0:
        raise RuntimeError("pinned Git tree unavailable")
    entries: list[tuple[str, bytes, int]] = []
    for record in listing.stdout.split(b"\0"):
        if not record:
            continue
        meta, sep, raw_path = record.partition(b"\t")
        if not sep:
            raise RuntimeError("invalid pinned Git tree entry")
        fields = meta.decode("ascii").split()
        if len(fields) != 3 or fields[1] != "blob":
            continue
        mode = 0o755 if fields[0] == "100755" else 0o644
        relative = raw_path.decode("utf-8")
        if not _snapshot_path_allowed(relative):
            continue
        blob = _git_bytes(root, "show", f"{commit}:{relative}")
        if blob.returncode != 0:
            raise RuntimeError("pinned Git blob unavailable: " + relative)
        entries.append((prefix.rstrip("/") + "/" + relative, blob.stdout, mode))
    return sorted(entries, key=lambda row: row[0])


def tv_source_proof(root: Path) -> dict:
    root = root.expanduser().resolve()
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": "StegVerse-Labs/TV",
        "materialized_subpath": "vendor/TV",
        "exact_head": TV_RESIDENT_PROOF_SHA,
        "required_paths": list(TV_RESIDENT_PROOF_REQUIRED_PATHS),
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {**proof, "state": "UNVERIFIED_GIT_HEAD_UNAVAILABLE"}
    observed = head.stdout.strip().lower()
    if observed != TV_RESIDENT_PROOF_SHA:
        return {**proof, "state": "UNVERIFIED_EXACT_HEAD_MISMATCH", "head": observed}
    status = _git(root, "status", "--porcelain")
    if status.returncode != 0 or status.stdout.strip():
        return {**proof, "state": "UNVERIFIED_WORKTREE_NOT_CLEAN", "head": observed}
    missing = [rel for rel in TV_RESIDENT_PROOF_REQUIRED_PATHS if not (root / rel).is_file()]
    if missing:
        return {**proof, "state": "UNVERIFIED_REQUIRED_PATH_MISSING", "head": observed, "missing": missing}
    return {**proof, "state": "VERIFIED_LOCAL_GIT_SOURCE", "head": observed, "exact_head_verified": True, "clean_worktree_at_packaging": True}

def tvc_source_proof(root: Path, *, source_floor: str = TVC_HIL_SOURCE_FLOOR) -> dict:
    root = root.expanduser().resolve()
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": "StegVerse-Labs/TVC",
        "materialized_subpath": "vendor/TVC",
        "source_floor": source_floor,
        "protected_paths": list(TVC_HIL_PROTECTED_PATHS),
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {**proof, "state": "UNVERIFIED_GIT_HEAD_UNAVAILABLE"}
    ancestor = _git(root, "merge-base", "--is-ancestor", source_floor, "HEAD")
    if ancestor.returncode != 0:
        return {**proof, "state": "UNVERIFIED_SOURCE_FLOOR_NOT_PRESENT", "head": head.stdout.strip().lower()}
    resident_ancestor = _git(root, "merge-base", "--is-ancestor", TVC_RESIDENT_PROOF_MIN_SHA, "HEAD")
    changed = _git(root, "diff", "--name-only", source_floor, "HEAD", "--", *TVC_HIL_PROTECTED_PATHS)
    working = _git(root, "diff", "--name-only", "--", *TVC_HIL_PROTECTED_PATHS)
    staged = _git(root, "diff", "--cached", "--name-only", "--", *TVC_HIL_PROTECTED_PATHS)
    if (
        changed.returncode != 0
        or working.returncode != 0
        or staged.returncode != 0
        or changed.stdout.strip()
        or working.stdout.strip()
        or staged.stdout.strip()
    ):
        return {**proof, "state": "UNVERIFIED_PROTECTED_PATH_DRIFT", "head": head.stdout.strip().lower()}
    missing = [rel for rel in TVC_HIL_PROTECTED_PATHS if not (root / rel).is_file()]
    if missing:
        return {**proof, "state": "UNVERIFIED_PROTECTED_PATH_MISSING", "missing": missing, "head": head.stdout.strip().lower()}
    return {
        **proof,
        "state": "VERIFIED_LOCAL_GIT_SOURCE",
        "head": head.stdout.strip().lower(),
        "source_floor_present": True,
        "protected_paths_unchanged_since_floor": True,
        "protected_worktree_clean": True,
        "verified_ancestors": [source_floor] + ([TVC_RESIDENT_PROOF_MIN_SHA] if resident_ancestor.returncode == 0 else []),
        "resident_proof_min_sha_present": resident_ancestor.returncode == 0,
    }


def master_records_source_proof(root: Path, *, source_floor: str = MASTER_RECORDS_SV001_SOURCE_FLOOR) -> dict:
    root = root.expanduser().resolve()
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": "master-records/orchestration",
        "materialized_subpath": "vendor/master-records-orchestration",
        "source_floor": source_floor,
        "protected_paths": list(MASTER_RECORDS_SV001_PROTECTED_PATHS),
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    head = _git(root, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {**proof, "state": "UNVERIFIED_GIT_HEAD_UNAVAILABLE"}
    observed = head.stdout.strip().lower()
    ancestor = _git(root, "merge-base", "--is-ancestor", source_floor, "HEAD")
    if ancestor.returncode != 0:
        return {**proof, "state": "UNVERIFIED_SOURCE_FLOOR_NOT_PRESENT", "head": observed}
    status = _git(root, "status", "--porcelain")
    if status.returncode != 0 or status.stdout.strip():
        return {**proof, "state": "UNVERIFIED_WORKTREE_NOT_CLEAN", "head": observed}
    missing = [rel for rel in MASTER_RECORDS_SV001_PROTECTED_PATHS if not (root / rel).is_file()]
    if missing:
        return {**proof, "state": "UNVERIFIED_PROTECTED_PATH_MISSING", "head": observed, "missing": missing}
    changed = _git(root, "diff", "--name-only", source_floor, "HEAD", "--", *MASTER_RECORDS_SV001_PROTECTED_PATHS)
    if changed.returncode != 0 or changed.stdout.strip():
        return {**proof, "state": "UNVERIFIED_PROTECTED_PATH_DRIFT", "head": observed}
    return {
        **proof,
        "state": "VERIFIED_LOCAL_GIT_SOURCE",
        "head": observed,
        "source_floor_present": True,
        "protected_paths_unchanged_since_floor": True,
        "clean_worktree_at_packaging": True,
    }


def _safe_tree_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDE_PARTS for part in relative.parts):
            continue
        posix = relative.as_posix()
        if any(posix.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
            continue
        lower = posix.lower()
        if any(fragment in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
            if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".js", ".html", ".css"}:
                continue
        paths.append(path)
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def _included_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for name in INCLUDE_FILES:
        path = root / name
        if path.is_file():
            paths.add(path)
    for rel in INCLUDE_DIRS:
        base = root / rel
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.is_symlink():
                continue
            relative = path.relative_to(root)
            if any(part in EXCLUDE_PARTS for part in relative.parts):
                continue
            posix = relative.as_posix()
            if any(posix.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
                continue
            lower = posix.lower()
            if any(fragment in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
                # Canonical source references to credentials/tokens are valid code.
                # Only reject likely secret-bearing file classes, not source filenames.
                if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".yaml", ".yml"}:
                    continue
            paths.add(path)
    return sorted(paths, key=lambda p: p.relative_to(root).as_posix())


def build_bundle(
    root: Path,
    output: Path,
    *,
    stegos_root: Path | None = None,
    kv_source_root: Path | None = None,
    healer_root: Path | None = None,
    tv_root: Path | None = None,
    tvc_root: Path | None = None,
    master_records_root: Path | None = None,
    micro_node_root: Path | None = None,
    tt_root: Path | None = None,
    rtg_root: Path | None = None,
    gtg_root: Path | None = None,
    ae_root: Path | None = None,
) -> dict:
    root = root.resolve()
    output = output.resolve()
    files = _included_files(root)
    required = root / "scripts" / "bootstrap_sovereign_runtime.py"
    if required not in files:
        raise RuntimeError("canonical bootstrap missing from bundle source")

    bundle_files: list[tuple[str, Path]] = [
        (path.relative_to(root).as_posix(), path) for path in files
    ]
    vendor_sources = {}
    vendor_source_proofs = {}
    bundle_blobs: list[tuple[str, bytes, int]] = []
    if stegos_root is not None:
        sr = stegos_root.expanduser().resolve()
        if not (sr / "stegos" / "intr_backbone.py").is_file():
            raise RuntimeError("StegOS source root invalid")
        vendor_sources["StegOS"] = True
        bundle_files.extend(
            ("vendor/StegOS/" + path.relative_to(sr).as_posix(), path)
            for path in _safe_tree_files(sr)
        )
    if kv_source_root is not None:
        kr = kv_source_root.expanduser().resolve()
        if not (kr / "runtime" / "kv_interlock_endpoint.py").is_file():
            raise RuntimeError("continuity-vault-kit source root invalid")
        vendor_sources["continuity-vault-kit"] = True
        bundle_files.extend(
            ("vendor/continuity-vault-kit/" + path.relative_to(kr).as_posix(), path)
            for path in _safe_tree_files(kr)
        )
    if healer_root is not None:
        hr = healer_root.expanduser().resolve()
        healer_required = (
            hr / "app" / "dispatch_orchestrators.py",
            hr / "data" / "orchestrator_targets.json",
            hr / "docs" / "HEALER_MIRROR_HANDOFF.md",
        )
        if not all(path.is_file() for path in healer_required):
            raise RuntimeError("StegVerse-Healer source root invalid")
        vendor_sources["StegVerse-Healer"] = True
        bundle_files.extend(
            ("vendor/StegVerse-Healer/" + path.relative_to(hr).as_posix(), path)
            for path in _safe_tree_files(hr)
        )
    if tv_root is not None:
        vr = tv_root.expanduser().resolve()
        missing_tv = [rel for rel in TV_RESIDENT_PROOF_REQUIRED_PATHS if not (vr / rel).is_file()]
        if missing_tv:
            raise RuntimeError("TV source root invalid")
        vendor_sources["TV"] = True
        vendor_source_proofs["TV"] = tv_source_proof(vr)
        bundle_files.extend(
            ("vendor/TV/" + path.relative_to(vr).as_posix(), path)
            for path in _safe_tree_files(vr)
        )
    if tvc_root is not None:
        tr = tvc_root.expanduser().resolve()
        tvc_required = (
            tr / "TVC_MIRROR_HANDOFF.md",
            tr / "scripts" / "activate_coinbase_intr_resident.py",
            tr / "tools" / "hil_intr_lifecycle_intake.py",
        )
        if not all(path.is_file() for path in tvc_required):
            raise RuntimeError("TVC source root invalid")
        vendor_sources["TVC"] = True
        vendor_source_proofs["TVC"] = tvc_source_proof(tr)
        bundle_files.extend(
            ("vendor/TVC/" + path.relative_to(tr).as_posix(), path)
            for path in _safe_tree_files(tr)
        )
    if master_records_root is not None:
        mr = master_records_root.expanduser().resolve()
        missing_master_records = [
            rel for rel in MASTER_RECORDS_SV001_PROTECTED_PATHS if not (mr / rel).is_file()
        ]
        if missing_master_records:
            raise RuntimeError("Master Records source root invalid")
        proof = master_records_source_proof(mr)
        if proof.get("state") != "VERIFIED_LOCAL_GIT_SOURCE":
            raise RuntimeError("Master Records source proof not verified: " + str(proof.get("state")))
        vendor_sources["master-records/orchestration"] = True
        vendor_source_proofs["master-records/orchestration"] = proof
        bundle_files.extend(
            ("vendor/master-records-orchestration/" + path.relative_to(mr).as_posix(), path)
            for path in _safe_tree_files(mr)
        )
    if micro_node_root is not None:
        micro = micro_node_root.expanduser().resolve()
        proof = git_snapshot_source_proof(
            micro,
            repository="StegVerse-002/micro-node-runtime",
            materialized_subpath="vendor/micro-node-runtime",
            commit=SV002_MICRO_NODE_COMMIT,
        )
        if proof.get("state") != "VERIFIED_LOCAL_GIT_OBJECT_SNAPSHOT":
            raise RuntimeError("SV002 micro-node pinned source not locally available")
        snapshot = git_snapshot_entries(micro, commit=SV002_MICRO_NODE_COMMIT, prefix="vendor/micro-node-runtime")
        names = {rel for rel, _data, _mode in snapshot}
        missing = [
            rel for rel in SV002_MICRO_NODE_REQUIRED_PATHS
            if "vendor/micro-node-runtime/" + rel not in names
        ]
        if missing:
            raise RuntimeError("SV002 micro-node pinned snapshot missing required path")
        vendor_sources["StegVerse-002/micro-node-runtime"] = True
        vendor_source_proofs["StegVerse-002/micro-node-runtime"] = proof
        bundle_blobs.extend(snapshot)

    formal_roots = {"TT": tt_root, "RTG": rtg_root, "GTG": gtg_root, "AE": ae_root}
    for name, formal_root in formal_roots.items():
        if formal_root is None:
            continue
        fr = formal_root.expanduser().resolve()
        commit = SV002_FORMAL_PINS[name]
        repository = f"Admissible-Existence/{name}"
        subpath = f"vendor/formal/{name}"
        proof = git_snapshot_source_proof(
            fr,
            repository=repository,
            materialized_subpath=subpath,
            commit=commit,
        )
        if proof.get("state") != "VERIFIED_LOCAL_GIT_OBJECT_SNAPSHOT":
            raise RuntimeError(f"{repository} pinned source not locally available")
        snapshot = git_snapshot_entries(fr, commit=commit, prefix=subpath)
        if not snapshot:
            raise RuntimeError(f"{repository} pinned snapshot empty")
        vendor_sources[repository] = True
        vendor_source_proofs[repository] = proof
        bundle_blobs.extend(snapshot)

    entries = []
    for rel, path in bundle_files:
        data = path.read_bytes()
        entries.append({
            "path": rel,
            "sha256": _sha256(data),
            "size": len(data),
        })
    for rel, data, _mode in bundle_blobs:
        entries.append({
            "path": rel,
            "sha256": _sha256(data),
            "size": len(data),
        })

    manifest = {
        "schema": "stegverse.sovereign-control-plane-bundle/v1",
        "file_count": len(entries),
        "files": entries,
        "network_fetch_required": False,
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
        "heartbeat_grants_execution_authority": False,
        "bundle_grants_authority": False,
        "authority_effect": "NONE_SOURCE_TRANSPORT_ONLY",
        "vendor_sources": vendor_sources,
        "vendor_source_proofs": vendor_source_proofs,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")

    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for rel, path in bundle_files:
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = path.stat().st_mode
            info.external_attr = ((stat.S_IMODE(mode) or 0o644) & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())
        for rel, data, mode in bundle_blobs:
            info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, data)
        info = zipfile.ZipInfo(MANIFEST_NAME, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = (0o644 & 0xFFFF) << 16
        archive.writestr(info, manifest_bytes)

    bundle_bytes = output.read_bytes()
    receipt = {
        **manifest,
        "bundle_path": str(output),
        "bundle_sha256": _sha256(bundle_bytes),
        "bundle_size": len(bundle_bytes),
    }
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stegos-root", type=Path)
    parser.add_argument("--kv-source-root", type=Path)
    parser.add_argument("--healer-root", type=Path)
    parser.add_argument("--tv-root", type=Path)
    parser.add_argument("--tvc-root", type=Path)
    parser.add_argument("--master-records-root", type=Path)
    parser.add_argument("--micro-node-root", type=Path)
    parser.add_argument("--tt-root", type=Path)
    parser.add_argument("--rtg-root", type=Path)
    parser.add_argument("--gtg-root", type=Path)
    parser.add_argument("--ae-root", type=Path)
    args = parser.parse_args()
    receipt = build_bundle(
        args.source_root,
        args.output,
        stegos_root=args.stegos_root,
        kv_source_root=args.kv_source_root,
        healer_root=args.healer_root,
        tv_root=args.tv_root,
        tvc_root=args.tvc_root,
        master_records_root=args.master_records_root,
        micro_node_root=args.micro_node_root,
        tt_root=args.tt_root,
        rtg_root=args.rtg_root,
        gtg_root=args.gtg_root,
        ae_root=args.ae_root,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
