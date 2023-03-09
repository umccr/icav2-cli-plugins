#!/usr/bin/env python3

"""
View a file
"""

import argparse
import os
from subprocess import SubprocessError
from typing import Optional

from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id_from_session_file, get_project_id
from utils.projectdata_helpers import check_is_file, \
    create_data_download_url, get_data_obj_from_project_id_and_path, view_in_browser, write_url_contents_to_stdout
from utils.logger import get_logger
from utils.subprocess_handler import run_subprocess_proc

from subcommands import Command

logger = get_logger()


class ProjectDataView(Command):
    """Usage:
    icav2 projectdata view help
    icav2 projectdata view <data_path>
                           [-b | --browser]


Description:
    View a file to stdout

Options:
    <data_path>             Required, path to file
    -b, --browser           Optional, display in browser


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Required, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    BROWSER                  Optional, required if --browser is set

Example: icav2 projectdata view /output_data/tiny.fastq.gz | zcat | head
"""

    def __init__(self, command_argv):
        # Initialise args
        self.data_path: Optional[str] = None
        self.project_id: Optional[str] = None
        self.data_id: Optional[str] = None
        self.is_browser: Optional[bool] = False
        self.download_url: Optional[str] = None

        # Now initialise from super command
        super().__init__(command_argv)

    def check_args(self):
        """
        Check to ensure data_path object exists and ends with a '/'
        :return:
        """

        # Get data path
        self.data_path: str = self.args.get("<data_path>", None)

        # Check data path is not None
        if self.data_path is None:
            logger.error("Please ensure <data_path> positional argument is specified")
            self._help(fail=True)

        # Get project id
        self.project_id = get_project_id()

        # Check data path ends with a '/'
        if self.data_path.endswith("/"):
            logger.error("view subcommand can only view files not folders")
            raise InvalidArgumentError

        # Check data path is a file
        if not check_is_file(
            project_id=self.project_id,
            file_path=self.data_path
        ):
            logger.error(f"Path '{self.data_path}' does not exist in project id '{self.project_id}'")
            raise ValueError

        self.data_id = get_data_obj_from_project_id_and_path(
            project_id=self.project_id,
            data_path=self.data_path
        ).data.get("id")

        # Check browser configuration
        self.is_browser = self.args.get("--browser", False)
        if self.is_browser and not os.environ.get("BROWSER", None) is None:
            logger.error("--browser option set but BROWSER env var is empty")
            raise EnvironmentError

        # Get download url
        self.download_url: str = create_data_download_url(
            project_id=self.project_id,
            data_id=self.data_id
        )

    def __call__(self):
        # Get files
        if self.is_browser:
            view_in_browser(self.download_url)
        else:
            write_url_contents_to_stdout(self.download_url)
