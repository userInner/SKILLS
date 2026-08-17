import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_registry_v1.py")
SPEC = importlib.util.spec_from_file_location("build_registry_v1", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


COMMIT = "1" * 40
SOURCE_COMMIT = "2" * 40


class BuildRegistryV1Tests(unittest.TestCase):
    def fixture(self, root: Path) -> None:
        direct = root / "skills" / "workflow" / "direct-one"
        direct.mkdir(parents=True)
        (direct / "SKILL.md").write_text("---\nname: direct-one\ndescription: direct\n---\n")

        candidate = root / "community-skills" / "engineering" / "candidate-one"
        candidate.mkdir(parents=True)
        (candidate / "SKILL.md").write_text("---\nname: candidate-one\ndescription: candidate\n---\n")
        candidate_files = MODULE.package_files(candidate)
        candidate_digest = MODULE.content_digest(candidate, candidate_files)

        catalog = {
            "snapshotDate": "2026-08-16",
            "minimumStarsExclusive": 300,
            "repositories": [
                {
                    "repository": "owner/repo",
                    "rank": 1,
                    "stars": 1000,
                    "license": "MIT",
                    "url": "https://github.com/owner/repo",
                    "description": "source",
                    "defaultBranch": "main",
                    "skillFileCount": 1,
                    "kind": "standalone-skill",
                    "qualification": "contains-skill-file",
                    "status": "selected-import",
                }
            ],
        }
        (root / "catalog.json").write_text(json.dumps(catalog))
        index = {
            "skills": [
                {
                    "name": "direct-one",
                    "category": "workflow",
                    "description": "direct",
                    "sourceRepository": "userInner/SKILLS",
                    "sourcePath": "skills/workflow/direct-one",
                    "sourceCommit": "local-reviewed",
                    "sourceRank": None,
                    "sourceStars": None,
                    "license": "see-package",
                    "status": "direct",
                    "staticScan": {"status": "passed", "findings": []},
                    "localPath": "skills/workflow/direct-one",
                },
                {
                    "name": "candidate-one",
                    "category": "engineering",
                    "description": "candidate",
                    "sourceRepository": "owner/repo",
                    "sourcePath": "skills/candidate-one",
                    "sourceCommit": SOURCE_COMMIT,
                    "sourceRank": 1,
                    "sourceStars": 1000,
                    "license": "MIT",
                    "contentDigest": candidate_digest,
                    "fileCount": 1,
                    "totalBytes": (candidate / "SKILL.md").stat().st_size,
                    "status": "extracted",
                    "staticScan": {"status": "passed", "findings": []},
                    "localPath": "community-skills/engineering/candidate-one",
                },
            ]
        }
        (root / "community-skills" / "index.json").write_text(json.dumps(index))

    def test_builds_stable_package_and_release_objects(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            output = root / "registry" / "v1"

            index = MODULE.write_registry(root, output, direct_commit=COMMIT)

            self.assertEqual(index["counts"], {"direct": 1, "extracted": 1, "needs-review": 0, "total": 2})
            self.assertEqual(len(list((output / "packages").glob("*.json"))), 2)
            self.assertEqual(len(list((output / "releases").glob("*.json"))), 2)
            for item in index["capabilities"]:
                package = json.loads((output / item["packageFile"]).read_text())
                release = json.loads((output / item["releaseFile"]).read_text())
                self.assertEqual(package["id"], item["packageId"])
                self.assertEqual(release["releaseId"], item["releaseId"])
                self.assertEqual(release["packageId"], package["id"])
                self.assertEqual(item["sourceCommit"], release["source"]["commit"])
                self.assertEqual(item["sourceUrl"], release["source"]["url"])

    def test_same_input_generates_identical_tree(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            first = root / "registry" / "first"
            second = root / "registry" / "second"

            MODULE.write_registry(root, first, direct_commit=COMMIT)
            MODULE.write_registry(root, second, direct_commit=COMMIT)

            self.assertEqual(MODULE.directory_snapshot(first), MODULE.directory_snapshot(second))

    def test_source_observations_keep_first_duplicate(self):
        catalog = {
            "snapshotDate": "2026-08-16",
            "repositories": [
                {"repository": "Owner/Repo", "rank": 1, "stars": 1000},
                {"repository": "owner/repo", "rank": 2, "stars": 900},
            ],
        }

        observations = MODULE.build_source_observations(catalog)["observations"]

        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["repository"], "Owner/Repo")
        self.assertEqual(observations[0]["stars"], 1000)

    def test_direct_content_change_creates_new_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            first = root / "registry" / "first"
            second = root / "registry" / "second"
            initial = MODULE.write_registry(root, first, direct_commit=COMMIT)
            initial_release = next(item["releaseId"] for item in initial["capabilities"] if item["status"] == "direct")

            with (root / "skills" / "workflow" / "direct-one" / "SKILL.md").open("a") as skill:
                skill.write("changed\n")
            updated = MODULE.write_registry(root, second, direct_commit=COMMIT)
            updated_release = next(item["releaseId"] for item in updated["capabilities"] if item["status"] == "direct")

            self.assertNotEqual(initial_release, updated_release)

    def test_unrelated_commit_does_not_change_direct_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Registry Test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "registry@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "add", "catalog.json", "community-skills", "skills"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "fixture"], cwd=root, check=True)

            first = root / "registry" / "first"
            second = root / "registry" / "second"
            MODULE.write_registry(root, first)

            unrelated = root / "UNRELATED.md"
            unrelated.write_text("does not change a Skill\n")
            subprocess.run(["git", "add", "UNRELATED.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "unrelated"], cwd=root, check=True)
            MODULE.write_registry(root, second)

            self.assertEqual(MODULE.directory_snapshot(first), MODULE.directory_snapshot(second))

    def test_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            index_path = root / "community-skills" / "index.json"
            index = json.loads(index_path.read_text())
            index["skills"][0]["localPath"] = "../outside"
            index_path.write_text(json.dumps(index))

            with self.assertRaises(MODULE.RegistryError):
                MODULE.write_registry(root, root / "registry" / "v1", direct_commit=COMMIT)


if __name__ == "__main__":
    unittest.main()
