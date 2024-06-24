#!/usr/bin/env python3

"""
Use AWS sync command to upload data to ICAv2
"""

# External imports
from pathlib import Path
from typing import List, Optional, Dict
from urllib.parse import urlunparse

# Wrapica imports
from wrapica.project_data import (
    get_aws_credentials_access_for_project_folder, ProjectData
)

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.projectdata_helpers import (
    get_s3_sync_script, run_s3_sync_command
)
from ...utils.logger import get_logger

# Local imports
from .. import Command, DocOptArg
from ...utils.subprocess_handler import run_subprocess_proc

# Get logger
logger = get_logger()


class S3SyncUpload(Command):
    """Usage:
    icav2 projectdata s3-sync-upload help
    icav2 projectdata s3-sync-upload <upload_path> <data>
                                     [-w=<file_path> | --write-script-path=<file_path> ]
                                     [-s=<s3_sync_arg> | --s3-sync-arg=<s3_sync_arg>]...


Description:
    Upload a folder to icav2 using aws s3 sync.


Options:
    <upload_path>                                      Required, the source directory, directory must exist
    <data>                                             Required, the data path to icav2 data folder you wish to upload to
                                                       May also specify a folder id or an icav2 uri

    -w=<file_path>, --write-script-path=<file_path>    Optional, write out a script instead of invoking aws s3 command
                                                       that holds the AWS S3 Sync parameters.
                                                       upload path parameter folder does not necessarily need to exist if this option
                                                       is set. Parent folder of this parameter must exist.

    -s=<s3_sync_arg>, --s3-sync-arg=<s3_sync_arg>      Other arguments are sent to aws s3 sync, specify multiple times for multiple arguments


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Required, taken from "$HOME/.icav2/.session.ica.yaml" if not set


Extras:
    AWS CLI V2 must be installed

    You MUST have write permissions to this project to run this command

Examples: icav2 projectdata s3-sync-upload $HOME/test_inputs/ /test_data/inputs/
    icav2 projectdata s3-sync-upload $HOME/test_inputs/ /test_data/inputs/ --s3-sync-arg --dryrun
    icav2 projectdata s3-sync-upload $HOME/test_inputs/ /test_data/inputs/ --s3-sync-arg --exclude='*' --s3-sync-arg --include='*.bam'
    """

    project_data_obj: Optional[ProjectData]
    upload_path: Optional[Path]
    write_script_path: Optional[Path]
    s3_sync_args: Optional[List[str]]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "project_data_obj": DocOptArg(
                cli_arg_keys=["data"],
                config={
                    "create_data_if_not_found": True
                }
            ),
            "upload_path": DocOptArg(
                cli_arg_keys=["upload_path"],
            ),
            "write_script_path": DocOptArg(
                cli_arg_keys=["write_script_path"],
            ),
            "s3_sync_args": DocOptArg(
                cli_arg_keys=["s3_sync_arg"],
            )
        }

        # Additional args
        self.s3_env_vars: Optional[Dict] = None
        self.s3_path: Optional[str] = None
        self.project_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        # Run command
        if self.write_script_path is not None:
            self.create_sync_script()
        else:
            self.run_aws_s3_sync_upload_command()

    def check_args(self):
        # Set project id
        self.project_id = get_project_id()

        # Check upload path is not a file
        if self.upload_path.is_file() and \
                self.write_script_path is not None:
            logger.error(f"Cannot upload data to {self.upload_path}, expected upload path to be a directory, not a file")
            raise InvalidArgumentError

        # Check write script path is not a folder
        if self.write_script_path is not None and self.write_script_path.is_dir():
            logger.error(f"Cannot write script to {self.write_script_path}, is a directory")
            raise InvalidArgumentError

        # Check if parent script path exists
        if self.write_script_path is not None and \
                not self.write_script_path.parent.is_dir():
            logger.error(
                f"Please ensure parent folder of the write-script-path parameter"
                f" '{self.write_script_path}' exists"
            )
            raise InvalidArgumentError

        # Check awsv2 is installed if write script path is not set
        if self.write_script_path is None:
            # Check awsv2 is installed
            aws_v2_returncode, aws_v2_stdout, aws_v2_stderr = run_subprocess_proc(
                [
                    "aws", "--version"
                ]
            )
            if not aws_v2_returncode == 0:
                logger.error("AWS CLI V2 not installed")
                raise InvalidArgumentError

        # Get s3 env vars
        self.s3_env_vars = get_aws_credentials_access_for_project_folder(
            project_id=self.project_id,
            folder_id=self.project_data_obj.data.id
        )

        # Trailing slash already part of object prefix
        self.s3_path = urlunparse(
            (
                "s3", self.s3_env_vars.get('bucket'), self.s3_env_vars.get('object_prefix'),
                None, None, None
            )
        )

    def create_sync_script(self):
        with open(self.write_script_path, "w") as file_h:
            file_h.write(
                get_s3_sync_script(
                    aws_env_vars=self.s3_env_vars,
                    aws_s3_path=self.s3_path,
                    aws_s3_sync_args=self.s3_sync_args,
                    upload=True,
                    download=False,
                    upload_path=self.upload_path
                )
            )

    def run_aws_s3_sync_upload_command(self):
        run_s3_sync_command(
            aws_env_vars=self.s3_env_vars,
            aws_s3_path=self.s3_path,
            aws_s3_sync_args=self.s3_sync_args,
            upload=True,
            download=False,
            upload_path=self.upload_path
        )

