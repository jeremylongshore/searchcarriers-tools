#!/usr/bin/env bash
# SearchCarriers Repo Validator
# Single validator for plugins + skills, aligned with skill-creator rules.
# Usage: ./scripts/validate.sh [--verbose] [--skills-only] [--plugins-only]

set -euo pipefail

VERBOSE=false
SKILLS_ONLY=false
PLUGINS_ONLY=false
ERRORS=0
WARNINGS=0

for arg in "$@"; do
    case $arg in
        --verbose) VERBOSE=true ;;
        --skills-only) SKILLS_ONLY=true ;;
        --plugins-only) PLUGINS_ONLY=true ;;
        *) echo "Unknown arg: $arg"; exit 1 ;;
    esac
done

log() { echo "  $1"; }
pass() { echo "  [PASS] $1"; }
fail() { echo "  [FAIL] $1"; ERRORS=$((ERRORS + 1)); }
warn() { echo "  [WARN] $1"; WARNINGS=$((WARNINGS + 1)); }

# --- SKILL VALIDATION ---
validate_skill() {
    local skill_file="$1"
    local skill_dir
    skill_dir=$(dirname "$skill_file")
    local skill_name
    skill_name=$(basename "$skill_dir")

    $VERBOSE && log "Checking $skill_file" || true

    # Check frontmatter exists
    if ! head -1 "$skill_file" | grep -q "^---$"; then
        fail "$skill_file: Missing YAML frontmatter (must start with ---)"
        return
    fi

    # Extract frontmatter
    local frontmatter
    frontmatter=$(sed -n '/^---$/,/^---$/p' "$skill_file" | sed '1d;$d')

    # Check name field
    local name
    name=$(echo "$frontmatter" | grep "^name:" | head -1 | sed 's/^name: *//')
    if [ -z "$name" ]; then
        fail "$skill_file: Missing 'name' field in frontmatter"
    else
        # Validate name format: kebab-case, 1-64 chars
        if ! echo "$name" | grep -qE "^[a-z][a-z0-9-]*[a-z0-9]$"; then
            fail "$skill_file: Invalid name '$name' (must be kebab-case, start with letter)"
        fi
        if [ ${#name} -gt 64 ]; then
            fail "$skill_file: Name '$name' exceeds 64 chars (${#name})"
        fi
        # Check name doesn't contain banned words
        if echo "$name" | grep -qiE "anthropic|claude"; then
            fail "$skill_file: Name cannot contain 'anthropic' or 'claude'"
        fi
    fi

    # Check description field (handles both inline and multiline >- YAML)
    local desc
    desc=$(python3 -c "
import yaml, sys
text = open('$skill_file').read()
parts = text.split('---')
if len(parts) >= 3:
    fm = yaml.safe_load(parts[1])
    print(str(fm.get('description', '')).strip())
" 2>/dev/null)
    if [ -z "$desc" ]; then
        fail "$skill_file: Missing 'description' field in frontmatter"
    else
        if [ ${#desc} -gt 200 ]; then
            warn "$skill_file: Description exceeds 200 chars (${#desc})"
        fi
        if echo "$desc" | grep -qiE "^I |^I'|^You "; then
            warn "$skill_file: Description should be third person (no I/you)"
        fi
    fi

    # Check for absolute paths in body (skip frontmatter)
    local body_content
    body_content=$(sed -n '/^---$/,/^---$/d; p' "$skill_file")
    if echo "$body_content" | grep -qE "/home/|/Users/|C:\\\\"; then
        fail "$skill_file: Contains absolute paths (use {baseDir}/ instead)"
    fi

    # Check for required sections (all 6)
    for section in "## Overview" "## Prerequisites" "## Instructions" "## Examples" "## Error Handling" "## Resources"; do
        if ! grep -qi "^${section}" "$skill_file"; then
            warn "$skill_file: Missing '${section}' section"
        fi
    done

    # Check description contains "Use when" pattern
    if [ -n "$desc" ]; then
        if ! echo "$desc" | grep -qi "use when"; then
            warn "$skill_file: Description should include 'Use when' pattern"
        fi
    fi

    # Check tier field format (if present in metadata)
    local tier_val
    tier_val=$(echo "$frontmatter" | grep "^  *tier:" | head -1 | sed 's/.*tier: *//')
    if [ -n "$tier_val" ]; then
        case "$tier_val" in
            free|basic|pro|proplus|smb|enterprise) ;;
            *) warn "$skill_file: Invalid tier '$tier_val' (must be free|basic|pro|proplus|smb|enterprise)" ;;
        esac
    fi

    # Check line count
    local lines
    lines=$(wc -l < "$skill_file")
    if [ "$lines" -gt 500 ]; then
        warn "$skill_file: $lines lines (recommended < 500, consider references/)"
    fi

    # Check allowed-tools for unscoped Bash
    if echo "$frontmatter" | grep -q "allowed-tools:"; then
        local tools
        tools=$(echo "$frontmatter" | grep "allowed-tools:" | sed 's/.*allowed-tools: *"\(.*\)"/\1/')
        if echo "$tools" | grep -qE "(^|,)Bash(,|$)"; then
            warn "$skill_file: Unscoped 'Bash' in allowed-tools (use Bash(cmd:*) instead)"
        fi
    fi

    $VERBOSE && pass "$skill_file" || true
}

# --- PLUGIN VALIDATION ---
validate_plugin() {
    local plugin_dir="$1"
    local plugin_name
    plugin_name=$(basename "$plugin_dir")

    $VERBOSE && log "Checking plugin: $plugin_name" || true

    # Check plugin.json exists
    local pjson="$plugin_dir/.claude-plugin/plugin.json"
    if [ -f "$pjson" ]; then
        # Validate JSON
        if ! python3 -m json.tool "$pjson" > /dev/null 2>&1; then
            fail "$pjson: Invalid JSON"
        else
            # Check required fields
            for field in name description; do
                if ! python3 -c "import json; d=json.load(open('$pjson')); assert '$field' in d" 2>/dev/null; then
                    fail "$pjson: Missing required field '$field'"
                fi
            done
            $VERBOSE && pass "$pjson" || true
        fi
    else
        warn "$plugin_dir: No .claude-plugin/plugin.json found"
    fi

    # Check MCP config exists
    if [ ! -f "$plugin_dir/.mcp.json" ]; then
        warn "$plugin_dir: No .mcp.json found"
    fi

    # Check docs/ completeness
    if [ -d "$plugin_dir/docs" ]; then
        for doc in 01-BUSINESS-CASE.md 02-PRD.md 03-ARCHITECTURE.md 04-USER-JOURNEY.md 05-TECHNICAL-SPEC.md 06-STATUS.md; do
            if [ ! -f "$plugin_dir/docs/$doc" ]; then
                warn "$plugin_dir/docs/$doc: Missing from 6-doc set"
            fi
        done
    else
        warn "$plugin_dir: No docs/ directory"
    fi

    # Validate embedded skills
    /usr/bin/find "$plugin_dir" -name "SKILL.md" -type f 2>/dev/null | while read -r sf; do
        validate_skill "$sf"
    done
}

# --- MAIN ---
echo "SearchCarriers Validator"
echo "========================"
echo ""

if [ "$PLUGINS_ONLY" != "true" ]; then
    echo "Skills:"
    skill_count=0
    while IFS= read -r skill_file; do
        validate_skill "$skill_file"
        skill_count=$((skill_count + 1))
    done < <(/usr/bin/find skills -name "SKILL.md" -type f 2>/dev/null || true)
    # Also check plugin-embedded skills
    while IFS= read -r skill_file; do
        validate_skill "$skill_file"
        skill_count=$((skill_count + 1))
    done < <(/usr/bin/find plugins -name "SKILL.md" -type f 2>/dev/null || true)
    # Also check workflow skills
    while IFS= read -r skill_file; do
        validate_skill "$skill_file"
        skill_count=$((skill_count + 1))
    done < <(/usr/bin/find workflows -name "SKILL.md" -type f 2>/dev/null || true)
    echo "  Checked $skill_count skill(s)"
    echo ""
fi

if [ "$SKILLS_ONLY" != "true" ]; then
    echo "Plugins:"
    plugin_count=0
    for plugin_dir in plugins/*/; do
        [ -d "$plugin_dir" ] || continue
        # Skip shared utilities directory
        [ "$(basename "$plugin_dir")" = "shared" ] && continue
        validate_plugin "$plugin_dir"
        plugin_count=$((plugin_count + 1))
    done
    echo "  Checked $plugin_count plugin(s)"
    echo ""
fi

# --- REPORT ---
echo "========================"
echo "Results: $ERRORS error(s), $WARNINGS warning(s)"
if [ $ERRORS -gt 0 ]; then
    echo "FAILED"
    exit 1
else
    echo "PASSED"
    exit 0
fi
