#!/usr/bin/env python

"""
Update the users default config.yaml under ~/.icav2/config.yaml

Reads the users config.yaml under ~/.icav2-cli-plugins/tenants/<tenant_name>/config.yaml

Then runs icav2 config set and auto fills the prompts using the Fabric package
but replaces the api-key prompt twith the api key found in ~/.icav2-cli-plugins/tenants/<tenant_name>/config.yaml
"""


import json
import os
import shutil
from collections import OrderedDict
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional
from getpass import getpass

from invoke import Responder, run
from fabric import Connection

from ruamel.yaml import YAML

from utils import is_uuid_format
from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id, create_access_token_from_api_key, get_jwt_token_obj, \
    get_project_name_from_project_id_curl, get_project_id_from_project_name_curl, get_icav2_base_url
from utils.cwl_helpers import ZippedCWLWorkflow
from utils.gh_helpers import download_zipped_workflow_from_github_release, get_release_repo_and_tag_from_release_url
from utils.globals import ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE, ICAv2AnalysisStorageSize, ICAV2_ACCESS_TOKEN_AUDIENCE
from utils.logger import get_logger
from utils.plugin_helpers import get_tenants_directory
from utils.projectpipeline_helpers import get_analysis_storage_id_from_analysis_storage_size, create_params_xml
import requests

from urllib.parse import unquote, urlparse

from subcommands import Command
from utils.tenant_helpers import get_session_file_path_from_config_file

logger = get_logger()


class TenantsSetDefaultTenant(Command):
    """Usage:
    icav2 tenants set-default-tenant help
    icav2 tenants set-default-tenant <tenant_name>


Description:
    Sets a tenant initialised with tenants init as the default tenant.
    This will update the configuration yaml under ~/.icav2/config.yaml.
    This command will NOT update any existing environment variables such as ICAV2_ACCESS_TOKEN or ICAV2_PROJECT_ID.

Options:

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 tenants set-default-tenant umccr-beta
    """

    def __init__(self, command_argv):
        # The tenant name provided by the user
        self.tenant_name: Optional[str] = None
        self.tenant_path: Optional[Path] = None
        self.tenant_config_file: Optional[Path] = None
        self.tenant_config_yaml_object: Optional[OrderedDict] = None
        self.tenant_session_file: Optional[Path] = None
        self.server_url = None

        self.current_config_path: Optional[Path] = Path.home() / ".icav2" / "config.yaml"
        self.current_session_path: Optional[Path] = get_session_file_path_from_config_file(self.current_config_path)

        # Store the tenant namespace and id in the configuration yaml
        self.x_api_key: Optional[str] = None
        self.current_config_yaml_object: Optional[OrderedDict] = None

        super().__init__(command_argv)

    def __call__(self):
        # Collect the api key from the tenant config file
        self.read_tenant_config()

        if self.current_config_path.is_file():
            self.read_current_config()
        else:
            self.current_config_yaml_object = {
                "server-url": urlparse(get_icav2_base_url()).netloc,
                "x-api-key": None,
                "output-format": None,
                "colormode": None
            }

        # Fill out prompts
        self.fill_prompts()

        # Remove existing session files
        for session_file in Path.glob(Path("~/.icav2/").expanduser(), ".session.*.yaml"):
            if not session_file == Path("~/.icav2/").expanduser() / self.tenant_session_file.name:
                logger.info(f"Deleting session file {session_file}. Midfix does not match server url prefix of this tenant")
                os.remove(session_file)

        # Copy tenant session file
        if self.tenant_session_file.is_file():
            shutil.copy2(self.tenant_session_file, self.current_session_path)

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
        self.tenant_session_file = get_session_file_path_from_config_file(self.tenant_config_file)

    def read_tenant_config(self):
        """
        Read the tenant config file
        Returns:

        """
        yaml = YAML()

        with open(self.tenant_config_file, "r") as file_h:
            self.tenant_config_yaml_object = yaml.load(file_h)

        self.server_url = self.tenant_config_yaml_object.get("server-url", None)
        self.x_api_key = self.tenant_config_yaml_object.get("x-api-key", None)

    def read_current_config(self):
        """
        Read the current configuration file
        Returns:

        """
        yaml = YAML()

        with open(self.current_config_path, "r") as file_h:
            self.current_config_yaml_object = yaml.load(file_h)

    def fill_prompts(self):
        """
        Tenant config
        Returns:

        """

        icav2_config_set_server_url = Responder(
            pattern=f"server-url \[{self.current_config_yaml_object.get('server-url')}\]:",
            response=self.current_config_yaml_object.get("server-url") + "\n"
        )

        if self.current_config_yaml_object.get("x-api-key") is not None:
            icav2_config_set_api_key = Responder(
                pattern="API key \(press enter to keep the current one\) :",
                response=self.x_api_key + "\n"
            )
        else:
            icav2_config_set_api_key = Responder(
                pattern="API key :",
                response=self.x_api_key + "\n"
            )

        if self.current_config_yaml_object.get("output-format") is not None:
            icav2_config_set_output_format = Responder(
                pattern=f"output-format \[{self.current_config_yaml_object.get('output-format')}\]:",
                response=self.current_config_yaml_object.get("output-format") + "\n"
            )
        else:
            icav2_config_set_output_format = Responder(
                pattern=f"output-format \(allowed values table,yaml,json defaults to table\) :",
                response="\n"
            )

        if self.current_config_yaml_object.get('colormode') is not None:
            icav2_config_set_color_mode = Responder(
                pattern=f"colormode \[{self.current_config_yaml_object.get('colormode')}\]:",
                response=self.current_config_yaml_object.get("colormode") + "\n"
            )
        else:
            icav2_config_set_color_mode = Responder(
                pattern="colormode \(allowed values none,dark,light defaults to none\) :",
                response="\n"
            )

        run(
            "icav2 config set",
            pty=True,
            watchers=[
                icav2_config_set_server_url,
                icav2_config_set_api_key,
                icav2_config_set_output_format,
                icav2_config_set_color_mode
            ],
            hide='out'
        )
