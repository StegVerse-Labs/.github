#!/usr/bin/env python3
"""One-shot activation of the complete resident StegVerse execution stack.

This is a local sovereign orchestration entrypoint. It packages the canonical
.github control plane, starts LLM-adapter's host-native Service Gateway
(scripts/stegdeploy_native_gateway.py start; no container framework), then
materializes the packaged bundle and invokes its resident bootstrap exactly as
StegDeploy's former post-deploy hook (_activate_resident_control_plane) did.
The start transition closes on the spawned process; gateway health is never
awaited. The bootstrap primes the resident WorkerCoordinator, dispatches
resident requests, and immediately advances independently admitted successors.
G18 verification is retained only as diagnostic/housekeeping evidence and does
not gate downstream work.

The entrypoint grants no claim, fence, heartbeat, credential, route, provider,
or execution authority. It refuses hosted execution surfaces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_sovereign_control_plane_bundle.py"
HOSTED_ENV = (
    "GITHUB_ACTIONS", "CI", "RENDER", "RENDER_SERVICE_ID",
    "VERCEL", "VERCEL_ENV", "CF_PAGES", "CLOUDFLARE_WORKERS",
)
FORBIDDEN_RUNTIME_ENV = (
    "GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT", "STEGVERSE_GITHUB_TOKEN",
)
DEFAULT_RECEIPT = ROOT / "receipts" / "sovereign-host" / "resident-stack-activation.latest.json"
NATIVE_GATEWAY_RECEIPT_SCHEMA = "stegdeploy.native-sovereign-gateway-receipt/v1"
NATIVE_GATEWAY_STARTED = "LOCAL_NATIVE_GATEWAY_STARTED"
NATIVE_GATEWAY_ALREADY_RUNNING = "native_gateway_already_running"
CONTROL_BUNDLE_MANIFEST = "stegverse-control-plane-manifest.json"


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in {"", "0", "false", "no"}


def clean_env(values: Mapping[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if values is None else values)
    hosted = sorted(name for name in HOSTED_ENV if truthy(source.get(name)))
    if hosted:
        raise RuntimeError("hosted execution surface rejected: " + ",".join(hosted))
    for name in FORBIDDEN_RUNTIME_ENV:
        source.pop(name, None)
    source["STEGVERSE_GITHUB_TOKEN_RUNTIME_AUTHORITY"] = "NONE"
    source["STEGVERSE_TV_TVC_CREDENTIAL_AUTHORITY"] = "TV/TVC"
    return source


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except Exception:
        return None


def parse_last_json(stdout: str) -> dict[str, Any] | None:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict):
            return value
    return None


def native_gateway_receipt_path(env: Mapping[str, str]) -> Path:
    """Receipt path written by LLM-adapter scripts/stegdeploy_native_gateway.py start."""
    override = env.get("STEGVERSE_SERVICE_GATEWAY_NATIVE_STATE_ROOT")
    if override:
        root = Path(override).expanduser()
    else:
        if sys.platform == "win32":
            base = Path(env.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path(env.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state")))
        root = base / "stegverse" / "service-gateway"
    return root.resolve() / "native-deployment-receipt.json"


def parse_json_document(stdout: str) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout)
    except Exception:
        return parse_last_json(stdout)
    return value if isinstance(value, dict) else None


def materialize_control_bundle(bundle_path: Path, state_dir: Path) -> Path:
    """Verify and unpack the packaged control bundle, as StegDeploy's hook did."""
    bundle = bundle_path.expanduser().resolve()
    if not bundle.is_file():
        raise RuntimeError("resident_control_bundle_missing")
    target = state_dir / "resident-control-plane"
    staging = state_dir / "resident-control-plane.staging"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(bundle) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if CONTROL_BUNDLE_MANIFEST not in names:
            raise RuntimeError("resident_control_bundle_manifest_missing")
        for info in infos:
            path = Path(info.filename)
            if path.is_absolute() or ".." in path.parts:
                raise RuntimeError("resident_control_bundle_path_invalid")
            if stat.S_ISLNK((info.external_attr >> 16) & 0xFFFF):
                raise RuntimeError("resident_control_bundle_symlink_rejected")
        manifest = json.loads(archive.read(CONTROL_BUNDLE_MANIFEST).decode("utf-8"))
        if manifest.get("schema") != "stegverse.sovereign-control-plane-bundle/v1":
            raise RuntimeError("resident_control_bundle_schema_invalid")
        if manifest.get("network_fetch_required") is not False:
            raise RuntimeError("resident_control_bundle_network_policy_invalid")
        if manifest.get("credential_authority") != "TV/TVC":
            raise RuntimeError("resident_control_bundle_credential_authority_invalid")
        if manifest.get("github_token_runtime_authority") != "NONE":
            raise RuntimeError("resident_control_bundle_github_authority_invalid")
        if manifest.get("bundle_grants_authority") is not False:
            raise RuntimeError("resident_control_bundle_authority_invalid")
        declared = {entry.get("path"): entry for entry in manifest.get("files", []) if isinstance(entry, dict)}
        actual = {name for name in names if name != CONTROL_BUNDLE_MANIFEST and not name.endswith("/")}
        if set(declared) != actual:
            raise RuntimeError("resident_control_bundle_file_set_mismatch")
        for name in sorted(actual):
            data = archive.read(name)
            entry = declared[name]
            if len(data) != entry.get("size"):
                raise RuntimeError("resident_control_bundle_size_mismatch")
            if hashlib.sha256(data).hexdigest() != entry.get("sha256"):
                raise RuntimeError("resident_control_bundle_digest_mismatch")
            destination = staging / Path(name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
    (staging / ".stegverse-source-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not (staging / "scripts" / "bootstrap_sovereign_runtime.py").is_file():
        raise RuntimeError("resident_control_bundle_bootstrap_missing")
    if target.exists():
        shutil.rmtree(target)
    staging.replace(target)
    return target.resolve()


def _all_files(root: Path, rels: tuple[str, ...]) -> bool:
    return all((root / rel).is_file() for rel in rels)


def activate_resident_control_plane(
    bundle: Path,
    llm_root: Path,
    *,
    env: Mapping[str, str],
    runner=subprocess.run,
) -> dict[str, Any]:
    """Run the packaged resident bootstrap after the native gateway start.

    Carries StegDeploy's former post-deploy hook (_activate_resident_control_plane)
    over unchanged in effect: same materialization root, same vendored source
    bindings, same bootstrap command and the same result record.
    """
    state_dir = llm_root / ".stegdeploy"
    control_root = materialize_control_bundle(bundle, state_dir)
    command = [
        env.get("PYTHON") or sys.executable,
        str(control_root / "scripts" / "bootstrap_sovereign_runtime.py"),
        "--source-root", str(control_root),
        "--skip-post-bootstrap-stegfin",
    ]
    child_env = dict(env)
    child_env["STEGVERSE_HEARTBEAT_SOURCE_ROOT"] = str(control_root)
    child_env["STEGVERSE_LLM_ADAPTER_ROOT"] = str(llm_root)
    source_manifest = control_root / ".stegverse-source-manifest.json"
    if source_manifest.is_file():
        child_env["STEGVERSE_RESIDENT_SOURCE_MANIFEST"] = str(source_manifest)
    vendor = control_root / "vendor"
    vendor_stegos = vendor / "StegOS"
    vendor_kv = vendor / "continuity-vault-kit"
    vendor_healer = vendor / "StegVerse-Healer"
    vendor_tv = vendor / "TV"
    vendor_tvc = vendor / "TVC"
    vendor_micro_node = vendor / "micro-node-runtime"
    vendor_master_records = vendor / "master-records-orchestration"
    vendor_stegindex = vendor / "StegIndex"
    vendor_formal = {name: vendor / "formal" / name for name in ("TT", "RTG", "GTG", "AE")}
    stegos_bound = (vendor_stegos / "stegos" / "intr_backbone.py").is_file()
    kv_source_bound = (vendor_kv / "runtime" / "kv_interlock_endpoint.py").is_file()
    healer_bound = _all_files(vendor_healer, (
        "app/dispatch_orchestrators.py", "data/orchestrator_targets.json", "docs/HEALER_MIRROR_HANDOFF.md",
    ))
    tv_bound = _all_files(vendor_tv, (
        "scripts/tv_run_resident_operational_proof.py", "docs/TV_OPERATIONAL_PROOF_SCHEMA.json",
    ))
    tvc_bound = _all_files(vendor_tvc, (
        "TVC_MIRROR_HANDOFF.md", "scripts/activate_coinbase_intr_resident.py", "tools/hil_intr_lifecycle_intake.py",
    ))
    micro_node_bound = _all_files(vendor_micro_node, (
        "tools/run_self_characterization_principal.py",
        "tools/verify_self_characterization_runtime_identity.py",
        "experiments/self-characterization-001/CONSTRUCTION_PROVENANCE.v0.1.json",
        "schemas/self_characterization_runtime_identity.schema.json",
    ))
    master_records_bound = (vendor_master_records / "scripts" / "verify_sv002_self_characterization_reconstruction.py").is_file()
    stegindex_bound = _all_files(vendor_stegindex, (
        "STEGINDEX_MIRROR_HANDOFF.md",
        "scripts/preflight.py",
        "scripts/refresh_sources.py",
        "scripts/reconcile_truth.py",
        "registry/capabilities.json",
        "registry/predicates.json",
        "registry/source-catalog.json",
        "registry/discovered-candidates.json",
        "registry/ecosystem-purpose-contributions.json",
        "registry/external-capability-risk-sources.json",
    ))
    formal_bound = {
        name: root.is_dir() and any(path.is_file() for path in root.rglob("*"))
        for name, root in vendor_formal.items()
    }
    bindings = (
        (stegos_bound, ("STEGVERSE_STEGOS_ROOT",), vendor_stegos, "StegVerse-Labs/StegOS"),
        (kv_source_bound, ("STEGVERSE_KV_SOURCE_ROOT",), vendor_kv, None),
        (healer_bound, ("STEGVERSE_HEALER_ROOT",), vendor_healer, "StegVerse-Labs/StegVerse-Healer"),
        (tv_bound, ("STEGVERSE_TV_ROOT",), vendor_tv, "StegVerse-Labs/TV"),
        (tvc_bound, ("STEGVERSE_TVC_ROOT",), vendor_tvc, "StegVerse-Labs/TVC"),
        (micro_node_bound, ("STEGVERSE_MICRO_NODE_RUNTIME_ROOT",), vendor_micro_node, "StegVerse-002/micro-node-runtime"),
        (
            master_records_bound,
            ("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT", "STEGVERSE_MASTER_RECORDS_ROOT"),
            vendor_master_records,
            "master-records/orchestration",
        ),
        (stegindex_bound, ("STEGVERSE_STEGINDEX_SOURCE_ROOT",), vendor_stegindex, "StegVerse-Labs/StegIndex"),
    ) + tuple(
        (formal_bound[name], (f"STEGVERSE_{name}_ROOT",), vendor_formal[name], f"Admissible-Existence/{name}")
        for name in ("TT", "RTG", "GTG", "AE")
    )
    repo_roots: dict[str, str] = {}
    raw_repo_roots = str(child_env.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
    if raw_repo_roots:
        try:
            parsed_repo_roots = json.loads(raw_repo_roots)
        except Exception:
            parsed_repo_roots = {}
        if isinstance(parsed_repo_roots, dict):
            repo_roots.update({
                str(key): str(value)
                for key, value in parsed_repo_roots.items()
                if isinstance(key, str) and isinstance(value, str) and value
            })
    repo_roots["StegVerse-Labs/.github"] = str(control_root)
    repo_roots["StegVerse-org/LLM-adapter"] = str(llm_root)
    for bound, env_names, root, repository in bindings:
        if not bound:
            continue
        for name in env_names:
            child_env[name] = str(root)
        if repository:
            repo_roots[repository] = str(root)
    child_env["STEGVERSE_REPO_ROOTS_JSON"] = json.dumps(repo_roots, sort_keys=True, separators=(",", ":"))
    if not str(child_env.get("STEGVERSE_KV_ROOT") or "").strip():
        kv_root_path = (state_dir / "resident-kv").resolve()
        kv_root_path.mkdir(parents=True, exist_ok=True)
        child_env["STEGVERSE_KV_ROOT"] = str(kv_root_path)
    completed = runner(
        command,
        cwd=control_root,
        check=False,
        text=True,
        capture_output=True,
        timeout=3600,
        env=child_env,
    )
    result = parse_last_json(completed.stdout or "")
    return {
        "attempted": True,
        "state": (
            result.get("state")
            if isinstance(result, dict) and isinstance(result.get("state"), str)
            else ("COMPLETE" if completed.returncode == 0 else "INCOMPLETE")
        ),
        "returncode": completed.returncode,
        "control_root": str(control_root),
        "heartbeat_source_root_bound": child_env.get("STEGVERSE_HEARTBEAT_SOURCE_ROOT") == str(control_root),
        "llm_adapter_root_bound": child_env.get("STEGVERSE_LLM_ADAPTER_ROOT") == str(llm_root),
        "resident_source_manifest_bound": (
            child_env.get("STEGVERSE_RESIDENT_SOURCE_MANIFEST") == str(source_manifest)
            if source_manifest.is_file() else False
        ),
        "stegos_source_bound": stegos_bound,
        "kv_source_bound": kv_source_bound,
        "healer_source_bound": healer_bound,
        "tv_source_bound": tv_bound,
        "tvc_source_bound": tvc_bound,
        "micro_node_source_bound": micro_node_bound,
        "master_records_source_bound": master_records_bound,
        "stegindex_source_bound": stegindex_bound,
        "formal_source_bound": formal_bound,
        "repository_root_map_bound": True,
        "kv_root_bound": bool(child_env.get("STEGVERSE_KV_ROOT")),
        "result": result,
        "invoked_by": "StegVerse-Labs/.github:scripts/activate_resident_stack.py",
        "container_framework_required": False,
        "network_fetch_performed": False,
        "github_token_runtime_authority": "NONE",
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE_LOCAL_POST_START_BOOTSTRAP_TRIGGER",
    }


def activate(
    source_root: Path,
    llm_adapter_root: Path,
    *,
    stegos_root: Path,
    kv_source_root: Path,
    healer_root: Path,
    tv_root: Path,
    tvc_root: Path,
    master_records_root: Path,
    micro_node_root: Path,
    tt_root: Path,
    rtg_root: Path,
    gtg_root: Path,
    ae_root: Path,
    stegindex_root: Path,
    receipt_path: Path,
    gateway_host: str = "127.0.0.1",
    gateway_port: int = 8000,
    durable_root: Path | None = None,
    enable_evaluator_intr: bool = False,
    evaluator_upstream: str | None = None,
    tls_cert_file: Path | None = None,
    tls_key_file: Path | None = None,
    runner=subprocess.run,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    source = source_root.expanduser().resolve()
    llm = llm_adapter_root.expanduser().resolve()
    receipt_path = receipt_path.expanduser().resolve()
    packager = source / "scripts" / "package_sovereign_control_plane_bundle.py"
    native_gateway = llm / "scripts" / "stegdeploy_native_gateway.py"
    if not packager.is_file():
        raise RuntimeError("canonical control-plane packager missing")
    if not native_gateway.is_file():
        raise RuntimeError("StegDeploy native gateway launcher missing")
    if bool(tls_cert_file) != bool(tls_key_file):
        raise RuntimeError("tls_cert_key_pair_required")

    safe_env = clean_env(env)
    with tempfile.TemporaryDirectory(prefix="stegverse-resident-stack-") as tmp:
        bundle = Path(tmp) / "sovereign-control-plane.zip"
        package = runner(
            [
                sys.executable, str(packager),
                "--source-root", str(source),
                "--output", str(bundle),
                "--stegos-root", str(stegos_root.expanduser().resolve()),
                "--kv-source-root", str(kv_source_root.expanduser().resolve()),
                "--healer-root", str(healer_root.expanduser().resolve()),
                "--tv-root", str(tv_root.expanduser().resolve()),
                "--tvc-root", str(tvc_root.expanduser().resolve()),
                "--master-records-root", str(master_records_root.expanduser().resolve()),
                "--micro-node-root", str(micro_node_root.expanduser().resolve()),
                "--tt-root", str(tt_root.expanduser().resolve()),
                "--rtg-root", str(rtg_root.expanduser().resolve()),
                "--gtg-root", str(gtg_root.expanduser().resolve()),
                "--ae-root", str(ae_root.expanduser().resolve()),
                "--stegindex-root", str(stegindex_root.expanduser().resolve()),
            ],
            cwd=source,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
            env=safe_env,
        )
        package_result = parse_last_json(package.stdout) or {}
        if package.returncode != 0 or not bundle.is_file():
            raise RuntimeError("control-plane bundle packaging failed")

        start_command = [
            sys.executable, str(native_gateway),
            "start",
            "--host", gateway_host,
            "--port", str(gateway_port),
        ]
        if durable_root is not None:
            start_command += ["--durable-root", str(durable_root.expanduser().resolve())]
        if enable_evaluator_intr:
            start_command.append("--enable-evaluator-intr")
        if evaluator_upstream:
            start_command += ["--evaluator-upstream", evaluator_upstream]
        if tls_cert_file and tls_key_file:
            start_command += [
                "--tls-cert-file", str(tls_cert_file.expanduser().resolve()),
                "--tls-key-file", str(tls_key_file.expanduser().resolve()),
            ]
        start = runner(
            start_command,
            cwd=llm,
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
            env=safe_env,
        )
        # The start transition closes on the spawned process; health is never
        # awaited. An already-running native gateway is the same closed state.
        gateway_already_running = start.returncode != 0 and NATIVE_GATEWAY_ALREADY_RUNNING in (start.stderr or "")
        gateway_receipt_path = native_gateway_receipt_path(safe_env)
        gateway = parse_json_document(start.stdout or "") if start.returncode == 0 else None
        gateway = gateway or load_json(gateway_receipt_path) or {}
        gateway_started = (
            (start.returncode == 0 or gateway_already_running)
            and gateway.get("schema") == NATIVE_GATEWAY_RECEIPT_SCHEMA
            and gateway.get("state") == NATIVE_GATEWAY_STARTED
        )

        if gateway_started:
            resident = activate_resident_control_plane(bundle, llm, env=safe_env, runner=runner)
        else:
            resident = {
                "attempted": False,
                "state": "NATIVE_GATEWAY_NOT_STARTED",
                "failure_code": "NATIVE_GATEWAY_START_NOT_RECEIPTED",
                "failed_predicate": (
                    "stegdeploy_native_gateway.py start receipt "
                    f"{NATIVE_GATEWAY_RECEIPT_SCHEMA} state {NATIVE_GATEWAY_STARTED}"
                ),
                "required_evidence_or_repair": (
                    "a native gateway start receipt at " + str(gateway_receipt_path)
                    + "; start stderr: " + (start.stderr or "").strip()[-500:]
                ),
                "retry_entrypoint": "python scripts/activate_resident_stack.py",
                "owning_existing_goal": "StegVerse-org/LLM-adapter#368",
                "next_attempt": "re-run this activation after the start failure is repaired",
                "authority_effect": "NONE",
                "network_fetch_performed": False,
                "github_token_runtime_authority": "NONE",
                "credential_authority": "TV/TVC",
            }
        resident_result = resident.get("result") if isinstance(resident.get("result"), dict) else {}
        skap = resident_result.get("post_bootstrap_tvc_skap_successor") if isinstance(resident_result, dict) else None
        skap = skap if isinstance(skap, dict) else {}

        prime = resident_result.get("post_install_worker_prime") if isinstance(resident_result, dict) else None
        prime = prime if isinstance(prime, dict) else {}
        dispatch = resident_result.get("post_bootstrap_resident_request_dispatch") if isinstance(resident_result, dict) else None
        dispatch = dispatch if isinstance(dispatch, dict) else {}
        resident_task_capable = prime.get("task_capable_cycle_observed") is True
        resident_dispatch_attempted = dispatch.get("attempted") is True

        state = "COMPLETE" if (
            gateway_started
            and resident.get("attempted") is True
            and resident_task_capable
            and resident_dispatch_attempted
        ) else "INCOMPLETE"

        receipt = {
            "schema": "stegverse.resident-stack-activation/v1",
            "state": state,
            "source_root": str(source),
            "llm_adapter_root": str(llm),
            "gateway_runtime": "HOST_NATIVE_PYTHON_UVICORN",
            "container_framework_required": False,
            "control_bundle_packaged": True,
            "stegos_source_bundled": True,
            "kv_source_bundled": True,
            "healer_source_bundled": True,
            "tv_source_bundled": True,
            "tvc_source_bundled": True,
            "master_records_source_bundled": True,
            "micro_node_source_bundled": True,
            "stegindex_source_bundled": True,
            "formal_sources_bundled": {
                "TT": True,
                "RTG": True,
                "GTG": True,
                "AE": True,
            },
            "sv002_principal_execution_claimed": False,
            "formal_evaluation_claimed": False,
            "control_bundle_sha256": package_result.get("bundle_sha256"),
            "healer_source_proof": (
                package_result.get("vendor_source_proofs", {}).get("StegVerse-Healer")
                if isinstance(package_result.get("vendor_source_proofs"), dict)
                else None
            ),
            "native_gateway_start_returncode": start.returncode,
            "native_gateway_already_running": gateway_already_running,
            "native_gateway_started": gateway_started,
            "native_gateway_receipt_ref": str(gateway_receipt_path),
            "native_gateway_receipt_observed": bool(gateway),
            "native_gateway_health": gateway.get("health"),
            "native_gateway_health_reconciliation_entrypoint": "python scripts/stegdeploy_native_gateway.py status",
            "destination_liveness_is_transition_predicate": False,
            "resident_bootstrap": resident,
            "resident_task_capable_cycle_observed": resident_task_capable,
            "resident_request_dispatch_attempted": resident_dispatch_attempted,
            "g18_housekeeping_state": resident.get("state"),
            "g18_required_for_stack_completion": False,
            "tvc_skap_successor_attempted": skap.get("attempted") is True,
            "tvc_skap_successor_state": skap.get("state"),
            "network_source_fetch_performed_by_orchestrator": False,
            "github_token_runtime_authority": "NONE",
            "credential_authority": "TV/TVC",
            "heartbeat_grants_execution_authority": False,
            "orchestrator_grants_authority": False,
            "third_party_primary_runtime": False,
            "authority_effect": "NONE_LOCAL_STACK_ORCHESTRATION_ONLY",
        }
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--llm-adapter-root", type=Path, default=None)
    parser.add_argument("--gateway-host", default="127.0.0.1")
    parser.add_argument("--gateway-port", type=int, default=8000)
    parser.add_argument("--durable-root", type=Path, default=None)
    parser.add_argument("--enable-evaluator-intr", action="store_true")
    parser.add_argument("--evaluator-upstream", default=None)
    parser.add_argument("--tls-cert-file", type=Path, default=None)
    parser.add_argument("--tls-key-file", type=Path, default=None)
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
    parser.add_argument("--stegindex-root", type=Path)
    parser.add_argument("--receipt-path", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()
    llm = args.llm_adapter_root
    if llm is None:
        configured = str(os.environ.get("STEGVERSE_LLM_ADAPTER_ROOT") or "").strip()
        if not configured:
            raise SystemExit("--llm-adapter-root or STEGVERSE_LLM_ADAPTER_ROOT is required")
        llm = Path(configured)
    stegos = args.stegos_root or (Path(os.environ["STEGVERSE_STEGOS_ROOT"]) if os.environ.get("STEGVERSE_STEGOS_ROOT") else None)
    kv_source = args.kv_source_root or (Path(os.environ["STEGVERSE_KV_SOURCE_ROOT"]) if os.environ.get("STEGVERSE_KV_SOURCE_ROOT") else None)
    healer = args.healer_root or (Path(os.environ["STEGVERSE_HEALER_ROOT"]) if os.environ.get("STEGVERSE_HEALER_ROOT") else None)
    tv = args.tv_root or (Path(os.environ["STEGVERSE_TV_ROOT"]) if os.environ.get("STEGVERSE_TV_ROOT") else None)
    tvc = args.tvc_root or (Path(os.environ["STEGVERSE_TVC_ROOT"]) if os.environ.get("STEGVERSE_TVC_ROOT") else None)
    master_records = args.master_records_root or (Path(os.environ["STEGVERSE_MASTER_RECORDS_ROOT"]) if os.environ.get("STEGVERSE_MASTER_RECORDS_ROOT") else None)
    if master_records is None and os.environ.get("STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"):
        master_records = Path(os.environ["STEGVERSE_MASTER_RECORDS_ORCHESTRATION_ROOT"])
    micro_node = args.micro_node_root or (Path(os.environ["STEGVERSE_MICRO_NODE_RUNTIME_ROOT"]) if os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT") else None)
    tt = args.tt_root or (Path(os.environ["STEGVERSE_TT_ROOT"]) if os.environ.get("STEGVERSE_TT_ROOT") else None)
    rtg = args.rtg_root or (Path(os.environ["STEGVERSE_RTG_ROOT"]) if os.environ.get("STEGVERSE_RTG_ROOT") else None)
    gtg = args.gtg_root or (Path(os.environ["STEGVERSE_GTG_ROOT"]) if os.environ.get("STEGVERSE_GTG_ROOT") else None)
    ae = args.ae_root or (Path(os.environ["STEGVERSE_AE_ROOT"]) if os.environ.get("STEGVERSE_AE_ROOT") else None)
    stegindex = args.stegindex_root or (Path(os.environ["STEGVERSE_STEGINDEX_SOURCE_ROOT"]) if os.environ.get("STEGVERSE_STEGINDEX_SOURCE_ROOT") else None)
    if stegindex is None:
        roots_raw = str(os.environ.get("STEGVERSE_REPO_ROOTS_JSON") or "").strip()
        if roots_raw:
            try:
                roots = json.loads(roots_raw)
            except Exception:
                roots = {}
            if isinstance(roots, dict):
                candidate = roots.get("StegVerse-Labs/StegIndex") or roots.get("StegIndex")
                if isinstance(candidate, str) and candidate.strip():
                    stegindex = Path(candidate)
    if (
        stegos is None or kv_source is None or healer is None or tv is None or tvc is None
        or master_records is None or micro_node is None
        or tt is None or rtg is None or gtg is None or ae is None or stegindex is None
    ):
        raise SystemExit(
            "StegOS, KV source, Healer, TV, TVC, Master Records, micro-node-runtime, "
            "pinned TT/RTG/GTG/AE, and StegIndex local roots are required for the complete resident stack"
        )
    receipt = activate(
        args.source_root,
        llm,
        stegos_root=stegos,
        kv_source_root=kv_source,
        healer_root=healer,
        tv_root=tv,
        tvc_root=tvc,
        master_records_root=master_records,
        micro_node_root=micro_node,
        tt_root=tt,
        rtg_root=rtg,
        gtg_root=gtg,
        ae_root=ae,
        stegindex_root=stegindex,
        receipt_path=args.receipt_path,
        gateway_host=args.gateway_host,
        gateway_port=args.gateway_port,
        durable_root=args.durable_root,
        enable_evaluator_intr=args.enable_evaluator_intr,
        evaluator_upstream=args.evaluator_upstream,
        tls_cert_file=args.tls_cert_file,
        tls_key_file=args.tls_key_file,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["state"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
