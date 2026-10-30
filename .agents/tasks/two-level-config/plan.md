# Implementation Plan: Two-Level (Tenant + Profile) Configuration

Refactor the single-level profile config into an AWS-CLI-style two-level layout:
a shared `[tenant <name>]` section holds user-scoped fields (server_url, api_key,
encryption keys, access_token + expiry) and a lightweight `[profile <name>]` /
`[default]` section holds project-scoped fields (project_id, project_name,
tenant_name pointer, output_format). Add `configure set-tenant`, `configure
set-profile`, `configure export`; deprecate `configure set` and `tokens export`
(warn + still work); update CLI help and the wiki.

Work happens in the worktree at
`/home/alexiswl/GitHub/UMCCR/icav2-cli-plugins/.worktrees/refactor-two-level-config`
(branch `refactor/two-level-config`). The wiki is a separate repo at
`/home/alexiswl/GitHub/UMCCR/icav2-cli-plugins.wiki` (branch `master`).

## Design decisions

- **Token lives on the tenant.** The ICAv2 access token is user-scoped (valid
  across all projects in a tenant), so `access_token` / `access_token_expiry`
  live on the `[tenant]` section and are cached/refreshed per tenant, never per
  profile. (Confirmed from the task + original request.)
- **Two dataclasses, not one.** Add `TenantConfig` (server_url, x_api_key,
  encryption_public_key, encryption_private_key, access_token,
  access_token_expiry) and slim `ProfileConfig` to (name, project_id,
  project_name, tenant_name, output_format). This mirrors AWS CLI's split and
  keeps serialization deterministic per section type. `token_tid` is dropped
  (it is never read anywhere outside the parser/serializer).
- **Parser returns both maps.** `ConfigParser.parse` returns a 2-tuple
  `(tenants: Dict[str, TenantConfig], profiles: Dict[str, ProfileConfig])`
  rather than one dict, because section headers now have distinct namespaces
  (`[tenant x]` vs `[profile x]`/`[default]`). Chosen over a merged dict because
  a tenant and a profile may share a name and must not collide.
- **Resolver merges tenant into profile.** `ProfileResolver.resolve()` looks up
  `profile.tenant_name` in the tenants map, pulls server_url/api_key/
  access_token from the tenant, and keeps project_id/project_name/output_format
  from the profile. Missing-tenant is a clear error naming profile, missing
  tenant, and available tenants.
- **TokenManager keyed by tenant.** Constructor takes `tenant_name` (not
  `profile_name`); persistence writes `access_token`/`access_token_expiry` back
  onto the `[tenant <name>]` section. JWT freshness (>3600s) logic unchanged.
- **No migration.** New format only, going forward. Do not read/write the live
  `~/.icav2-cli-plugins/config`.

## Test runner note

Run tests from the worktree root with:
`uv run pytest tests/ -p no:orcabus_pipeline_test_utils`
The `-p no:orcabus_pipeline_test_utils` flag is REQUIRED — a stray global
pytest11 entrypoint (`orcabus_pipeline_test_utils.conftest_plugin`) in the shared
environment otherwise aborts collection. Pre-existing baseline state (do NOT try
to fix these): `tests/test_cli_unit.py::TestUnknownCommandDelegation::test_unknown_command_attempts_delegation`
fails (expects `projects` to be delegated), and
`src/icav2_cli_plugins/utils/tests/test_config_helpers.py` fails to collect (bad
relative import). Everything else in `tests/` passes (122 passed, 1 failed).

---

- [ ] 1. Add `TenantConfig` dataclass and split sections in `config_parser.py`.
      Add `TenantConfig` (server_url, x_api_key, encryption_public_key,
      encryption_private_key, access_token, access_token_expiry). Slim
      `ProfileConfig` to (name, project_id, project_name, tenant_name,
      output_format); drop server_url/x_api_key/encryption*/access_token*/
      token_tid. Change `parse`/`parse_file` to return `(tenants, profiles)`;
      update `_KNOWN_KEYS`, add `[tenant <name>]` header parsing (reuse
      PROFILE_NAME_REGEX for the tenant name), and keep comment handling,
      whitespace trim, duplicate-last-wins, malformed-line errors with line
      numbers, output_format validation, and the existing `[default]`/`[profile]`
      rules. Update `serialize` to take `(tenants, profiles)` and emit tenants
      first (alphabetical), then `[default]`, then named profiles (alphabetical),
      each with only its section's keys. Update `write_file` signature to match;
      keep mode 0600.
      Files: src/icav2_cli_plugins/utils/config_parser.py
      Verify: `uv run pytest tests/test_config_parser_properties.py -p no:orcabus_pipeline_test_utils`
      (after item 4 updates the tests) passes.

- [ ] 2. Update `ProfileResolver`/`ResolvedConfig` to merge tenant + profile.
      In `resolve()`, parse into `(tenants, profiles)`, select the profile as
      today (env/--profile/ICAV2_TENANT_NAME/default precedence unchanged), then
      look up `profile.tenant_name` in `tenants`. If absent, exit with an error
      naming the profile, the missing tenant, and the available tenant names.
      Build `ResolvedConfig` from merged values: server_url/api_key/
      cached_access_token/encryption_* from the tenant; project_id/project_name/
      output_format from the profile. `base_url = https://<server_url>/ica/rest`.
      Keep env overrides (ICAV2_ACCESS_TOKEN, ICAV2_PROJECT_ID, ICAV2_BASE_URL).
      Add `tenant_name` to `ResolvedConfig` so TokenManager can key by it.
      Files: src/icav2_cli_plugins/utils/profile_resolver.py
      Verify: `uv run pytest tests/test_profile_resolver_properties.py -p no:orcabus_pipeline_test_utils`
      (after item 4) passes.

- [ ] 3. Make `TokenManager` tenant-keyed and persist to the tenant section.
      Rename the constructor param `profile_name` -> `tenant_name` (update all
      references incl. error messages). In `_persist_token`, parse into
      `(tenants, profiles)`, update the matching `[tenant <name>]`'s
      `access_token`/`access_token_expiry`, and write both maps back. Keep JWT
      freshness (>3600s), encryption-at-rest, and graceful malformed-cache
      handling. Update the call site in `utils/cli.py::_resolve_profile_and_token`
      to pass `tenant_name=config.tenant_name` and read encryption key paths from
      the resolved (tenant) values.
      Files: src/icav2_cli_plugins/utils/token_manager.py,
      src/icav2_cli_plugins/utils/cli.py
      Verify: `uv run pytest tests/test_token_manager.py tests/test_token_manager_properties.py -p no:orcabus_pipeline_test_utils`
      (after item 4) passes.

- [ ] 4. Update existing property/unit tests for the two-level format and add
      new coverage. Update strategies and assertions in the config_parser,
      profile_resolver, and token_manager test modules to the `(tenants,
      profiles)` API and the moved fields. Add: tenant+profile round-trip
      serialize/parse; profile-references-missing-tenant error (message names
      profile, missing tenant, available tenants); tenant-keyed token caching
      shared across two profiles of the same tenant. Keep the
      `# Feature: profile-based-config, Property N: ...` tagging convention when
      extending a property; add new properties/units as needed. Mock token
      generation and project-id resolution (no live network), following the
      existing `patch(...requests.post/get...)` fixtures.
      Files: tests/test_config_parser_properties.py,
      tests/test_profile_resolver_properties.py, tests/test_token_manager.py,
      tests/test_token_manager_properties.py
      Verify: `uv run pytest tests/test_config_parser_properties.py tests/test_profile_resolver_properties.py tests/test_token_manager.py tests/test_token_manager_properties.py -p no:orcabus_pipeline_test_utils`
      — all pass.

- [ ] 5. Add `configure set-tenant` command.
      New module with a docopt `Command` class modeled on `configure_set.py` but
      WITHOUT the project-name/project-id steps: prompt server_url + x_api_key,
      handle encryption as today, validate the key by generating a token via
      `TokenManager._generate_token`, store the fresh (optionally encrypted)
      access_token + expiry on a `[tenant <name>]` section, default tenant name
      `default`. Read existing config into `(tenants, profiles)`, upsert the
      tenant, write back.
      Files: src/icav2_cli_plugins/subcommands/configure/configure_set_tenant.py
      Verify: `uv run pytest tests/test_configure_commands.py -k set_tenant -p no:orcabus_pipeline_test_utils`
      (tests added in item 9) passes.

- [ ] 6. Add `configure set-profile` command.
      New module: prompt tenant_name (must exist in the parsed tenants map; else
      error listing available tenants), project_name, and output_format; resolve
      project_id using the tenant's server_url + a freshly generated/valid token
      via the same project-list mechanism `configure_set` uses
      (`_resolve_project_id` / `get_project_id_from_project_name_curl`). Write a
      `[profile <name>]`/`[default]` with project_id, project_name, tenant_name,
      output_format. Does NOT prompt for server_url or api_key.
      Files: src/icav2_cli_plugins/subcommands/configure/configure_set_profile.py
      Verify: `uv run pytest tests/test_configure_commands.py -k set_profile -p no:orcabus_pipeline_test_utils`
      (item 9) passes.

- [ ] 7. Add `configure export <profile>` command.
      New module: resolve the profile via `ProfileResolver` (tenant-merged),
      obtain a fresh token via `TokenManager.get_valid_token` (refresh if stale),
      and print exactly four lines to stdout:
      `export ICAV2_SERVER_URL=<server_url>`,
      `export ICAV2_BASE_URL=https://<server_url>/ica/rest`,
      `export ICAV2_PROJECT_ID=<project_id>`,
      `export ICAV2_ACCESS_TOKEN=<access_token>`.
      Files: src/icav2_cli_plugins/subcommands/configure/configure_export.py
      Verify: `uv run pytest tests/test_configure_commands.py -k export -p no:orcabus_pipeline_test_utils`
      (item 9) passes.

- [ ] 8. Deprecate `configure set` and `tokens export`; update list + CLI wiring.
      Print a clear stderr deprecation warning at the start of
      `configure_set.Command.__call__` (point to `configure set-tenant` +
      `configure set-profile`) and `TokensExport.__call__` (point to `configure
      export`), then run as before. Update `configure_list` to the `(tenants,
      profiles)` API: show each profile and the tenant it references, and list
      tenants. Register `set-tenant`/`set-profile`/`export` in
      `configure/__init__.py::CONFIGURE_SUBCOMMANDS` and in the `_print_configure_help`
      block + `configure/__init__` docstring in `utils/cli.py`; note `set` as
      deprecated in help text. No change to COMMAND_MODULE_MAP (configure is
      already registered).
      Files: src/icav2_cli_plugins/subcommands/configure/configure_set.py,
      src/icav2_cli_plugins/subcommands/configure/configure_list.py,
      src/icav2_cli_plugins/subcommands/configure/__init__.py,
      src/icav2_cli_plugins/subcommands/tokens/export.py,
      src/icav2_cli_plugins/utils/cli.py
      Verify: `uv run pytest tests/test_configure_commands.py tests/test_cli_unit.py tests/test_configure_set.py -p no:orcabus_pipeline_test_utils`
      — new/updated tests pass; the one pre-existing `test_cli_unit` delegation
      failure remains unchanged.

- [ ] 9. Add command tests for set-tenant / set-profile / export + deprecations.
      In `tests/test_configure_commands.py` (and/or new sibling modules) add:
      set-tenant writes a `[tenant]` section with token+expiry and no project
      keys; set-profile errors on missing tenant (message lists available) and
      writes a profile pointing at an existing tenant; export emits the four
      lines with correct base_url derivation; deprecation warnings appear on
      stderr for `configure set` and `tokens export` while they still function.
      Mock `requests.post`/`requests.get` as existing configure tests do.
      Files: tests/test_configure_commands.py (+ new test modules if needed)
      Verify: `uv run pytest tests/ -p no:orcabus_pipeline_test_utils` — full
      suite green except the two documented pre-existing failures.

- [ ] 10. Update the wiki.
      In the wiki repo (`master` branch), document the new tenant+profile format,
      the `set-tenant`/`set-profile`/`export` commands, the user-scoped token
      model, and the deprecation of `configure set` and `tokens export`. Touch
      Configuration.md (primary), plus Installation.md, Home.md, and the relevant
      `commands/` / `stories/` pages that reference the old commands or config.
      Commit on `master`; do not create a worktree for the wiki.
      Files: /home/alexiswl/GitHub/UMCCR/icav2-cli-plugins.wiki/Configuration.md,
      Installation.md, Home.md, commands/ContextHandling.md (+ others grep finds)
      Verify: `git -C /home/alexiswl/GitHub/UMCCR/icav2-cli-plugins.wiki diff --stat`
      shows the edits; `grep -rl "set-tenant" .` finds the new content; a local
      commit exists on `master`.

## Digest

### src/icav2_cli_plugins/utils/config_parser.py
- `@dataclass ProfileConfig` (currently ~12 fields, lines ~18-32): slim to
  `name, project_id, project_name, tenant_name, output_format`.
- ADD `@dataclass TenantConfig`: `name, server_url, x_api_key,
  encryption_public_key, encryption_private_key, access_token,
  access_token_expiry`.
- `_KNOWN_KEYS` frozenset (~line 50): split per section type.
- `parse(self, content) -> Dict[str, ProfileConfig]` (~line 56): change return to
  `Tuple[Dict[str,TenantConfig], Dict[str,ProfileConfig]]`; route `[tenant x]`
  sections to TenantConfig.
- `_parse_section_header` (~line 130): add `tenant ` prefix branch (regex-validate
  name), keep `default`/`profile ` branches and all error cases.
- `serialize(self, profiles)` (~line 170): change to
  `serialize(self, tenants, profiles)`; tenants first, then default, then named.
- `parse_file` / `write_file` (~line 215/240): update signatures to the tuple/two-map
  shape; keep 0600.
- Test: tests/test_config_parser_properties.py (round-trip Property 1, duplicate
  Property 9, output-format Property 8, malformed Property 10, comments Property 2).
- Verified today: 36 passed (config_parser + token_manager) with
  `-p no:orcabus_pipeline_test_utils`.

### src/icav2_cli_plugins/utils/profile_resolver.py
- `@dataclass ResolvedConfig` (~line 18): ADD `tenant_name: Optional[str]`.
- `ProfileResolver.resolve` (~line 48): parse tuple; merge referenced tenant;
  missing-tenant error; keep env overrides and profile-selection precedence.
- `_apply_env_overrides`, `_determine_profile_name`,
  `_has_explicit_profile_source`: unchanged.
- Test: tests/test_profile_resolver_properties.py (Properties 3,4,5,7).

### src/icav2_cli_plugins/utils/token_manager.py
- `TokenManager.__init__(self, profile_name, ...)` (~line 72): rename
  `profile_name` -> `tenant_name`; update all `self.profile_name` refs and error
  strings.
- `_persist_token` (~line 200): parse tuple, write token+expiry onto the
  `[tenant <name>]` section, write both maps back.
- `_is_token_fresh` / `_get_token_expiry` / `_generate_token` /
  `validate_env_token`: unchanged.
- Test: tests/test_token_manager.py, tests/test_token_manager_properties.py.

### src/icav2_cli_plugins/utils/cli.py
- `_resolve_profile_and_token` (~line 90): construct `TokenManager(tenant_name=
  config.tenant_name, ...)`; encryption key paths from resolved tenant fields.
- `_dispatch` configure branch + `_print_configure_help` (~line, in the
  `cmd == "configure"` block): add set-tenant/set-profile/export; mark set
  deprecated. Module docstring `tokens`/`configure` lines updated.
- Test: tests/test_cli_unit.py (note: one pre-existing delegation failure stays).

### src/icav2_cli_plugins/subcommands/configure/__init__.py
- `CONFIGURE_SUBCOMMANDS` dict: add `set-tenant`, `set-profile`, `export` entries
  mapping to the new modules; module docstring subcommand list updated.

### src/icav2_cli_plugins/subcommands/configure/configure_set_tenant.py  (NEW)
- docopt `Command` modeled on configure_set.py minus project prompts; writes
  `[tenant <name>]`.

### src/icav2_cli_plugins/subcommands/configure/configure_set_profile.py  (NEW)
- docopt `Command`: prompt tenant_name (validate against tenants map),
  project_name, output_format; resolve project_id; write profile section.

### src/icav2_cli_plugins/subcommands/configure/configure_export.py  (NEW)
- docopt `Command`: resolve profile, fresh token, print the four export lines.

### src/icav2_cli_plugins/subcommands/configure/configure_set.py
- `__call__` (~line 70): prepend stderr deprecation warning; rest unchanged but
  adapted to the new ConfigParser tuple API (it currently builds a single
  self-contained ProfileConfig — update to write a tenant + a profile, or keep
  legacy single-section write guarded by the deprecation; align with item 8).

### src/icav2_cli_plugins/subcommands/configure/configure_list.py
- `__call__` (~line 30): use `(tenants, profiles)`; show profile -> tenant and
  list tenants.

### src/icav2_cli_plugins/subcommands/tokens/export.py
- `TokensExport.__call__` (~line 50): prepend stderr deprecation warning pointing
  at `configure export`; still print the token.
- Test: tests/test_configure_commands.py, tests/test_configure_set.py.

### Wiki (separate repo, master branch)
- Configuration.md, Installation.md, Home.md, commands/ContextHandling.md,
  stories/*.md as grep for `configure set`/`tokens export`/`tenant` identifies.
- No build/test; verify via `git -C <wiki> diff --stat` and a `master` commit.
