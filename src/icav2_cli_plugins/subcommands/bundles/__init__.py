#!/usr/bin/env python3

"""
Bundles
"""

# External imports
import sys

# Internal imports
from .. import SuperCommand


class Bundles(SuperCommand):
    """
Usage:
  icav2 bundles <command> <args...>

Plugin Commands:
    init                        Initialise a bundle
    get                         Get a bundle
    list                        List bundles
    add-data                    Add data to a bundle
    add-pipeline                Add pipeline to a bundle
    release                     Release a bundle
    add-bundle-to-project       Add a released bundle to a project
    remove-bundle-from-project  Remove a bundle from a project
    deprecate                   Deprecate a bundle


Flags:
  -h, --help   help for bundles

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 bundles [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):

        if cmd == "init":
            from .bundles_init import BundlesInit as subcommand
        elif cmd == 'get':
            from .bundles_get import BundlesGet as subcommand
        elif cmd == "release":
            from .bundles_release import BundlesRelease as subcommand
        elif cmd == "list":
            from .bundles_list import BundlesList as subcommand
        elif cmd == "add-data":
            from .bundles_add_data import BundlesAddData as subcommand
        elif cmd == "add-pipeline":
            from .bundles_add_pipeline import BundlesAddPipeline as subcommand
        elif cmd == "add-bundle-to-project":
            from .bundles_add_to_project import BundlesAddToProject as subcommand
        elif cmd == "remove-bundle-from-project":
            from .bundles_remove_from_project import BundlesRemoveFromProject as subcommand
        elif cmd == "deprecate":
            from .bundles_deprecate import BundlesDeprecate as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)
        # Initialise and return
        return subcommand(command_argv)







