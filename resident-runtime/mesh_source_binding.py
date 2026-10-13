#!/usr/bin/env python3
"""Bind an emitting organization's mesh locator to a fetchable, anonymous source.

The locator is supplied, never inferred. Action is by manifest: a decision
request committed under `.stegverse/governance-decision-requests/` declares it,
and the push that lands that request starts the run (`resolve_mesh_root`). A
dispatched locator is still accepted unchanged. The only accepted form is

    git+https://github.com/<owner>/<repo>#refs/<name>

A public GitHub repository and a fully qualified ref. Anything else -- another
host, another scheme, an unqualified ref, a ref git itself would refuse -- is a
malformed locator. A well-formed locator whose ref cannot be listed without
credentials is not a source this organization can read, and is refused too.
Every refusal is a six-field FAIL_CLOSED.

Stdlib only. Nothing here grants authority.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

OWNING_GOAL = "SDK-MR-A-VALIDATION-CUSTODY-001"
RETRY_ENTRYPOINT = ".github/workflows/organization-governance-decision.yml"
LOCATOR_FORM = "git+https://github.com/<owner>/<repo>#refs/<name>"

_LOCATOR = re.compile(
    r"^git\+https://github\.com/"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)/"
    r"(?P<repo>[A-Za-z0-9._-]{1,100})"
    r"#(?P<ref>refs/\S+)$")
_REF_FORBIDDEN = re.compile(r"[\x00-\x20\x7f~^:?*\[\\]")


class MeshSourceRefused(ValueError):
    """A locator or source this organization will not read."""

    def __init__(self, failure_code: str, failed_predicate: str, required: str):
        super().__init__(failure_code + ": " + failed_predicate)
        self.failure_code = failure_code
        self.failed_predicate = failed_predicate
        self.required = required


def fail_closed(failure_code: str, failed_predicate: str, required: str, *,
                retry_entrypoint: str = RETRY_ENTRYPOINT, owning_goal: str = OWNING_GOAL,
                next_attempt: str | None = None) -> dict[str, Any]:
    """The six-field refusal every step of this binding emits."""
    return {"disposition": "FAIL_CLOSED",
            "failure_code": failure_code,
            "failed_predicate": failed_predicate,
            "required_evidence_or_repair": required,
            "retry_entrypoint": retry_entrypoint,
            "owning_existing_goal": owning_goal,
            "next_attempt": next_attempt or ("re-dispatch " + retry_entrypoint
                                             + " once the required evidence or repair is in place")}


def _valid_ref(ref: str) -> bool:
    """The subset of git check-ref-format a qualified mesh ref must satisfy."""
    if not ref.startswith("refs/") or ref.endswith("/") or ref.endswith("."):
        return False
    if ".." in ref or "@{" in ref or "//" in ref or _REF_FORBIDDEN.search(ref):
        return False
    components = ref.split("/")
    if len(components) < 2:
        return False
    return all(part and not part.startswith(".") and not part.endswith(".lock")
               for part in components)


def parse_mesh_root(locator: Any) -> dict[str, Any]:
    """The source a locator names, or MeshSourceRefused."""
    if not isinstance(locator, str) or not locator.strip():
        raise MeshSourceRefused("MESH_ROOT_LOCATOR_MALFORMED", "mesh_root_absent",
                                "supply mesh_root as " + LOCATOR_FORM)
    match = _LOCATOR.match(locator.strip())
    if match is None:
        if not locator.startswith("git+https://github.com/"):
            raise MeshSourceRefused("MESH_ROOT_SOURCE_NOT_GITHUB",
                                    "mesh_root_not_a_github_https_source:" + locator[:200],
                                    "supply mesh_root as " + LOCATOR_FORM)
        if "#" in locator and not locator.split("#", 1)[1].startswith("refs/"):
            raise MeshSourceRefused("MESH_ROOT_REF_NOT_QUALIFIED",
                                    "mesh_root_ref_not_qualified:" + locator.split("#", 1)[1][:200],
                                    "name the ref in full, beginning refs/")
        raise MeshSourceRefused("MESH_ROOT_LOCATOR_MALFORMED",
                                "mesh_root_locator_malformed:" + locator[:200],
                                "supply mesh_root as " + LOCATOR_FORM)
    owner, repo, ref = match.group("owner"), match.group("repo"), match.group("ref")
    if repo.endswith(".git"):
        repo = repo[:-4]
    if repo in {"", ".", ".."}:
        raise MeshSourceRefused("MESH_ROOT_LOCATOR_MALFORMED", "mesh_root_repository_invalid:" + repo,
                                "supply mesh_root as " + LOCATOR_FORM)
    if not _valid_ref(ref):
        raise MeshSourceRefused("MESH_ROOT_REF_NOT_QUALIFIED", "mesh_root_ref_invalid:" + ref[:200],
                                "name a valid fully qualified ref, beginning refs/")
    return {"locator": locator.strip(), "owner": owner, "repository": owner + "/" + repo,
            "url": "https://github.com/" + owner + "/" + repo, "ref": ref,
            "emitting_organization": owner}


def anonymous_git_env() -> dict[str, str]:
    """An environment in which git can use no credential and prompt for none."""
    env = dict(os.environ)
    env.update(GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/false", SSH_ASKPASS="/bin/false",
               GCM_INTERACTIVE="never")
    return env


def anonymous_git(*args: str, git_dir: Path | None = None,
                  runner: Callable[..., Any] = subprocess.run) -> Any:
    """Run git with every credential helper cleared."""
    command = ["git", "-c", "credential.helper=", "-c", "core.askPass="]
    if git_dir is not None:
        command += ["--git-dir", str(git_dir)]
    return runner(command + list(args), capture_output=True, text=True,
                  env=anonymous_git_env(), check=False)


def probe_anonymous(url: str, ref: str, *, runner: Callable[..., Any] = subprocess.run) -> str:
    """The ref's tip as an anonymous reader sees it, or MeshSourceRefused."""
    completed = anonymous_git("ls-remote", "--refs", url, ref, runner=runner)
    if completed.returncode != 0:
        raise MeshSourceRefused("MESH_ROOT_SOURCE_NOT_ANONYMOUSLY_FETCHABLE",
                                "ls_remote_failed:" + (completed.stderr or "").strip()[-300:],
                                "make " + url + " readable without credentials, or supply a public source")
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == ref and re.fullmatch(r"[0-9a-f]{40,64}", parts[0]):
            return parts[0]
    raise MeshSourceRefused("MESH_ROOT_REF_ABSENT", "mesh_root_ref_not_published:" + url + "#" + ref,
                            "publish " + ref + " on " + url + " before dispatching")


def bind(locator: str, *, probe: bool = True,
         runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    binding = parse_mesh_root(locator)
    binding["source_tip"] = probe_anonymous(binding["url"], binding["ref"], runner=runner) if probe else None
    binding["anonymous"] = True
    binding["authority_effect"] = "NONE_BINDING_ONLY"
    return binding


DECISION_REQUEST_DIR = ".stegverse/governance-decision-requests/"
DECISION_REQUEST_SCHEMA = "stegverse.organization-governance-decision-request/v1"


def resolve_mesh_root(dispatch_mesh_root: str, changed_paths: list[str]) -> dict[str, Any]:
    """The emitting organization's locator for one run: dispatched, or declared by one committed request.

    Only resolution: the locator still goes through `bind`. A refusal is six-field.
    """
    entrypoint = RETRY_ENTRYPOINT + " (push: " + DECISION_REQUEST_DIR + "*.json)"
    if dispatch_mesh_root:
        locator, source = dispatch_mesh_root, "WORKFLOW_DISPATCH"
    else:
        requests = [p for p in changed_paths if p.startswith(DECISION_REQUEST_DIR) and p.endswith(".json")]
        if len(requests) != 1:
            return {**fail_closed("DECISION_REQUEST_NOT_SINGULAR", "ONE_COMMITTED_DECISION_REQUEST_PER_RUN",
                                  "commit exactly one governance decision request per push",
                                  retry_entrypoint=entrypoint, next_attempt="commit each decision request on its own"),
                    "requests": requests}
        try:
            request = json.loads(Path(requests[0]).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            request = None
        if (not isinstance(request, dict) or request.get("schema") != DECISION_REQUEST_SCHEMA
                or not request.get("owning_existing_goal")):
            return fail_closed("DECISION_REQUEST_SCHEMA_INVALID", "COMMITTED_DECISION_REQUEST_SCHEMA",
                               "declare schema " + DECISION_REQUEST_SCHEMA + ", owning_existing_goal and mesh_root",
                               retry_entrypoint=entrypoint, next_attempt="commit a corrected successor request")
        locator, source = request.get("mesh_root"), "COMMITTED_DECISION_REQUEST:" + requests[0]
    # The value is written to GITHUB_ENV; one printable line only.
    if not isinstance(locator, str) or not locator or not all(32 <= ord(c) <= 126 for c in locator):
        return fail_closed("DECISION_MESH_ROOT_INVALID", "DECLARED_MESH_ROOT_IS_A_PRINTABLE_LOCATOR",
                           "declare mesh_root as " + LOCATOR_FORM, retry_entrypoint=entrypoint,
                           next_attempt="commit a corrected successor request")
    return {"disposition": "ALLOW", "mesh_root": locator, "source": source,
            "authority_effect": "NONE_INPUT_RESOLUTION_ONLY"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mesh-root", default="")
    parser.add_argument("--resolve-changed", type=Path,
                        help="resolve the locator from the committed decision request this push changed")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--no-probe", action="store_true")
    args = parser.parse_args(argv)
    if args.resolve_changed is not None:
        changed = [line for line in args.resolve_changed.read_text(encoding="utf-8").splitlines() if line]
        document = resolve_mesh_root(args.mesh_root, changed)
        sys.stdout.write(json.dumps(document, sort_keys=True) + "\n")
        return 0 if document["disposition"] == "ALLOW" else 1
    if not args.mesh_root:
        parser.error("--mesh-root is required")
    try:
        document = bind(args.mesh_root, probe=not args.no_probe)
        status = 0
    except MeshSourceRefused as exc:
        document = fail_closed(exc.failure_code, exc.failed_predicate, exc.required)
        status = 1
    text = json.dumps(document, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return status


if __name__ == "__main__":
    sys.exit(main())
