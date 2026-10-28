#!/usr/bin/env python3

"""
Storage configurations
"""

# External
import sys

# Internal
from .. import SuperCommand


class StorageConfigurations(SuperCommand):
    """
Usage:
  icav2 storageconfigurations <command> <args...>

Plugin Commands:
  list        List the storage configurations available to the user

Flags:
  -h, --help   help for storageconfigurations

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 storageconfigurations [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):
        if cmd == "list":
            from .list import StorageConfigurationsList as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)

        # Initialise and return
        return subcommand(command_argv)
