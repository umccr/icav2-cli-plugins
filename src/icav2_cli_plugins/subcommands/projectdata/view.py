#!/usr/bin/env python3

"""
View a file
"""

# External data
from os import environ
from typing import Optional

# Wrapica imports
from wrapica.project_data import (
    create_download_url
)

# Get utils
from ...utils.config_helpers import get_project_id
from ...utils.projectdata_helpers import (
    view_in_browser, write_url_contents_to_stdout, ProjectData
)
from ...utils.logger import get_logger

# Get locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectDataView(Command):
    """Usage:
    icav2 projectdata view help
    icav2 projectdata view <data>
                           [-b | --browser]


Description:
    View a file to stdout

Options:
    <data>                  Required, path to file
    -b, --browser           Optional, display in browser


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Required, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    BROWSER                  Optional, required if --browser is set

Example: icav2 projectdata view /output_data/tiny.fastq.gz | zcat | head
"""

    project_data_obj: ProjectData
    is_browser: bool

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "project_data_obj": DocOptArg(
                cli_arg_keys=["data"],
            ),
            "is_browser": DocOptArg(
                cli_arg_keys=["browser"],
            ),
        }

        # Additional parameters
        self.download_url: Optional[str] = None
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

        # Check browser configuration
        if self.is_browser and not environ.get("BROWSER", None) is None:
            logger.error("--browser option set but BROWSER env var is empty")
            raise EnvironmentError

        # Get download url
        self.download_url: str = create_download_url(
            project_id=self.project_id,
            file_id=self.project_data_obj.data.id
        )

    def __call__(self):
        # Get files
        if self.is_browser:
            view_in_browser(self.download_url)
        else:
            write_url_contents_to_stdout(self.download_url)
