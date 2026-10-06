#!/usr/bin/env python3

"""
Projects
"""

from .. import SuperCommand
import sys


class Projects(SuperCommand):
    """
Usage:
  icav2 projects <command> <args...>

Available Commands:
  create               Create a new project
  get                  Get details of a project
  list                 List projects

Flags:
  -h, --help   help for projects

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 projects [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):
        if cmd in ("create", "get", "list"):
            # Delegate to the native _icav2 binary
            self._delegate_to_icav2(command_argv)
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)
