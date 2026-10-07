#!/usr/bin/env python3
"""
ConfigureList command - Display all configured profiles.

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
        Display all configured profiles.

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
            profiles = parser.parse_file(CONFIG_FILE_PATH)
        except ConfigParseError:
            # Config file doesn't exist or can't be parsed — treat as no profiles
            print("No profiles configured. Run 'icav2 configure set' to create one.")
            sys.exit(0)

        if not profiles:
            print("No profiles configured. Run 'icav2 configure set' to create one.")
            sys.exit(0)

        # Display table of profiles
        print(f"{'Profile':<20} {'Server URL':<40}")
        print(f"{'-' * 20} {'-' * 40}")

        for name in sorted(profiles.keys()):
            profile = profiles[name]
            print(f"{name:<20} {profile.server_url:<40}")
