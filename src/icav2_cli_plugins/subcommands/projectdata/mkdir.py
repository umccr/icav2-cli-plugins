#!/usr/bin/env python3

"""
Create a directory, which isn't a trivial task, using the ICAv2 CLI
"""

# External data
from os import environ
from pathlib import Path
from typing import Optional
from urllib.parse import urlunparse, urlparse

from wrapica.data import coerce_data_id_path_or_icav2_uri_to_data_obj
# Wrapica imports
from wrapica.project_data import (
    create_folder_in_project
)
from ...utils import is_uri_format

# Get utils
from ...utils.config_helpers import get_project_id
from ...utils.errors import InvalidArgumentError
from ...utils.projectdata_helpers import (
    view_in_browser, write_url_contents_to_stdout, ProjectData
)
from ...utils.logger import get_logger

# Get locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectDataMkdir(Command):
    """Usage:
    icav2 projectdata mkdir help
    icav2 projectdata mkdir <data>
                           [-p | --parents]


Description:
    View a file to stdout

Options:
    <data>                  Required, path to file
    -p, --parents           Equal to mkdir -p, no error if existing, make parent directories as needed


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Required, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    BROWSER                  Optional, required if --browser is set

Example: icav2 projectdata mkdir /output_data/
"""

    parent_project_data_object: Optional[ProjectData] = None
    project_data_obj: None
    is_parents: bool

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "project_data_obj": DocOptArg(
                cli_arg_keys=["data"],
            ),
            "is_parents": DocOptArg(
                cli_arg_keys=["--parents"],
            ),
        }

        # Project id
        self.project_id: Optional[str] = None

        # Now initialise from super command
        super().__init__(command_argv)

    def check_args(self):
        """
        Check to ensure data_path object exists and ends with a '/'
        :return:
        """
        # Set the project id
        self.project_id = get_project_id()

        # We don't initialise the project data object before, because we need to check the value
        # ends with a '/' first
        if not self.project_data_obj.endswith('/'):
            logger.error(f"Data path '{self.project_data_obj}' must end with a '/' to create a folder.")
            raise InvalidArgumentError(f"Data path '{self.project_data_obj}' must end with a '/' to create a folder.")

        # If it's a uri we need to strip back to the parent and then create the folder inside that
        if is_uri_format(self.project_data_obj):
            # Coerce to data object
            data_uri = urlparse(self.project_data_obj)
            parent_uri = str(urlunparse((
                data_uri.scheme,
                data_uri.netloc,
                str(Path(data_uri.path).parent) + '/',
                None, None, None
            )))
            self.parent_project_data_object = coerce_data_id_path_or_icav2_uri_to_data_obj(
                parent_uri,
            )
        else:
            # Path format
            self.parent_project_data_object = coerce_data_id_path_or_icav2_uri_to_data_obj(
                str(Path(self.project_data_obj).parent) + '/',
                create_data_if_not_found=(
                    True if self.is_parents else False
                )
            )


    def __call__(self):
        create_folder_in_project(
            project_id=self.parent_project_data_object.project_id,
            folder_path=(
                    Path(self.parent_project_data_object.data.details.path) / Path(urlparse(self.project_data_obj).path).name
            ),
        )
