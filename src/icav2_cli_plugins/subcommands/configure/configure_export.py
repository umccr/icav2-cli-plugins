#!/usr/bin/env python3
"""
Configure export command - emit shell export lines for a profile.

Resolves the named profile (merging its referenced tenant), obtains a fresh
access token, and prints four shell `export` lines to stdout so they can be
eval'd into the current shell, e.g.

    eval "$(icav2 configure export my-profile)"
"""

import sys
from pathlib import Path

from docopt import docopt

from icav2_cli_plugins.utils.globals import CONFIG_FILE_PATH
from icav2_cli_plugins.utils.profile_resolver import ProfileResolver
from icav2_cli_plugins.utils.token_manager import TokenManager


class Command:
    """
Usage:
    icav2 configure export help
    icav2 configure export [<profile>]

Description:
    Print four shell export lines for the resolved profile (merged with its
    referenced tenant), using a fresh access token:

        export ICAV2_SERVER_URL=<server_url>
        export ICAV2_BASE_URL=https://<server_url>/ica/rest
        export ICAV2_PROJECT_ID=<project_id>
        export ICAV2_ACCESS_TOKEN=<access_token>

    The profile is resolved from (highest precedence first): the <profile>
    positional argument, then the ICAV2_PROFILE environment variable. If
    neither is set, the [default] profile is used.

Options:
    <profile>   Name of the profile to export (optional; overrides ICAV2_PROFILE)

Examples:
    eval "$(icav2 configure export my-profile)"
    export ICAV2_PROFILE=my-profile
    eval "$(icav2 configure export)"
    """

    def __init__(self, command_argv):
        self.args = docopt(self.__doc__, argv=command_argv)

        # Print help if requested
        if self.args.get("help"):
            print(self.__doc__)
            sys.exit(0)

        self.profile = self.args.get("<profile>")

    def __call__(self):
        # Resolve the profile (merges the referenced tenant)
        resolver = ProfileResolver(config_path=CONFIG_FILE_PATH, cli_profile=self.profile)
        config = resolver.resolve()

        # Obtain a fresh (or cached-fresh) access token for the tenant
        access_token = config.access_token
        if not access_token:
            if config.api_key is None:
                print(
                    f"Error: Profile '{config.profile_name}' has no API key configured "
                    f"on its tenant. Run 'icav2 configure set-tenant' to set one.",
                    file=sys.stderr,
                )
                sys.exit(1)

            token_manager = TokenManager(
                tenant_name=config.tenant_name,
                config_path=CONFIG_FILE_PATH,
                private_key_path=(
                    Path(config.encryption_private_key)
                    if config.encryption_private_key
                    else None
                ),
                public_key_path=(
                    Path(config.encryption_public_key)
                    if config.encryption_public_key
                    else None
                ),
            )
            try:
                access_token = token_manager.get_valid_token(
                    api_key=config.api_key,
                    base_url=config.base_url,
                    cached_token=config.cached_access_token,
                )
            except RuntimeError as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)

        # Emit exactly four export lines, in order
        print(f"export ICAV2_SERVER_URL={config.server_url}")
        print(f"export ICAV2_BASE_URL=https://{config.server_url}/ica/rest")
        print(f"export ICAV2_PROJECT_ID={config.project_id}")
        print(f"export ICAV2_ACCESS_TOKEN={access_token}")
