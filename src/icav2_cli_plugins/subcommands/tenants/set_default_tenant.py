#!/usr/bin/env python

"""
Update the users default config.yaml under ~/.icav2/config.yaml

Reads the users config.yaml under ~/.icav2-cli-plugins/tenants/<tenant_name>/config.yaml

Then runs icav2 config set and autofills the prompts using the Fabric package
but replaces the api-key prompt twith the api key found in ~/.icav2-cli-plugins/tenants/<tenant_name>/config.yaml
"""

# External imports
from pathlib import Path
from typing import Optional

# Util imports
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.plugin_helpers import get_tenants_directory, get_default_tenant_file_path

# Local imports
from .. import Command, DocOptArg

logger = get_logger()


class TenantsSetDefaultTenant(Command):
    """Usage:
    icav2 tenants set-default-tenant help
    icav2 tenants set-default-tenant <tenant_name>


Description:
    Sets a tenant initialised with tenants init as the default tenant.
    This will update the tenant-name under ~/.icav2-cli-plugins/tenants/default_tenant.txt
    This command will NOT update any existing environment variables such as ICAV2_ACCESS_TOKEN or ICAV2_PROJECT_ID.

Options:

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 tenants set-default-tenant umccr-beta
    """

    tenant_name: str

    def __init__(self, command_argv):
        # Add in the cli args
        self._docopt_type_args = {
            "tenant_name": DocOptArg(
                cli_arg_keys=["tenant_name"]
            )
        }

        # The tenant name provided by the user
        self.tenant_path: Optional[Path] = None

        super().__init__(command_argv)

    def __call__(self):
        # Set the default tenant
        default_tenant_path = get_default_tenant_file_path()

        if default_tenant_path.is_file():
            # Collect the current default tenant
            with open(default_tenant_path, 'r') as tenant_h:
                current_default_tenant = tenant_h.read().strip()
            if current_default_tenant == self.tenant_name:
                logger.info(f"{self.tenant_name} is already the default tenant")
                return
            else:
                # Check if the user would like to continue with the change
                continue_or_exit = input(
                    f"Default tenant is current set to {current_default_tenant}, "
                    f"would you like to update to {self.tenant_name}? (y/n): "
                )

                if continue_or_exit.lower() != 'y':
                    logger.info("Exiting...")
                    return

        with open(default_tenant_path, 'w') as tenant_h:
            tenant_h.write(self.tenant_name)

    def check_args(self):
        # Check the tenant directory
        self.tenant_path = get_tenants_directory() / self.tenant_name

        if not self.tenant_path.is_dir():
            logger.error(f"Could not find tenant {self.tenant_name}, have you run 'icav2 tenants init \"{self.tenant_name}\"'")
            raise InvalidArgumentError(f"Could not find tenant {self.tenant_name}")
