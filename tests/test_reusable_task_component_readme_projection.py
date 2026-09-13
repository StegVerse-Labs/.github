import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/project_reusable_task_component_readme.py"
spec = importlib.util.spec_from_file_location("readme_projection", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_projection_inserts_before_existing_reusable_construct_section():
    source = "prefix\n\n### Reusable task ephemeral constructs and entropy recovery\nbody\n"
    projected = module.project(source)
    assert "## Reusable Task Component Model" in projected
    assert projected.index("## Reusable Task Component Model") < projected.index(module.MARKER)
    assert projected.endswith("body\n")


def test_projection_is_idempotent():
    source = "prefix\n\n### Reusable task ephemeral constructs and entropy recovery\nbody\n"
    once = module.project(source)
    twice = module.project(once)
    assert once == twice


def test_projection_fails_closed_without_anchor():
    try:
        module.project("README without canonical anchor\n")
    except ValueError as exc:
        assert "projection marker missing" in str(exc)
    else:
        raise AssertionError("missing README anchor must fail closed")


def test_repository_readme_accepts_projection_without_losing_existing_tail():
    original = (ROOT / "README.md").read_text(encoding="utf-8")
    projected = module.project(original)
    assert len(projected) > len(original)
    assert original.split(module.MARKER, 1)[1] == projected.split(module.MARKER, 1)[1]
    assert projected.count(module.HEADING) == 1
