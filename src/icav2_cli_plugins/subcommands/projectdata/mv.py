#!/usr/bin/env python3
import json
from pathlib import Path
# External imports
from typing import List, Optional

# Wrapica
from wrapica.enums import (
    DataType
)
from wrapica.job import (
    Job,
    get_job, wait_for_job_completion
)
from wrapica.project_data import (
    ProjectData,
    list_project_data_non_recursively, move_project_data
)

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class ProjectDataMv(Command):
    """Usage:
    icav2 projectdata mv help
    icav2 projectdata mv <src_path> <dest_path>
                         [--wait | --json]

Description:
    Move data from one folder to another folder, similar to mv in a posix file system.
    Using uris, you may also move data across projects

Options:
    <src_path>              Required, path to icav2 data folder you wish to move data from,
                            May also specify a folder id or an icav2 uri,
                            Default is the root folder '/'
    <dest_path>             Required, path to icav2 data folder you wish to move data to,
    --wait                  Wait for the move job to complete before returning
    --json                  Output the job id in json format to stdout. Not compatible with --wait

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example: icav2 projectdata mv icav2://development/analysis_data/path/to/run/ icav2://archive/analysis_data/path/to/archive/
    """
    src_project_data_obj: Optional[ProjectData]
    dest_project_data_obj: Optional[ProjectData]
    wait: Optional[bool]
    json: Optional[bool]

    def __init__(self, command_argv):
        # Collect args from doc strings
        self._docopt_type_args = {
            "src_project_data_obj": DocOptArg(
                cli_arg_keys=["src_path"],
            ),
            "dest_project_data_obj": DocOptArg(
                cli_arg_keys=["dest_path"],
                config={
                    "create_data_if_not_found": True
                }
            ),
            "wait": DocOptArg(
                cli_arg_keys=["--wait"],
            ),
            "json": DocOptArg(
                cli_arg_keys=["--json"],
            ),
        }

        # Set other commands
        self.job: Optional[Job] = None

        super().__init__(command_argv)

    def check_args(self):
        # Get the project id
        self.project_id = get_project_id()

        # Check args
        # Check data is a folder
        if not DataType(self.src_project_data_obj.data.details.data_type) == DataType.FOLDER:
            logger.error("data path parameter should end in a '/'")
            raise InvalidArgumentError

        # Check destination is a folder
        if not DataType(self.dest_project_data_obj.data.details.data_type) == DataType.FOLDER:
            logger.error("destination path parameter should end in a '/'")
            raise InvalidArgumentError

    def get_data_items_in_source_directory(self) -> List[ProjectData]:
        """
        Get data items from the data path
        :return:
        """
        return list_project_data_non_recursively(
            project_id=self.src_project_data_obj.data.details.owning_project_id,
            parent_folder_path=Path(self.src_project_data_obj.data.details.path)
        )

    def __call__(self):
        mv_data_items: List[ProjectData] = self.get_data_items_in_source_directory()

        logger.debug("Moving data output")

        job = move_project_data(
            dest_project_id=self.dest_project_data_obj.data.details.owning_project_id,
            dest_folder_id=self.dest_project_data_obj.data.id,
            src_data_list=list(
                map(lambda src_data_iter: src_data_iter.data.id, mv_data_items)
            )
        )

        if self.wait:
            wait_for_job_completion(
                job_id=job.id
            )

        if self.json:
            print(
                json.dumps(
                    {
                        "job_id": job.id
                    },
                    indent=4
                )
            )



