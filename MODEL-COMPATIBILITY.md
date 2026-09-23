# Model compatibility

The SearchCarriers operating layer is model-agnostic. Its executable boundary is
the open Model Context Protocol (MCP), and its evidence and decision contracts are
plain Markdown, YAML, and JSON. The five MCP servers do not call Anthropic, xAI,
OpenAI, Google, or another inference provider.

## Supported paths

| Client path | What works | Setup |
|---|---|---|
| Grok Build | Skills, Claude-compatible plugin packages, and all five local MCP servers | Run `./scripts/setup-dev.sh`, export `SEARCHCARRIERS_API_KEY`, then run `grok inspect` and `grok mcp doctor searchcarriers-carrier-intel`. Grok reads the root `.mcp.json`. |
| Claude Code | Skills, plugin packages, and all five local MCP servers | Run the same setup. Claude Code reads the root `.mcp.json` and the plugin manifests. |
| Other MCP clients | All five local MCP servers over standard stdio MCP | Translate the entries in `.mcp.json` into the client's MCP configuration format. Keep the server command, arguments, and environment boundary unchanged. |
| Direct agent or automation | The fourteen standalone skills and seven composed workflows | Use the documented SearchCarriers routes and evidence contracts directly through `curl`, Python, or the caller's own tool adapter. |

The language model chooses whether and how to request a tool. The MCP server owns
SearchCarriers authentication, route selection, tier checks, input schemas, and
structured results. Changing the model does not change those operational controls.

## What CI proves

`tests/test_model_compatibility.py` starts each configured server through a generic
MCP client, completes the protocol initialization handshake, requests `tools/list`,
and checks the published JSON schemas. The same test also fails if an MCP runtime
imports a model-provider SDK or if the root multi-client configuration drifts from
the five plugin configurations.

This verifies protocol and runtime independence. It does not claim that every
model will make identical tool choices or produce identical prose; those remain
model behavior and must be evaluated separately.

## Grok Bot deployment boundary

Grok Build can use the repository's local stdio servers directly. A hosted Grok
Bot or Grok Business custom connector needs a publicly reachable, authenticated
Streamable HTTP deployment. That is a transport and operations layer around the
same MCP tools, not a rewrite of the carrier logic, and it is not shipped by this
repository today.

## Primary compatibility sources

- [Grok Build MCP servers](https://docs.x.ai/build/features/mcp-servers)
- [Grok Build skills, plugins, and Claude compatibility](https://docs.x.ai/build/features/skills-plugins-marketplaces)
- [Model Context Protocol](https://modelcontextprotocol.io/)
