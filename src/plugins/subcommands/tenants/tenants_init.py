#!/usr/bin/env python3

"""
Initialise a tenant from an api key
"""

from pathlib import Path
from typing import Optional
from getpass import getpass

from ruamel.yaml import YAML

from utils import is_uuid_format
from utils.errors import InvalidArgumentError
from utils.config_helpers import create_access_token_from_api_key, get_jwt_token_obj, \
    get_project_name_from_project_id_curl, get_project_id_from_project_name_curl, get_icav2_base_url
from utils.globals import ICAV2_ACCESS_TOKEN_AUDIENCE
from utils.logger import get_logger
from utils.plugin_helpers import get_tenants_directory

from subcommands import Command
from utils.tenant_helpers import get_session_file_path_from_config_file

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
        self.server_url: Optional[str] = None  # "ica.illumina.com"

        # Add in the project id and name
        self.project_id: Optional[str] = None
        self.project_name: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        # Ask the user for the server url?
        server_url_input = input("server-url [ica.illumina.com]: ")
        if server_url_input == "":
            self.server_url = "ica.illumina.com"
        else:
            self.server_url = server_url_input

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
            self.project_name = get_project_name_from_project_id_curl(get_icav2_base_url(), self.project_id, self.access_token)
        elif self.project_name is not None:
            self.project_id = get_project_id_from_project_name_curl(get_icav2_base_url(), self.project_name, self.access_token)

        # Write out configuration yaml to file
        self.write_config_file()

        # Now define the session file
        self.tenant_session_file = get_session_file_path_from_config_file(self.tenant_config_file)
        self.write_session_file()


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

