#!/usr/bin/env python3

# External imports
from pathlib import Path
from typing import List, Optional

# Wrapica
from wrapica.enums import (
    DataType
)
from wrapica.literals import ProjectDataSortParameterType
from wrapica.project_data import (
    ProjectData,
    list_project_data_non_recursively
)

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.projectdata_helpers import (
    list_files_short, list_files_long, list_files_short_with_linked_suffix
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
                         [--include-linked]
                         [--case-insensitive]


Description:
    List data in directory, similar to ls in a posix file system

Options:
    <data>                  Optional, path to icav2 data folder you wish to download from,
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
    include_linked: Optional[bool]
    case_insensitive: Optional[bool]

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
            "include_linked": DocOptArg(
                cli_arg_keys=["--include-linked"],
            ),
            "case_insensitive": DocOptArg(
                cli_arg_keys=["--case-insensitive"],
            ),
        }
        # Set other commands
        self.project_id: Optional[str] = None
        self.data_id: Optional[str] = None
        self.data_path: Optional[Path] = None
        self.sort_parameter: Optional[ProjectDataSortParameterType] = None
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
            self.data_id = self.project_data_obj.data.id
            self.data_path = Path(self.project_data_obj.data.details.path)
        else:
            self.data_path = Path("/")

        # Get project id
        self.project_id = get_project_id()

        # Check if --include-linked is set, then --data-path must not be set
        if (
                self.include_linked and
                not self.data_path == Path("/")
        ):
            logger.error("--include-linked only supported at top directory")
            raise InvalidArgumentError

        # Get sort order
        if self.sort_time:
            self.sort_parameter = "timeModified"
        else:
            self.sort_parameter = "name"

        if self.sort_reverse:
            self.sort_parameter = f"-{self.sort_parameter}"


    def get_data_items(self) -> List[ProjectData]:
        """
        Get data items from the data path
        :return:
        """
        # If case sensitive, filter out the data items
        # API is case-insensitive, so we need to filter out the data items ourselves
        if not self.case_insensitive:
            project_data_list = list(
                filter(
                    lambda project_data_iter_: project_data_iter_.data.details.path.startswith(str(self.data_path)),
                    list_project_data_non_recursively(
                        project_id=self.project_id,
                        sort=self.sort_parameter,
                        **(
                            {
                                "parent_folder_id": self.data_id
                            }
                            if self.data_id is not None
                            else
                            {
                                "parent_folder_path": self.data_path
                            }
                        )
                    )
                )
            )
        else:
            project_data_list = list_project_data_non_recursively(
                project_id=self.project_id,
                sort=self.sort_parameter,
                **(
                    {
                        "parent_folder_id": self.data_id
                    }
                    if self.data_id is not None
                    else
                    {
                        "parent_folder_path": self.data_path
                    }
                )
            )

        if not self.include_linked:
            project_data_list = list(filter(
                lambda project_data_iter_: (
                    # Ensure owning project id matches the current project id
                    str(project_data_iter_.data.details.owning_project_id) == str(self.project_id)
                ),
                project_data_list
            ))

        return project_data_list


    def __call__(self):
        from datetime import datetime
        data_items: List[ProjectData] = self.get_data_items()

        logger.debug("Writing output")
        if not self.long_listing:
            list_files_short_with_linked_suffix(self.project_id, data_items)
        else:
            list_files_long(data_items)
