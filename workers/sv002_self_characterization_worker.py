#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from typing import Any, Callable

ROOT = Path.cwd().resolve()
TASK_ID = "SHWP-SV002-SELF-CHARACTERIZATION-001"
CHECKPOINT = f"receipts/sv002-self-characterization/{TASK_ID}.json"
PINS = {
    "TT": "ab60b42934222a2cb5335a5a8194f258a491fc57",
    "RTG": "ca69954cb3dc4ad073c9244e003bc8f0ef3837e2",
    "GTG": "8cdb7bce87bb9f8429c35e9c66cc5dc28a46a225",
    "AE": "53c8eedddc4e54d8fa0660039d65ab9ac63057a1",
}
LOOPBACK_PREFIXES = (
    "http://127.0.0.1:",
    "http://localhost:",
    "https://127.0.0.1:",
    "https://localhost:",
)
MASTER_RECORDS_RECONSTRUCTION_OUTPUT = (
    "STEGVERSE_002_SELF_CHARACTERIZATION_RECONSTRUCTION_RECEIPT.json"
)
MASTER_RECORDS_RECONSTRUCTION_COMMIT = "2e117902d4f261b10cb3b5122b7ef48fb0e36e57"
MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB = "cc96556a23b5bd804f3cdaa96539b379c1904437"


def git_head(p: Path) -> str:
    return subprocess.check_output(["git", "-C", str(p), "rev-parse", "HEAD"], text=True).strip()


def git_commit_exists(p: Path, commit: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(p), "cat-file", "-e", f"{commit}^{commit}"],
            capture_output=True,
            text=True,
            check=False,
        ).returncode
        == 0
    )


def candidates(org: str, repo: str, override: str | None = None):
    out = []
    if override:
        out.append(Path(override).expanduser())
    home = Path(os.environ.get("HOME", str(Path.home())))
    out += [
        home / ".stegverse/repos" / org / repo,
        Path("/var/lib/stegverse/source") / org / repo,
        Path("/srv/stegverse/repos") / org / repo,
        Path("/opt/stegverse/repos") / org / repo,
    ]
    return [p.resolve() for p in out]


def find_repo(org, repo, expected=None, override=None, required=()):
    seen = []
    for p in candidates(org, repo, override):
        rec = {"path": str(p), "present": p.is_dir()}
        if p.is_dir() and all((p / x).is_file() for x in required) and (p / ".git").exists():
            try:
                h = git_head(p)
            except Exception:
                h = None
            rec["head"] = h
            commit_ok = True if expected is None else git_commit_exists(p, expected)
            if expected is not None:
                rec["pinned_commit_available"] = commit_ok
            if commit_ok:
                rec["selected"] = True
                seen.append(rec)
                return p, seen
        seen.append(rec)
    return None, seen


def git_blob_sha(root: Path, path: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), "hash-object", str(path)],
        text=True,
    ).strip()


def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_sha256(value: str) -> str:
    value = str(value or "").strip().lower()
    if value.startswith("sha256:"):
        value = value[7:]
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise RuntimeError("subject identity digest is not SHA-256")
    return value


def loopback_endpoint(endpoint: str) -> bool:
    return endpoint.rstrip("/").startswith(LOOPBACK_PREFIXES)


def _json_url(url: str, *, urlopen: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    with urlopen(url, timeout=3) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError("local model endpoint returned non-object JSON")
    return value


def discover_ollama_model(
    endpoint: str,
    requested_model: str | None,
    *,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[str | None, dict[str, Any] | None]:
    if not loopback_endpoint(endpoint):
        return None, None
    try:
        tags = _json_url(endpoint.rstrip("/") + "/api/tags", urlopen=urlopen)
    except Exception:
        return None, None
    rows = [row for row in tags.get("models", []) if isinstance(row, dict)]
    if requested_model:
        names = {requested_model}
        if ":" not in requested_model:
            names.add(requested_model + ":latest")
        for row in rows:
            if row.get("name") in names or row.get("model") in names:
                return requested_model, row
        return None, None

    non_reference = []
    for row in rows:
        name = str(row.get("name") or row.get("model") or "").strip()
        if not name or "reference" in name.lower() or name == "stegverse-reference-lm-v1":
            continue
        non_reference.append((name, row))
    if len(non_reference) != 1:
        return None, None
    return non_reference[0]


def find_ollama_process(proc_root: Path = Path("/proc")) -> tuple[int, Path] | None:
    if not proc_root.is_dir():
        return None
    found: list[tuple[int, Path]] = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            pid = int(entry.name)
            exe = (entry / "exe").resolve(strict=True)
            cmdline = (entry / "cmdline").read_bytes().replace(b"\x00", b" ").decode("utf-8", "replace").lower()
        except Exception:
            continue
        executable_name = exe.name.lower()
        if "ollama" not in executable_name and "ollama" not in cmdline:
            continue
        if "serve" not in cmdline and "ollama" not in executable_name:
            continue
        found.append((pid, exe))
    if len(found) != 1:
        return None
    return found[0]


def _process_argv(entry: Path) -> list[str]:
    try:
        raw = (entry / "cmdline").read_bytes()
    except Exception:
        return []
    return [
        part.decode("utf-8", "replace")
        for part in raw.split(b"\x00")
        if part
    ]


def _arg_value(argv: list[str], *names: str) -> str | None:
    for index, value in enumerate(argv):
        for name in names:
            if value == name and index + 1 < len(argv):
                return argv[index + 1]
            prefix = name + "="
            if value.startswith(prefix):
                return value[len(prefix):]
    return None


def _endpoint_port(endpoint: str) -> int:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise RuntimeError("principal model endpoint must be loopback/private")
    if parsed.port is not None:
        return parsed.port
    return 443 if parsed.scheme == "https" else 80


def find_llamacpp_process_candidates(
    *,
    proc_root: Path = Path("/proc"),
) -> list[dict[str, Any]]:
    if not proc_root.is_dir():
        return []
    found: list[dict[str, Any]] = []
    for entry in proc_root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            pid = int(entry.name)
            exe = (entry / "exe").resolve(strict=True)
        except Exception:
            continue
        argv = _process_argv(entry)
        if not argv:
            continue
        identity_text = " ".join([str(exe), *argv]).lower()
        if "llama-server" not in identity_text and "llama_server" not in identity_text:
            continue
        port_raw = _arg_value(argv, "--port", "-p")
        try:
            port = int(port_raw) if port_raw else 8080
        except Exception:
            continue
        if port < 1 or port > 65535:
            continue
        model_raw = _arg_value(argv, "--model", "-m")
        if not model_raw:
            continue
        model_path = Path(model_raw).expanduser()
        if not model_path.is_absolute():
            try:
                cwd = (entry / "cwd").resolve(strict=True)
                model_path = (cwd / model_path).resolve()
            except Exception:
                continue
        else:
            model_path = model_path.resolve()
        if not model_path.is_file():
            continue
        alias = _arg_value(argv, "--alias", "--model-alias")
        found.append(
            {
                "pid": pid,
                "executable": exe,
                "model_path": model_path,
                "alias": alias,
                "port": port,
                "argv": argv,
            }
        )
    return found


def find_llamacpp_process(
    endpoint: str,
    *,
    proc_root: Path = Path("/proc"),
) -> dict[str, Any] | None:
    if not loopback_endpoint(endpoint):
        return None
    target_port = _endpoint_port(endpoint)
    found = [
        row
        for row in find_llamacpp_process_candidates(proc_root=proc_root)
        if row.get("port") == target_port
    ]
    if len(found) != 1:
        return None
    return found[0]


def discover_llamacpp_model(
    endpoint: str,
    requested_model: str | None,
    *,
    proc_root: Path = Path("/proc"),
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[str | None, dict[str, Any] | None]:
    process = find_llamacpp_process(endpoint, proc_root=proc_root)
    if process is None:
        return None, None
    model_path = Path(process["model_path"])
    candidates = {
        value
        for value in (
            process.get("alias"),
            model_path.name,
            model_path.stem,
        )
        if isinstance(value, str) and value.strip()
    }
    model_id = requested_model.strip() if requested_model else None
    observed_ids: set[str] = set()
    try:
        models = _json_url(endpoint.rstrip("/") + "/v1/models", urlopen=urlopen)
        for row in models.get("data", []):
            if isinstance(row, dict):
                value = str(row.get("id") or "").strip()
                if value:
                    observed_ids.add(value)
        candidates.update(observed_ids)
    except Exception:
        pass
    if model_id:
        if model_id not in candidates:
            return None, None
    else:
        preferred = str(process.get("alias") or "").strip()
        if preferred:
            model_id = preferred
        elif len(observed_ids) == 1:
            model_id = next(iter(observed_ids))
        else:
            model_id = model_path.stem
    if not model_id or "reference" in model_id.lower() or model_id == "stegverse-reference-lm-v1":
        return None, None
    return model_id, process


def build_llamacpp_subject_identity(
    endpoint: str,
    model: str,
    *,
    proc_root: Path = Path("/proc"),
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    endpoint = endpoint.rstrip("/")
    if not loopback_endpoint(endpoint):
        raise RuntimeError("principal model endpoint must be loopback/private")
    if model == "stegverse-reference-lm-v1" or "reference" in model.lower():
        raise RuntimeError("reference model is not a qualifying principal subject model")

    discovered, process = discover_llamacpp_model(
        endpoint,
        model,
        proc_root=proc_root,
        urlopen=urlopen,
    )
    if discovered != model or not isinstance(process, dict):
        raise RuntimeError("llama.cpp model/process identity not independently observed")
    executable = Path(process["executable"]).resolve()
    model_path = Path(process["model_path"]).resolve()
    return {
        "schema": "stegverse.self-characterization-runtime-identity/v0.1",
        "model_id": model,
        "endpoint": endpoint,
        "model_digest": file_digest(model_path),
        "runtime_digest": file_digest(executable),
        "runtime_executable": str(executable),
        "process_id": int(process["pid"]),
        "runtime_engine": "llama.cpp",
        "model_artifact_path": str(model_path),
        "identity_source": "LOCAL_LLAMACPP_PROCESS_PLUS_EXACT_GGUF",
        "network_fetch_performed": False,
        "credential_required": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    }


def build_ollama_subject_identity(
    endpoint: str,
    model: str,
    *,
    proc_root: Path = Path("/proc"),
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> dict[str, Any]:
    endpoint = endpoint.rstrip("/")
    if not loopback_endpoint(endpoint):
        raise RuntimeError("principal model endpoint must be loopback/private")
    if model == "stegverse-reference-lm-v1" or "reference" in model.lower():
        raise RuntimeError("reference model is not a qualifying principal subject model")

    discovered, row = discover_ollama_model(endpoint, model, urlopen=urlopen)
    if discovered != model or not isinstance(row, dict):
        raise RuntimeError("Ollama model identity not independently observed")
    model_digest = normalize_sha256(str(row.get("digest") or ""))

    process = find_ollama_process(proc_root)
    if process is None:
        raise RuntimeError("unique local Ollama runtime process not independently observed")
    pid, executable = process
    runtime_digest = file_digest(executable)

    return {
        "schema": "stegverse.self-characterization-runtime-identity/v0.1",
        "model_id": model,
        "endpoint": endpoint,
        "model_digest": model_digest,
        "runtime_digest": runtime_digest,
        "runtime_executable": str(executable),
        "process_id": pid,
        "runtime_engine": "ollama",
        "model_artifact_path": None,
        "identity_source": "LOCAL_OLLAMA_API_PLUS_PROCESS_EXECUTABLE",
        "network_fetch_performed": False,
        "credential_required": False,
        "credential_authority": "TV/TVC",
        "authority_effect": "NONE",
    }


def discover_local_principal(
    endpoint: str | None,
    model: str | None,
    *,
    ollama_requested: str | None = None,
    proc_root: Path = Path("/proc"),
    urlopen: Callable[..., Any] = urllib.request.urlopen,
) -> tuple[str | None, str | None, str | None]:
    explicit_endpoint = str(endpoint or "").strip().rstrip("/")
    explicit_model = str(model or "").strip()
    requested_ollama = str(ollama_requested or "").strip()

    if explicit_endpoint:
        if explicit_model:
            return explicit_endpoint, explicit_model, "EXPLICIT_ENDPOINT_AND_MODEL"
        ollama_model, _ = discover_ollama_model(
            explicit_endpoint,
            requested_ollama or None,
            urlopen=urlopen,
        )
        if ollama_model:
            return explicit_endpoint, ollama_model, "EXPLICIT_ENDPOINT_LOCAL_OLLAMA_DISCOVERY"
        llama_model, _ = discover_llamacpp_model(
            explicit_endpoint,
            None,
            proc_root=proc_root,
            urlopen=urlopen,
        )
        if llama_model:
            return explicit_endpoint, llama_model, "EXPLICIT_ENDPOINT_LOCAL_LLAMACPP_DISCOVERY"
        return explicit_endpoint, None, "EXPLICIT_ENDPOINT_NO_UNIQUE_MODEL"

    ollama_endpoint = "http://127.0.0.1:11434"
    ollama_model, _ = discover_ollama_model(
        ollama_endpoint,
        requested_ollama or None,
        urlopen=urlopen,
    )
    if ollama_model:
        return ollama_endpoint, ollama_model, "CANONICAL_OLLAMA_LOOPBACK_DISCOVERY"

    llama_candidates = find_llamacpp_process_candidates(proc_root=proc_root)
    if len(llama_candidates) != 1:
        return None, None, (
            "NO_LOCAL_PRINCIPAL_OBSERVED"
            if not llama_candidates
            else "AMBIGUOUS_LOCAL_LLAMACPP_PRINCIPALS"
        )
    candidate = llama_candidates[0]
    llama_endpoint = f"http://127.0.0.1:{int(candidate['port'])}"
    llama_model, _ = discover_llamacpp_model(
        llama_endpoint,
        None,
        proc_root=proc_root,
        urlopen=urlopen,
    )
    if not llama_model:
        return None, None, "LLAMACPP_PROCESS_OBSERVED_MODEL_IDENTITY_UNRESOLVED"
    return llama_endpoint, llama_model, "UNIQUE_LOCAL_LLAMACPP_PROCESS_DISCOVERY"


def resolve_subject_identity(endpoint: str, model: str) -> tuple[dict[str, Any] | None, str | None]:
    explicit = os.environ.get("STEGVERSE_SELF_CHAR_SUBJECT_IDENTITY_JSON", "").strip()
    if explicit:
        try:
            value = json.loads(explicit)
        except Exception:
            return None, "EXPLICIT_SUBJECT_IDENTITY_JSON_INVALID"
        if not isinstance(value, dict):
            return None, "EXPLICIT_SUBJECT_IDENTITY_OBJECT_REQUIRED"
        if value.get("model_id") != model or str(value.get("endpoint") or "").rstrip("/") != endpoint.rstrip("/"):
            return None, "EXPLICIT_SUBJECT_IDENTITY_BINDING_MISMATCH"
        return value, None
    errors = []
    try:
        return build_ollama_subject_identity(endpoint, model), None
    except Exception as exc:
        errors.append("ollama=" + str(exc))
    try:
        return build_llamacpp_subject_identity(endpoint, model), None
    except Exception as exc:
        errors.append("llama.cpp=" + str(exc))
    return None, "SUBJECT_IDENTITY_NOT_INDEPENDENTLY_VERIFIED:" + ";".join(errors)


def attempt_master_records_reconstruction(state_root: Path) -> dict[str, Any]:
    master_records, candidates_seen = find_repo(
        "master-records",
        "orchestration",
        expected=MASTER_RECORDS_RECONSTRUCTION_COMMIT,
        override=os.environ.get("STEGVERSE_MASTER_RECORDS_ROOT"),
        required=("scripts/verify_sv002_self_characterization_reconstruction.py",),
    )
    if master_records is None:
        return {
            "state": "PENDING",
            "blocker": "MASTER_RECORDS_RECONSTRUCTION_VERIFIER_NOT_MATERIALIZED",
            "master_records_candidates": candidates_seen,
            "network_fetch_performed": False,
            "credential_required": False,
            "authority_effect": "NONE",
        }

    verifier_path = master_records / "scripts/verify_sv002_self_characterization_reconstruction.py"
    try:
        verifier_blob = git_blob_sha(master_records, verifier_path)
    except Exception:
        verifier_blob = None
    if verifier_blob != MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB:
        return {
            "state": "PENDING",
            "blocker": "MASTER_RECORDS_RECONSTRUCTION_VERIFIER_SOURCE_PIN_MISMATCH",
            "verifier_repository": str(master_records),
            "required_commit": MASTER_RECORDS_RECONSTRUCTION_COMMIT,
            "required_verifier_blob": MASTER_RECORDS_RECONSTRUCTION_VERIFIER_BLOB,
            "observed_verifier_blob": verifier_blob,
            "network_fetch_performed": False,
            "credential_required": False,
            "authority_effect": "NONE",
        }

    output = state_root / MASTER_RECORDS_RECONSTRUCTION_OUTPUT
    clean_env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", str(Path.home())),
    }
    proc = subprocess.run(
        [
            sys.executable,
            str(verifier_path),
            str(state_root),
            "--output",
            str(output),
        ],
        cwd=master_records,
        env=clean_env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    result = {}
    if output.is_file():
        try:
            result = json.loads(output.read_text())
        except Exception:
            result = {}
    passed = (
        proc.returncode == 0
        and result.get("status") == "PASS"
        and result.get("reconstruction") == "PASS"
        and result.get("experiment_id") == "STEGVERSE-002-SELF-CHARACTERIZATION-001"
    )
    return {
        "state": "PASS" if passed else "FAIL",
        "verifier_repository": str(master_records),
        "verifier_returncode": proc.returncode,
        "receipt_path": str(output) if output.is_file() else None,
        "receipt": result if result else None,
        "network_fetch_performed": False,
        "credential_required": False,
        "authority_effect": "NONE",
    }


def response(state, transition, epoch):
    return {
        "schema": "stegverse.worker-response/v0.1",
        "state": state,
        "transition_id": transition,
        "transition_sequence": 1,
        "expected_next_transition": None if state == "COMPLETED" else "SV002_SELF_CHARACTERIZATION_RECHECK",
        "expected_next_earliest_epoch": None if state == "COMPLETED" else epoch + 1,
        "expected_next_latest_epoch": None if state == "COMPLETED" else epoch + 1,
        "checkpoint_ref": CHECKPOINT,
        "evidence_refs": [CHECKPOINT],
        "cost_observation": {
            "hb_transition_count": 1,
            "compute_units": 2,
            "external_cost_usd": 0,
            "task_class": "sv002_self_characterization",
        },
    }


def main():
    inv = json.load(sys.stdin)
    epoch = inv.get("heartbeat_epoch")
    task = inv.get("task") or {}
    if inv.get("schema") != "stegverse.worker-invocation/v0.1" or task.get("task_id") != TASK_ID or not isinstance(epoch, int):
        return 2
    if any(
        str(os.environ.get(x, "")).lower() in {"1", "true", "yes"}
        for x in ("GITHUB_ACTIONS", "CI", "RENDER", "VERCEL", "CF_PAGES")
    ):
        return 3

    out = ROOT / CHECKPOINT
    out.parent.mkdir(parents=True, exist_ok=True)
    micro, micro_seen = find_repo(
        "StegVerse-002",
        "micro-node-runtime",
        override=os.environ.get("STEGVERSE_MICRO_NODE_RUNTIME_ROOT"),
        required=("tools/run_self_characterization_principal.py",),
    )
    formal = {}
    observed = {}
    for repo, sha in PINS.items():
        p, seen = find_repo("Admissible-Existence", repo, sha, os.environ.get(f"STEGVERSE_{repo}_ROOT"))
        observed[repo] = seen
        if p:
            formal[f"Admissible-Existence/{repo}"] = str(p)

    configured_endpoint = os.environ.get("STEGVERSE_SELF_CHAR_MODEL_ENDPOINT", "").strip().rstrip("/")
    configured_model = os.environ.get("STEGVERSE_SELF_CHAR_MODEL_ID", "").strip()
    ollama_requested = os.environ.get("STEGVERSE_OLLAMA_MODEL", "").strip()
    endpoint, model, principal_discovery = discover_local_principal(
        configured_endpoint or None,
        configured_model or None,
        ollama_requested=ollama_requested or None,
    )
    endpoint = endpoint or ""
    model = model or ""

    blockers = []
    if micro is None:
        blockers.append("MICRO_NODE_RUNTIME_NOT_MATERIALIZED")
    if len(formal) != 4:
        blockers.append("PINNED_FORMAL_COMMITS_NOT_LOCALLY_AVAILABLE")
    if not endpoint or not model:
        blockers.append("QUALIFYING_LOCAL_REASONING_ENDPOINT_NOT_OBSERVED")
    if model == "stegverse-reference-lm-v1" or "reference" in model.lower():
        blockers.append("REFERENCE_MODEL_NOT_QUALIFYING_PRINCIPAL")

    subject_identity = None
    subject_identity_error = None
    if endpoint and model and not blockers:
        subject_identity, subject_identity_error = resolve_subject_identity(endpoint, model)
        if subject_identity is None:
            blockers.append("QUALIFYING_SUBJECT_IDENTITY_NOT_OBSERVED")

    if blockers:
        receipt = {
            "schema": "stegverse.sv002-self-characterization-worker-receipt/v0.2",
            "task_id": TASK_ID,
            "state": "BLOCKED",
            "blockers": blockers,
            "micro_node_candidates": micro_seen,
            "formal_candidates": observed,
            "model_id": model or None,
            "endpoint": endpoint or None,
            "subject_identity_error": subject_identity_error,
            "principal_discovery": principal_discovery,
            "subject_identity_verified": False,
            "network_fetch_performed": False,
            "credential_authority": "TV/TVC",
            "github_token_required": False,
            "authority_effect_resolution": "NOT_APPLICABLE_NO_PRINCIPAL_TRANSITION",
            "authority_transfer_assumed": False,
        }
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(response("BLOCKED", "SV002_SELF_CHARACTERIZATION_BLOCKED", epoch), sort_keys=True))
        return 0

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", str(Path.home())),
        "STEGVERSE_FORMAL_ROOTS_JSON": json.dumps(formal),
        "STEGVERSE_SELF_CHAR_MODEL_ENDPOINT": endpoint,
        "STEGVERSE_SELF_CHAR_MODEL_ID": model,
        "STEGVERSE_SELF_CHAR_SUBJECT_IDENTITY_JSON": json.dumps(subject_identity, sort_keys=True),
        "STEGVERSE_SELF_CHAR_STATE_ROOT": str(
            Path(os.environ.get("HOME", str(Path.home()))) / ".stegverse/self-characterization-001"
        ),
    }
    proc = subprocess.run(
        [sys.executable, str(micro / "tools/run_self_characterization_principal.py")],
        cwd=micro,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    state_root = Path(env["STEGVERSE_SELF_CHAR_STATE_ROOT"])
    execution = state_root / "EXPERIMENT_EXECUTION_RECEIPT.json"
    result = json.loads(execution.read_text()) if execution.is_file() else {}
    completed = proc.returncode == 0 and result.get("state") == "COMPLETED"
    master_records_reconstruction = (
        attempt_master_records_reconstruction(state_root)
        if completed
        else {
            "state": "NOT_ATTEMPTED",
            "reason": "PRINCIPAL_EXECUTION_NOT_COMPLETED",
            "authority_effect": "NONE",
        }
    )
    receipt = {
        "schema": "stegverse.sv002-self-characterization-worker-receipt/v0.2",
        "task_id": TASK_ID,
        "state": "COMPLETED" if completed else "BLOCKED",
        "principal_returncode": proc.returncode,
        "principal_result": result,
        "model_id": model,
        "endpoint": endpoint,
        "subject_identity": subject_identity,
        "principal_discovery": principal_discovery,
        "subject_identity_verified": True,
        "formal_roots": formal,
        "state_root": str(state_root),
        "self_characterization_path": str(state_root / "SELF_CHARACTERIZATION.md") if completed else None,
        "formal_result_path": str(state_root / "SELF_CHARACTERIZATION_FORMAL.json") if completed else None,
        "interaction_receipt_chain_path": str(state_root / "INTERACTION_RECEIPT_CHAIN.json") if completed else None,
        "transition_effects_path": str(state_root / "TRANSITION_EFFECTS.json") if completed else None,
        "master_records_reconstruction": master_records_reconstruction,
        "network_fetch_performed": False,
        "credential_authority": "TV/TVC",
        "github_token_required": False,
        "authority_transfer_assumed": False,
        "authority_effect_resolution": result.get("authority_effect_resolution", "DERIVED_FROM_APPLICABLE_TRANSITION_ELEMENTS") if completed else "NOT_APPLICABLE_NO_PRINCIPAL_TRANSITION",
        "transition_effect_state": result.get("transition_effect_state", "PENDING_TRANSITION_ELEMENT_EVALUATION") if completed else "NOT_YET_EVALUATED",
    }
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            response(
                "COMPLETED" if completed else "BLOCKED",
                "SV002_SELF_CHARACTERIZATION_COMPLETED"
                if completed
                else "SV002_SELF_CHARACTERIZATION_EXECUTION_BLOCKED",
                epoch,
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
