# {Plugin Name} - Technical Specification

## Tech Stack

- Python 3.10+
- MCP protocol (Model Context Protocol)
- httpx for async HTTP
- pydantic for data validation

## Dependencies

```
httpx>=0.27
pydantic>=2.0
```

## File Structure

```
{plugin-name}/
  .claude-plugin/plugin.json
  .mcp.json
  docs/ (6-doc set)
  commands/ (slash commands)
  agents/ (autonomous agents)
  skills/ (embedded SKILL.md)
  scripts/ (*_mcp.py + requirements.txt)
  README.md
  SCHEMA.md
```

## API Reference

| Endpoint | Method | Params | Min Tier |
|----------|--------|--------|----------|
| | | | |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| SEARCHCARRIERS_API_KEY | Yes | - | Bearer token for API auth |

## Testing Strategy

- **Unit**: Mock API responses, test data parsing
- **Integration**: Real API calls (marked `@pytest.mark.integration`)
- **Tier gating**: Verify correct error messages per tier

## Performance Benchmarks

| Operation | p50 | p95 | p99 |
|-----------|-----|-----|-----|
| | | | |

## Deployment

1. Copy plugin directory to `.claude/plugins/`
2. Set API key in environment
3. Restart the MCP client
4. Verify: `/sc-{command} test`
