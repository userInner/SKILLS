import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("check_registry_auto_merge.py")
SPEC = importlib.util.spec_from_file_location("check_registry_auto_merge", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


def source(name="owner/skill", **updates):
    item = {
        "repository": name,
        "stars": 500,
        "status": "index-only",
        "reason": "awaiting-manual-review",
        "skillFileCount": 1,
        "kind": "standalone-skill",
        "qualification": "contains-skill-file",
    }
    item.update(updates)
    return item


def catalog(items, **updates):
    value = {
        "minimumStarsExclusive": 300,
        "sort": "githubStarsDescending",
        "repositoryCount": len(items),
        "repositoriesWithSkillFiles": sum(item["skillFileCount"] > 0 for item in items),
        "newlyDiscoveredCount": 0,
        "directSkillCount": 40,
        "removedRepositories": [],
        "repositories": items,
    }
    value.update(updates)
    return value


def registry(stars=500, **updates):
    value = {
        "apiVersion": "effecta.dev/v1",
        "kind": "CapabilityIndex",
        "generatorVersion": "1.0",
        "counts": {"total": 1, "direct": 1, "extracted": 0, "needs-review": 0},
        "inputDigests": {"catalog": "sha256:old", "communitySkills": "sha256:skills"},
        "capabilities": [
            {
                "packageId": "local:skill",
                "releaseId": "sha256:release",
                "contentDigest": "sha256:content",
                "sourceRank": 1,
                "sourceStars": stars,
            }
        ],
    }
    value.update(updates)
    return value


class AutoMergeTests(unittest.TestCase):
    def classify(self, before_catalog, after_catalog, before_registry=None, after_registry=None, files=None):
        return MODULE.classify_candidate(
            before_catalog,
            after_catalog,
            before_registry or registry(),
            after_registry or registry(stars=600),
            files or {"catalog.json", "RANKING.md", "registry/v1/index.json"},
        )

    def test_allows_observation_only_refresh(self):
        before = catalog([source()])
        after = catalog([source(stars=600)])

        self.assertEqual(self.classify(before, after), [])

    def test_allows_new_index_only_source(self):
        before = catalog([source()])
        after = catalog(
            [source(), source("owner/new", stars=900)],
            repositoryCount=2,
            repositoriesWithSkillFiles=2,
            newlyDiscoveredCount=1,
        )

        self.assertEqual(self.classify(before, after), [])

    def test_rejects_new_installable_source(self):
        before = catalog([source()])
        after = catalog(
            [source(), source("owner/new", status="selected-import")],
            repositoryCount=2,
            repositoriesWithSkillFiles=2,
            newlyDiscoveredCount=1,
        )

        self.assertIn("new repository is not index-only: owner/new", self.classify(before, after))

    def test_allows_candidate_branch_additions_from_an_earlier_run(self):
        before = catalog([source()])
        after = catalog(
            [source(), source("owner/new", stars=900)],
            repositoryCount=2,
            repositoriesWithSkillFiles=2,
            newlyDiscoveredCount=0,
        )

        self.assertEqual(self.classify(before, after), [])

    def test_allows_audited_archived_removal(self):
        before = catalog([source()])
        after = catalog(
            [],
            repositoryCount=0,
            repositoriesWithSkillFiles=0,
            removedRepositories=[
                {
                    "repository": "owner/skill",
                    "reason": "archived",
                    "previousStars": 500,
                    "observedStars": 500,
                }
            ],
        )

        self.assertEqual(self.classify(before, after), [])

    def test_rejects_unaudited_removal(self):
        before = catalog([source()])
        after = catalog([], repositoryCount=0, repositoriesWithSkillFiles=0)

        self.assertIn("removal audit does not match removed repositories", self.classify(before, after))

    def test_rejects_trusted_status_change(self):
        before = catalog([source(status="selected-import")])
        after = catalog([source(status="index-only")])

        self.assertIn("trusted field changed for owner/skill: status", self.classify(before, after))

    def test_rejects_concrete_skill_change(self):
        before = catalog([source()])
        after = catalog([source(stars=600)])
        changed_registry = registry()
        changed_registry["inputDigests"]["communitySkills"] = "sha256:changed"

        self.assertIn("concrete Skill digest changed", self.classify(before, after, after_registry=changed_registry))

    def test_rejects_unexpected_file(self):
        before = catalog([source()])
        after = catalog([source(stars=600)])

        self.assertIn(
            "unexpected files changed: skills/design/example/SKILL.md",
            self.classify(before, after, files={"catalog.json", "skills/design/example/SKILL.md"}),
        )


if __name__ == "__main__":
    unittest.main()
