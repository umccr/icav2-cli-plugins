#!/usr/bin/env python3
"""
ConfigureList command - Display all configured tenants and profiles.

Usage: icav2 configure list
"""

import sys

from icav2_cli_plugins.utils.config_parser import ConfigParser, ConfigParseError
from icav2_cli_plugins.utils.globals import CONFIG_FILE_PATH


class Command:
    """
    Usage:
        icav2 configure list

    Description:
        Display all configured tenants and profiles.

    Options:
        -h, --help  Show this help message
    """

    def __init__(self, command_argv):
        # Check for help flag
        if "--help" in command_argv or "-h" in command_argv or "help" in command_argv:
            self._help()

    def _help(self):
        """Print help and exit."""
        print(self.__doc__)
        sys.exit(0)

    def __call__(self):
        """Execute the configure list command."""
        parser = ConfigParser()

        try:
            tenants, profiles = parser.parse_file(CONFIG_FILE_PATH)
        except ConfigParseError:
            # Config file doesn't exist or can't be parsed — treat as nothing configured
            print("No profiles configured. Run 'icav2 configure set-profile' to create one.")
            sys.exit(0)

        if not tenants and not profiles:
            print("No profiles configured. Run 'icav2 configure set-profile' to create one.")
            sys.exit(0)

        # Display table of tenants
        if tenants:
            print(f"{'Tenant':<20} {'Server URL':<40}")
            print(f"{'-' * 20} {'-' * 40}")
            for name in sorted(tenants.keys()):
                tenant = tenants[name]
                print(f"{name:<20} {tenant.server_url:<40}")
            print("")

        # Display table of profiles with the tenant each references
        print(f"{'Profile':<20} {'Tenant':<20} {'Project':<30}")
        print(f"{'-' * 20} {'-' * 20} {'-' * 30}")
        for name in sorted(profiles.keys()):
            profile = profiles[name]
            tenant_name = profile.tenant_name or "-"
            project_name = profile.project_name or "-"
            print(f"{name:<20} {tenant_name:<20} {project_name:<30}")
