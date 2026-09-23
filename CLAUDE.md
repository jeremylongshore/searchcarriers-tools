# SearchCarriers repository instructions

SearchCarriers tools and skills provide motor-carrier research workflows for
Claude Code and other MCP clients. The repository contains five MCP plugins,
fourteen standalone skills, and seven composed workflows.

Read [`API-DISCOVERY.md`](API-DISCOVERY.md) before changing any API call. The
current contract is hybrid: v3 search/company/equipment/crashes, v2
qualification reports, and documented v1 specialty/detail/watch routes. A 200
response may still mean an obsolete parameter was ignored, so route tests must
assert outgoing parameter names.

## Data and secrets

- Never commit API tokens, decrypted `.env` files, or live API responses.
- Use synthetic fixtures with invented companies and `example.invalid` contact
  data. SearchCarriers API results may not be redistributed as public datasets.
- Run commands with secrets through `scripts/sops-env -- command arg...`.
  Decrypted values must be passed as data and never evaluated by a shell.
- Logs and test receipts may contain status codes, route names, counts, and
  response shapes. They must not contain carrier records or token values.

## Directory layout

```text
plugins/   Five MCP servers plus shared API and tier helpers
skills/    Fourteen standalone skills grouped by capability
workflows/ Seven composed workflow skills
scripts/   Validation, setup, and encrypted-environment helpers
tests/     Unit, contract, rendering, and opt-in live smoke tests
```

## Conventions

- Skill names use `searchcarriers-{name}` in kebab case.
- Skill descriptions use a concise third-person “Use when” form.
- File references inside skills use `{baseDir}` rather than machine paths.
- MCP wrappers preserve upstream data and make contract drift visible.
- Every MCP tool declares its minimum subscription tier.
- The shared API contract lives in `plugins/shared/api_contract.py`.
- API examples and route guidance live in `API-DISCOVERY.md`; link to that file
  rather than duplicating a full endpoint catalog in each skill.
- The source code is Apache-2.0 licensed. Running it still requires an
  appropriate SearchCarriers account and API subscription.

## Validation

```bash
./scripts/validate.sh --verbose
python -m pytest -q
ruff check .
```

Live tests are opt-in and require an authorized token. They must assert only
contract structure and must never save response bodies in the repository.
