import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REFRESH_WORKFLOW = WORKFLOWS / "update-skill-ranking.yml"
VALIDATE_WORKFLOW = WORKFLOWS / "validate-community-skills.yml"
LEGACY_EXTRACT_WORKFLOW = WORKFLOWS / "extract-community-skills.yml"


class WorkflowPolicyTests(unittest.TestCase):
    def test_refresh_is_one_candidate_pr_pipeline(self):
        text = REFRESH_WORKFLOW.read_text()
        self.assertIn("automation/skill-registry", text)
        self.assertIn("python3 scripts/update_skill_ranking.py", text)
        self.assertIn("python3 scripts/check_registry_auto_merge.py", text)
        self.assertIn("python3 scripts/extract_community_skills.py", text)
        self.assertIn("python3 scripts/build_registry_v1.py", text)
        self.assertIn("gh pr create", text)
        self.assertIn("gh workflow run validate-community-skills.yml", text)
        self.assertIn("statuses: write", text)
        self.assertIn("statuses/$candidate_sha", text)
        self.assertIn("Independent registry validation passed", text)
        self.assertIn('steps.safety.outputs.eligible == \'true\'', text)
        self.assertIn("gh pr merge", text)
        self.assertNotIn('merge_state="$(gh pr view', text)
        self.assertFalse(LEGACY_EXTRACT_WORKFLOW.exists())

    def test_refresh_never_pushes_to_default_branch(self):
        text = REFRESH_WORKFLOW.read_text()
        self.assertNotIn('HEAD:${{ github.event.repository.default_branch }}', text)
        self.assertNotIn("git push origin master", text)
        self.assertNotIn("git push origin main", text)
        self.assertIn('HEAD:refs/heads/$UPDATE_BRANCH', text)

    def test_pull_request_workflows_are_read_only(self):
        for workflow in WORKFLOWS.glob("*.yml"):
            text = workflow.read_text()
            self.assertNotIn("pull_request_target:", text, workflow.name)
            if "pull_request:" not in text:
                continue
            self.assertIn("permissions:\n  contents: read", text, workflow.name)
            self.assertNotIn("pull-requests: write", text, workflow.name)
            self.assertNotIn("contents: write", text, workflow.name)

    def test_refresh_uses_ephemeral_github_token(self):
        text = REFRESH_WORKFLOW.read_text()
        self.assertIn("${{ github.token }}", text)
        self.assertNotIn("secrets.GITHUB_TOKEN", text)

    def test_external_actions_are_pinned_to_commits(self):
        action_pattern = re.compile(r"uses:\s+[^\s@]+@([^\s#]+)")
        for workflow in WORKFLOWS.glob("*.yml"):
            for reference in action_pattern.findall(workflow.read_text()):
                self.assertRegex(reference, r"^[0-9a-f]{40}$", workflow.name)

    def test_registry_validation_has_full_git_history(self):
        text = VALIDATE_WORKFLOW.read_text()
        self.assertIn("fetch-depth: 0", text)

    def test_registry_validation_supports_trusted_dispatch(self):
        text = VALIDATE_WORKFLOW.read_text()
        self.assertIn("workflow_dispatch:", text)

    def test_auto_merge_guard_rejects_unexpected_files(self):
        text = REFRESH_WORKFLOW.read_text()
        self.assertIn("check_registry_auto_merge.py --base HEAD", text)
        self.assertIn("steps.safety.outputs.eligible == 'true'", text)


if __name__ == "__main__":
    unittest.main()
