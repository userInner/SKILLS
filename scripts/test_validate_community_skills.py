import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("validate_community_skills.py")
SPEC = importlib.util.spec_from_file_location("validate_community_skills", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ValidateCommunitySkillsTests(unittest.TestCase):
    def test_valid_direct_and_candidate_packages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            direct = root / "skills" / "workflow" / "direct-one"
            direct.mkdir(parents=True)
            (direct / "SKILL.md").write_text("# direct")
            candidate = root / "community-skills" / "workflow" / "candidate-one"
            candidate.mkdir(parents=True)
            (candidate / "SKILL.md").write_text("# candidate")
            (candidate / "LICENSE").write_text("MIT")
            (candidate / "NOTICE.effecta").write_text("source")
            manifest = {
                "name": "candidate-one",
                "category": "workflow",
                "status": "extracted",
                "contentDigest": "sha256:abc",
                "staticScan": {"findings": []},
            }
            (candidate / "effecta.manifest.json").write_text(json.dumps(manifest))
            index = {
                "concreteSkillCount": 2,
                "directSkillCount": 1,
                "extractedSkillCount": 1,
                "needsReviewCount": 0,
                "skills": [
                    {"name": "direct-one", "status": "direct", "localPath": "skills/workflow/direct-one"},
                    {**manifest, "localPath": "community-skills/workflow/candidate-one"},
                ],
            }
            (root / "community-skills" / "index.json").write_text(json.dumps(index))

            self.assertEqual(MODULE.validate(root), [])

    def test_rejects_candidate_missing_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "community-skills" / "workflow" / "bad"
            candidate.mkdir(parents=True)
            (candidate / "SKILL.md").write_text("# bad")
            index = {
                "concreteSkillCount": 1,
                "directSkillCount": 0,
                "extractedSkillCount": 1,
                "needsReviewCount": 0,
                "skills": [
                    {
                        "name": "bad",
                        "status": "extracted",
                        "localPath": "community-skills/workflow/bad",
                    }
                ],
            }
            (root / "community-skills" / "index.json").write_text(json.dumps(index))

            errors = MODULE.validate(root)
            self.assertTrue(any("missing LICENSE" in error for error in errors))
            self.assertTrue(any("missing effecta.manifest.json" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
