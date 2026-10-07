# Implementation Plan: Profile-Based Configuration

## Overview

This plan implements the profile-based configuration system that replaces shell-function-based tenant/project context management with an AWS CLI-style profile approach. The implementation proceeds bottom-up: core utilities first (config parser, profile resolver, token manager), then the refactored CLI entry point and configure commands, followed by installer updates. Property-based tests validate correctness properties from the design document.

## Tasks

- [x] 1. Set up project structure and core interfaces
  - [x] 1.1 Create module files and define data models
    - Create `src/icav2_cli_plugins/utils/config_parser.py` with `ProfileConfig` dataclass and `ConfigParseError` exception class
    - Create `src/icav2_cli_plugins/utils/profile_resolver.py` with `ResolvedConfig` dataclass stub
    - Create `src/icav2_cli_plugins/utils/token_manager.py` with `TokenManager` class stub
    - Create `src/icav2_cli_plugins/subcommands/configure/__init__.py` with command registration
    - Add `hypothesis` to `[project.optional-dependencies]` test group in `pyproject.toml`
    - _Requirements: 1.1, 1.2, 3.1, 3.5, 4.1_

  - [x] 1.2 Define constants and configuration paths
    - Add constants for `CONFIG_FILE_PATH`, `CACHE_DIR`, `BIN_DIR`, `LOCAL_BINARY_PATH` to a new or existing globals module
    - Define `PROFILE_NAME_REGEX = r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$'`
    - Define `VALID_OUTPUT_FORMATS = ('table', 'json', 'yaml')`
    - Define `TOKEN_REFRESH_THRESHOLD = 3600`
    - _Requirements: 1.1, 1.3, 1.6, 4.2, 5.3_

- [x] 2. Implement config file parser
  - [x] 2.1 Implement `ConfigParser.parse()` method
    - Parse INI-style content handling `[default]` and `[profile <name>]` section headers
    - Handle comments (lines starting with `#` or `;`), blank lines, key=value pairs
    - Trim whitespace from keys and values
    - Resolve duplicate keys to last occurrence
    - Raise `ConfigParseError` with line number for malformed lines
    - Validate profile names against regex and output_format against allowed values
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.7, 3.8, 1.1, 1.6_

  - [x] 2.2 Implement `ConfigParser.serialize()` method
    - Serialize `Dict[str, ProfileConfig]` back to INI format string
    - Write `[default]` section first, then `[profile <name>]` sections alphabetically
    - _Requirements: 3.6_

  - [x] 2.3 Implement `ConfigParser.parse_file()` and `ConfigParser.write_file()` methods
    - `parse_file`: read from disk path, handle file not found with clear error
    - `write_file`: serialize and write with `mode 0600` permissions
    - _Requirements: 1.3, 1.7, 8.4_

  - [x] 2.4 Write property test for config round-trip (Property 1)
    - **Property 1: Config file round-trip**
    - Generate arbitrary valid ProfileConfig dicts, serialize then parse, assert identical result
    - `# Feature: profile-based-config, Property 1: Config file round-trip`
    - **Validates: Requirements 3.6, 3.1, 3.3, 3.5, 1.1, 1.2**

  - [x] 2.5 Write property test for comment invariance (Property 2)
    - **Property 2: Comments do not affect parse result**
    - Generate valid config content, insert random comment lines, assert same parse result
    - `# Feature: profile-based-config, Property 2: Comments do not affect parse result`
    - **Validates: Requirements 3.2**

  - [x] 2.6 Write property test for duplicate key resolution (Property 9)
    - **Property 9: Duplicate keys resolve to last occurrence**
    - Generate sections with repeated keys, assert last value wins
    - `# Feature: profile-based-config, Property 9: Duplicate keys resolve to last occurrence`
    - **Validates: Requirements 3.8**

  - [x] 2.7 Write property test for malformed line detection (Property 10)
    - **Property 10: Malformed lines produce parse errors with line info**
    - Generate lines without `=`, not blank/comment/header, assert ConfigParseError with line number
    - `# Feature: profile-based-config, Property 10: Malformed lines produce parse errors with line info`
    - **Validates: Requirements 3.7**

  - [x] 2.8 Write property test for output format validation (Property 8)
    - **Property 8: Output format validation**
    - Generate arbitrary strings for output_format, assert accepted iff in {table, json, yaml}
    - `# Feature: profile-based-config, Property 8: Output format validation`
    - **Validates: Requirements 1.6**

- [x] 3. Checkpoint - Ensure config parser tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement profile resolver
  - [x] 4.1 Implement `ProfileResolver.resolve()` with precedence chain
    - Implement `_determine_profile_name()`: check `--profile` flag → `ICAV2_PROFILE` env → `ICAV2_TENANT_NAME` env → `[default]`
    - Load profile from parsed config using determined name
    - Apply environment variable overrides (`ICAV2_ACCESS_TOKEN`, `ICAV2_PROJECT_ID`, `ICAV2_BASE_URL`)
    - Construct `base_url` from `server_url` (prepend `https://` scheme)
    - Apply defaults: `server_url` → `ica.illumina.com`, `output_format` → `table`
    - _Requirements: 2.1, 2.2, 2.5, 2.6, 7.1, 7.4, 9.1, 9.3, 9.4, 9.5, 9.6, 9.7_

  - [x] 4.2 Implement error handling for profile resolution
    - Exit with error listing available profiles if requested profile not found
    - Exit with error if no default profile and no env var set
    - Exit with error if config file missing or unreadable
    - _Requirements: 2.3, 2.4, 2.7, 7.5_

  - [x] 4.3 Write property test for default value resolution (Property 3)
    - **Property 3: Default values applied when keys absent**
    - Generate profiles missing `server_url` and/or `output_format`, assert defaults applied
    - `# Feature: profile-based-config, Property 3: Default values applied when keys absent`
    - **Validates: Requirements 1.4, 1.5**

  - [x] 4.4 Write property test for profile selection (Property 4)
    - **Property 4: Profile selection resolves correct profile**
    - Generate multi-profile configs, set ICAV2_PROFILE to various names, assert correct profile loaded
    - `# Feature: profile-based-config, Property 4: Profile selection resolves correct profile`
    - **Validates: Requirements 2.1, 2.2**

  - [x] 4.5 Write property test for precedence resolution (Property 5)
    - **Property 5: Configuration precedence resolution**
    - Generate all combinations of env vars and profile values, assert highest-precedence source wins per key
    - `# Feature: profile-based-config, Property 5: Configuration precedence resolution`
    - **Validates: Requirements 2.5, 7.4, 9.1, 9.3, 9.4, 9.5, 9.6, 9.7**

  - [x] 4.6 Write property test for invalid profile error (Property 7)
    - **Property 7: Invalid profile name produces error with available profiles**
    - Generate config with N profiles, request nonexistent name, assert error contains name + available list
    - `# Feature: profile-based-config, Property 7: Invalid profile name produces error with available profiles`
    - **Validates: Requirements 2.4**

- [x] 5. Implement token manager
  - [x] 5.1 Implement `TokenManager` with caching and refresh logic
    - Implement `_read_cache()`: read `session.yaml` from `~/.icav2-cli-plugins/cache/<profile>/session.yaml`
    - Implement `_write_cache()`: write token + epoch to YAML with mode 0600
    - Implement `_is_token_fresh()`: decode JWT `exp` claim, compare with current time + 3600s threshold
    - Implement `_generate_token()`: POST to ICAv2 API with API key to obtain access token
    - Implement `get_valid_token()`: orchestrate cache check → freshness → generate if stale
    - Handle malformed/invalid cache gracefully (treat as absent, regenerate)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 5.2 Implement JWT validation for environment token
    - Validate `ICAV2_ACCESS_TOKEN` env var: decode JWT, check `exp` > current time
    - Reject expired/malformed JWT with error, no fallback to profile token
    - _Requirements: 9.1, 9.2_

  - [x] 5.3 Write property test for token freshness decision (Property 6)
    - **Property 6: Token cache freshness decision**
    - Generate JWTs with various `exp` values, assert fresh iff (exp - now) > 3600
    - `# Feature: profile-based-config, Property 6: Token cache freshness decision`
    - **Validates: Requirements 4.2, 4.3**

  - [x] 5.4 Write property test for expired JWT rejection (Property 11)
    - **Property 11: Expired/malformed JWT environment token is rejected without fallback**
    - Generate expired/malformed JWT strings in ICAV2_ACCESS_TOKEN, assert error raised without fallback
    - `# Feature: profile-based-config, Property 11: Expired/malformed JWT environment token is rejected without fallback`
    - **Validates: Requirements 9.2**

- [x] 6. Checkpoint - Ensure all core utility tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Refactor CLI entry point and implement lazy dispatch
  - [x] 7.1 Refactor `utils/cli.py` as standalone entry point
    - Rewrite `main()` to: parse `--profile` and `--debug` global args, handle `help`/`version` early (no heavy imports)
    - Integrate `ProfileResolver` to determine active profile
    - Integrate `TokenManager` to ensure valid access token
    - Dispatch to plugin subcommand or delegate to `_icav2` binary
    - Keep `docopt` as argument parser with updated docstring including `--profile` flag and `configure` command group
    - _Requirements: 6.4, 6.5, 7.1, 7.2, 7.3, 7.4_

  - [x] 7.2 Implement lazy import dispatcher
    - Create `COMMAND_MODULE_MAP` dict mapping command names to module paths
    - Implement `lazy_import_command()` using `importlib.import_module()`
    - Replace the if-else chain in `_dispatch()` with lazy dispatcher lookup
    - Ensure `help`/`version` never import `wrapica`, `libica`, `pandas`, or other heavy libraries
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_

  - [x] 7.3 Implement delegation to local `_icav2` binary
    - Implement `_delegate_to_icav2()`: exec `~/.icav2-cli-plugins/bin/_icav2` with `ICAV2_ACCESS_TOKEN`, `ICAV2_BASE_URL`, `ICAV2_PROJECT_ID` set in environment
    - Exit with error if binary not found, suggesting re-run of installer
    - _Requirements: 5.6, 5.7, 7.3_

  - [x] 7.4 Write unit tests for lazy import and startup performance
    - Test that `help`/`version` do not import heavy libraries (check `sys.modules`)
    - Test that unknown commands produce helpful error
    - Test that `--profile` flag is parsed correctly
    - _Requirements: 6.4, 6.5, 6.7_

- [x] 8. Implement configure commands
  - [x] 8.1 Implement `ConfigureSet` command
    - Create `src/icav2_cli_plugins/subcommands/configure/configure_set.py`
    - Prompt for `server_url`, `x_api_key`, `project_name` interactively
    - Validate API key by attempting token generation before saving
    - Write profile to config file (create file + parent dirs with mode 0600 if absent)
    - Handle existing profile overwrite
    - Default to `[default]` section if no profile name given
    - _Requirements: 8.1, 8.3, 8.4, 8.5, 8.6, 8.8_

  - [x] 8.2 Implement `ConfigureList` command
    - Create `src/icav2_cli_plugins/subcommands/configure/configure_list.py`
    - Display table of configured profiles (name + server_url)
    - Display message when no profiles configured
    - _Requirements: 8.2, 8.7_

  - [x] 8.3 Write unit tests for configure commands
    - Test `configure set` with mocked stdin and mocked token generation
    - Test `configure list` output format with sample profiles
    - Test `configure list` empty state message
    - Test file permissions set correctly (0600)
    - _Requirements: 8.1, 8.2, 8.4, 8.7_

- [x] 9. Checkpoint - Ensure CLI and configure command tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 10. Update installer for new architecture
  - [x] 10.1 Update `install.sh` for binary bundling and directory structure
    - Create directory structure: `~/.icav2-cli-plugins/bin/`, `~/.icav2-cli-plugins/cache/`
    - Download icav2 binary for current platform/architecture to `~/.icav2-cli-plugins/bin/_icav2`
    - Set executable permissions (0755) on downloaded binary
    - Create empty config file with mode 0600 if not present
    - Remove `command icav2` prerequisite check
    - Abort all setup if binary download fails
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 10.1, 10.2, 10.3, 10.5_

  - [x] 10.2 Update `source.sh` generation and add migration prompt
    - Simplify generated `source.sh`: set `ICAV2_CLI_PLUGINS_HOME` and prepend `bin/` to PATH
    - Detect existing `~/.icav2-cli-plugins/tenants/` directory
    - If interactive and tenants/ exists: prompt user to migrate tenant configs into profiles
    - If non-interactive or declined: skip migration, leave tenants/ unchanged
    - _Requirements: 10.4, 10.6, 10.7_

  - [x] 10.3 Write unit tests for installer logic
    - Test platform/architecture detection
    - Test directory structure creation
    - Test migration prompt logic (interactive vs non-interactive)
    - Test source.sh content generation
    - _Requirements: 10.1, 10.2, 10.4, 10.6, 10.7_

- [x] 11. Decouple `subcommands/__init__.py` from heavy imports
  - [x] 11.1 Refactor `subcommands/__init__.py` to defer wrapica/libica/pandas imports
    - Move `wrapica`, `libica`, and `pandas` imports out of module-level in `subcommands/__init__.py`
    - Defer these imports to point of first use within `DocOptArg.coerce_magical_value()` and `Command` methods
    - Ensure `Command` and `DocOptArg` classes can be imported without triggering heavy library loads
    - _Requirements: 6.2, 6.6_

  - [x] 11.2 Write unit tests for deferred imports
    - Import `subcommands/__init__` and verify `wrapica`, `libica`, `pandas` not in `sys.modules`
    - Verify coercion still works when triggered
    - _Requirements: 6.2, 6.6_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The implementation uses Python 3.12+ with `hypothesis` for property-based testing
- All new modules follow the existing `src/icav2_cli_plugins/` package layout

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2"] },
    { "id": 1, "tasks": ["2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["2.4", "2.5", "2.6", "2.7", "2.8"] },
    { "id": 4, "tasks": ["4.1"] },
    { "id": 5, "tasks": ["4.2", "4.3", "4.4", "4.5", "4.6"] },
    { "id": 6, "tasks": ["5.1"] },
    { "id": 7, "tasks": ["5.2", "5.3", "5.4"] },
    { "id": 8, "tasks": ["7.1", "7.2", "7.3", "11.1"] },
    { "id": 9, "tasks": ["7.4", "11.2", "8.1", "8.2"] },
    { "id": 10, "tasks": ["8.3", "10.1"] },
    { "id": 11, "tasks": ["10.2", "10.3"] }
  ]
}
```
