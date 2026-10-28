# Tech Stack

## Language & Runtime

- Python ≥ 3.12
- Package layout: `src/icav2_cli_plugins/`

## Build System

- **setuptools** (via pyproject.toml)
- Package manager: **uv** (uv.lock present) / pip compatible
- No test framework is currently configured in pyproject.toml

## Key Dependencies

| Library | Purpose |
|---------|---------|
| `docopt` | CLI argument parsing (docstring-driven) |
| `wrapica` | High-level ICAv2 API wrapper (typed models) |
| `libica` | Low-level ICAv2 SDK |
| `ruamel.yaml` | YAML read/write |
| `cwl_utils` / `cwltool` | CWL workflow parsing and validation |
| `nf-core` | Nextflow pipeline utilities |
| `pandas` | Tabular data handling |
| `requests` | HTTP client |
| `PyJWT` | JWT token handling |
| `boto3-stubs` / `mypy-boto3-s3` | Type stubs for AWS S3 interactions |
| `beautifulsoup4` | HTML parsing |
| `matplotlib` | Gantt chart generation |
| `tabulate` | CLI table formatting |
| `verboselogs` | Enhanced logging levels |
| `websocket_client` | WebSocket streaming |
| `fabric` / `invoke` | Remote/local command execution |
| `deepdiff` | Object comparison |
| `humanfriendly` | Human-readable sizes/durations |

## Common Commands

```bash
# Install in development mode
uv pip install -e .

# Install with optional pandoc support
uv pip install -e ".[pandoc]"

# Install with docs dependencies
uv pip install -e ".[docs]"

# Run the CLI entry point
icav2-cli-plugins.py <command> <subcommand> [args...]

# Full user installation (creates venv at ~/.icav2-cli-plugins/)
bash install.sh

# Bump version
bash dev_scripts/bump_version.sh

# Update autocompletion scripts
bash .github/scripts/update_autocompletion.sh
```

## CI/CD

- GitHub Actions workflows for release asset building and autocompletion updates
- Releases are built per-platform with the `build-release` composite action
