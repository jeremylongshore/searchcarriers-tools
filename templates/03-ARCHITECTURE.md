# {Plugin Name} - Architecture

## System Context

How this plugin fits in the SearchCarriers ecosystem. Which pipeline stage (INPUT/ANALYSIS/OUTPUT/STANDALONE)?

## Component Design

| Component | Responsibility |
|-----------|---------------|
| MCP Server | API calls + tier gating |
| Commands | User-facing slash commands |
| Skill | Claude instructions for interpretation |
| Agent | Autonomous analysis workflow |

## Data Flow

```
User Command -> MCP Tool -> SC API -> Raw Data -> Claude Interpretation -> Formatted Output
```

Input contract: What data this plugin accepts.
Output contract: What data this plugin produces (for pipeline chaining).

## Integration Points

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/... | GET | |

## Security Model

- API key handling: env var `SEARCHCARRIERS_API_KEY`
- Data classification: PII vs non-PII fields
- What gets logged, what doesn't

## Error Handling Strategy

| Error | HTTP Code | User Message | Recovery |
|-------|----------|-------------|----------|
| API timeout | 504 | "SearchCarriers API is slow, retrying..." | Retry 3x |
| Rate limited | 429 | "Rate limit hit, waiting {n}s..." | Retry-After header |
| Insufficient tier | 403 | "This feature requires {tier}. Upgrade at..." | Show upgrade URL |
| Invalid DOT | 422 | "DOT number '{n}' not found" | Suggest search |

## Performance Requirements

| Operation | Target Latency | Max Latency |
|-----------|---------------|-------------|
| Single lookup | < 1s | 3s |
| Bulk (100) | < 30s | 60s |
