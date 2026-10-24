"""The six InTr-area files this PR changes are pinned byte-for-byte (V-P11 InTr predicate, 20:16Z).

Each differs from main only by hunks that map to a fix commit of this PR. The
PR body lists every hunk with its commit. The sha256 of each file as mapped is
pinned here with no skip: an edit to any of them fails until its hunk is
mapped again and the pin moved with it, so no unmapped change rides along.

Hunk → commit (new-side lines at the pin):
  org-boundary/registry/services.json            88 e46f536 · 124-125 c49767c
  org-boundary/runtime/capability_ingress.py     92-100, 302-306 21254ad+af88f8c · 111-138, 296, 308-310, 321 af88f8c
  org-boundary/runtime/process_boundary.py       2, 72-75, 77, 81-147, 150, 152-153, 155, 169 e46f536
  resident-runtime/intr_destination_ingress.py   225-228 184750e · 241 (deletion) · 252 e1bec48 · 260-267 e46f536 ·
                                                 356-357 ee8a4e8 · 364-369 67c3e94+ee8a4e8 · 374, 383, 394 67c3e94
  resident-runtime/sdk_manifest_crossing.py      168-182 072a481 (merge of e46f536)+b595d14 · 213-216, 222-224, 226-227 b595d14
  workers/manifest_state_transition_intr_ingress.py  every hunk e46f536 (#3296 slice g, folded in)

Source validation only. No authority effect is claimed.
"""
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PINNED = {
    "org-boundary/registry/services.json": "dc6dd8bed77c569679a5a758f8455633489352f03fb07deadd490690a8cb9a8f",
    "org-boundary/runtime/capability_ingress.py": "4f5eebd4db21bfb6076179180d84b95a636f71f83e1af268fe3b6df0c3b78cbf",
    "org-boundary/runtime/process_boundary.py": "a48a52337e942434dbf82775c547d56b17cd101e9c0e24b4e64793be1ad1d262",
    "resident-runtime/intr_destination_ingress.py": "d01911f41985d6f85830ed860948f487816ba7c7ab5a25268abb1d37dc188210",
    "resident-runtime/sdk_manifest_crossing.py": "072a0bdfd66df1e3449bb5eecb1eb869ea8f941b0b22b4a5e00a4d642f88ce1f",
    "workers/manifest_state_transition_intr_ingress.py": "3acb3cfd21ae47cfe7cf1e86be5ac82e26cf62129a19dcde06a1f5298bf20e94",
}


class IntrPathFilesPinnedTests(unittest.TestCase):
    def test_each_intr_area_file_is_byte_identical_to_its_mapped_pin(self):
        for relative, expected in PINNED.items():
            with self.subTest(file=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), expected)


if __name__ == "__main__":
    unittest.main()
