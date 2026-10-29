#!/usr/bin/env python3
"""
Configure subcommand group for profile management.

Provides commands to create, list, and manage tenants and profiles in the
~/.icav2-cli-plugins/config file.

Subcommands:
  set-tenant      - Interactively configure a tenant (user-scoped credentials)
  set-profile     - Interactively configure a profile (project-scoped)
  export          - Emit shell export lines for a profile
  set             - (deprecated) Interactively configure a profile
  list            - Display all configured tenants and profiles
  generate-keys   - Generate RSA key pair for API key encryption
"""

# Command registration mapping for the configure subcommand group
CONFIGURE_SUBCOMMANDS = {
    "set-tenant": "icav2_cli_plugins.subcommands.configure.configure_set_tenant",
    "set-profile": "icav2_cli_plugins.subcommands.configure.configure_set_profile",
    "export": "icav2_cli_plugins.subcommands.configure.configure_export",
    "set": "icav2_cli_plugins.subcommands.configure.configure_set",
    "list": "icav2_cli_plugins.subcommands.configure.configure_list",
    "generate-keys": "icav2_cli_plugins.subcommands.configure.configure_generate_keys",
}


def get_configure_subcommand(subcommand_name: str):
    """
    Lazy-import and return the configure subcommand module.

    Parameters
    ----------
    subcommand_name : str
        The name of the configure subcommand (e.g., 'set', 'list')

    Returns
    -------
    module or None
        The imported subcommand module, or None if not found
    """
    import importlib

    module_path = CONFIGURE_SUBCOMMANDS.get(subcommand_name)
    if module_path is None:
        return None
    return importlib.import_module(module_path)
