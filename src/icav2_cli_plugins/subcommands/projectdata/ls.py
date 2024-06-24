#!/usr/bin/env python3
# External imports
from pathlib import Path
from typing import List, Optional

# Wrapica
from wrapica.enums import (
    DataType, ProjectDataSortParameter
)
from wrapica.project_data import (
    ProjectData,
    list_project_data_non_recursively
)

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.projectdata_helpers import (
    list_files_short, list_files_long
)
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class ProjectDataLs(Command):
    """Usage:
    icav2 projectdata ls help
    icav2 projectdata ls [<data>]
                         [-l | --long-listing]
                         [-t | --time]
                         [-r | --reverse]


Description:
    List data in directory, similar to ls in a posix file system

Options:
    <data_path>             Optional, path to icav2 data folder you wish to download from,
                            May also specify a folder id or an icav2 uri,
                            Default is the root folder '/'
    -l, --long-listing      Optional, use long-listing format to show owner, modification timestamp and size
    -t, --time              Optional, sort items by time
    -r, --reverse           Optional, reverse order

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example: icav2 projectdata ls /reference_data/
    """
    project_data_obj: Optional[ProjectData]
    long_listing: Optional[bool]
    sort_time: Optional[bool]
    sort_reverse: Optional[bool]

    def __init__(self, command_argv):
        # Collect args from doc strings
        self._docopt_type_args = {
            "project_data_obj": DocOptArg(
                cli_arg_keys=["data"],
            ),
            "long_listing": DocOptArg(
                cli_arg_keys=["--long-listing"],
            ),
            "sort_time": DocOptArg(
                cli_arg_keys=["--time"],
            ),
            "sort_reverse": DocOptArg(
                cli_arg_keys=["--reverse"],
            ),
        }

        # Set other commands
        self.project_id: Optional[str] = None
        self.data_path: Optional[Path] = None
        self.sort_parameter: Optional[str] = None

        super().__init__(command_argv)

    def check_args(self):
        # Get the project id
        self.project_id = get_project_id()

        # Check args
        if self.project_data_obj is not None:
            # Check data is a folder
            if not DataType(self.project_data_obj.data.details.data_type) == DataType.FOLDER:
                logger.error("data path parameter should end in a '/'")
                raise InvalidArgumentError

            # self.data = get_project_data_obj_from_project_id_and_path(
            #     self.project_id,
            #     Path("/"),
            #     data_type=DataType.FOLDER
            # )
            # Set data path
            self.data_path = Path(self.project_data_obj.data.details.path)
        else:
            self.data_path = Path("/")

        # Get project id
        self.project_id = get_project_id()

        # Get sort order
        if self.sort_reverse:
            if self.sort_time:
                self.sort_parameter = ProjectDataSortParameter.TIME_MODIFIED_DESC
            else:
                self.sort_parameter = ProjectDataSortParameter.NAME_DESC
        else:
            if self.sort_time:
                self.sort_parameter = ProjectDataSortParameter.TIME_MODIFIED
            else:
                self.sort_parameter = ProjectDataSortParameter.NAME

    def get_data_items(self) -> List[ProjectData]:
        """
        Get data items from the data path
        :return:
        """
        return list_project_data_non_recursively(
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
