# {Plugin Name} - User Journey

## Persona

**Name**: [Role name]
**Role**: Freight broker / Safety manager / Ops lead
**Goal**: What they're trying to accomplish
**Tier**: Minimum required tier

## Prerequisites

- [ ] SearchCarriers account at {tier} tier or above
- [ ] API key set: `export SEARCHCARRIERS_API_KEY=your-key`
- [ ] Plugin installed in Claude Code

## Step-by-Step Walkthrough

### Step 1: [First Action]

```
/sc-{command} {args}
```

**Expected output**:
```
[Show real example output]
```

### Step 2: [Next Action]

```
/sc-{command} {args}
```

**Expected output**:
```
[Show real example output]
```

### Step 3: [Final Action]

```
/sc-{command} {args}
```

**Expected output**:
```
[Show formatted report/summary]
```

## Error Scenarios

### Scenario: API Key Not Set
**Trigger**: Running any command without SEARCHCARRIERS_API_KEY
**Message**: "SEARCHCARRIERS_API_KEY not set. Get your key at searchcarriers.com/settings/api-tokens"

### Scenario: Insufficient Tier
**Trigger**: Using a Pro feature on Free tier
**Message**: "This feature requires Pro. Upgrade at searchcarriers.com/pricing"

### Scenario: Carrier Not Found
**Trigger**: Invalid DOT number
**Message**: "No carrier found for DOT {number}. Try searching by name instead."

## FAQ

**Q: How fresh is the data?**
A: Data syncs from FMCSA nightly. Most records are < 24 hours old.

**Q: Can I use this offline?**
A: No, all lookups require an active API connection.
