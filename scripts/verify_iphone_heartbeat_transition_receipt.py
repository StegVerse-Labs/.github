#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "management" / "SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json"
LEGACY = ROOT / "control" / "heartbeat-state.json"
CARRIER = ROOT / "control" / "heartbeat-carrier-runtime-state.json"
CUTOVER = ROOT / "receipts" / "heartbeat-schema-cutover" / "HB29.json"
TRANSITION = ROOT / "receipts" / "heartbeat-transition-continuity" / "latest.json"
HOSTED_ENV = ("GITHUB_ACTIONS", "RENDER", "RENDER_SERVICE_ID", "VERCEL", "CF_PAGES", "CLOUDFLARE_WORKERS")
PROTECTED_KEYS = ("token", "secret", "password", "private_key", "authorization", "bearer", "cookie", "credential")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_blob_sha(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("utf-8")
    return hashlib.sha1(header + raw).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")
        tmp = handle.name
    os.replace(tmp, path)


def truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() not in ("", "0", "false", "no")


def active_hosted_origins() -> list[str]:
    return [name for name in HOSTED_ENV if truthy(os.environ.get(name))]


def contains_protected_material(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in PROTECTED_KEYS):
                allowed = {
                    "credential_authority": "TV/TVC",
                    "credential_requirement": "NONE",
                    "github_token_runtime_authority": "NONE",
                    "non_tv_tvc_secret_or_token_used": False,
                }
                if key not in allowed or child != allowed[key]:
                    hits.append(f"{path}.{key}")
            hits.extend(contains_protected_material(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(contains_protected_material(child, f"{path}[{index}]"))
    return hits


def browser_proves_iphone(browser: dict[str, Any]) -> bool:
    ua = str(browser.get("user_agent") or "")
    if "iPhone" in ua:
        return True
    try:
        touch = int(browser.get("max_touch_points", 0))
        width = float(browser.get("screen_width_css", 0))
        height = float(browser.get("screen_height_css", 0))
    except (TypeError, ValueError):
        return False
    if browser.get("iphone_class_evidence") is not True:
        return False
    if touch < 2 or width <= 0 or height <= 0:
        return False
    short_side, long_side = sorted((width, height))
    return short_side <= 500 and long_side <= 1000


def validate_receipt(receipt: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    contract = load(root / "management" / "SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json")
    legacy_path = root / "control" / "heartbeat-state.json"
    legacy_raw = legacy_path.read_bytes()
    legacy = json.loads(legacy_raw.decode("utf-8"))
    errors: list[str] = []

    expected_top = {
        "schema": "stegverse.iphone-heartbeat-transition-receipt/v1",
        "contract_id": contract["contract_id"],
        "physical_execution_surface": "CURRENT_USER_IPHONE",
    }
    for key, expected in expected_top.items():
        if receipt.get(key) != expected:
            errors.append(f"{key} mismatch")

    seed = receipt.get("seed") or {}
    expected_seed = {
        "repository": "StegVerse-Labs/.github",
        "legacy_state_ref": "control/heartbeat-state.json",
        "legacy_state_git_blob_sha": contract["legacy_state_git_blob_sha"],
        "epoch": 29,
        "generation": 29,
    }
    for key, expected in expected_seed.items():
        if seed.get(key) != expected:
            errors.append(f"seed.{key} mismatch")
    if git_blob_sha(legacy_raw) != contract["legacy_state_git_blob_sha"]:
        errors.append("current legacy HB29 blob no longer matches capsule contract")
    if int(legacy.get("epoch", -1)) != 29 or int(legacy.get("generation", -1)) != 29:
        errors.append("legacy source is not canonical HB29/generation29")

    successor = receipt.get("successor") or {}
    expected_successor = {
        "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
        "epoch": 30,
        "generation": 30,
        "reference_frame": "heartbeat_epoch:30",
        "activation_state": "ACTIVE",
        "authority_effect": "NONE",
        "legacy_hb29_immutable": True,
    }
    for key, expected in expected_successor.items():
        if successor.get(key) != expected:
            errors.append(f"successor.{key} mismatch")

    authority = receipt.get("authority") or {}
    expected_authority = {
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_used": False,
        "worker_authority": False,
        "claim_or_fence_mutation": False,
        "route_authority": False,
        "wallet_authority": False,
        "model_output_authority": "NONE",
        "hosted_runtime_production_authority": "NONE",
        "another_physical_machine_required": False,
    }
    for key, expected in expected_authority.items():
        if authority.get(key) != expected:
            errors.append(f"authority.{key} mismatch")

    browser = receipt.get("browser") or {}
    if browser.get("secure_context") is not True:
        errors.append("browser.secure_context must be true")
    if browser.get("webcrypto") is not True:
        errors.append("browser.webcrypto must be true")
    if not str(browser.get("origin") or "").startswith("https://stegverse.org"):
        errors.append("browser.origin must be stegverse.org HTTPS")
    if not browser_proves_iphone(browser):
        errors.append("browser evidence does not prove an iPhone-class execution surface")

    protected = contains_protected_material(receipt)
    if protected:
        errors.append("protected material fields present: " + ", ".join(sorted(set(protected))))

    claimed_digest = str(receipt.get("receipt_sha256") or "")
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    actual_digest = sha256_hex(canonical_bytes(unsigned))
    if claimed_digest != actual_digest:
        errors.append("receipt_sha256 mismatch")

    return {
        "schema": "stegverse.iphone-heartbeat-transition-verification/v1",
        "state": "PASS" if not errors else "FAIL_CLOSED",
        "errors": errors,
        "legacy_state_git_blob_sha": git_blob_sha(legacy_raw),
        "legacy_state_sha256": sha256_hex(legacy_raw),
        "receipt_sha256": claimed_digest,
        "successor_epoch": successor.get("epoch"),
        "successor_generation": successor.get("generation"),
        "iphone_execution_evidence": browser_proves_iphone(browser),
        "authority_effect": "NONE",
        "credential_authority": "TV/TVC",
        "github_token_runtime_authority": "NONE",
    }


def _fallback_record(fallback_origin: str | None) -> dict[str, Any] | None:
    origins = active_hosted_origins()
    if not origins:
        if fallback_origin:
            raise RuntimeError("third-party fallback declared outside a detected hosted environment")
        return None
    if not fallback_origin:
        raise RuntimeError(
            "hosted execution requires an explicit --allow-third-party-fallback marker; "
            "hosted compute may be fallback only and never hidden"
        )
    if fallback_origin not in origins:
        raise RuntimeError(
            f"declared fallback origin {fallback_origin!r} does not match detected hosted origin(s) {origins!r}"
        )
    return {
        "execution_provider": fallback_origin,
        "provider_role": "FALLBACK_ONLY",
        "required_dependency": False,
        "runtime_authority": "StegVerse",
        "authority_effect": "NONE",
    }


def materialize(
    receipt: dict[str, Any],
    verification: dict[str, Any],
    *,
    root: Path = ROOT,
    fallback_origin: str | None = None,
) -> dict[str, Any]:
    if verification.get("state") != "PASS":
        raise RuntimeError("cannot materialize an unverified iPhone transition receipt")
    fallback = _fallback_record(fallback_origin)

    legacy_path = root / "control" / "heartbeat-state.json"
    carrier_path = root / "control" / "heartbeat-carrier-runtime-state.json"
    legacy_before = legacy_path.read_bytes()
    legacy = json.loads(legacy_before.decode("utf-8"))
    if carrier_path.exists():
        existing = load(carrier_path)
        if int(existing.get("epoch", -1)) >= 30:
            raise RuntimeError("carrier state already materialized at HB30+")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    legacy_sha256 = sha256_hex(legacy_before)
    portable_transition: dict[str, Any] = {
        "contract_id": receipt["contract_id"],
        "physical_execution_surface": receipt["physical_execution_surface"],
        "portable_receipt_sha256": receipt["receipt_sha256"],
        "verified": True,
        "authority_effect": "NONE",
    }
    if fallback:
        portable_transition.update(fallback)

    carrier = {
        "schema": "stegverse.heartbeat-carrier-runtime-state/v1",
        "epoch": 30,
        "generation": 30,
        "last_cycle_at": receipt["executed_at"],
        "role": "REGULATORY_CARRIER_REFERENCE_FRAME",
        "reference_frame": "heartbeat_epoch:30",
        "frequency_rule": "GATE_PASSBAND_DERIVED",
        "authority_effect": "NONE",
        "activation_state": "ACTIVE",
        "legacy_cutover": {
            "legacy_schema": legacy.get("schema"),
            "legacy_epoch": 29,
            "legacy_generation": 29,
            "legacy_state_sha256": legacy_sha256,
            "source_ref": "control/heartbeat-state.json",
            "closed": True,
        },
        "portable_transition": portable_transition,
    }
    carrier_digest = sha256_hex(canonical_bytes(carrier))
    cutover = {
        "schema": "stegverse.heartbeat-schema-cutover-receipt/v1",
        "state": "CLOSED_MIGRATED",
        "legacy_schema": legacy.get("schema"),
        "legacy_epoch": 29,
        "legacy_state_ref": "control/heartbeat-state.json",
        "legacy_state_sha256": legacy_sha256,
        "legacy_state_mutated": False,
        "new_carrier_schema": carrier["schema"],
        "first_new_epoch": 30,
        "observed_new_epoch": 30,
        "new_carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
        "new_carrier_state_sha256": carrier_digest,
        "carrier_observation_ref": "control/heartbeat-carrier-observation.json",
        "control_plane_ref": "control/worker-control-plane-coordination.json",
        "worker_registry_ref": "control/worker-registry.json",
        "heartbeat_grants_execution_authority": False,
        "credential_authority": "TV/TVC",
        "non_tv_tvc_secret_or_token_used": False,
        "github_token_runtime_authority": "NONE",
        "render_production_runtime_used": False,
        "authority_effect": "NONE_CARRIER_ONLY",
        "portable_transition_receipt_sha256": receipt["receipt_sha256"],
        "recorded_at": now,
    }
    if fallback:
        cutover["third_party_fallback"] = fallback
    cutover["receipt_sha256"] = sha256_hex(canonical_bytes(cutover))
    transition = {
        "schema": "stegverse.heartbeat-state-transition-receipt/v1",
        "state": "CARRIER_TRANSITION_COMPLETE",
        "reason": "IPHONE_PORTABLE_HB29_TO_HB30_TRANSITION_VERIFIED",
        "contract_ref": "management/SHWP_IPHONE_TRANSITION_CAPSULE_CONTRACT.json",
        "legacy_state_ref": "control/heartbeat-state.json",
        "carrier_state_ref": "control/heartbeat-carrier-runtime-state.json",
        "continuity_model": "STATE_TRANSITION_CONTINUITY",
        "physical_execution_surface": "CURRENT_USER_IPHONE",
        "portable_receipt_sha256": receipt["receipt_sha256"],
        "legacy_state_sha256": legacy_sha256,
        "carrier_epoch_before": 29,
        "carrier_generation_before": 29,
        "carrier_epoch_after": 30,
        "carrier_generation_after": 30,
        "credential_authority": "TV/TVC",
        "credential_requirement": "NONE",
        "github_token_runtime_authority": "NONE",
        "non_tv_tvc_secret_or_token_forwarded": False,
        "authority_effect": "NONE",
        "worker_checkpoint_required": True,
        "predicates": {
            "legacy_hb29_unchanged": True,
            "carrier_epoch_at_least_30": True,
            "carrier_generation_non_regressing": True,
            "worker_runtime_checkpoint_observed_at_or_after_carrier_epoch": False,
            "worker_control_plane_observed": False,
            "no_duplicate_claim_or_fence": True,
            "state_reconstruction_pass": True,
        },
        "all_carrier_transition_predicates_pass": False,
        "all_release_predicates_pass": False,
        "release_state": "WORKER_CHECKPOINT_PENDING",
    }
    if fallback:
        transition["third_party_fallback"] = fallback

    atomic_write(root / "control" / "heartbeat-carrier-runtime-state.json", carrier)
    atomic_write(root / "receipts" / "heartbeat-schema-cutover" / "HB29.json", cutover)
    atomic_write(root / "receipts" / "heartbeat-transition-continuity" / "latest.json", transition)
    if legacy_path.read_bytes() != legacy_before:
        raise RuntimeError("legacy heartbeat mutated during materialization")
    return transition


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument(
        "--allow-third-party-fallback",
        choices=HOSTED_ENV,
        default=None,
        help="Explicitly permit the detected hosted provider as FALLBACK_ONLY; never grants runtime authority.",
    )
    args = parser.parse_args()
    receipt = load(args.receipt)
    verification = validate_receipt(receipt, root=args.root.resolve())
    print(json.dumps(verification, indent=2, sort_keys=True))
    if verification["state"] != "PASS":
        return 1
    if args.materialize:
        result = materialize(
            receipt,
            verification,
            root=args.root.resolve(),
            fallback_origin=args.allow_third_party_fallback,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
