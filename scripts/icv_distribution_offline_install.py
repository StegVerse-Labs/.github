#!/usr/bin/env python3
"""ICV distribution: verify pinned source bytes, then install, upgrade and
uninstall them offline into a temporary prefix. Standard library only.

Workstream B of StegVerse-Labs/.github#3183 (pinned, rights-cleared packages;
offline, customer-controlled install, uninstall and upgrade). The pins live in
distribution/icv/package-pins.v1.json. Each pinned file carries its git blob
SHA as observed through the GitHub connector; this script recomputes every blob
SHA (and the package-root tree SHA) from the bytes before anything is placed.

Phases, kept separate on purpose:
  acquire   download https://github.com/<repo>/archive/<commit>.tar.gz
            (the same anonymous route org-runtime-boundary.yml already uses)
            into a cache directory. This is the only phase that touches the
            network.
  verify    recompute git blob/tree SHAs and compare them with the pins.
  install / upgrade / uninstall
            run with socket creation disabled, from verified local bytes only.

Every step emits one receipt: disposition PASS, or FAIL_CLOSED with the six
fields failure_code, failed_predicate, required_evidence_or_repair,
retry_entrypoint, owning_existing_goal and next_attempt. A package whose
license is not declared in its own source is never installed: it gets a
FAIL_CLOSED receipt instead.

Non-authorizing. This is not pip, not a release, not a legal determination and
not customer runtime evidence; it mints no admission and changes no registry.
"""
from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import io
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
PINS = ROOT / "distribution" / "icv" / "package-pins.v1.json"
RECEIPT_SCHEMA = "stegverse.icv.offline-lifecycle-receipt/v1"
INSTALLER = "icv-stdlib-offline/1"
GOAL = "StegVerse-Labs/.github#3183 workstream B; StegVerse-org/.github#165 (Lane A)"
RETRY = "python scripts/icv_distribution_offline_install.py --lifecycle"
CLEARED_PREFIX = "CLEARED_AS_DECLARED"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair",
       "retry_entrypoint", "owning_existing_goal", "next_attempt")


class FailClosed(Exception):
    def __init__(self, code: str, predicate: str, repair: str,
                 next_attempt: str = "after the repair is observed",
                 goal: str = GOAL, retry: str = RETRY):
        super().__init__(code)
        self.fields = {
            "failure_code": code,
            "failed_predicate": predicate,
            "required_evidence_or_repair": repair,
            "retry_entrypoint": retry,
            "owning_existing_goal": goal,
            "next_attempt": next_attempt,
        }


# ---------------------------------------------------------------- hashing

def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def git_tree_sha(directory: Path) -> str:
    """The git tree SHA of a directory of regular files (no symlinks/submodules)."""
    entries = []
    for child in directory.iterdir():
        if child.is_symlink():
            raise FailClosed("ICV_SOURCE_SYMLINK_REFUSED", f"{child} is a regular file or directory",
                             "pin a source tree without symlinks")
        if child.is_dir():
            mode, sha, sort_key = b"40000", git_tree_sha(child), child.name + "/"
        else:
            executable = os.stat(child).st_mode & 0o100
            mode = b"100755" if executable else b"100644"
            sha, sort_key = git_blob_sha(child.read_bytes()), child.name
        entries.append((sort_key.encode(), mode + b" " + child.name.encode() + b"\0" + bytes.fromhex(sha)))
    body = b"".join(item for _, item in sorted(entries))
    return hashlib.sha1(b"tree %d\0" % len(body) + body).hexdigest()


def record_hash(data: bytes) -> str:
    digest = hashlib.sha256(data).digest()
    return "sha256=" + base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


# ---------------------------------------------------------------- pins

def load_pins(path: Path = PINS) -> dict:
    try:
        pins = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FailClosed("ICV_PINS_UNREADABLE", f"{path} parses as JSON", str(exc)) from exc
    if pins.get("schema") != "stegverse.icv.distribution-pins/v1":
        raise FailClosed("ICV_PINS_SCHEMA_MISMATCH", "schema is stegverse.icv.distribution-pins/v1",
                         "regenerate the pins file")
    return pins


def find_pin(pins: dict, package: str, version: str) -> dict:
    for pin in pins.get("packages", []):
        if pin.get("package") == package and pin.get("version") == version:
            return pin
    raise FailClosed("ICV_PIN_ABSENT", f"{package}=={version} is pinned", "add the pin from authenticated source")


def cleared(pin: dict) -> bool:
    return str(pin.get("rights_clearance", "")).startswith(CLEARED_PREFIX) and pin.get("lifecycle_test") is True


def check_requires_python(pin: dict, version_info=sys.version_info) -> None:
    spec = pin.get("requires_python", "")
    match = re.fullmatch(r">=\s*(\d+)\.(\d+)", spec or "")
    if not match:
        raise FailClosed("ICV_REQUIRES_PYTHON_UNPARSED", f"requires_python {spec!r} is of the form >=X.Y",
                         "extend the checker or the pin; nothing is installed meanwhile")
    floor = (int(match.group(1)), int(match.group(2)))
    if tuple(version_info[:2]) < floor:
        raise FailClosed("ICV_PYTHON_BELOW_DECLARED_FLOOR",
                         f"python {version_info[0]}.{version_info[1]} satisfies {spec}",
                         f"run on python {floor[0]}.{floor[1]} or newer")


# ---------------------------------------------------------------- acquire

def archive_url(pin: dict) -> str:
    return f"https://github.com/{pin['source_repository']}/archive/{pin['commit']}.tar.gz"


def safe_extract(archive: bytes, commit: str, destination: Path) -> Path:
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        comment = (tar.pax_headers or {}).get("comment")
        if comment is not None and comment != commit:
            raise FailClosed("ICV_ARCHIVE_COMMIT_MISMATCH", f"archive pax comment {comment} equals pinned {commit}",
                             "re-acquire from the pinned commit")
        members = tar.getmembers()
        for member in members:
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts:
                raise FailClosed("ICV_ARCHIVE_PATH_ESCAPE", f"{member.name} stays inside the archive root",
                                 "refuse this archive")
            if member.issym() or member.islnk() or member.isdev():
                raise FailClosed("ICV_ARCHIVE_LINK_REFUSED", f"{member.name} is a regular file or directory",
                                 "pin a source tree without links")
        tops = {PurePosixPath(m.name).parts[0] for m in members if m.name}
        if len(tops) != 1:
            raise FailClosed("ICV_ARCHIVE_LAYOUT", "the archive has a single top-level directory",
                             "refuse this archive")
        for member in members:
            target = destination / member.name
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar.extractfile(member) as source:
                target.write_bytes(source.read())
            os.chmod(target, 0o755 if member.mode & 0o100 else 0o644)
        return destination / tops.pop()


def acquire(pin: dict, cache: Path, opener=urllib.request.urlopen) -> Path:
    root = cache / f"{pin['source_repository'].replace('/', '__')}@{pin['commit']}"
    if root.is_dir():
        return root / "src"
    url = archive_url(pin)
    try:
        with opener(url, timeout=60) as response:
            data = response.read()
    except Exception as exc:  # network, HTTP or TLS failure
        raise FailClosed("ICV_SOURCE_ACQUISITION_FAILED", f"{url} returns the pinned archive",
                         f"network access to the public archive route ({type(exc).__name__})",
                         next_attempt="on the next run with network access") from exc
    staging = Path(tempfile.mkdtemp(prefix="icv-acquire-", dir=cache))
    top = safe_extract(data, pin["commit"], staging)
    root.mkdir(parents=True)
    top.rename(root / "src")
    shutil.rmtree(staging)
    (root / "archive.sha256").write_text(hashlib.sha256(data).hexdigest() + "\n", encoding="utf-8")
    return root / "src"


# ---------------------------------------------------------------- verify

def verify_source(pin: dict, src: Path) -> dict:
    mismatches = []
    checked = 0
    for rel, expected in sorted({**pin.get("manifest_blobs", {}), **pin.get("install_files", {})}.items()):
        path = src / rel
        if not path.is_file():
            mismatches.append({"path": rel, "expected": expected, "observed": None})
            continue
        observed = git_blob_sha(path.read_bytes())
        checked += 1
        if observed != expected:
            mismatches.append({"path": rel, "expected": expected, "observed": observed})
    trees_observed = {}
    for package_root in pin.get("package_roots", []):
        observed_tree = git_tree_sha(src / package_root["path"]) if (src / package_root["path"]).is_dir() else None
        trees_observed[package_root["path"]] = observed_tree
        if observed_tree != package_root["tree"]:
            mismatches.append({"path": package_root["path"] + "/", "expected": package_root["tree"],
                               "observed": observed_tree})
    if mismatches:
        raise FailClosed("ICV_PINNED_BYTES_MISMATCH",
                         f"every pinned blob and package-root tree of {pin['package']}=={pin['version']} match",
                         "re-acquire from the pinned commit, or refresh the pins from authenticated source: "
                         + json.dumps(mismatches[:5]))
    return {"blobs_verified": checked, "package_root_trees": trees_observed}


# ---------------------------------------------------------------- offline guard

@contextlib.contextmanager
def network_disabled():
    original = socket.socket, socket.create_connection

    def refuse(*_args, **_kwargs):
        raise OSError("network disabled during offline install")

    socket.socket, socket.create_connection = refuse, refuse  # type: ignore[assignment]
    try:
        yield
    finally:
        socket.socket, socket.create_connection = original  # type: ignore[assignment]


# ---------------------------------------------------------------- install

def dist_info_name(pin: dict) -> str:
    return f"{re.sub(r'[-_.]+', '_', pin['package'])}-{pin['version']}.dist-info"


def installed_dist(site: Path, package: str) -> Path | None:
    prefix = re.sub(r"[-_.]+", "_", package) + "-"
    found = [p for p in site.glob(prefix + "*.dist-info") if p.is_dir()] if site.is_dir() else []
    if len(found) > 1:
        raise FailClosed("ICV_MULTIPLE_DIST_INFO", f"at most one {package} dist-info under {site}",
                         "uninstall the extra copies by hand")
    return found[0] if found else None


def _metadata(pin: dict) -> str:
    lines = ["Metadata-Version: 2.1", f"Name: {pin['package']}", f"Version: {pin['version']}",
             f"Requires-Python: {pin['requires_python']}", f"License: {pin['license_declared']['spdx']}"]
    lines += [f"Requires-Dist: {dep}" for dep in pin.get("runtime_dependencies", [])]
    return "\n".join(lines) + "\n"


def _place(pin: dict, src: Path, site: Path) -> list[tuple[str, str, int]]:
    rows = []
    for rel in sorted(pin["install_files"]):
        data = (src / rel).read_bytes()
        target = site / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append((rel, record_hash(data), len(data)))
    info = site / dist_info_name(pin)
    info.mkdir()
    extra = {
        "METADATA": _metadata(pin),
        "INSTALLER": INSTALLER + "\n",
        "PINNED_SOURCE.json": json.dumps({
            "source_repository": pin["source_repository"], "commit": pin["commit"],
            "package_roots": pin.get("package_roots"), "license_declared": pin["license_declared"]["spdx"],
            "rights_clearance": pin["rights_clearance"]}, indent=2, sort_keys=True) + "\n",
    }
    if (src / "LICENSE").is_file():
        extra["LICENSE"] = (src / "LICENSE").read_text(encoding="utf-8")
    for name, text in extra.items():
        data = text.encode("utf-8")
        (info / name).write_bytes(data)
        rows.append((f"{info.name}/{name}", record_hash(data), len(data)))
    record = "".join(f"{p},{h},{n}\n" for p, h, n in rows) + f"{info.name}/RECORD,,\n"
    (info / "RECORD").write_text(record, encoding="utf-8")
    return rows


def install(pin: dict, src: Path, site: Path) -> dict:
    if not cleared(pin):
        raise FailClosed(**_refusal(pin))
    check_requires_python(pin)
    verify_source(pin, src)
    if installed_dist(site, pin["package"]) is not None:
        raise FailClosed("ICV_ALREADY_INSTALLED", f"no {pin['package']} is installed under {site}",
                         "uninstall first, or use --upgrade")
    with network_disabled():
        rows = _place(pin, src, site)
    return {"files_placed": len(rows)}


def _record_rows(info: Path) -> list[tuple[str, str]]:
    rows = []
    for line in (info / "RECORD").read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        path, digest, _size = line.rsplit(",", 2)
        rows.append((path, digest))
    return rows


def uninstall(site: Path, package: str) -> dict:
    info = installed_dist(site, package)
    if info is None:
        raise FailClosed("ICV_NOT_INSTALLED", f"{package} is installed under {site}", "nothing to uninstall")
    rows = _record_rows(info)
    site_resolved = site.resolve()
    changed = []
    for rel, digest in rows:
        target = (site / rel).resolve()
        if site_resolved not in target.parents:
            raise FailClosed("ICV_RECORD_PATH_ESCAPE", f"{rel} stays inside {site}", "refuse this RECORD")
        if digest and (not target.is_file() or record_hash(target.read_bytes()) != digest):
            changed.append(rel)
    if changed:
        raise FailClosed("ICV_INSTALLED_FILES_MODIFIED",
                         f"every RECORD file of {package} is unchanged since install",
                         "restore or review the changed files before uninstalling; nothing was removed: "
                         + ", ".join(changed[:5]))
    with network_disabled():
        removed = 0
        for rel, _digest in rows:
            target = site / rel
            if target.exists():
                target.unlink()
                removed += 1
        for directory in sorted({(site / rel).parent for rel, _ in rows}, key=lambda p: len(p.parts), reverse=True):
            with contextlib.suppress(OSError):
                for cache in directory.glob("__pycache__"):
                    shutil.rmtree(cache)
                while directory != site and directory.is_dir() and not any(directory.iterdir()):
                    directory.rmdir()
                    directory = directory.parent
    return {"files_removed": removed}


def upgrade(old: dict, new: dict, src: Path, site: Path) -> dict:
    if not cleared(new):
        raise FailClosed(**_refusal(new))
    check_requires_python(new)
    verify_source(new, src)
    info = installed_dist(site, new["package"])
    if info is None or info.name != dist_info_name(old):
        raise FailClosed("ICV_UPGRADE_FROM_STATE_ABSENT", f"{old['package']}=={old['version']} is installed",
                         "install the from-version first")
    staging = Path(tempfile.mkdtemp(prefix="icv-upgrade-"))
    try:
        with network_disabled():
            _place(new, src, staging)
        backup = Path(tempfile.mkdtemp(prefix="icv-backup-"))
        for rel, _ in _record_rows(info):
            if (site / rel).is_file():
                (backup / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(site / rel, backup / rel)
        uninstall(site, old["package"])
        try:
            with network_disabled():
                for path in sorted(staging.rglob("*")):
                    if path.is_file():
                        target = site / path.relative_to(staging)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(path, target)
        except Exception:
            for path in backup.rglob("*"):
                if path.is_file():
                    target = site / path.relative_to(backup)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
            raise
        finally:
            shutil.rmtree(backup, ignore_errors=True)
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    old_only = set(old["install_files"]) - set(new["install_files"])
    lingering = sorted(p for p in old_only if (site / p).exists())
    if lingering:
        raise FailClosed("ICV_UPGRADE_LEFT_STALE_FILES", "files only in the from-version are gone after upgrade",
                         "repair the upgrade: " + ", ".join(lingering[:5]))
    return {"removed_from_version_only_files": len(old_only), "files_placed": len(new["install_files"])}


def import_smoke(pin: dict, site: Path) -> dict:
    code = ("import importlib,sys; sys.path.insert(0, sys.argv[1]); "
            f"m=importlib.import_module({pin['import_name']!r}); print(m.__file__)")
    completed = subprocess.run([sys.executable, "-I", "-S", "-c", code, str(site)],
                               capture_output=True, text=True, timeout=120)
    location = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else ""
    if completed.returncode != 0 or not location.startswith(str(site)):
        raise FailClosed("ICV_IMPORT_SMOKE_FAILED",
                         f"import {pin['import_name']} succeeds from {site} with no other site-packages",
                         (completed.stderr.strip().splitlines() or ["no output"])[-1])
    return {"imported_from": "<prefix>/" + str(Path(location).relative_to(site))}


def _refusal(pin: dict) -> dict:
    declared = pin.get("fail_closed")
    if isinstance(declared, dict) and all(k in declared for k in SIX):
        return {"code": declared["failure_code"], "predicate": declared["failed_predicate"],
                "repair": declared["required_evidence_or_repair"], "next_attempt": declared["next_attempt"],
                "goal": declared["owning_existing_goal"], "retry": declared["retry_entrypoint"]}
    return {"code": "ICV_PIN_NOT_RIGHTS_CLEARED",
            "predicate": f"{pin.get('package')}=={pin.get('version')} has a declared, cleared license",
            "repair": "a license declared in the package's own source"}


# ---------------------------------------------------------------- receipts

def receipt(step: str, pin: dict | None, fn) -> dict:
    base = {
        "schema": RECEIPT_SCHEMA, "step": step,
        "package": pin.get("package") if pin else None, "version": pin.get("version") if pin else None,
        "source": f"{pin['source_repository']}@{pin['commit']}" if pin and "commit" in pin else None,
        "python": platform.python_version(), "implementation": platform.python_implementation(),
        "platform": f"{platform.system()}-{platform.machine()}",
        "authority_effect": "NONE_OBSERVATION_ONLY",
    }
    try:
        detail = fn() or {}
        return {**base, "disposition": "PASS", **detail}
    except FailClosed as exc:
        return {**base, "disposition": "FAIL_CLOSED", **exc.fields}


def lifecycle(pins: dict, cache: Path) -> list[dict]:
    receipts = []
    sources: dict[tuple[str, str], Path] = {}

    def src_of(pin):
        key = (pin["package"], pin["version"])
        if key not in sources:
            sources[key] = acquire(pin, cache)
        return sources[key]

    for pin in pins["packages"]:
        if not cleared(pin):
            receipts.append(receipt("rights-gate", pin, lambda p=pin: (_ for _ in ()).throw(FailClosed(**_refusal(p)))))
            continue
        receipts.append(receipt("acquire", pin, lambda p=pin: {"archive": archive_url(p), "cached": str(src_of(p).name)}))
        receipts.append(receipt("verify", pin, lambda p=pin: verify_source(p, src_of(p))))
    by_key = {(p["package"], p["version"]): p for p in pins["packages"]}
    if any(r["disposition"] != "PASS" for r in receipts if r["step"] in ("acquire", "verify")):
        return receipts
    for pin in pins["packages"]:
        if not cleared(pin):
            continue
        with tempfile.TemporaryDirectory(prefix="icv-prefix-") as prefix:
            site = Path(prefix) / "site-packages"
            receipts.append(receipt("install", pin, lambda p=pin: install(p, src_of(p), site)))
            if pin.get("import_smoke"):
                receipts.append(receipt("import-smoke", pin, lambda p=pin: import_smoke(p, site)))
            receipts.append(receipt("uninstall", pin, lambda p=pin: {
                **uninstall(site, p["package"]),
                "residue": sorted(str(x.relative_to(site)) for x in site.rglob("*"))}))
            if receipts[-1]["disposition"] == "PASS" and receipts[-1]["residue"]:
                receipts[-1] = {**receipts[-1], "disposition": "FAIL_CLOSED", **FailClosed(
                    "ICV_UNINSTALL_RESIDUE", "uninstall leaves the prefix empty",
                    "repair uninstall: " + ", ".join(receipts[-1]["residue"][:5])).fields}
    for path in pins.get("upgrade_paths", []):
        old = by_key[(path["package"], path["from"])]
        new = by_key[(path["package"], path["to"])]
        with tempfile.TemporaryDirectory(prefix="icv-prefix-") as prefix:
            site = Path(prefix) / "site-packages"
            receipts.append(receipt("upgrade-from-install", old, lambda: install(old, src_of(old), site)))
            receipts.append(receipt("upgrade", new, lambda: {"from": old["version"], **upgrade(old, new, src_of(new), site)}))
            if new.get("import_smoke"):
                receipts.append(receipt("upgrade-import-smoke", new, lambda: import_smoke(new, site)))
            receipts.append(receipt("upgrade-uninstall", new, lambda: {
                **uninstall(site, new["package"]),
                "residue": sorted(str(x.relative_to(site)) for x in site.rglob("*"))}))
    icv = pins.get("icv_repositories") or {}
    if isinstance(icv.get("fail_closed"), dict):
        receipts.append({"schema": RECEIPT_SCHEMA, "step": "icv-repository-bytes", "package": None,
                         "version": None, "source": ", ".join(icv.get("repositories", [])),
                         "authority_effect": "NONE_OBSERVATION_ONLY", "disposition": "FAIL_CLOSED",
                         "classification": icv.get("classification"), **icv["fail_closed"]})
    return receipts


def expected_ok(receipts: list[dict], pins: dict) -> bool:
    """PASS for every cleared-package step; FAIL_CLOSED for every refusal step."""
    cleared_keys = {(p["package"], p["version"]) for p in pins["packages"] if cleared(p)}
    for r in receipts:
        if r["step"] in ("rights-gate", "icv-repository-bytes"):
            if r["disposition"] != "FAIL_CLOSED":
                return False
        elif (r["package"], r["version"]) in cleared_keys and r["disposition"] != "PASS":
            return False
    steps = {r["step"] for r in receipts}
    return {"install", "uninstall", "upgrade", "upgrade-uninstall"} <= steps


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pins", type=Path, default=PINS)
    parser.add_argument("--cache", type=Path, default=None,
                        help="directory holding acquired archives (default: a temporary directory)")
    parser.add_argument("--lifecycle", action="store_true", help="acquire, verify, install, upgrade, uninstall")
    parser.add_argument("--receipts-out", type=Path, default=None)
    args = parser.parse_args(argv)
    if not args.lifecycle:
        parser.error("nothing to do: pass --lifecycle")
    try:
        pins = load_pins(args.pins)
    except FailClosed as exc:
        print(json.dumps({"disposition": "FAIL_CLOSED", **exc.fields}, indent=2))
        return 2
    with tempfile.TemporaryDirectory(prefix="icv-cache-") as tmp:
        cache = args.cache or Path(tmp)
        cache.mkdir(parents=True, exist_ok=True)
        receipts = lifecycle(pins, cache)
    text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in receipts)
    if args.receipts_out:
        args.receipts_out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    ok = expected_ok(receipts, pins)
    summary = {"ICV_OFFLINE_LIFECYCLE": "PASS" if ok else "FAIL_CLOSED",
               "receipts": len(receipts),
               "pass": sum(r["disposition"] == "PASS" for r in receipts),
               "fail_closed": sum(r["disposition"] == "FAIL_CLOSED" for r in receipts)}
    print(json.dumps(summary, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
