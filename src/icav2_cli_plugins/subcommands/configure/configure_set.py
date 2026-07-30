#!/usr/bin/env python3
"""
Configure set command - interactively configure a profile.

Prompts for server_url, x_api_key, and project_name,
validates the API key by attempting token generation, and saves the
profile to the config file.
"""

import sys

from docopt import docopt

from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig, ConfigParseError
from icav2_cli_plugins.utils.globals import CONFIG_FILE_PATH, CACHE_DIR
from icav2_cli_plugins.utils.token_manager import TokenManager


class Command:
    """
Usage:
    icav2 configure set help
    icav2 configure set [<profile_name>]

Description:
    Interactively configure a profile. Prompts for server_url, x_api_key,
    and project_name. Validates the API key before saving.

Options:
    <profile_name>    Name of the profile to configure (defaults to 'default')

Examples:
    icav2 configure set
    icav2 configure set production
    """

    def __init__(self, command_argv):
        self.args = docopt(self.__doc__, argv=command_argv)

        # Print help if requested
        if self.args.get("help"):
            print(self.__doc__)
            sys.exit(0)

        self.profile_name = self.args.get("<profile_name>") or "default"

    def __call__(self):
        # Prompt interactively for profile values
        server_url = input("ICA server URL [ica.illumina.com]: ").strip() or "ica.illumina.com"
        x_api_key = input("ICA API key: ").strip()
        project_name = input("Default project name (optional): ").strip() or None

        # Validate that an API key was provided
        if not x_api_key:
            print(
                "Error: API key is required.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate the API key by attempting token generation
        base_url = f"https://{server_url}/ica/rest"
        token_manager = TokenManager(
            profile_name=self.profile_name,
            cache_dir=CACHE_DIR,
        )

        try:
            token_manager._generate_token(api_key=x_api_key, base_url=base_url)
        except RuntimeError as e:
            print(
                f"Error: API key validation failed - {e}",
                file=sys.stderr,
            )
            print(
                "The provided API key could not be validated. "
                "Profile was not saved.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Load existing config (or start fresh if file doesn't exist)
        parser = ConfigParser()
        try:
            profiles = parser.parse_file(CONFIG_FILE_PATH)
        except ConfigParseError:
            # File doesn't exist or is empty — start with an empty dict
            profiles = {}

        # Create/overwrite the profile
        profiles[self.profile_name] = ProfileConfig(
            name=self.profile_name,
            server_url=server_url,
            x_api_key=x_api_key,
            project_name=project_name,
        )

        # Write config file (creates file + parent dirs with mode 0600)
        parser.write_file(CONFIG_FILE_PATH, profiles)

        print(f"Profile '{self.profile_name}' configured successfully.")
