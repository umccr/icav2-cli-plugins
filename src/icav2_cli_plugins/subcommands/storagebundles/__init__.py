#!/usr/bin/env python3

"""
Storage bundles
"""

# External
import sys

# Internal
from .. import SuperCommand


class StorageBundles(SuperCommand):
    """
Usage:
  icav2 storagebundles <command> <args...>

Plugin Commands:
  list        List the storage bundles available to the user

Flags:
  -h, --help   help for storagebundles

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 storagebundles [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):
        if cmd == "list":
            from .list import StorageBundlesList as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)

        # Initialise and return
        return subcommand(command_argv)
