#!/usr/bin/env python3
"""Regenerate the published explanation examples from the committed fixtures.

Deterministic: the same fixtures always produce the same artifacts, so a test can
prove the committed examples have not drifted from the builder. Non-authorizing;
every example is SYNTHETIC_TEST evidence class and says so.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from user_facing_explanation import build_explanation, render_prose, validate_explanation  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "data" / "user-facing-explanation" / "fixtures.d"
EXAMPLES = ROOT / "data" / "user-facing-explanation" / "examples.d"


def render_all() -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for path in sorted(FIXTURES.glob("*.json")):
        fixture = json.loads(path.read_text(encoding="utf-8"))
        artifact = validate_explanation(build_explanation(fixture["outcome"], surface=fixture["surface"]))
        out[path.stem] = {"json": json.dumps(artifact, indent=2, sort_keys=True) + "\n", "txt": render_prose(artifact)}
    return out


def main(argv: list[str] | None = None) -> int:
    check = "--check" in (argv or sys.argv[1:])
    rendered = render_all()
    EXAMPLES.mkdir(parents=True, exist_ok=True)
    drift = []
    for stem, files in rendered.items():
        for ext, content in files.items():
            target = EXAMPLES / (stem + "." + ext)
            if check:
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    drift.append(str(target.relative_to(ROOT)))
            else:
                target.write_text(content, encoding="utf-8")
    if check:
        print("USER_FACING_EXPLANATION_EXAMPLES_" + ("DRIFT " + ",".join(drift) if drift else "PASS"))
        return 1 if drift else 0
    print("USER_FACING_EXPLANATION_EXAMPLES_RENDERED " + str(len(rendered)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
