import copy
import importlib.util
import json
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check_verification_auto_merge.py")
SPEC = importlib.util.spec_from_file_location("check_verification_auto_merge", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class CheckVerificationAutoMergeTests(unittest.TestCase):
    def test_normalized_index_ignores_only_verification_fields(self):
        base = {
            "inputDigests": {"catalog": "a", "communitySkills": "b"},
            "capabilities": [{"releaseId": "one", "name": "skill"}],
        }
        candidate = copy.deepcopy(base)
        candidate["inputDigests"]["verifications"] = "digest"
        candidate["capabilities"][0]["verification"] = {"status": "passed"}
        candidate["capabilities"][0]["verificationFile"] = "verifications/one.json"
        self.assertEqual(MODULE.normalized_index(base), MODULE.normalized_index(candidate))

    def test_normalized_index_preserves_capability_changes(self):
        base = {"capabilities": [{"releaseId": "one", "name": "skill"}]}
        candidate = copy.deepcopy(base)
        candidate["capabilities"][0]["name"] = "changed"
        self.assertNotEqual(MODULE.normalized_index(base), MODULE.normalized_index(candidate))


if __name__ == "__main__":
    unittest.main()
