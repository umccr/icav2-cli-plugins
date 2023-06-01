#!/usr/bin/env python3

"""
List registered tenants for the plugin
"""

import json
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional, List, Dict
from getpass import getpass

import pandas as pd
from ruamel.yaml import YAML

from utils import is_uuid_format
from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id, create_access_token_from_api_key, get_jwt_token_obj, \
    get_project_name_from_project_id_curl, get_project_id_from_project_name_curl
from utils.cwl_helpers import ZippedCWLWorkflow
from utils.gh_helpers import download_zipped_workflow_from_github_release, get_release_repo_and_tag_from_release_url
from utils.globals import ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE, ICAv2AnalysisStorageSize, ICAV2_ACCESS_TOKEN_AUDIENCE
from utils.logger import get_logger
from utils.plugin_helpers import get_tenants_directory
from utils.projectpipeline_helpers import get_analysis_storage_id_from_analysis_storage_size, create_params_xml
import requests

from urllib.parse import unquote

from subcommands import Command

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
