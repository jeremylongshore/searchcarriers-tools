# Agent instructions

Read `CLAUDE.md` and `API-DISCOVERY.md` before editing this repository.

- Keep SearchCarriers tokens and API response data out of Git, logs, issues,
  and generated fixtures.
- Use the shared API contract instead of defining new version constants inside
  individual MCP servers.
- Add or update route-contract tests whenever an endpoint, parameter, or
  response normalizer changes.
- Run `./scripts/validate.sh --verbose`, `python -m pytest -q`, and
  `ruff check .` before completing code changes.
