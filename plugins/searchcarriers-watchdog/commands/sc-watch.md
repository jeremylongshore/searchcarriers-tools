---
name: sc-watch
description: Manage carrier watch list — add, remove, or list monitored carriers
allowed-tools: "Bash(python:*),Read"
---

# /sc-watch -- Carrier Watch List Management

When the user runs `/sc-watch <action> [arguments]`, manage the carrier monitoring watch list.

## Parse the Input

The first argument is the action. Supported actions:

| Action | Arguments | Description |
|--------|-----------|-------------|
| `add` | `<DOT>` | Add a carrier to the watch list by DOT number |
| `remove` | `<DOT>` | Remove a carrier from the watch list |
| `list` | (none) | Display all currently watched carriers |

If the user omits the action, default to `list`.

DOT numbers must be 7-digit numeric. If the user passes an MC number or name instead,
tell them to run `/sc-lookup` first to resolve the DOT number.

## Execute the Action

### Add a Carrier

Call the `watchlist_manage` MCP tool with `action: "add"` and the DOT number.

The tool validates the DOT number against FMCSA records before adding. If the carrier
does not exist, it returns a 404. If the carrier is already on the watch list, it returns
a duplicate notice.

### Remove a Carrier

Call the `watchlist_manage` MCP tool with `action: "remove"` and the DOT number.

If the DOT number is not on the watch list, report that and take no action.

### List Watched Carriers

Call the `watchlist_manage` MCP tool with `action: "list"`.

This returns all carriers currently on the watch list with their monitoring metadata.

## Display Results

### Add Confirmation

```
CARRIER WATCH -- ADDED
DOT:        {dot_number}
Carrier:    {legal_name}
Status:     {status}
Location:   {city}, {state}
Added:      {timestamp}
Monitoring: Active -- alerts will be generated for status changes,
            insurance lapses, safety rating changes, and OOS orders.
```

After confirmation, suggest using the configured SearchCarriers notification channel or running `monitor_compliance` for a current-state review.

### Remove Confirmation

```
CARRIER WATCH -- REMOVED
DOT:        {dot_number}
Carrier:    {legal_name}
Removed:    {timestamp}
Note:       Monitoring stopped. Historical alerts are retained for 90 days.
```

### Watch List Display

```
CARRIER WATCH LIST
Total monitored: {count}

| # | DOT     | Legal Name            | Status | Since      | Alerts (30d) |
|---|---------|----------------------|--------|------------|--------------|
| 1 | 1234567 | ACME TRUCKING LLC    | ACTIVE | 2026-01-15 | 2            |
| 2 | 2345678 | FAST FREIGHT INC     | ACTIVE | 2026-02-01 | 0            |
| 3 | 3456789 | ROAD RUNNER TRANSPORT | ACTIVE | 2025-12-10 | 5            |
```

After the list, suggest running `monitor_compliance` for a specific DOT when a current-state review is needed.

If the watch list is empty, display: "No carriers on the watch list. Run `/sc-watch add {DOT}` to start monitoring a carrier."

## Error Handling

- **Carrier not found (404)**: "No carrier found with DOT {dot_number}. Verify the number or use `/sc-lookup` to search."
- **Duplicate add**: "DOT {dot_number} is already on the watch list. Monitoring is active."
- **Not on list (remove)**: "DOT {dot_number} is not on the watch list. No action taken."
- **Tier insufficient (403)**: "Carrier Watch requires a Pro Plus subscription. Upgrade at searchcarriers.com/pricing."
- **API authentication (401)**: "API authentication failed. Check that SEARCHCARRIERS_API_KEY is set and valid."
- **Watch list full**: "Watch list limit reached ({max} carriers). Remove a carrier before adding another, or upgrade your plan for higher limits."
