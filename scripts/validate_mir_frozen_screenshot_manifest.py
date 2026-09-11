#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "stegverse.mir-frozen-screenshot-manifest/v1"


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def manifest_digest(manifest):
    return hashlib.sha256(canonical_bytes(manifest)).hexdigest()


def validate_shape(manifest):
    errors = []
    if manifest.get("schema") != SCHEMA:
        errors.append("SCREENSHOT_MANIFEST_SCHEMA_INVALID")
    for field in ("experiment_id", "evidence_epoch", "frozen_at", "frozen_by"):
        if not isinstance(manifest.get(field), str) or not manifest[field]:
            errors.append(f"SCREENSHOT_MANIFEST_FIELD_MISSING:{field}")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("SCREENSHOT_EVIDENCE_UNAVAILABLE")
        return errors

    purposes = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"SCREENSHOT_ENTRY_INVALID:{index}")
            continue
        purpose = entry.get("purpose_id")
        if not isinstance(purpose, str) or not purpose:
            errors.append(f"SCREENSHOT_PURPOSE_UNREGISTERED:{index}")
        elif purpose in purposes:
            errors.append(f"SCREENSHOT_PURPOSE_DUPLICATE:{purpose}")
        else:
            purposes.add(purpose)
        if not isinstance(entry.get("purpose_description"), str) or not entry.get("purpose_description"):
            errors.append(f"SCREENSHOT_PURPOSE_DESCRIPTION_MISSING:{index}")
        if not isinstance(entry.get("artifact_ref"), str) or not entry.get("artifact_ref"):
            errors.append(f"SCREENSHOT_EVIDENCE_UNAVAILABLE:{purpose or index}")
        digest = entry.get("artifact_sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            errors.append(f"SCREENSHOT_ARTIFACT_DIGEST_INVALID:{purpose or index}")
        else:
            try:
                int(digest, 16)
            except ValueError:
                errors.append(f"SCREENSHOT_ARTIFACT_DIGEST_INVALID:{purpose or index}")
    return errors


def bindings(manifest):
    return {
        entry["purpose_id"]: (entry["artifact_ref"], entry["artifact_sha256"])
        for entry in manifest.get("entries", [])
        if isinstance(entry, dict)
        and isinstance(entry.get("purpose_id"), str)
        and isinstance(entry.get("artifact_ref"), str)
        and isinstance(entry.get("artifact_sha256"), str)
    }


def compare(baseline, candidate):
    errors = []
    if baseline.get("experiment_id") != candidate.get("experiment_id"):
        errors.append("SCREENSHOT_EXPERIMENT_CHANGED")
    if baseline.get("evidence_epoch") != candidate.get("evidence_epoch"):
        errors.append("SCREENSHOT_EVIDENCE_EPOCH_CHANGED")
    before = bindings(baseline)
    after = bindings(candidate)
    if set(before) != set(after):
        errors.append("SCREENSHOT_SET_MUTATED")
    for purpose in sorted(set(before) & set(after)):
        if before[purpose] != after[purpose]:
            errors.append(f"SCREENSHOT_PURPOSE_BINDING_CHANGED:{purpose}")
    if manifest_digest(baseline) != manifest_digest(candidate):
        errors.append("SCREENSHOT_MANIFEST_DIGEST_CHANGED")
    return errors


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--against")
    args = parser.parse_args()

    manifest = load(args.manifest)
    errors = validate_shape(manifest)
    digest = manifest_digest(manifest)

    if args.against:
        baseline = load(args.against)
        errors.extend(validate_shape(baseline))
        errors.extend(compare(baseline, manifest))

    result = {
        "schema": "stegverse.mir-frozen-screenshot-validation/v1",
        "manifest_sha256": digest,
        "valid": not errors,
        "errors": sorted(set(errors)),
    }
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
