#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location("demo_install", Path(__file__).with_name("demo_install.py"))
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DemoInstallTests(unittest.TestCase):
    def make_skill(self, root: Path, name: str = "demo-skill") -> Path:
        skill = root / "skills" / "workflow" / name
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Reproducible demo Skill\n---\n\n# Demo\n",
            encoding="utf-8",
        )
        (skill / "reference.md").write_text("evidence\n", encoding="utf-8")
        return skill

    def test_discovers_and_installs_verified_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_skill(root)
            skills = MODULE.discover_skills(root)
            self.assertEqual(skills, {"demo-skill": source})

            destination, digest, file_count = MODULE.install_skill(source, root / "target")
            self.assertEqual(destination.name, "demo-skill")
            self.assertEqual(file_count, 2)
            self.assertEqual(MODULE.directory_digest(destination), (digest, file_count))

    def test_refuses_to_overwrite_existing_install(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_skill(root)
            target = root / "target"
            MODULE.install_skill(source, target)
            with self.assertRaises(FileExistsError):
                MODULE.install_skill(source, target)

    def test_rejects_incomplete_frontmatter(self):
        with tempfile.TemporaryDirectory() as directory:
            skill_file = Path(directory) / "SKILL.md"
            skill_file.write_text("# Missing metadata\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                MODULE.parse_frontmatter(skill_file)


if __name__ == "__main__":
    unittest.main()
