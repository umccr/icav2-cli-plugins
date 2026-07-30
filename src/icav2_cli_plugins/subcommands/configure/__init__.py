#!/usr/bin/env python3
"""
Configure subcommand group for profile management.

Provides commands to create, list, and manage profiles in the
~/.icav2-cli-plugins/config file.

Subcommands:
  set   - Interactively configure a profile
  list  - Display all configured profiles
"""

# Command registration mapping for the configure subcommand group
CONFIGURE_SUBCOMMANDS = {
    "set": "icav2_cli_plugins.subcommands.configure.configure_set",
    "list": "icav2_cli_plugins.subcommands.configure.configure_list",
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
