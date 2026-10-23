#!/usr/bin/env python3
"""A pinned source tree as a declared verification input (E0, stdlib + git only).

StegVerse-org/.github#163 (P1). A test set that needs another repository's code at an exact commit (the StegVerse
SDK, say) declares it as an input; this tool supplies that input and proves it is the declared one:

  * the manifest (.stegverse/verification-inputs/<input>.json) names the repository, and for each pin the commit,
    its git tree, and the module paths the tests load, with every file's sha256 and a per-module sha256 (over the
    canonical {path: sha256} map of that module's files);
  * `materialize` fetches exactly that commit with git (one anonymous `git fetch --depth=1 <repository> <commit>`,
    the same read every workflow here already does; no package index, no install, no credential), extracts ONLY the
    declared module paths, and re-hashes every file;
  * `verify` re-hashes a materialized root against the manifest (the selector calls it before it calls the input
    available, so a root that drifted after it was materialized is refused too).

Anything that does not match - a different commit or tree, a file whose sha256 differs, a declared file absent, a
file present that the manifest does not declare, a manifest whose seal does not verify - is FAIL_CLOSED with six
fields and nothing is loaded. Nothing is skipped, nothing is published, no clock is read.

  materialize --manifest M --pin ID --dest DIR [--source URL_OR_PATH]   -> DIR/tree (the import root), DIR/receipt.json
  verify      --manifest M --pin ID --root DIR/tree
  env         --manifest M --pin ID --root DIR/tree                     -> the pin's exports, KEY=VALUE per line
  declared    --spec .stegverse/test-set-spec.json --dest-root DIR [--env-out FILE]
              -> materializes every pin a `pinned_source` input of the spec declares, writes ENV=DIR/<pin>/tree for
                 each one that verifies; a pin that does not is printed as six fields and its env is NOT written, so
                 the selector reports the sets that need it as REQUIRED_VERIFICATION_INPUT_UNAVAILABLE (blocking only
                 changes that select them) instead of the job dying for every change
  pin         --manifest M --pin ID --repo LOCAL_GIT --commit C --module PATH [--module PATH ...]   (authoring)
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

SCHEMA = "stegverse.pinned-source-input/v1"
RECEIPT_SCHEMA = "stegverse.pinned-source-input-receipt/v1"
SEAL = "manifest_sha256"
SIX = ("failure_code", "failed_predicate", "required_evidence_or_repair", "retry_entrypoint",
       "owning_existing_goal", "next_attempt")
GOAL = "StegVerse-org/.github#163 (P1 Ecosystem AI Lane: pinned SDK verification input)"
NEXT = "the next run of the job that materializes this input, at the exact head"
NO_CREDENTIAL = ["-c", "http.https://github.com/.extraheader="]


class PinRefused(Exception):
    def __init__(self, record: Mapping[str, Any]):
        super().__init__(record["failure_code"])
        self.record = dict(record)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def refuse(code: str, predicate: str, repair: str, retry: str, **detail: Any) -> PinRefused:
    return PinRefused({"disposition": "FAIL_CLOSED", "failure_code": code, "failed_predicate": predicate,
                       "required_evidence_or_repair": repair, "retry_entrypoint": retry,
                       "owning_existing_goal": GOAL, "next_attempt": NEXT, **detail})


def sealed(body: Mapping[str, Any]) -> dict:
    clean = {k: v for k, v in body.items() if k != SEAL}
    return {**clean, SEAL: hashlib.sha256(canonical(clean)).hexdigest()}


def module_digest(files: Mapping[str, str]) -> str:
    return hashlib.sha256(canonical(dict(sorted(files.items())))).hexdigest()


def load_manifest(path: Path, pin_id: str, retry: str) -> tuple[dict, dict]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise refuse("PINNED_INPUT_MANIFEST_UNREADABLE", "PINNED_INPUT_MANIFEST_IS_READABLE",
                     f"{path} could not be read as JSON ({exc}); restore the committed manifest", retry)
    if manifest.get("schema") != SCHEMA or sealed(manifest).get(SEAL) != manifest.get(SEAL):
        raise refuse("PINNED_INPUT_MANIFEST_SEAL_MISMATCH", "PINNED_INPUT_MANIFEST_IS_SEALED",
                     f"{path} is not a sealed {SCHEMA} manifest (its {SEAL} does not verify); regenerate it with "
                     "`pinned_source_input.py pin` from the source repository, never by hand", retry)
    pin = manifest.get("pins", {}).get(pin_id)
    if not pin:
        raise refuse("PINNED_INPUT_PIN_UNDECLARED", "TEST_SET_PIN_IS_DECLARED_IN_THE_MANIFEST",
                     f"pin {pin_id!r} is not declared in {path} (declared: {sorted(manifest.get('pins', {}))}); "
                     "declare it with `pinned_source_input.py pin`", retry)
    return manifest, pin


def hash_root(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.rglob("*")):
        if p.is_symlink():
            out[p.relative_to(root).as_posix()] = "SYMLINK"
        elif p.is_file():
            out[p.relative_to(root).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def verify(manifest_path: Path, pin_id: str, root: Path, retry: str = "pinned_source_input.py verify") -> dict:
    """The verification record of a materialized root; raises PinRefused (six fields) on any mismatch."""
    manifest, pin = load_manifest(manifest_path, pin_id, retry)
    if not root.is_dir():
        raise refuse("PINNED_INPUT_ROOT_ABSENT", "PINNED_INPUT_IS_MATERIALIZED",
                     f"{root} is not a directory; materialize pin {pin_id} first "
                     f"(pinned_source_input.py materialize --manifest {manifest_path} --pin {pin_id})", retry)
    got = hash_root(root)
    declared: dict[str, str] = {}
    for mod in pin["modules"].values():
        declared.update(mod["file_sha256"])
    differ = sorted(p for p in declared if p in got and got[p] != declared[p])
    absent = sorted(p for p in declared if p not in got)
    extra = sorted(p for p in got if p not in declared and not p.endswith(".pyc"))
    if differ or absent or extra:
        code = ("PINNED_INPUT_SHA256_MISMATCH" if differ else
                "PINNED_INPUT_DECLARED_FILE_ABSENT" if absent else "PINNED_INPUT_UNDECLARED_FILE")
        raise refuse(code, "PINNED_INPUT_FILES_MATCH_THE_DECLARED_SHA256",
                     f"the tree at {root} is not pin {pin_id} ({pin['commit']}): {len(differ)} file(s) differ, "
                     f"{len(absent)} declared file(s) absent, {len(extra)} undeclared file(s); re-materialize it "
                     "from the pinned commit, or re-pin the manifest from the source repository if the pin is meant "
                     "to move", retry, differ=differ[:20], absent=absent[:20], undeclared=extra[:20])
    modules = {}
    for name, mod in sorted(pin["modules"].items()):
        digest = module_digest(mod["file_sha256"])
        if digest != mod["sha256"]:
            raise refuse("PINNED_INPUT_MODULE_DIGEST_MISMATCH", "PINNED_INPUT_MODULE_SHA256_MATCHES_ITS_FILES",
                         f"module {name} of pin {pin_id} declares sha256 {mod['sha256']} but its files hash to "
                         f"{digest}; regenerate the manifest with `pinned_source_input.py pin`", retry)
        modules[name] = digest
    return {"schema": RECEIPT_SCHEMA, "input": manifest["input"], "repository": manifest["repository"],
            "pin": pin_id, "commit": pin["commit"], "tree": pin["tree"], "root": str(root),
            "manifest": {"path": str(manifest_path), SEAL: manifest[SEAL]}, "modules": modules,
            "files_verified": len(declared), "disposition": "ALLOW", "lowest_supported_mode": "E0",
            "derived_from_clock": False, "authority_effect": "NONE"}


def git(cwd: Path, *args: str, data: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *NO_CREDENTIAL, *args], cwd=cwd, capture_output=True, text=not data)


def _extract(blob: bytes, dest: Path, retry: str) -> None:
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        for member in tar.getmembers():
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or not (member.isfile() or member.isdir()):
                raise refuse("PINNED_INPUT_ARCHIVE_ENTRY_REFUSED", "PINNED_INPUT_IS_PLAIN_FILES_UNDER_ITS_ROOT",
                             f"archive entry {member.name!r} is not a plain file or directory under the root",
                             retry)
            target = dest / Path(*name.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            fh = tar.extractfile(member)
            target.write_bytes(fh.read() if fh else b"")
            if member.mode & 0o111:
                target.chmod(0o755)


def materialize(manifest_path: Path, pin_id: str, dest: Path, source: str | None = None,
                retry: str = "pinned_source_input.py materialize") -> dict:
    manifest, pin = load_manifest(manifest_path, pin_id, retry)
    url = source or manifest["repository"]
    commit = pin["commit"]
    if dest.exists() and any(dest.iterdir()):
        raise refuse("PINNED_INPUT_DEST_NOT_EMPTY", "PINNED_INPUT_IS_MATERIALIZED_INTO_AN_EMPTY_ROOT",
                     f"{dest} is not empty; materialize into a fresh directory", retry)
    fetch, tree = dest / "fetch", dest / "tree"
    fetch.mkdir(parents=True)
    tree.mkdir()
    git(fetch, "init", "-q")
    done = git(fetch, "fetch", "--no-tags", "--quiet", "--depth=1", url, commit)
    if done.returncode != 0:
        raise refuse("PINNED_INPUT_FETCH_FAILED", "PINNED_INPUT_COMMIT_IS_READABLE",
                     f"git fetch --depth=1 {url} {commit} failed ({done.stderr.strip()[:300]}); the pinned commit "
                     "must be readable anonymously from the declared repository", retry)
    got = git(fetch, "rev-parse", "FETCH_HEAD").stdout.strip()
    got_tree = git(fetch, "rev-parse", f"{commit}^{{tree}}").stdout.strip()
    if got != commit:
        raise refuse("PINNED_INPUT_COMMIT_MISMATCH", "PINNED_INPUT_IS_THE_DECLARED_COMMIT",
                     f"{url} served {got or 'nothing'} for {commit}", retry)
    if got_tree != pin["tree"]:
        raise refuse("PINNED_INPUT_TREE_MISMATCH", "PINNED_INPUT_IS_THE_DECLARED_TREE",
                     f"commit {commit} has tree {got_tree}, the manifest pins {pin['tree']}", retry)
    archive = git(fetch, "archive", "--format=tar", commit, "--", *sorted(pin["modules"]), data=True)
    if archive.returncode != 0:
        raise refuse("PINNED_INPUT_MODULE_ABSENT", "PINNED_INPUT_DECLARED_MODULES_EXIST_AT_THE_COMMIT",
                     f"git archive {commit} -- {' '.join(sorted(pin['modules']))} failed "
                     f"({archive.stderr.decode(errors='replace').strip()[:300]})", retry)
    _extract(archive.stdout, tree, retry)
    record = verify(manifest_path, pin_id, tree, retry)
    record["fetched_from"] = url
    (dest / "receipt.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def exports(manifest_path: Path, pin_id: str, root: Path) -> dict[str, str]:
    manifest, pin = load_manifest(manifest_path, pin_id, "pinned_source_input.py env")
    return {k: v.replace("{root}", str(root)) for k, v in sorted(manifest.get("exports", {}).items())}


def author_pin(manifest_path: Path, pin_id: str, repo: Path, commit: str, modules: list[str],
               base: Mapping[str, Any], requires: list[str] | None = None, note: str | None = None) -> dict:
    full = subprocess.run(["git", "rev-parse", f"{commit}^{{commit}}"], cwd=repo, capture_output=True,
                          text=True, check=True).stdout.strip()
    tree = subprocess.run(["git", "rev-parse", f"{full}^{{tree}}"], cwd=repo, capture_output=True, text=True,
                          check=True).stdout.strip()
    blob = subprocess.run(["git", "archive", "--format=tar", full, "--", *modules], cwd=repo, capture_output=True,
                          check=True).stdout
    entry: dict[str, Any] = {"commit": full, "tree": tree, "modules": {}}
    if requires:
        # modules the pinned commit itself needs at runtime from the job's interpreter; never installed by this input
        entry["runtime_requires_importable"] = sorted(requires)
    if note:
        entry["note"] = note
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        files = {m.name: hashlib.sha256(tar.extractfile(m).read()).hexdigest()  # type: ignore[union-attr]
                 for m in tar.getmembers() if m.isfile()}
    for mod in sorted(modules):
        mine = {p: h for p, h in files.items() if p == mod or p.startswith(mod.rstrip("/") + "/")}
        if not mine:
            raise SystemExit(f"module {mod} has no files at {full}")
        git_obj = subprocess.run(["git", "rev-parse", f"{full}:{mod}"], cwd=repo, capture_output=True, text=True,
                                 check=True).stdout.strip()
        entry["modules"][mod] = {"git_object": git_obj, "files": len(mine), "sha256": module_digest(mine),
                                 "file_sha256": dict(sorted(mine.items()))}
    manifest = dict(base)
    manifest.setdefault("pins", {})
    manifest["pins"] = {**manifest["pins"], pin_id: entry}
    return sealed(manifest)


def declared(spec_path: Path, dest_root: Path, root: Path, retry: str) -> tuple[dict[str, str], list[dict]]:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    env: dict[str, str] = {}
    refused: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for name, decl in sorted(spec.get("inputs", {}).items()):
        check = decl.get("check", {})
        if check.get("kind") != "pinned_source" or (check["manifest"], check["pin"]) in seen:
            continue
        seen.add((check["manifest"], check["pin"]))
        dest = dest_root / f"{Path(check['manifest']).stem}-{check['pin']}"
        try:
            record = materialize(root / check["manifest"], check["pin"], dest, None, retry)
            env[check["env"]] = record["root"]
            print(f"ALLOW input={name} pin={check['pin']} commit={record['commit']} files={record['files_verified']}")
        except PinRefused as exc:
            refused.append({"input": name, **exc.record})
            print(json.dumps({"input": name, **exc.record}, indent=2, sort_keys=True))
            print(f"FAIL_CLOSED {exc.record['failure_code']} input={name} pin={check['pin']} (env {check['env']} "
                  "not set: the selector reports the sets that need it as unavailable)")
    return env, refused


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("materialize", "verify", "env", "pin"):
        p = sub.add_parser(name)
        p.add_argument("--manifest", required=True)
        p.add_argument("--pin", required=True)
        p.add_argument("--retry-entrypoint", default=f"pinned_source_input.py {name}")
        if name == "materialize":
            p.add_argument("--dest", required=True)
            p.add_argument("--source", help="read the commit from here instead of the manifest's repository "
                           "(a local clone, for an offline proof); commit, tree and sha256 are checked the same")
        if name in ("verify", "env"):
            p.add_argument("--root", required=True)
        if name == "pin":
            p.add_argument("--repo", required=True)
            p.add_argument("--commit", required=True)
            p.add_argument("--module", action="append", required=True)
            p.add_argument("--requires", action="append", help="a runtime module the pinned commit itself declares "
                           "and the job's interpreter must already provide (never installed)")
            p.add_argument("--note")
    d = sub.add_parser("declared")
    d.add_argument("--spec", required=True)
    d.add_argument("--root", default=".")
    d.add_argument("--dest-root", required=True)
    d.add_argument("--env-out", help="append KEY=VALUE lines here (e.g. $GITHUB_ENV)")
    d.add_argument("--retry-entrypoint", default="pinned_source_input.py declared")
    a = parser.parse_args(argv)
    if a.command == "declared":
        root = Path(a.root).resolve()
        env, refused = declared(root / a.spec, Path(a.dest_root).resolve(), root, a.retry_entrypoint)
        if a.env_out:
            with open(a.env_out, "a", encoding="utf-8") as fh:
                fh.writelines(f"{k}={v}\n" for k, v in sorted(env.items()))
        print(f"PINNED_INPUTS materialized={len(env)} refused={len(refused)}")
        return 0
    manifest_path = Path(a.manifest)
    try:
        if a.command == "materialize":
            record = materialize(manifest_path, a.pin, Path(a.dest).resolve(), a.source, a.retry_entrypoint)
            print(f"ALLOW pin={a.pin} commit={record['commit']} files={record['files_verified']} root={record['root']}")
        elif a.command == "verify":
            record = verify(manifest_path, a.pin, Path(a.root).resolve(), a.retry_entrypoint)
            print(f"ALLOW pin={a.pin} commit={record['commit']} files={record['files_verified']}")
        elif a.command == "env":
            for k, v in exports(manifest_path, a.pin, Path(a.root).resolve()).items():
                print(f"{k}={v}")
        else:
            base = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
            text = json.dumps(author_pin(manifest_path, a.pin, Path(a.repo), a.commit, a.module, base,
                                             a.requires, a.note),
                              indent=1, sort_keys=True) + "\n"
            manifest_path.write_text(text, encoding="utf-8")
            print(f"pinned {a.pin} sha256={hashlib.sha256(text.encode()).hexdigest()}")
    except PinRefused as exc:
        print(json.dumps(exc.record, indent=2, sort_keys=True))
        print(f"FAIL_CLOSED {exc.record['failure_code']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
