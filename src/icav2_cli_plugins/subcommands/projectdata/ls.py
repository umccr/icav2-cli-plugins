#!/usr/bin/env python3

# External imports
from typing import List, Optional

# Libica
from libica.openapi.v2.model.project_data import ProjectData

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.projectdata_helpers import check_is_directory, list_data_non_recursively, list_files_short, list_files_long
from ...utils.logger import get_logger

# Locals
from .. import Command

logger = get_logger()


class ProjectDataLs(Command):
    """Usage:
    icav2 projectdata ls help
    icav2 projectdata ls [-l | --long-listing]
                         [-t | --time]
                         [-r | --reverse]
    icav2 projectdata ls <data_path>
                         [-l | --long-listing]
                         [-t | --time]
                         [-r | --reverse]


Description:
    List data in directory, similar to ls in a posix file system

Options:
    <data_path>             Optional, data path, defaults to '/'
    -l, --long-listing      Optional, use long-listing format to show owner, modification timestamp and size
    -t, --time              Optional, sort items by time
    -r, --reverse           Optional, reverse order

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example: icav2 projectdata ls /reference_data/
    """

    def __init__(self, command_argv):
        # Collect args from doc strings
        # command_argv = command_argv
        # command_argv[1] = {"<data_path>": command_argv[1]}
        self.data_path: Optional[str] = None
        self.project_id: Optional[str] = None
        self.sort_parameter: Optional[str] = None

        # Boolean args
        self.long_listing: Optional[bool] = False

        # Now initialise from super command
        super().__init__(command_argv)

    def check_args(self):
        # Check arguments
        data_path: str = self.args.get("<data_path>", None)
        if data_path is None:
            data_path = "/"

        # Check data path ends with a '/'
        if not data_path.endswith("/"):
            logger.error("data path parameter should end in a '/'")
            raise InvalidArgumentError
        self.data_path = data_path

        # Get project id
        self.project_id = get_project_id()

        # Check data path is a directory
        if self.data_path == "/":
            pass
        elif not check_is_directory(
                project_id=self.project_id,
                folder_path=self.data_path
        ):
            logger.error(f"Path '{self.data_path}' does not exist in project id '{self.project_id}'")
            raise ValueError

        # Check bool args
        if self.args.get("--long-listing", False):
            self.long_listing = True

        # Get sort order
        sort_prefix = "name"
        sort_suffix = "asc"
        if self.args.get("--time"):
            sort_prefix = "timeModified"
        if self.args.get("--reverse"):
            sort_suffix = "desc"

        self.sort_parameter = " ".join([sort_prefix, sort_suffix])

    def get_data_items(self) -> List[ProjectData]:
        """
        Get data items from the data path
        :return:
        """

        return list_data_non_recursively(
            project_id=self.project_id,
            parent_folder_path=self.data_path,
            sort=self.sort_parameter
        )

    def __call__(self):
        data_items: List[ProjectData] = self.get_data_items()

        logger.debug("Writing output")
        if not self.long_listing:
            list_files_short(data_items)
        else:
            list_files_long(data_items)
