#!/usr/bin/env python3

from typing import List, Optional
import re

from libica.openapi.v2.model.project_data import ProjectData

from utils import is_uuid_format
from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id_from_session_file, get_project_id
from utils.projectdata_helpers import check_is_directory, list_data_non_recursively, list_files_short, list_files_long, \
    find_data_recursively
from utils.logger import get_logger
from utils.user_helpers import get_user_from_user_id, get_user_from_user_name

from subcommands import Command

logger = get_logger()


class ProjectDataFind(Command):
    """Usage:
    icav2 projectdata find help
    icav2 projectdata find [-w=<min_depth> | --min-depth=<min_depth>]
                           [-x=<max_depth> | --max-depth=<max_depth]
                           [--type=<type>]
                           [-n=<name> | --name=<name>]
                           [-c=<creator_username_or_id> | --creator=<creator_username_or_id>]
                           [-l | --long-listing]
                           [-t | --time]
                           [-r | --reverse]
    icav2 projectdata find <data_path>
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
    <data_path>                                                Optional, data path, defaults to '/'
    -w=<min_depth>, --min-depth=<min_depth>                    Optional, minimum depth to search
    -x=<max_depth>, --max-depth=<max_depth>                    Optional, maximum depth to search
    --type=<type>                                              Optional, one of "FILE" or "DIRECTORY"
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

    def __init__(self, command_argv):
        # Collect args from doc strings
        # command_argv = command_argv
        # command_argv[1] = {"<data_path>": command_argv[1]}
        self.data_path: Optional[str] = None
        self.project_id: Optional[str] = None

        # Optional args
        self.min_depth: Optional[int] = None
        self.max_depth: Optional[int] = None
        self.type: Optional[str] = None
        self.name: Optional[re] = None
        self.creator_id: Optional[str] = None
        self.creator_name: Optional[str] = None

        # Boolean args
        self.time: Optional[bool] = False
        self.reverse: Optional[bool] = False
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

        # Check optional args
        min_depth_arg = self.args.get("--min-depth", None)
        if min_depth_arg is not None:
            if not str(min_depth_arg).isdigit():
                logger.error(f"Expecting a numeric value for --min-depth but got '{min_depth_arg}'")
                raise InvalidArgumentError
            self.min_depth = int(self.args.get("--min-depth"))

        max_depth_arg = self.args.get("--max-depth", None)
        if max_depth_arg is not None:
            if not str(max_depth_arg).isdigit():
                logger.error(f"Expecting a numeric value for --max-depth but got '{max_depth_arg}'")
                raise InvalidArgumentError
            self.max_depth = int(self.args.get("--max-depth"))

        type_arg = self.args.get("--type", None)
        if type_arg is not None:
            if not str(type_arg).upper() in [ "FILE", "DIRECTORY" ]:
                logger.error(f"Expected type arg to be one of 'FILE' or 'DIRECTORY' but got '{type_arg}'")
                raise InvalidArgumentError
            self.type = type_arg

        name_arg = self.args.get("--name", None)
        if name_arg is not None:
            self.name = re.compile(rf"{name_arg.replace('*', '.*')}")
        else:
            self.name = ""

        creator_arg = self.args.get("--creator", None)
        if creator_arg is not None:
            if is_uuid_format(creator_arg):
                self.creator_id = creator_arg
                self.creator_name = get_user_from_user_id(self.creator_id).username
            else:
                self.creator_name = creator_arg
                self.creator_id = get_user_from_user_name(self.creator_name).id

        if self.args.get("--long-listing", ):
            self.long_listing = True

        # Check bool args
        if self.args.get("--long-listing", False):
            self.long_listing = True

        # Get sort order
        if self.args.get("--time"):
            self.time = True
        if self.args.get("--reverse"):
            self.reverse = True

    def get_data_items(self) -> List[ProjectData]:
        """
        Get data items from the data path
        :param project_id: ID of project
        :param data_path: Path to data
        :param sort: Sort order
        :return:
        """

        return find_data_recursively(
            project_id=self.project_id,
            parent_folder_path=self.data_path,
            mindepth=self.min_depth-1 if self.min_depth is not None else None,
            maxdepth=self.max_depth-1 if self.max_depth is not None else None,
            data_type=self.type,
            name=self.name
        )

    def __call__(self):
        data_items: List[ProjectData] = self.get_data_items()

        if self.time:
            data_items.sort(
                key=lambda x: x.data.details.time_modified,
                reverse=self.reverse
            )
        else:
            data_items.sort(
                key=lambda x: x.data.details.path,
                reverse=self.reverse
            )

        # If creator id is set, filter on creator id
        if self.creator_id is not None:
            data_items = list(
                filter(
                    lambda x: x.data.details.get("creator_id", None) == self.creator_id,
                    data_items
                )
            )

        logger.debug("Writing output")
        if not self.long_listing:
            list_files_short(data_items)
        else:
            list_files_long(data_items)
