#!/usr/bin/env python3

"""
Initialise a tenant from an api key
"""
# Standard imports
import os
from pathlib import Path
from typing import Optional
from getpass import getpass
from ruamel.yaml import YAML

# Utils
from ...utils.config_helpers import (
    create_access_token_from_api_key, get_jwt_token_obj,
    get_project_name_from_project_id_curl, get_project_id_from_project_name_curl,
    get_tenant_id_from_b64_tid
)
from ...utils.globals import ICAV2_ACCESS_TOKEN_AUDIENCE
from ...utils.logger import get_logger
from ...utils.plugin_helpers import get_tenants_directory, get_default_tenant_file_path
from ...utils.tenant_helpers import (
    get_session_file_path_from_config_file, get_tenant_id_from_project_list,
    get_tenant_name_from_project_list
)

# Locals
from .. import Command, DocOptArg

# Get logger
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

    tenant_name: str
    default_project: Optional[str]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "tenant_name": DocOptArg(
                cli_arg_keys=["tenant_name"],
            ),
            "default_project": DocOptArg(
                cli_arg_keys=["--default-project"],
            )
        }

        # The tenant name provided by the user
        self.tenant_path: Optional[Path] = None
        self.tenant_config_file: Optional[Path] = None
        self.tenant_session_file: Optional[Path] = None

        # Store the tenant namespace and id in the configuration yaml
        self.x_api_key: Optional[str] = None
        self.access_token: Optional[str] = None
        self.tenant_namespace: Optional[str] = None
        self.tid: Optional[str] = None
        self.tns: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.tenant_name: Optional[str] = None
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
        # Set the ICAV2_TENANT_NAME env var before calling this function
        os.environ["ICAV2_TENANT_NAME"] = self.tenant_name
        # And write out the initial config file (containing just the server url and api key)
        self.write_config_file()

        # Now collect the access token which will query the server url from the configuration file
        self.access_token = create_access_token_from_api_key(
            self.x_api_key
        )

        # From the access token, collect the namespace and id
        token_obj = get_jwt_token_obj(self.access_token, ICAV2_ACCESS_TOKEN_AUDIENCE)
        self.tns = token_obj.get("tns")
        self.tid = token_obj.get("tid")

        # Use the access token to collect the project name if set
        if self.project_id is not None:
            self.project_name = get_project_name_from_project_id_curl(
                base_url=f"https://{self.server_url}/ica/rest",
                project_id=self.project_id,
                access_token=self.access_token
            )
        elif self.project_name is not None:
            self.project_id = get_project_id_from_project_name_curl(
                base_url=f"https://{self.server_url}/ica/rest",
                project_name=self.project_name,
                access_token=self.access_token
            )

        # Write out configuration yaml to file
        self.write_config_file()
        # Chmod of config file to 600
        self.tenant_config_file.chmod(0o600)

        # Now define the session file
        self.tenant_session_file = get_session_file_path_from_config_file(self.tenant_config_file)
        self.write_session_file()

        # Chmod of session file to 600
        self.tenant_session_file.chmod(0o600)

        # Check if default tenant is empty
        if not get_default_tenant_file_path().is_file() or get_default_tenant_file_path().read_text() == "":
            # Write the default tenant file
            get_default_tenant_file_path().write_text(self.tenant_name+"\n")

    def write_session_file(self):
        yaml = YAML()

        with open(self.tenant_session_file, "w") as file_h:
            yaml.dump(
                dict(
                    filter(
                        lambda dict_iter: dict_iter[1] is not None,
                        {
                            "access-token": self.access_token,
                            "project-id": self.project_id
                        }.items()
                    )
                ),
                file_h
            )

    def write_config_file(self):
        yaml = YAML()

        with open(self.tenant_config_file, "w") as file_h:
            yaml.dump(
                dict(
                    filter(
                        lambda dict_iter: dict_iter[1] is not None,
                        {
                            "server-url": self.server_url,
                            "x-api-key": self.x_api_key,
                            "token-tid": get_tenant_id_from_b64_tid(self.tid) if self.tid is not None else None,
                            "token-tns": self.tns,
                            "api-tid": get_tenant_id_from_project_list(
                                base_url=f"https://{self.server_url}/ica/rest",
                                access_token=self.access_token
                            ) if self.access_token is not None else None,
                            "api-tns": get_tenant_name_from_project_list(
                                base_url=f"https://{self.server_url}/ica/rest",
                                access_token=self.access_token
                            ) if self.access_token is not None else None,
                        }.items()
                    )
                ),
                file_h
            )

    def check_args(self):
        # Create the tenant directory
        self.tenant_path = get_tenants_directory() / self.tenant_name
        self.tenant_path.mkdir(mode=0o700, parents=True, exist_ok=True)

        # Set the tenant session and config files
        self.tenant_config_file = self.tenant_path / "config.yaml"
