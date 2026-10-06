#!/usr/bin/env python3

"""
Print the current JWT access token to stdout.

The access token is resolved by the top-level dispatcher (utils/cli.py) before
plugin commands run, and is exported into the environment as ICAV2_ACCESS_TOKEN.
This command simply prints that resolved token to stdout so it can be captured,
for example:

    export ICAV2_ACCESS_TOKEN="$(icav2 tokens export)"
"""

# External imports
from os import environ
import sys

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class TokensExport(Command):
    """Usage:
    icav2 tokens export help
    icav2 tokens export

Description:
    Print the current JWT access token to stdout.

    The token is resolved from the active profile (or from the ICAV2_ACCESS_TOKEN
    environment variable if set), refreshing it from the profile's API key if needed.

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)

Example:
    export ICAV2_ACCESS_TOKEN="$(icav2 tokens export)"
    """

    def __init__(self, command_argv):
        # No CLI args beyond help
        self._docopt_type_args = {}

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Nothing to validate
        pass

    def __call__(self):
        access_token = environ.get("ICAV2_ACCESS_TOKEN", None)

        if not access_token:
            logger.error(
                "No access token found. "
                "Ensure a profile is configured (run 'icav2 configure set') "
                "or set the ICAV2_ACCESS_TOKEN environment variable."
            )
            raise InvalidArgumentError

        print(access_token)
