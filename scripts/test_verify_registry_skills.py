import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("verify_registry_skills.py")
SPEC = importlib.util.spec_from_file_location("verify_registry_skills", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class VerifyRegistrySkillsTests(unittest.TestCase):
    def capability(self, root: Path, name: str, category: str, status: str, stars: int | None = None) -> dict:
        package = root / "skills" / category / name
        package.mkdir(parents=True)
        (package / "SKILL.md").write_text(f"---\nname: {name}\ndescription: test {name}\n---\n")
        files = MODULE.package_files(package)
        digest = MODULE.content_digest(package, files)
        release = "sha256:" + (f"{len(list(root.rglob('SKILL.md'))):064x}"[-64:])
        commit = "a" * 40
        source_path = package.relative_to(root).as_posix()
        return {
            "category": category,
            "contentDigest": digest,
            "localPath": source_path,
            "name": name,
            "packageId": f"github:owner/repo:{source_path}",
            "releaseId": release,
            "sourceCommit": commit,
            "sourcePath": source_path,
            "sourceRepository": "owner/repo",
            "sourceStars": stars,
            "sourceUrl": f"https://github.com/owner/repo/tree/{commit}/{source_path}",
            "staticScanStatus": "passed",
            "status": status,
        }

    def test_balances_categories_and_prioritizes_direct(self):
        items = [
            {"category": "design", "name": "third", "packageId": "3", "releaseId": "3", "status": "extracted", "staticScanStatus": "passed", "sourceStars": 999},
            {"category": "design", "name": "direct", "packageId": "1", "releaseId": "1", "status": "direct", "staticScanStatus": "passed", "sourceStars": None},
            {"category": "research", "name": "research", "packageId": "2", "releaseId": "2", "status": "direct", "staticScanStatus": "passed", "sourceStars": None},
        ]
        selected = MODULE.select_candidates({"capabilities": items}, set(), 3)
        self.assertEqual([item["name"] for item in selected], ["direct", "research", "third"])

    def test_creates_reproducible_pass_record_without_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capability = self.capability(root, "safe-one", "design", "direct")
            record = MODULE.verify_capability(
                root,
                capability,
                run_id="test:1",
                recorded_at="2026-08-17T00:00:00Z",
                signature="test:signature",
            )
            self.assertEqual(record["status"], "passed")
            self.assertEqual(record["metrics"]["commandsExecuted"], 0)
            self.assertEqual(record["metrics"]["networkRequests"], 0)
            self.assertFalse(record["environment"]["sourceCodeExecution"])
            self.assertEqual(MODULE.validate_record(record), [])

    def test_digest_mismatch_is_recorded_as_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            capability = self.capability(root, "changed", "research", "extracted", 900)
            capability["contentDigest"] = "sha256:" + "f" * 64
            record = MODULE.verify_capability(
                root,
                capability,
                run_id="test:2",
                recorded_at="2026-08-17T00:00:00Z",
                signature="test:signature",
            )
            self.assertEqual(record["status"], "failed")
            self.assertEqual(next(item for item in record["checks"] if item["name"] == "content-digest")["status"], "failed")

    def test_run_never_rewrites_existing_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.capability(root, "first", "design", "direct")
            second = self.capability(root, "second", "research", "direct")
            (root / "registry" / "v1").mkdir(parents=True)
            (root / "registry" / "v1" / "index.json").write_text(json.dumps({"capabilities": [first, second]}))
            path = MODULE.verification_path(root, first["releaseId"])
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"releaseId": first["releaseId"]}))
            records = MODULE.run(
                root,
                limit=5,
                run_id="test:3",
                recorded_at="2026-08-17T00:00:00Z",
                signature="test:signature",
            )
            self.assertEqual([record["releaseId"] for record in records], [second["releaseId"]])


if __name__ == "__main__":
    unittest.main()
