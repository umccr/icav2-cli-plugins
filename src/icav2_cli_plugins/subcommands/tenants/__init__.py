#!/usr/bin/env python3

"""
Tenants
"""

from .. import SuperCommand
import sys


class Tenants(SuperCommand):
    """
Usage:
  icav2 tenants <command> <args...>

Plugin Commands:
    init                 Initialise a tenant and provide an API Key used for that tenant
    enter                Enter a tenant (updates users ICAV2_ACCESS_TOKEN env var)
    list                 List available tenants to enter
    set-default-project  Set the default project for a given tenant
    set-default-tenant   Set the default tenant

Flags:
  -h, --help   help for tenants

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 tenants [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):

        if cmd == "init":
            from subcommands.tenants.tenants_init import TenantsInit as subcommand
        elif cmd == "list":
            from subcommands.tenants.tenants_list import TenantsList as subcommand
        elif cmd == "set-default-tenant":
            from subcommands.tenants.set_default_tenant import TenantsSetDefaultTenant as subcommand
        elif cmd == "set-default-project":
            from subcommands.tenants.set_default_project import TenantsSetDefaultProject as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)
        # Initialise and return
        return subcommand(command_argv)







