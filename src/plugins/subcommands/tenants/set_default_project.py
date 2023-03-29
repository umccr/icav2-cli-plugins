#!/usr/bin/env python

"""
Set the project id in the tenants session ica yaml file.
This means when tenants enter command is invoked the ICAV2_PROJECT_ID is added
"""


import json
import os
import shutil
from collections import OrderedDict
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional
from getpass import getpass

from invoke import Responder
from fabric import Connection

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


class TenantsSetDefaultProject(Command):
    """Usage:
    icav2 tenants set-default-project help
    icav2 tenants set-default-project <tenant_name>
                                      (--project-name <project_name)

Description:
    Given a tenant name and project name parameter, set the project in the tenants session ica yaml file.
    This means ICAV2_PROJECT_ID env var is added when icav2 tenants enter is used.

Options:
    --project-name <project_name>    Required

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 tenants set-default-project umccr-beta --project-name playground_v2
    """

    def __init__(self, command_argv):
        # The tenant name provided by the user
        self.tenant_name: Optional[str] = None
        self.tenant_path: Optional[Path] = None
        self.tenant_config_file: Optional[Path] = None
        self.tenant_session_file: Optional[Path] = None
        self.tenant_session_yaml_object: Optional[OrderedDict] = None

        self.tenant_api_key: Optional[str] = None
        self.tenant_access_token: Optional[str] = None

        self.project_id: Optional[str] = None

        # Server url
        self.server_url: Optional[str] = "ica.illumina.com"

        # Store the tenant namespace and id in the configuration yaml
        self.x_api_key: Optional[str] = None
        self.current_config_yaml_object: Optional[OrderedDict] = None

        super().__init__(command_argv)

    def __call__(self):
        # Update the tenant session config to have project_id as the project-id attribute
        self.tenant_session_yaml_object["project-id"] = self.project_id

        self.write_session_file()

    def check_args(self):
        # Check the tenant name arg exists
        tenant_name_arg = self.args.get("<tenant_name>", None)
        if tenant_name_arg is None:
            logger.error("Could not get arg <tenant_name>")
            raise InvalidArgumentError

        self.tenant_name = tenant_name_arg

        # Check the tenant directory
        self.tenant_path = get_tenants_directory() / self.tenant_name

        if not self.tenant_path.is_dir():
            logger.error(f"Could not find tenant {self.tenant_name}, have you run 'icav2 tenants init \"{self.tenant_name}\"'")

        # Set the tenant session and config files
        self.tenant_config_file = self.tenant_path / "config.yaml"
        self.tenant_session_file = self.tenant_path / ".session.ica.yaml"

        if self.tenant_session_file.is_file():
            self.read_tenant_session_file()
        else:
            self.tenant_session_yaml_object = {}

        # Get the project name parameter
        project_name_arg = self.args.get("--project-name", None)
        if project_name_arg is None:
            logger.error("Please specify project name argument")
            raise InvalidArgumentError

        # Collect tenant api key
        self.tenant_api_key = self.get_tenant_api_key()

        # Create access token from api key
        self.tenant_access_token = create_access_token_from_api_key(self.tenant_api_key)

        # Check project
        if is_uuid_format(project_name_arg):
            # Check project id is in tenant
            self.project_id = project_name_arg
        else:
            # Get project id from project name
            self.project_id = get_project_id_from_project_name_curl(project_name_arg, self.tenant_access_token)

    def get_tenant_api_key(self) -> str:
        """
        Get the tenant api key
        Returns:

        """
        yaml = YAML()

        with open(self.tenant_config_file, "r") as file_h:
            return yaml.load(file_h).get("x-api-key")

    def read_tenant_session_file(self):
        """
        Read the tenant config file
        Returns:

        """
        yaml = YAML()

        with open(self.tenant_session_file, "r") as file_h:
            self.tenant_session_yaml_object = yaml.load(file_h)

    def write_session_file(self):
        """
        Write the session file to update the access token
        Returns:

        """

        yaml = YAML()

        with open(self.tenant_session_file, "w") as file_h:
            yaml.dump(self.tenant_session_yaml_object, file_h)