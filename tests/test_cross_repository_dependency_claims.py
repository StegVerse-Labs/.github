import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("allocate_claims", ROOT / "scripts" / "allocate_claims.py")
allocator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(allocator)


def claim(repo: str, mode: str = "shared_write", dependencies=None, exempt: str | None = None, path: str = "src/app.py") -> dict:
    owner, name = repo.split("/", 1)
    scope = {
        "paths": [path],
        "contracts": [],
        "release_surfaces": [],
        "capabilities": [],
        "workflows": [],
    }
    if dependencies is not None:
        scope["dependency_surfaces"] = dependencies
    if exempt is not None:
        scope["dependency_surface_exempt"] = exempt
    return {
        "repository": {
            "host": "github.com",
            "owner": owner,
            "name": name,
            "full_name": repo,
        },
        "mode": mode,
        "scope": scope,
    }


class CrossRepositoryDependencyClaimTests(unittest.TestCase):
    def test_render_collision_blocks_different_repositories(self):
        site = claim("StegVerse-Labs/Site", dependencies=["hosting:render"])
        core = claim("StegVerse-Labs/StegCore", dependencies=["hosting:render"])
        self.assertTrue(allocator.conflicts(site, core))
        self.assertTrue(allocator.conflicts(core, site))

    def test_dependency_surface_normalization_is_case_insensitive(self):
        left = claim("StegVerse-Labs/Site", dependencies=[" Hosting:Render "])
        right = claim("StegVerse-Labs/StegCore", dependencies=["hosting:render"])
        self.assertTrue(allocator.conflicts(left, right))

    def test_distinct_global_surfaces_remain_parallel(self):
        left = claim("StegVerse-Labs/Site", dependencies=["runtime:steggate-rendezvous"])
        right = claim("StegVerse-Labs/StegCore", dependencies=["schema:steggate-core"])
        self.assertFalse(allocator.conflicts(left, right))

    def test_same_repo_path_collision_is_preserved(self):
        left = claim("StegVerse-Labs/Site", dependencies=["runtime:left"], path="src/shared.py")
        right = claim("StegVerse-Labs/Site", dependencies=["runtime:right"], path="src/shared.py")
        self.assertTrue(allocator.conflicts(left, right))

    def test_shared_read_does_not_take_mutable_dependency_lock(self):
        left = claim("StegVerse-Labs/Site", mode="shared_read", dependencies=["hosting:render"])
        right = claim("StegVerse-Labs/StegCore", mode="shared_read", dependencies=["hosting:render"])
        self.assertFalse(allocator.conflicts(left, right))

    def test_mutable_claim_without_dependency_declaration_fails_admission(self):
        undeclared = claim("StegVerse-Labs/Site", dependencies=None)
        task = {"requirements": {"mandatory": [undeclared]}}
        self.assertFalse(allocator.task_claims_admissible(task))

    def test_explicit_no_global_dependency_exemption_is_admissible(self):
        bounded = claim(
            "StegVerse-Labs/Site",
            dependencies=None,
            exempt="Repository-local documentation mutation; no external/runtime/deployment surface",
        )
        task = {"requirements": {"mandatory": [bounded]}}
        self.assertTrue(allocator.task_claims_admissible(task))


if __name__ == "__main__":
    unittest.main()
