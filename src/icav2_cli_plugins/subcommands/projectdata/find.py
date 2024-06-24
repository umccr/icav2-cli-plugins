#!/usr/bin/env python3
from pathlib import Path

# External imports
from typing import List, Optional, Union, Pattern

# Wrapica imports
from wrapica.project_data import ProjectData
from wrapica.enums import DataType
from wrapica.project_data import find_project_data_recursively
from wrapica.user import User

# Utils imports
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg
from ...utils.projectdata_helpers import list_files_short, list_files_long

# Set logger
logger = get_logger()


class ProjectDataFind(Command):
    """Usage:
    icav2 projectdata find help
    icav2 projectdata find [<data>]
                           [-w=<min_depth> | --min-depth=<min_depth>]
                           [-x=<max_depth> | --max-depth=<max_depth]
                           [--type=<type>]
                           [-n=<name> | --name=<name>]
                           [-c=<creator_username_or_id> | --creator=<creator_username_or_id>]
                           [-l | --long-listing]
                           [-t | --time]
                           [-r | --reverse]

Description:
    Find data in directory, similar to find in a posix file system.

Options:
    <data>                                                     Optional, path to icav2 data folder you wish to download from,
                                                               May also specify a folder id or an icav2 uri,
                                                               If not set, defaults to '/'
    -w=<min_depth>, --min-depth=<min_depth>                    Optional, minimum depth to search
    -x=<max_depth>, --max-depth=<max_depth>                    Optional, maximum depth to search
    --type=<type>                                              Optional, one of "FILE" or "FOLDER"
    -n=<name>, --name=<name>                                   Optional, name of file or directory, regex expressions are possible here
    -c=<creator_id_or_name>, --creator=<creator_id_or_name>    Optional, creator username or id
    -l, --long-listing                                         Optional, use long-listing format to show owner, modification timestamp and size
    -t, --time                                                 Optional, sort items by time
    -r, --reverse                                              Optional, reverse order

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example: icav2 projectdata find /reference_data/
    """
    project_data_obj: Optional[ProjectData]
    min_depth: Optional[int]
    max_depth: Optional[int]
    data_type: Optional[DataType]
    name: Optional[Union[str, Pattern]]
    creator: Optional[User]
    time: Optional[bool]
    reverse: Optional[bool] = False
    long_listing: Optional[bool]

    def __init__(self, command_argv):
        # Collect CLI args
        self._docopt_type_args = {
            "project_data_obj": DocOptArg(
                cli_arg_keys=["data"],
            ),
            "min_depth": DocOptArg(
                cli_arg_keys=['--min-depth'],
            ),
            "max_depth": DocOptArg(
                cli_arg_keys=['--max-depth'],
            ),
            "data_type": DocOptArg(
                cli_arg_keys=['--type'],
            ),
            "name": DocOptArg(
                cli_arg_keys=['--name'],
            ),
            "creator": DocOptArg(
                cli_arg_keys=['--creator'],
            ),
            "time": DocOptArg(
                cli_arg_keys=['--time'],
            ),
            "reverse": DocOptArg(
                cli_arg_keys=['--reverse'],
            ),
            "long_listing": DocOptArg(
                cli_arg_keys=['--long-listing'],
            )
        }

        # Initialise attributes
        self.data_path: Optional[Path] = None
        self.project_id: Optional[str] = None

        # Now initialise from super command
        super().__init__(command_argv)

    def check_args(self):
        # Get project id
        self.project_id = get_project_id()

        # Check data is a folder
        if self.project_data_obj is not None:
            if not DataType(self.project_data_obj.data.details.data_type) == DataType.FOLDER:
                logger.error(f"Data '{self.project_data_obj.data.details.path}' is not a folder")
                raise ValueError

            # Set data path
            self.data_path = Path(self.project_data_obj.data.details.path)
        else:
            self.data_path = Path("/")

        # Check optional args
        if self.min_depth is not None and self.min_depth < 1:
            logger.error(f"Minimum depth must be greater than 0 but got {self.min_depth}")
            raise InvalidArgumentError
        if self.max_depth is not None and self.max_depth < 1:
            logger.error(f"Maximum depth must be greater than 0 but got {self.max_depth}")
            raise InvalidArgumentError
        # Ensure max depth is greater than or equal to min depth
        if (
                self.min_depth is not None and
                self.max_depth is not None and
                self.max_depth < self.min_depth
        ):
            logger.error(f"Maximum depth must be greater than or equal to minimum depth but got {self.max_depth} < {self.min_depth}")
            raise InvalidArgumentError

    def get_data_items(self) -> List[ProjectData]:
        """
        Get data items from the data path
        :return:
        """
        return find_project_data_recursively(
            project_id=self.project_id,
            parent_folder_path=self.data_path,
            min_depth=self.min_depth if self.min_depth is not None else None,
            max_depth=self.max_depth if self.max_depth is not None else None,
            data_type=self.data_type,
            name=self.name
        )

    def __call__(self):
        data_items: List[ProjectData] = self.get_data_items()

        if self.time:
            data_items.sort(
                key=lambda x: x.data.details.time_modified.timestamp(),
                reverse=self.reverse
            )

        else:
            data_items.sort(
                key=lambda x: x.data.details.path,
                reverse=self.reverse
            )

        # If creator id is set, filter on creator id
        if self.creator is not None:
            data_items = list(
                filter(
                    lambda x: x.data.details.get("creator_id", None) == self.creator.id,
                    data_items
                )
            )

        logger.debug("Writing output")
        if not self.long_listing:
            list_files_short(data_items)
        else:
            list_files_long(data_items)
