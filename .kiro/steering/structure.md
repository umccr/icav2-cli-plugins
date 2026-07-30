# Project Structure

```
src/icav2_cli_plugins/
├── __init__.py
├── run/
│   └── icav2-cli-plugins.py       # Script runner (legacy entry)
├── utils/                          # Shared utility modules
│   ├── cli.py                      # Main entry point & command dispatch
│   ├── logger.py                   # Logging setup
│   ├── errors.py                   # Custom exceptions
│   ├── config_helpers.py           # Session/config file handling
│   ├── globals.py                  # Global constants
│   ├── typing_helpers.py           # Type introspection utilities
│   ├── projectdata_helpers.py      # Project data formatting
│   ├── projectanalysis_helpers.py  # Analysis utilities
│   ├── pipeline_helpers.py         # Pipeline utilities
│   ├── cwl_helpers.py              # CWL workflow utilities
│   ├── nextflow_helpers.py         # Nextflow utilities
│   ├── bundle_helpers.py           # Bundle utilities
│   ├── tenant_helpers.py           # Tenant config management
│   ├── gh_helpers.py               # GitHub API helpers
│   ├── encryption_helpers.py       # Token encryption
│   └── ...                         # Other domain helpers
└── subcommands/                    # CLI command implementations
    ├── __init__.py                 # Command & DocOptArg base classes
    ├── bundles/                    # icav2 bundles *
    ├── pipelines/                  # icav2 pipelines *
    ├── projectanalyses/            # icav2 projectanalyses *
    ├── projectdata/                # icav2 projectdata *
    ├── projectpipelines/           # icav2 projectpipelines *
    └── tenants/                    # icav2 tenants *
```

## Architecture Patterns

### Command Pattern

Every CLI subcommand is a class inheriting from `Command` (defined in `subcommands/__init__.py`).

1. **Docstring-as-usage** – The class docstring IS the docopt usage string
2. **Type-annotated attributes** – Class-level type annotations declare expected argument types
3. **DocOptArg mapping** – `_docopt_type_args` dict maps attribute names to `DocOptArg` instances that handle CLI/YAML/env resolution
4. **Magic coercion** – Arguments named `project`, `pipeline`, `data`, `region`, `bundle`, etc. are auto-coerced to their wrapica model types
5. **`check_args()`** – Validates arguments after assignment
6. **`__call__()`** – Executes the command logic

### Argument Resolution Order

Arguments are resolved with increasing precedence: environment variables → YAML input file → CLI flags.

### Shell Integration

- `shell_functions/` – Bash functions sourced into the user's shell (project/tenant context switching)
- `autocompletion/` – Generated bash/zsh completions from `autocompletion/specs/icav2.yaml`

### File Naming

- Subcommand files: `<action>.py` (e.g., `ls.py`, `find.py`, `bundles_init.py`)
- Helper modules: `<domain>_helpers.py`
- Class names: PascalCase matching the subcommand (e.g., `ProjectDataLs`, `BundlesInit`)
