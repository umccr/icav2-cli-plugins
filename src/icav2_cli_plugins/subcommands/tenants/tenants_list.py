#!/usr/bin/env python3

"""
List registered tenants for the plugin
"""

# External data
from typing import Optional, List, Dict
import pandas as pd
from ruamel.yaml import YAML

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

            tenant_config_dict = self.read_config_file(tenant_dir / "config.yaml")

            self.tenant_list.append(
                {
                    "token_tid": tenant_config_dict.get("token-tid"),
                    "token_tns": tenant_config_dict.get("token-tns"),
                    "api_tid": tenant_config_dict.get("api-tid"),
                    "api_tns": tenant_config_dict.get("api-tns"),
                    "name": tenant_dir.name
                }
            )

        if len(self.tenant_list) == 0:
            logger.error("No tenants available, please initialise a tenant with 'icav2 tenants list'")
            raise ValueError

    def read_config_file(self, config_file) -> Dict:
        yaml = YAML()

        with open(config_file, "r") as file_h:
            return yaml.load(file_h)

    def print_columns(self):
        pd.set_option('expand_frame_repr', False)
        pd.set_option('display.max_columns', 999)

        print(pd.DataFrame(self.tenant_list).set_index("name"))

    def check_args(self):
        pass
