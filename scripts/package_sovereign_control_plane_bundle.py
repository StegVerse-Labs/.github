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
TV_RESIDENT_PROOF_REQUIRED_PATHS = (
    "scripts/tv_run_resident_operational_proof.py",
    "docs/TV_OPERATIONAL_PROOF_SCHEMA.json",
)
TVC_RESIDENT_PROOF_REQUIRED_PATHS = (
    "tools/task_dispatcher.py",
    "tv_resident_operational_proof_task.py",
    "scripts/activate_tv_resident_operational_proof.py",
)
SV002_MICRO_NODE_SOURCE_PIN = "496f17e0cb07433f3f9312e82a2c045f5d901dc9"
SV002_MICRO_NODE_REQUIRED_PATHS = (
    "tools/run_self_characterization_principal.py",
    "tools/verify_self_characterization_runtime_identity.py",
    "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json",
    "schemas/self_characterization_runtime_identity.schema.json",
)
MASTER_RECORDS_RECONSTRUCTION_COMMIT = "2e117902d4f261b10cb3b5122b7ef48fb0e36e57"
MASTER_RECORDS_RECONSTRUCTION_VERIFIER = "scripts/verify_sv002_self_characterization_reconstruction.py"
MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB = "cc96556a23b5bd804f3cdaa96539b379c1904437"
FORMAL_SOURCE_PINS = {
    "TT": "ab60b42934222a2cb5335a5a8194f258a491fc57",
    "RTG": "ca69954cb3dc4ad073c9244e003bc8f0ef3837e2",
    "GTG": "8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225",
    "AE": "53c8eedddc4e54d8fa0660039d65ab9ac63057a1",
}
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


def sv002_micro_node_source_proof(root: Path) -> dict:
    root = root.expanduser().resolve()
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": "StegVerse-002/micro-node-runtime",
        "materialized_subpath": "vendor/micro-node-runtime",
        "exact_head": SV002_MICRO_NODE_SOURCE_PIN,
        "required_paths": list(SV002_MICRO_NODE_REQUIRED_PATHS),
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    observed = head.stdout.strip().lower() if head.returncode == 0 else None
    if observed != SV002_MICRO_NODE_SOURCE_PIN:
        return {**proof, "state": "UNVERIFIED_EXACT_HEAD_MISMATCH", "head": observed}
    if status.returncode != 0 or status.stdout.strip():
        return {**proof, "state": "UNVERIFIED_WORKTREE_NOT_CLEAN", "head": observed}
    missing = [rel for rel in SV002_MICRO_NODE_REQUIRED_PATHS if not (root / rel).is_file()]
    if missing:
        return {**proof, "state": "UNVERIFIED_REQUIRED_PATH_MISSING", "head": observed, "missing": missing}
    return {**proof, "state": "VERIFIED_LOCAL_GIT_SOURCE", "head": observed, "exact_head_verified": True, "clean_worktree_at_packaging": True}


def master_records_source_proof(root: Path) -> dict:
    root = root.expanduser().resolve()
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": "master-records/orchestration",
        "materialized_subpath": "vendor/master-records-orchestration",
        "required_ancestor": MASTER_RECORDS_RECONSTRUCTION_COMMIT,
        "verifier_path": MASTER_RECORDS_RECONSTRUCTION_VERIFIER,
        "required_verifier_git_blob": MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB,
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    head = _git(root, "rev-parse", "HEAD")
    ancestor = _git(root, "merge-base", "--is-ancestor", MASTER_RECORDS_RECONSTRUCTION_COMMIT, "HEAD")
    verifier = root / MASTER_RECORDS_RECONSTRUCTION_VERIFIER
    if head.returncode != 0 or ancestor.returncode != 0:
        return {**proof, "state": "UNVERIFIED_REQUIRED_ANCESTOR_NOT_PRESENT", "head": head.stdout.strip().lower() if head.returncode == 0 else None}
    if not verifier.is_file():
        return {**proof, "state": "UNVERIFIED_VERIFIER_MISSING", "head": head.stdout.strip().lower()}
    status = _git(root, "status", "--porcelain", "--", MASTER_RECORDS_RECONSTRUCTION_VERIFIER)
    blob = _git(root, "hash-object", str(verifier))
    observed_blob = blob.stdout.strip().lower() if blob.returncode == 0 else None
    if status.returncode != 0 or status.stdout.strip() or observed_blob != MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB:
        return {**proof, "state": "UNVERIFIED_VERIFIER_SOURCE_MISMATCH", "head": head.stdout.strip().lower(), "observed_verifier_git_blob": observed_blob}
    return {**proof, "state": "VERIFIED_LOCAL_GIT_SOURCE", "head": head.stdout.strip().lower(), "required_ancestor_present": True, "verifier_git_blob": observed_blob, "verifier_worktree_clean": True}


def formal_snapshot_proof(name: str, root: Path) -> dict:
    root = root.expanduser().resolve()
    commit = FORMAL_SOURCE_PINS[name]
    proof = {
        "schema": "stegverse.portable-source-proof/v1",
        "repository": f"Admissible-Existence/{name}",
        "materialized_subpath": f"vendor/formal/{name}",
        "exact_commit": commit,
        "snapshot_source": "LOCAL_GIT_OBJECT_DATABASE",
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE_SOURCE_IDENTITY_ONLY",
    }
    if not (root / ".git").is_dir():
        return {**proof, "state": "UNVERIFIED_NO_LOCAL_GIT_IDENTITY"}
    exists = _git(root, "cat-file", "-e", f"{commit}^{commit}")
    if exists.returncode != 0:
        return {**proof, "state": "UNVERIFIED_PINNED_COMMIT_NOT_PRESENT"}
    return {**proof, "state": "VERIFIED_LOCAL_GIT_SNAPSHOT", "exact_commit_present": True}


def _git_snapshot_items(root: Path, commit: str, prefix: str) -> list[tuple[str, bytes]]:
    root = root.expanduser().resolve()
    listed = _git(root, "ls-tree", "-r", "--name-only", commit)
    if listed.returncode != 0:
        raise RuntimeError("pinned formal snapshot tree unavailable")
    items: list[tuple[str, bytes]] = []
    for rel in sorted(line.strip() for line in listed.stdout.splitlines() if line.strip()):
        path = Path(rel)
        if path.is_absolute() or ".." in path.parts or any(part in EXCLUDE_PARTS for part in path.parts):
            continue
        lower = rel.lower()
        if any(fragment in lower for fragment in FORBIDDEN_NAME_FRAGMENTS):
            if path.suffix.lower() not in {".py", ".json", ".md", ".txt", ".yaml", ".yml"}:
                continue
        shown = subprocess.run(
            ["git", "-C", str(root), "show", f"{commit}:{rel}"],
            capture_output=True,
            check=False,
            timeout=30,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.environ.get("HOME", str(Path.home()))},
        )
        if shown.returncode != 0:
            raise RuntimeError(f"pinned formal snapshot file unavailable:{rel}")
        items.append((prefix + "/" + rel, shown.stdout))
    return items


def _source_bytes(source: Path | bytes) -> bytes:
    return source if isinstance(source, bytes) else source.read_bytes()


def _source_mode(source: Path | bytes) -> int:
    return 0o644 if isinstance(source, bytes) else (stat.S_IMODE(source.stat().st_mode) or 0o644)


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
    micro_node_root: Path | None = None,
    master_records_root: Path | None = None,
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

    bundle_files: list[tuple[str, Path | bytes]] = [
        (path.relative_to(root).as_posix(), path) for path in files
    ]
    vendor_sources = {}
    vendor_source_proofs = {}
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
    if micro_node_root is not None:
        mr = micro_node_root.expanduser().resolve()
        missing_micro = [rel for rel in SV002_MICRO_NODE_REQUIRED_PATHS if not (mr / rel).is_file()]
        if missing_micro:
            raise RuntimeError("micro-node-runtime source root invalid")
        vendor_sources["micro-node-runtime"] = True
        vendor_source_proofs["micro-node-runtime"] = sv002_micro_node_source_proof(mr)
        bundle_files.extend(
            ("vendor/micro-node-runtime/" + path.relative_to(mr).as_posix(), path)
            for path in _safe_tree_files(mr)
        )
    if master_records_root is not None:
        rr = master_records_root.expanduser().resolve()
        if not (rr / MASTER_RECORDS_RECONSTRUCTION_VERIFIER).is_file():
            raise RuntimeError("master-records/orchestration source root invalid")
        vendor_sources["master-records-orchestration"] = True
        vendor_source_proofs["master-records-orchestration"] = master_records_source_proof(rr)
        bundle_files.extend(
            ("vendor/master-records-orchestration/" + path.relative_to(rr).as_posix(), path)
            for path in _safe_tree_files(rr)
        )
    formal_roots = {"TT": tt_root, "RTG": rtg_root, "GTG": gtg_root, "AE": ae_root}
    for formal_name, formal_root in formal_roots.items():
        if formal_root is None:
            continue
        fr = formal_root.expanduser().resolve()
        proof = formal_snapshot_proof(formal_name, fr)
        if proof.get("state") != "VERIFIED_LOCAL_GIT_SNAPSHOT":
            raise RuntimeError(f"{formal_name} pinned formal source unavailable:{proof.get('state')}")
        vendor_sources[f"formal-{formal_name}"] = True
        vendor_source_proofs[f"formal-{formal_name}"] = proof
        bundle_files.extend(_git_snapshot_items(fr, FORMAL_SOURCE_PINS[formal_name], f"vendor/formal/{formal_name}"))
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
    entries = []
    for rel, path in bundle_files:
        data = _source_bytes(path)
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
            mode = _source_mode(path)
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, _source_bytes(path))
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
    parser.add_argument("--micro-node-root", type=Path)
    parser.add_argument("--master-records-root", type=Path)
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
        micro_node_root=args.micro_node_root,
        master_records_root=args.master_records_root,
        tt_root=args.tt_root,
        rtg_root=args.rtg_root,
        gtg_root=args.gtg_root,
        ae_root=args.ae_root,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
