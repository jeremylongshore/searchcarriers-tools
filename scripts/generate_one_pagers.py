#!/usr/bin/env python3
"""Generate concise customer-facing one-pagers from each skill's evidence contract."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOTS = ("skills", "plugins", "workflows")

AUDIENCES = {
    "search-discovery": "Carrier sourcing, brokerage operations, and identity-review teams",
    "vetting-risk": "Carrier onboarding, risk, compliance, and brokerage operations teams",
    "safety-compliance": "Safety, compliance, and carrier-management teams",
    "operations": "Carrier operations, data, integration, and TMS teams",
    "searchcarriers-api-bridge": "Integration owners connecting carrier evidence to internal systems",
    "searchcarriers-carrier-intel": "Operations teams that need one MCP surface for carrier research",
    "searchcarriers-ops-reporter": "Analysts and managers who review or distribute carrier decisions",
    "searchcarriers-risk-engine": "Risk and onboarding teams applying explicit qualification policy",
    "searchcarriers-watchdog": "Compliance and operations teams responsible for change follow-up",
    "fleet-risk-dashboard": "Enterprise carrier-risk leaders managing large carrier panels",
    "tms-auto-sync": "Enterprise TMS and carrier-master-data owners",
    "daily-vetting-digest": "Carrier onboarding managers running a daily review queue",
    "compliance-dashboard": "Compliance leaders responsible for a live carrier panel",
    "insurance-lapse-alert": "Risk and operations teams responding to insurance changes",
    "slack-carrier-watch": "Operations teams routing carrier-change events into Slack",
    "bulk-vetting-pipeline": "Small and midsize brokerages qualifying carrier lists at scale",
}


def skill_files() -> list[Path]:
    files: list[Path] = []
    for root in SKILL_ROOTS:
        files.extend((ROOT / root).glob("**/SKILL.md"))
    return sorted(files)


def frontmatter(text: str) -> dict:
    return yaml.safe_load(text.split("---", 2)[1])


def field(text: str, label: str) -> str:
    match = re.search(rf"^- {re.escape(label)}:\s*(.+)$", text, re.MULTILINE)
    if not match:
        raise ValueError(f"missing playbook field: {label}")
    return match.group(1).strip()


def trigger(text: str) -> str:
    match = re.search(r'^\*\*Should trigger:\*\*\s*[“"](.+?)[”"]', text, re.MULTILINE)
    return match.group(1).strip() if match else "A carrier decision needs current evidence."


def audience(path: Path, name: str) -> str:
    for key, value in AUDIENCES.items():
        if key in path.parts or key in name:
            return value
    return "Carrier operations and compliance teams"


def sentence_case(value: str) -> str:
    return value[:1].upper() + value[1:]


def render(skill_file: Path) -> str:
    skill_text = skill_file.read_text(encoding="utf-8")
    playbook = (skill_file.parent / "references" / "playbook.md").read_text(encoding="utf-8")
    meta = frontmatter(skill_text)
    title = re.search(r"^#\s+(.+)$", skill_text, re.MULTILINE).group(1)
    name = meta["name"]
    tier = meta.get("metadata", {}).get("tier", "free")
    problem = re.search(r"## Operational problem\n\n(.+)", playbook).group(1).strip()
    job = field(playbook, "Job")
    api = field(playbook, "API surface")
    evidence = field(playbook, "Required evidence")
    missing = field(playbook, "Missing-data rule")
    boundary = field(playbook, "Decision boundary")
    follow = field(playbook, "Required follow-through")
    example = trigger(skill_text)
    who = audience(skill_file, name)

    return f"""# {title}

**{sentence_case(job)}**

`{name}` | SearchCarriers tier: **{tier}** | Version **{meta["version"]}**

## The customer pain

{problem}

## What this skill changes

{sentence_case(job)} The workflow resolves the subject first, requests the smallest relevant API evidence set, separates facts from policy and inference, and returns a bounded status with the next human-owned action. The operator can see what was checked, what is missing, and why the result stopped where it did.

## Best fit

- **Who:** {who}.
- **When:** “{example}”
- **Evidence:** {api}
- **Customer receives:** {evidence}

## Decision contract

{boundary}

If the API response is partial, stale, ambiguous, or unavailable, the record stays unresolved rather than becoming a pass. {missing}

## Operational follow-through

{follow}

This package uses SearchCarriers as licensed research evidence. It does not create an official FMCSA safety rating, endorsement, guarantee, or regulated eligibility decision. Running the workflow requires an eligible SearchCarriers account and API subscription.

**Inspect the implementation:** [SKILL.md](../SKILL.md) · [Decision playbook](../references/playbook.md) · [API contract](https://github.com/jeremylongshore/searchcarriers-tools/blob/main/API-DISCOVERY.md)
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when generated files drift")
    args = parser.parse_args()
    failures: list[str] = []
    for skill_file in skill_files():
        output = skill_file.parent / "docs" / "ONE-PAGER.md"
        expected = render(skill_file)
        if args.check:
            if not output.exists() or output.read_text(encoding="utf-8") != expected:
                failures.append(str(output.relative_to(ROOT)))
            continue
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected, encoding="utf-8")
    if failures:
        print("One-pager drift:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    verb = "Verified" if args.check else "Generated"
    print(f"{verb} {len(skill_files())} customer one-pagers.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
