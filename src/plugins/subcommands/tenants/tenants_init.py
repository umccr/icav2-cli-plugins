#!/usr/bin/env python3

"""
Initialise a tenant from an api key
"""

import json
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional
from getpass import getpass

from ruamel.yaml import YAML

from utils import is_uuid_format
from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id, create_access_token_from_api_key, get_jwt_token_obj, \
    get_project_name_from_project_id_curl, get_project_id_from_project_name_curl
from utils.cwl_helpers import ZippedCWLWorkflow
from utils.gh_helpers import download_zipped_workflow_from_github_release, get_release_repo_and_tag_from_release_url
from utils.globals import ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE, ICAv2AnalysisStorageSize, ICAV2_ACCESS_TOKEN_AUDIENCE
from utils.logger import get_logger
from utils.plugin_helpers import get_plugins_directory, get_tenants_directory
from utils.projectpipeline_helpers import get_analysis_storage_id_from_analysis_storage_size, create_params_xml
import requests

from urllib.parse import unquote

from subcommands import Command

logger = get_logger()


class TenantsInit(Command):
    """Usage:
    icav2 tenants init help
    icav2 tenants init <tenant_name>
                       [--default-project <project_name>]

Description:
    Register a tenant to the icav2 plugins home.
    This script will prompt you to enter in an api key and will then also test generating a token

Options:
  --default-project=<project_name>   Optional, set a default project (this can be set later with icav2 tenants set-default-project

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 tenants init umccr-beta
    """

    def __init__(self, command_argv):
        # The tenant name provided by the user
        self.tenant_name: Optional[str] = None
        self.tenant_path: Optional[Path] = None
        self.tenant_config_file: Optional[Path] = None
        self.tenant_session_file: Optional[Path] = None

        # Store the tenant namespace and id in the configuration yaml
        self.x_api_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.tenant_namespace: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.server_url: Optional[str] = "ica.illumina.com"

        # Add in the project id and name
        self.project_id: Optional[str] = None
        self.project_name: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        # Ask user (kindly) for the api key
        self.x_api_key = getpass(
            prompt=f"Please enter your api key for tenant '{self.tenant_name}' followed by the enter key: "
        )

        # Create the access token
        self.access_token = create_access_token_from_api_key(
            self.x_api_key
        )

        # From the access token, collect the namespace and id
        token_obj = get_jwt_token_obj(self.access_token, ICAV2_ACCESS_TOKEN_AUDIENCE)
        self.tenant_namespace = token_obj.get("tns")
        self.tenant_id = token_obj.get("tid")

        # Use the access token to collect the project name if set
        if self.project_id is not None:
            self.project_name = get_project_name_from_project_id_curl(self.project_id, self.access_token)
        elif self.project_name is not None:
            self.project_id = get_project_id_from_project_name_curl(self.project_name, self.access_token)

        # Write out configuration yaml to file
        self.write_session_file()
        self.write_config_file()

    def write_session_file(self):
        yaml = YAML()

        with open(self.tenant_session_file, "w") as file_h:
            yaml.dump(
                {
                    "access-token": self.access_token,
                    "project-id": self.project_id
                },
                file_h
            )

    def write_config_file(self):
        yaml = YAML()

        with open(self.tenant_config_file, "w") as file_h:
            yaml.dump(
                {
                    "server-url": self.server_url,
                    "x-api-key": self.x_api_key,
                    "tid": self.tenant_id,
                    "tns": self.tenant_namespace
                },
                file_h
            )

    def check_args(self):
        # Check the tenant name arg exists
        tenant_name_arg = self.args.get("<tenant_name>", None)
        if tenant_name_arg is None:
            logger.error("Could not get arg <tenant_name>")
            raise InvalidArgumentError

        self.tenant_name = tenant_name_arg

        project_name_arg = self.args.get("--project-name", None)
        if project_name_arg is not None:
            if is_uuid_format(project_name_arg):
                self.project_id = project_name_arg
            else:
                self.project_name = project_name_arg

        # Create the tenant directory
        self.tenant_path = get_tenants_directory() / self.tenant_name
        self.tenant_path.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Set the tenant session and config files
        self.tenant_config_file = self.tenant_path / "config.yaml"
        self.tenant_session_file = self.tenant_path / ".session.ica.yaml"
