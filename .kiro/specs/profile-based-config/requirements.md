# Requirements Document

## Introduction

Replace the current shell-function-based tenant/project context management with an AWS-style profile configuration system. The `ICAV2_PROFILE` environment variable selects a named profile from `~/.icav2-cli-plugins/config`, enabling CLI plugin usage in subshells and non-interactive scripts. Additionally, bundle a local copy of the `icav2` binary at `~/.icav2-cli-plugins/bin/_icav2` to remove the dependency on `command icav2` being in PATH. Finally, optimize CLI startup performance, particularly for data commands, through lazy imports and reduced module loading.

## Glossary

- **CLI_Plugins**: The icav2-cli-plugins Python application that extends the icav2 CLI with additional subcommands
- **Profile**: A named configuration section within the config file that maps to a single ICAv2 tenant, containing credentials and project context
- **Config_File**: The INI-style configuration file at `~/.icav2-cli-plugins/config` that stores all profile definitions
- **Config_File_Parser**: The component responsible for reading and writing the Config_File
- **Active_Profile**: The profile currently selected via the `ICAV2_PROFILE` environment variable or the `[default]` profile
- **Local_Binary**: The icav2 CLI binary stored at `~/.icav2-cli-plugins/bin/_icav2` and used internally by the plugins
- **Session_Cache**: A per-profile file that caches the current access token to avoid regenerating tokens on every invocation
- **Installer**: The `install.sh` script that sets up the icav2-cli-plugins environment in the user's home directory

## Requirements

### Requirement 1: Profile Configuration File

**User Story:** As a developer, I want to define named profiles in a single config file, so that I can switch between tenants and projects without sourcing shell functions.

#### Acceptance Criteria

1. THE Config_File SHALL use INI-style format with sections named `[profile <name>]` for named profiles and `[default]` for the default profile, where `<name>` consists of 1 to 64 characters limited to alphanumeric characters, hyphens, and underscores
2. WHEN a profile section is defined, THE Config_File SHALL support the following keys: `server_url`, `x_api_key`, `project_id`, `project_name`, `token_tid`, and `output_format`
3. THE Config_File SHALL be located at the path `~/.icav2-cli-plugins/config`
4. IF the `server_url` key is absent from a profile, THEN THE CLI_Plugins SHALL default to `ica.illumina.com`
5. IF the `output_format` key is absent from a profile, THEN THE CLI_Plugins SHALL default to `table`
6. THE Config_File SHALL accept the following values for the `output_format` key: `table`, `json`, and `yaml`
7. IF the config file does not exist or cannot be parsed, THEN THE CLI_Plugins SHALL exit with a non-zero status code and display an error message indicating the file is missing or malformed

### Requirement 2: Profile Selection via Environment Variable

**User Story:** As a developer, I want to select a profile via the `ICAV2_PROFILE` environment variable, so that my scripts work in subshells without requiring parent shell state.

#### Acceptance Criteria

1. WHEN the `ICAV2_PROFILE` environment variable is set to a non-empty value, THE CLI_Plugins SHALL load the profile matching that exact name from the Config_File
2. WHEN the `ICAV2_PROFILE` environment variable is not set or is set to an empty string, THE CLI_Plugins SHALL load the `[default]` profile from the Config_File
3. IF the Config_File does not exist or is not readable, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message indicating the Config_File path and that it could not be found or read
4. IF the specified profile does not exist in the Config_File, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message indicating the profile name that was not found and listing all available profile names from the Config_File
5. THE CLI_Plugins SHALL resolve configuration in the following precedence order (highest to lowest): explicit environment variables (`ICAV2_ACCESS_TOKEN`, `ICAV2_PROJECT_ID`, `ICAV2_BASE_URL`), then profile values from the Config_File
6. WHEN a profile is loaded, THE CLI_Plugins SHALL set the internal server URL, API key, and project context from the profile values, using the default value `ica.illumina.com` for server URL if the `server_url` key is absent from the profile
7. IF the `[default]` profile does not exist in the Config_File and no `ICAV2_PROFILE` environment variable is set, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message indicating that no default profile is configured and listing available profiles

### Requirement 3: Profile Configuration Parser

**User Story:** As a developer, I want the config file to be reliably parsed, so that profile values are correctly loaded regardless of whitespace or comment formatting.

#### Acceptance Criteria

1. THE Config_File_Parser SHALL parse INI-style sections delimited by `[section_name]` headers and key-value pairs separated by a `=` delimiter on each non-blank, non-comment line
2. THE Config_File_Parser SHALL treat lines whose first non-whitespace character is `#` or `;` as comments and ignore them
3. THE Config_File_Parser SHALL trim leading and trailing whitespace from both keys and values while preserving internal whitespace within values
4. THE Config_File_Parser SHALL support the `[default]` section header as the default profile, equivalent to a profile with no explicit name prefix
5. THE Config_File_Parser SHALL support named profiles in the format `[profile <name>]` where `<name>` contains only alphanumeric characters, hyphens, and underscores and is between 1 and 64 characters in length
6. FOR ALL valid Config_File contents, parsing then serializing then parsing SHALL produce a configuration object with identical section names, keys, and values as the original parse result (round-trip property)
7. IF a line is not blank, not a comment, not a section header, and does not contain a `=` delimiter, THEN THE Config_File_Parser SHALL raise a parse error indicating the line number and content of the malformed line
8. IF a section contains duplicate keys, THEN THE Config_File_Parser SHALL use the last occurrence of that key as the effective value for the section

### Requirement 4: Token Caching per Profile

**User Story:** As a developer, I want access tokens to be cached per profile, so that repeated CLI invocations do not require a new token generation on each call.

#### Acceptance Criteria

1. WHEN a token is generated for a profile, THE Session_Cache SHALL create the directory `~/.icav2-cli-plugins/cache/<profile_name>/` if it does not exist and store the token in `~/.icav2-cli-plugins/cache/<profile_name>/session.yaml` with file permissions readable only by the owner (mode 0600)
2. WHEN a CLI invocation requires an access token, IF a cached token exists in the profile's `session.yaml` and has more than 3600 seconds until the JWT `exp` claim, THEN THE CLI_Plugins SHALL use the cached token without generating a new one
3. WHEN a CLI invocation requires an access token, IF the cached token is expired or has 3600 seconds or fewer until the JWT `exp` claim, THEN THE CLI_Plugins SHALL generate a new token from the profile API key and update the cache
4. IF token generation from the API key fails, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message that includes the profile name and server URL
5. THE Session_Cache SHALL store the access token and the epoch time of token generation as YAML keys in `session.yaml`
6. IF the cached `session.yaml` file exists but contains invalid YAML or is missing required keys, THEN THE CLI_Plugins SHALL treat the cache as absent and generate a new token from the profile API key

### Requirement 5: Local icav2 Binary Bundling

**User Story:** As a developer, I want the icav2 binary bundled locally, so that the plugins do not depend on the user having the icav2 CLI independently installed and discoverable in PATH.

#### Acceptance Criteria

1. THE Installer SHALL download the icav2 binary matching the current platform (linux, darwin) and architecture (amd64, arm64) during installation
2. IF the Installer cannot determine a supported platform and architecture combination, THEN THE Installer SHALL exit with a non-zero exit code and an error message indicating the detected platform and architecture are unsupported
3. THE Installer SHALL store the downloaded binary at `~/.icav2-cli-plugins/bin/_icav2`
4. THE Installer SHALL set executable permissions (mode 0755) on the downloaded binary
5. IF the download of the icav2 binary fails due to a network error or non-success HTTP status, THEN THE Installer SHALL exit with a non-zero exit code and an error message indicating the download failure
6. WHEN the CLI_Plugins need to invoke the upstream icav2 CLI, THE CLI_Plugins SHALL use the binary at `~/.icav2-cli-plugins/bin/_icav2`
7. IF the local binary at `~/.icav2-cli-plugins/bin/_icav2` does not exist, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message instructing the user to re-run the installer

### Requirement 6: Performance Optimization through Lazy Imports

**User Story:** As a developer, I want CLI commands to start quickly, so that interactive use and scripted invocations have minimal latency overhead.

#### Acceptance Criteria

1. THE CLI_Plugins SHALL defer importing subcommand modules until the specific subcommand is dispatched
2. THE CLI_Plugins SHALL defer importing `wrapica`, `libica`, `pandas`, `cwl_utils`, `cwltool`, `nf_core`, `matplotlib`, and `beautifulsoup4` until a subcommand that requires them is executed
3. WHEN the `projectdata` subcommand group is invoked, THE CLI_Plugins SHALL import only the specific data subcommand module requested (e.g., `ls`, `find`, `view`)
4. THE CLI_Plugins main entry point (`cli.py`) SHALL complete argument parsing and subcommand dispatch without importing any module beyond `docopt`, `sys`, and standard-library modules used by the `utils/__init__.py` package (i.e., `re`, `typing`, `urllib.parse`, `uuid`, `ast`); ICAv2 API libraries MAY be imported during CLI startup for non-help/non-version subcommands
5. WHEN running the `help` or `version` subcommand, THE CLI_Plugins SHALL respond without importing any ICAv2 API libraries (`wrapica`, `libica`) or heavy data libraries (`pandas`, `matplotlib`, `cwl_utils`, `cwltool`, `nf_core`, `beautifulsoup4`)
6. THE CLI_Plugins `subcommands/__init__.py` module SHALL defer all imports of `wrapica`, `libica`, and `pandas` to the point of first use within the `Command` or `DocOptArg` classes, rather than importing them at module level
7. WHEN the `help` or `version` subcommand is executed, THE CLI_Plugins SHALL produce output within 500 milliseconds on a system where Python interpreter startup takes no more than 100 milliseconds

### Requirement 7: Removal of Shell Function Dependency for Command Dispatch

**User Story:** As a developer, I want to run icav2 plugin commands directly as a standalone executable without sourcing shell functions, so that scripts and subshells work without special shell configuration.

#### Acceptance Criteria

1. THE CLI_Plugins SHALL provide a standalone entry point that resolves the active profile from the `--profile` flag, the `ICAV2_PROFILE` environment variable, or the `[default]` section of the Config_File (checked in that precedence order), validates or refreshes the access token, and dispatches the command, without requiring shell functions to be sourced
2. WHEN a plugin subcommand is invoked, THE CLI_Plugins SHALL resolve the active profile per the precedence order in criterion 1, confirm the access token is present and not expiring within 3600 seconds, refresh the token from the stored API key if expired, and execute the subcommand only after a valid token is obtained within a single process
3. WHEN a non-plugin subcommand is invoked (e.g., standard icav2 commands like `projects list`), THE CLI_Plugins SHALL delegate to the Local_Binary with the environment variables `ICAV2_ACCESS_TOKEN`, `ICAV2_BASE_URL`, and `ICAV2_PROJECT_ID` set from the resolved profile context
4. THE CLI_Plugins SHALL support a `--profile` CLI flag as an alternative to the `ICAV2_PROFILE` environment variable, with the flag taking precedence over environment variables
5. IF the active profile cannot be resolved because no `--profile` flag, no `ICAV2_PROFILE` environment variable, and no `[default]` section in the Config_File are available, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message indicating that a profile must be configured
6. IF the access token is expired and the token refresh from the stored API key fails, THEN THE CLI_Plugins SHALL exit with a non-zero exit code and an error message indicating the token refresh failure

### Requirement 8: Profile Management Commands

**User Story:** As a developer, I want commands to create and list profiles, so that I can manage my configuration without manually editing the config file.

#### Acceptance Criteria

1. WHEN the `icav2 configure set` command is run with a profile name, THE CLI_Plugins SHALL prompt for `server_url`, `x_api_key`, and `project_name` in sequence, then write the profile to the Config_File under a section named after the provided profile name
2. WHEN the `icav2 configure list` command is run and one or more profiles exist in the Config_File, THE CLI_Plugins SHALL display a table listing each configured profile name alongside its server URL
3. WHEN the `icav2 configure set` command is run without a profile name, THE CLI_Plugins SHALL write to the `[default]` section of the Config_File
4. IF the Config_File does not exist when running `icav2 configure set`, THEN THE CLI_Plugins SHALL create the Config_File and its parent directory, and set file permissions to mode 0600 (owner read/write only)
5. WHEN the user provides an API key during `icav2 configure set`, THE CLI_Plugins SHALL attempt token generation using the provided API key and server URL, and save the profile only after successful token generation
6. IF API key validation fails during `icav2 configure set` (token generation returns an error), THEN THE CLI_Plugins SHALL display an error message indicating the API key is invalid, discard all entered values for that profile, and exit without modifying the Config_File
7. IF the `icav2 configure list` command is run and no profiles exist in the Config_File, THEN THE CLI_Plugins SHALL display a message indicating no profiles are configured
8. WHEN the `icav2 configure set` command is run with a profile name that already exists in the Config_File, THE CLI_Plugins SHALL overwrite the existing profile section with the newly provided values

### Requirement 9: Backward Compatibility with Existing Environment Variables

**User Story:** As a developer, I want existing environment variable overrides to continue working, so that I can migrate gradually from the old shell-function approach to profiles.

#### Acceptance Criteria

1. WHEN `ICAV2_ACCESS_TOKEN` is set to a non-empty value in the environment, THE CLI_Plugins SHALL use it directly instead of loading a token from the profile or cache
2. IF `ICAV2_ACCESS_TOKEN` is set in the environment but contains an expired or malformed JWT token, THEN THE CLI_Plugins SHALL reject the token and return an error message indicating the token is invalid or expired without falling back to the profile token
3. WHEN `ICAV2_PROJECT_ID` is set to a non-empty value in the environment, THE CLI_Plugins SHALL use it instead of the project configured in the profile
4. WHEN `ICAV2_BASE_URL` is set to a non-empty value in the environment, THE CLI_Plugins SHALL use it instead of constructing the URL from the profile `server_url`
5. WHEN `ICAV2_TENANT_NAME` is set to a non-empty value in the environment and `ICAV2_PROFILE` is not set, THE CLI_Plugins SHALL treat the value of `ICAV2_TENANT_NAME` as the profile name for resolving session files and configuration
6. WHEN both `ICAV2_PROFILE` and `ICAV2_TENANT_NAME` are set in the environment, THE CLI_Plugins SHALL use the value of `ICAV2_PROFILE` as the profile name and ignore `ICAV2_TENANT_NAME`
7. THE CLI_Plugins SHALL resolve configuration values in the following precedence order from highest to lowest: explicit environment variables (`ICAV2_ACCESS_TOKEN`, `ICAV2_PROJECT_ID`, `ICAV2_BASE_URL`), then `ICAV2_PROFILE` configuration, then `ICAV2_TENANT_NAME` configuration, then the default profile

### Requirement 10: Installer Updates for New Architecture

**User Story:** As a developer, I want the installer to set up the new profile-based configuration, so that fresh installations use the new system by default.

#### Acceptance Criteria

1. THE Installer SHALL create the directory structure `~/.icav2-cli-plugins/bin/`, `~/.icav2-cli-plugins/cache/`, and the Config_File if they do not exist, setting file permissions on the Config_File to mode 0600 (owner read/write only)
2. THE Installer SHALL download the icav2 binary matching the current operating system (linux or darwin) and architecture (amd64 or arm64), place it at `~/.icav2-cli-plugins/bin/_icav2`, and set executable permissions on it
3. IF the icav2 binary download fails, THEN THE Installer SHALL immediately abort all remaining setup operations, exit with a non-zero status, and display an error message indicating the download URL and failure reason
4. THE Installer SHALL generate a `source.sh` that only sets `ICAV2_CLI_PLUGINS_HOME` to `~/.icav2-cli-plugins` and prepends `~/.icav2-cli-plugins/bin/` to PATH
5. THE Installer SHALL not require `command icav2` to be pre-installed as a prerequisite and SHALL remove the icav2 CLI version check from its prerequisite validation
6. WHEN an existing `~/.icav2-cli-plugins/tenants/` directory is detected and the Installer is running interactively (stdin is a terminal), THE Installer SHALL prompt the user to confirm migration of existing tenant configurations into profiles in the Config_File
7. IF the user declines the migration prompt or the Installer is running non-interactively, THEN THE Installer SHALL skip migration and leave the existing `tenants/` directory unchanged
