import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("update_skill_ranking.py")
SPEC = importlib.util.spec_from_file_location("update_skill_ranking", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class RankingTests(unittest.TestCase):
    def test_update_refreshes_existing_and_indexes_new_sources(self):
        class FakeAPI:
            def refresh_existing(self, repositories):
                self.asserted_repositories = repositories
                return {
                    "owner/existing": {
                        "nameWithOwner": "owner/existing",
                        "url": "https://github.com/owner/existing",
                        "description": "Existing reviewed skill",
                        "isArchived": False,
                        "stargazerCount": 800,
                        "defaultBranchRef": {"name": "main"},
                        "licenseInfo": {"spdxId": "MIT"},
                    }
                }

            def discover(self, minimum_stars):
                self.asserted_minimum = minimum_stars
                return {
                    "owner/existing": {
                        "full_name": "owner/existing",
                        "html_url": "https://github.com/owner/existing",
                        "description": "Existing reviewed skill",
                        "archived": False,
                        "stargazers_count": 800,
                        "default_branch": "main",
                        "license": {"spdx_id": "MIT"},
                    },
                    "owner/new": {
                        "full_name": "owner/new",
                        "html_url": "https://github.com/owner/new",
                        "description": "New agent skills",
                        "archived": False,
                        "stargazers_count": 1200,
                        "default_branch": "main",
                        "license": {"spdx_id": "Apache-2.0"},
                    },
                }

            def skill_files(self, repository, branch):
                self.asserted_skill_check = (repository, branch)
                return 2, False

        current = {
            "directSkillCount": 5,
            "repositories": [
                {
                    "repository": "owner/existing",
                    "stars": 700,
                    "url": "https://github.com/owner/existing",
                    "description": "Old description",
                    "defaultBranch": "main",
                    "license": "MIT",
                    "skillFileCount": 1,
                    "status": "selected-import",
                    "reason": "reviewed",
                }
            ],
        }
        api = FakeAPI()

        updated = MODULE.update_index(current, api, 300)

        self.assertEqual([item["repository"] for item in updated["repositories"]], ["owner/new", "owner/existing"])
        self.assertEqual([item["rank"] for item in updated["repositories"]], [1, 2])
        self.assertEqual(updated["repositories"][0]["status"], "index-only")
        self.assertEqual(updated["repositories"][1]["status"], "selected-import")
        self.assertEqual(updated["newlyDiscoveredCount"], 1)
        self.assertEqual(updated["directSkillCount"], 5)

    def test_new_source_is_never_directly_installable(self):
        source = MODULE.new_source(
            {
                "full_name": "owner/skill",
                "html_url": "https://github.com/owner/skill",
                "description": "Agent skills",
                "license": {"spdx_id": "MIT"},
            },
            900,
            "main",
            3,
            False,
        )
        self.assertEqual(source["status"], "index-only")
        self.assertEqual(source["reason"], "awaiting-manual-review")

    def test_existing_review_state_is_preserved(self):
        old = {
            "repository": "owner/skill",
            "stars": 500,
            "status": "selected-import",
            "reason": "reviewed",
            "url": "https://github.com/owner/skill",
            "defaultBranch": "main",
        }
        merged = MODULE.merge_existing(
            old,
            {
                "nameWithOwner": "owner/skill",
                "url": "https://github.com/owner/skill",
                "stargazerCount": 700,
                "defaultBranchRef": {"name": "main"},
                "licenseInfo": {"spdxId": "MIT"},
            },
            700,
        )
        self.assertEqual(merged["status"], "selected-import")
        self.assertEqual(merged["stars"], 700)

    def test_ranking_uses_visible_rank_numbers(self):
        text = MODULE.render_ranking(
            {
                "snapshotDate": "2026-08-15",
                "repositoryCount": 1,
                "minimumStarsExclusive": 300,
                "repositoriesWithSkillFiles": 1,
                "repositories": [
                    {
                        "rank": 1,
                        "repository": "owner/skill",
                        "url": "https://github.com/owner/skill",
                        "stars": 1234,
                        "license": "MIT",
                        "skillFileCount": 1,
                        "status": "index-only",
                        "reason": "awaiting-manual-review",
                    }
                ],
            }
        )
        self.assertIn("| 1 |", text)
        self.assertIn("1,234", text)


if __name__ == "__main__":
    unittest.main()
