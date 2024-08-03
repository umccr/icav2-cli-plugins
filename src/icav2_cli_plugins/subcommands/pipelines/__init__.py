#!/usr/bin/env python3

"""
Pipelines
"""

from .. import SuperCommand
import sys


class Pipelines(SuperCommand):
    """
This is the root command for actions that act on pipelines

Usage:
  icav2 pipelines [command]

Available Commands:
  get               Get details of a pipeline
  list              List pipelines

Plugin Commands:
  status-check      Check pipeline state
  list-projects     List projects a pipeline can be found in

Flags:
  -h, --help   help for pipelines

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 pipelines [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):
        if cmd == "status-check":
            from .status_check import StatusCheck as subcommand
        elif cmd == "list-projects":
            from .list_projects import ListProjects as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)
        # Initialise and return
        return subcommand(command_argv)







