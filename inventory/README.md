# Inventory Tracking

## plugins_inventory.csv

| Column | Description |
|--------|-------------|
| name | Plugin directory name |
| type | stackable or standalone |
| stage | Pipeline stage: INPUT, ANALYSIS, OUTPUT, MONITORING, INTEGRATION |
| status | planned, in_progress, working, shipped |
| min_tier | Minimum subscription tier (free/basic/pro/proplus/smb/enterprise) |
| who | Assigned developer |
| what | One-line description |
| when | Build phase |
| target_goal | Definition of done |
| production | Is it production-ready? (Yes/No) |
| version | Current version (semver) |
| docs_complete | All 6 enterprise docs written? (Yes/No) |

## skills_inventory.csv

| Column | Description |
|--------|-------------|
| name | Skill name (kebab-case, matches directory) |
| category | search-discovery, safety-compliance, vetting-risk, operations |
| type | standalone or embedded (in a plugin) |
| status | planned, in_progress, working, shipped |
| min_tier | Minimum subscription tier |
| plugin_embedded | If embedded, which plugin? (No if standalone) |
| has_scripts | Has scripts/ directory? (Yes/No) |
| has_references | Has references/ directory? (Yes/No) |
| has_templates | Has templates/ directory? (Yes/No) |
| description | Skill description (matches SKILL.md frontmatter) |

## Updating

Update CSVs when:
- A plugin or skill changes status (planned -> working)
- New plugins or skills are added
- Version bumps occur
- Docs are completed
