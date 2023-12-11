#!/usr/bin/env python3

"""
Use AWS sync command to download data from ICAv2
"""

# External imports
from pathlib import Path
from typing import List, Optional, Dict

# Utils imports
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.projectdata_helpers import (
    check_is_directory,
    get_data_obj_from_project_id_and_path,
    get_s3_sync_script,
    get_aws_credentials_access,
    run_s3_sync_command
)
from ...utils.logger import get_logger

# Local imports
from .. import Command


logger = get_logger()


class S3SyncDownload(Command):
    """Usage:
    icav2 projectdata s3-sync-download help
    icav2 projectdata s3-sync-download <data_path> <download_path>
                                     [-w=<file_path> | --write-script-path=<file_path> ]
                                     [-s=<s3_sync_arg> | --s3-sync-arg=<s3_sync_arg>]...


Description:
    Download a folder from icav2 using aws s3 sync.


Options:
    <data_path>                                        Required, path to icav2 data folder you wish to download from
    <download_path>                                    Required, the local download directory, parent folder must exist

    -w=<file_path>, --write-script-path=<file_path>    Optional, write out a script instead of invoking aws s3 command
                                                       that holds the AWS S3 Sync parameters.
                                                       download path parameter parent folder does not necessarily need to exist if this option
                                                       is set. Parent folder of this parameter must exist.

    -s=<s3_sync_arg>, --s3-sync-arg=<s3_sync_arg>      Other arguments are sent to aws s3 sync, specify multiple times for multiple arguments


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Required, taken from "$HOME/.icav2/.session.ica.yaml" if not set


Extras:
    AWS CLI V2 must be installed

    Due to permission requirements with aws s3 sync, you MUST have write permissions to this project to run this command

Examples: icav2 projectdata s3-sync-download /test_data/outputs/ $HOME/outputs/
    icav2 projectdata s3-sync-download /test_data/outputs/ $HOME/outputs/ --s3-sync-arg --dryrun
    icav2 projectdata s3-sync-download /test_data/outputs/ $HOME/outputs/ --s3-sync-arg --exclude='*' --s3-sync-arg --include='*.bam'
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.data_path: Optional[str] = None
        self.data_id: Optional[str] = None
        self.download_path: Optional[Path] = None
        self.project_id: Optional[str] = None
        self.write_script_path: Optional[Path] = None
        self.s3_sync_args: Optional[List] = None
        self.s3_env_vars: Optional[Dict] = None
        self.s3_path: Optional[str] = None

        super().__init__(command_argv)

    def check_args(self):
        # Get data path
        self.data_path = self.args.get("<data_path>", None)

        # Check data path ends with a '/'
        if not self.data_path.endswith("/"):
            logger.error("data path parameter should end in a '/'")
            raise InvalidArgumentError

        self.project_id = get_project_id()

        # Check data path exists
        if not check_is_directory(
            project_id=self.project_id,
            folder_path=self.data_path
        ):
            logger.error(f"Path '{self.data_path}' does not exist in project id '{self.project_id}'")
            raise ValueError

        # Get download path
        self.download_path = self.args.get("<download_path>", None)
        self.download_path = Path(self.download_path)

        self.write_script_path = self.args.get("--write-script-path", None)
        if self.write_script_path is not None:
            self.write_script_path = Path(self.write_script_path)

        # Check if parent of download path exists (if write-script-path not set)
        if not self.download_path.parent.is_dir() and \
                self.write_script_path is None:
            logger.error(f"Please ensure parent folder of download path parameter '{self.download_path}' exists")
            raise InvalidArgumentError

        # Check download path is not a file
        if self.download_path.is_file() and \
                self.write_script_path is not None:
            logger.error(f"Cannot download data to {self.download_path}, file exists")
            raise InvalidArgumentError

        # Check write script path is not a folder
        if self.write_script_path is not None and self.write_script_path.is_dir():
            logger.error(f"Cannot write script to {self.write_script_path}, is a directory")
            raise InvalidArgumentError

        # Check if parent script path exists
        if self.write_script_path is not None and (
            not self.write_script_path.parent.is_dir()
        ):
            logger.error(
                f"Please ensure parent folder of the write-script-path parameter '{self.write_script_path}' exists"
            )
            raise InvalidArgumentError

        # Check awsv2 is installed if write script path is not set
        if self.write_script_path is None:
            # Check awsv2 is installed
            # TODO
            pass

        # Get s3 sync args
        self.s3_sync_args = []
        for s3_sync_arg in self.args.get("--s3-sync-arg"):
            self.s3_sync_args.append(s3_sync_arg)

        # Get the data id now we know all the arguments are working
        self.data_id = get_data_obj_from_project_id_and_path(
            project_id=self.project_id,
            data_path=self.data_path
        ).data.id

        # Get s3 env vars
        self.s3_env_vars = get_aws_credentials_access(
            project_id=self.project_id,
            data_id=self.data_id
        )

        # Trailing slash already part of object prefix
        self.s3_path = f"s3://{self.s3_env_vars.get('bucket')}/{self.s3_env_vars.get('object_prefix')}"

    def create_sync_script(self):
        with open(self.write_script_path, "w") as file_h:
            file_h.write(
                get_s3_sync_script(
                    aws_env_vars=self.s3_env_vars,
                    aws_s3_path=self.s3_path,
                    aws_s3_sync_args=self.s3_sync_args,
                    upload=False,
                    download=True,
                    download_path=self.download_path
                )
            )

    def run_aws_s3_sync_download_command(self):
        run_s3_sync_command(
            aws_env_vars=self.s3_env_vars,
            aws_s3_path=self.s3_path,
            aws_s3_sync_args=self.s3_sync_args,
            upload=False,
            download=True,
            download_path=self.download_path
        )

    def __call__(self):
        # Run command
        if self.write_script_path is not None:
            self.create_sync_script()
        else:
            self.run_aws_s3_sync_download_command()
