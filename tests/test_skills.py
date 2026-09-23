"""Validate all SKILL.md files against skill-creator spec."""

import re

import pytest
from conftest import parse_frontmatter

NAME_RE = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")
BANNED_WORDS = ["anthropic", "claude"]
VALID_TOOLS = {
    "Read",
    "Write",
    "Edit",
    "Bash",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
    "Task",
    "NotebookEdit",
    "AskUserQuestion",
    "Skill",
    "TodoWrite",
}


class TestSkillFrontmatter:
    def test_skills_exist(self, all_skill_files):
        """At least one SKILL.md should exist once skills are created."""
        # This will pass even with 0 skills during initial setup
        assert isinstance(all_skill_files, list)

    def test_frontmatter_present(self, all_skill_files):
        for sf in all_skill_files:
            fm = parse_frontmatter(sf)
            assert fm, f"{sf}: Missing or invalid YAML frontmatter"

    def test_name_required(self, all_skill_files):
        for sf in all_skill_files:
            fm = parse_frontmatter(sf)
            if not fm:
                continue
            assert "name" in fm, f"{sf}: Missing 'name' field"

    def test_name_format(self, all_skill_files):
        for sf in all_skill_files:
            fm = parse_frontmatter(sf)
            if not fm or "name" not in fm:
                continue
            name = fm["name"]
            assert NAME_RE.match(name), f"{sf}: Invalid name '{name}' (must be kebab-case)"
            assert len(name) <= 64, f"{sf}: Name exceeds 64 chars ({len(name)})"
            for word in BANNED_WORDS:
                assert word not in name.lower(), f"{sf}: Name cannot contain '{word}'"

    def test_description_required(self, all_skill_files):
        for sf in all_skill_files:
            fm = parse_frontmatter(sf)
            if not fm:
                continue
            assert "description" in fm, f"{sf}: Missing 'description' field"

    def test_description_length(self, all_skill_files):
        for sf in all_skill_files:
            fm = parse_frontmatter(sf)
            if not fm or "description" not in fm:
                continue
            desc = str(fm["description"]).strip()
            assert len(desc) <= 200, f"{sf}: Description exceeds 200 chars ({len(desc)})"

    def test_description_third_person(self, all_skill_files):
        for sf in all_skill_files:
            fm = parse_frontmatter(sf)
            if not fm or "description" not in fm:
                continue
            desc = str(fm["description"]).strip()
            assert not re.match(r"^(I |I'|You )", desc, re.IGNORECASE), (
                f"{sf}: Description must be third person (no I/you)"
            )


class TestSkillBody:
    def test_no_absolute_paths(self, all_skill_files):
        for sf in all_skill_files:
            content = sf.read_text()
            # Skip code blocks for this check
            lines = content.split("\n")
            in_code = False
            for i, line in enumerate(lines, 1):
                if line.strip().startswith("```"):
                    in_code = not in_code
                    continue
                if in_code:
                    continue
                assert not re.search(r"/home/|/Users/|C:\\", line), (
                    f"{sf}:{i}: Absolute path found (use {{baseDir}}/)"
                )

    def test_basedir_refs_pattern(self, all_skill_files):
        """Ensure {baseDir} is used correctly (no escapes)."""
        for sf in all_skill_files:
            content = sf.read_text()
            assert "{baseDir}/../" not in content, f"{sf}: Path escape detected ({'{baseDir}/../'})"

    def test_line_count_warning(self, all_skill_files):
        """Flag skills over 500 lines — consider moving code to scripts/."""
        over_limit = []
        for sf in all_skill_files:
            lines = len(sf.read_text().split("\n"))
            if lines > 500:
                over_limit.append(f"{sf.parent.name}: {lines} lines")
        if over_limit:
            pytest.skip(
                f"Advisory: {len(over_limit)} skill(s) over 500 lines: {', '.join(over_limit)}"
            )
