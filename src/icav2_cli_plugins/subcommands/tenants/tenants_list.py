#!/usr/bin/env python3

"""
List registered tenants for the plugin
"""

# External data
from typing import Optional, List, Dict
import pandas as pd
from ruamel.yaml import YAML

from ...utils.config_helpers import read_config_file
# Set utils
from ...utils.logger import get_logger
from ...utils.plugin_helpers import get_tenants_directory

# Locals
from .. import Command

logger = get_logger()


class TenantsList(Command):
    """Usage:
    icav2 tenants list help
    icav2 tenants list

Description:
    List all tenants

Options:

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 tenants list
    """

    def __init__(self, command_argv):
        self._docopt_type_args = {}
        # The tenant name provided by the user
        self.tenant_list: Optional[List] = None

        super().__init__(command_argv)

    def __call__(self):
        # Ask user (kindly) for the api key
        self.get_tenants()
        self.print_columns()

    def get_tenants(self):
        self.tenant_list = []
        tenants_directory = get_tenants_directory()

        # Iterate through tenants
        for tenant_dir in tenants_directory.glob("*"):
            if not tenant_dir.is_dir():
                continue
            if not (tenant_dir / "config.yaml").is_file():
                continue

            tenant_config_dict = read_config_file(tenant_name=tenant_dir.name)

            self.tenant_list.append(
                {
                    "name": tenant_dir.name,
                    "token_tid": tenant_config_dict.get("token-tid"),
                    "token_tns": tenant_config_dict.get("token-tns"),
                    "api_tid": tenant_config_dict.get("api-tid"),
                    "api_tns": tenant_config_dict.get("api-tns"),
                }
            )

        if len(self.tenant_list) == 0:
            logger.error("No tenants available, please initialise a tenant with 'icav2 tenants list'")
            raise ValueError

    def print_columns(self):
        pd.set_option('expand_frame_repr', False)
        pd.set_option('display.max_columns', 999)

        print(pd.DataFrame(self.tenant_list).to_markdown(index=False))

    def check_args(self):
        pass
