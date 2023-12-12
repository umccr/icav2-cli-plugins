#!/usr/bin/env python3

"""
Update a project pipeline by

1. User provides a local zip file of the pipeline
2. A pipeline-id or code
3. We then extract local zip file, and download all pipeline files from the server
4. Compare each with filecmp report, and confirm with user that they would like to update the pipeline
5. Each file in the pipeline is updated
"""
# External imports
from filecmp import cmpfiles
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory
from typing import Optional, List
from zipfile import ZipFile
from deepdiff import DeepDiff

# Utils
from ...utils import is_uuid_format
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.pipeline_helpers import (
    compare_yaml_files, download_pipeline_to_directory, update_pipeline_file,
    add_pipeline_file, delete_pipeline_file, get_pipeline_id_from_pipeline_code,
    get_pipeline_from_pipeline_id
)
from ...utils.subprocess_handler import run_subprocess_proc

# Locals
from .. import Command

# Get logger
logger = get_logger()


def confirm_pipeline_update():
    confirm_update = input("Would you like to continue with the pipeline update? (y/yes)")
    if confirm_update.lower() not in ["y", "yes"]:
        logger.info("Exiting without updating the pipeline")
        raise SystemExit


class PipelinesUpdate(Command):
    """Usage:
    icav2 pipelines update help
    icav2 pipelines update <zipped_pipeline_path> <pipeline_id> [--force]

Description:
    Update a pipeline on ICAv2. The zipped workflow can be created with cwl-ica icav2-zip-workflow

Options:
    <zipped_pipeline_path>   Required, the path to the zip file containing the pipeline.
    <pipeline_id>            Required, the id (or code) of the pipeline to update
    --force                  Optional, dont ask for input from user

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 pipelines update my_pipeline.zip uuid-1234-5678-9101
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.pipeline_id: Optional[str] = None
        self.zipped_pipeline_path: Optional[Path] = None

        # Local dirs
        self.tmp_local_unzipped_pipeline_directory: Optional[TemporaryDirectory] = None
        self.tmp_icav2_pipeline_directory: Optional[TemporaryDirectory] = None

        # Force
        self.force: Optional[bool] = False

        # File comparisons
        self.file_cmp_list_match: Optional[List] = None
        self.file_cmp_list_edited: Optional[List] = None
        self.file_cmp_list_missing: Optional[List] = None
        self.file_cmp_list_new: Optional[List] = None

        super().__init__(command_argv)

    def __call__(self):
        # Compare files
        self.compare_pipeline_files()

        # Confirm with user that they would like to update the pipeline
        if not self.force:
            confirm_pipeline_update()

        # Update pipeline
        self.update_pipeline()

        # End script
        logger.info(f"Pipeline {self.pipeline_id} has been successfully updated!")

    def get_pipeline_id(self):
        pipeline_id_arg = self.args.get("<pipeline_id>", None)
        if pipeline_id_arg is None:
            logger.error("Please specify a pipeline id or code")
            raise InvalidArgumentError

        # Get pipeline id (if in code format)
        if is_uuid_format(pipeline_id_arg):
            pipeline_id = pipeline_id_arg
        else:
            pipeline_id = get_pipeline_id_from_pipeline_code(pipeline_id_arg)

        return pipeline_id

    def is_valid_pipeline(self) -> bool:
        """
        Confirm the pipeline id exists, and is not released
        Returns: bool
        """
        ## Check status (is released?)
        ## Get pipeline id
        # FIXME - see the following for more info
        # https://github.com/umccr-illumina/ica_v2/issues/135
        # Still run regardless to confirm pipeline exists
        pipeline_id_obj = get_pipeline_from_pipeline_id(self.pipeline_id)

        return True

    def check_args(self):
        # Get the pipeline id
        self.pipeline_id = self.get_pipeline_id()

        # Check pipeline id exists and is not released
        if not self.is_valid_pipeline():
            logger.error(
                f"Pipeline id '{self.pipeline_id}' is either not a valid pipeline or pipeline has already been released"
            )

        # Check pipeline_path
        zipped_pipeline_path_arg = self.args.get("<zipped_pipeline_path>", None)
        if zipped_pipeline_path_arg is None:
            logger.error("Please specify the path to the zipped pipeline")
            raise InvalidArgumentError

        # Assign pipeline path
        self.zipped_pipeline_path = Path(zipped_pipeline_path_arg)

        # Check force parameter
        self.force = self.args.get("--force", False)

        # Check file exists
        if not self.zipped_pipeline_path.is_file():
            logger.error("Please specify a valid zip file")
            raise InvalidArgumentError

        # Check endswith zip
        if not self.zipped_pipeline_path.name.endswith(".zip"):
            logger.error("Please specify a zip file")
            raise InvalidArgumentError

        # Unzip the local pipeline
        self.unzip_pipeline()

        # Pull pipeline from icav2
        self.pull_pipeline_from_icav2()

    def unzip_pipeline(self):
        # Create a temporary directory
        self.tmp_local_unzipped_pipeline_directory = TemporaryDirectory()

        # Unzip the pipeline
        logger.info(f"Unzipping {self.zipped_pipeline_path} to {self.tmp_local_unzipped_pipeline_directory.name}")
        ZipFile(self.zipped_pipeline_path).extractall(self.tmp_local_unzipped_pipeline_directory.name)

    def pull_pipeline_from_icav2(self):
        # Create a temporary directory
        self.tmp_icav2_pipeline_directory = TemporaryDirectory()

        # Get the pipeline
        logger.info(f"Downloading pipeline {self.pipeline_id} to {self.tmp_icav2_pipeline_directory.name}")
        download_pipeline_to_directory(self.pipeline_id, Path(self.tmp_icav2_pipeline_directory.name))

    def compare_pipeline_files(self):
        """
        Compare the files in the local pipeline with the files in the icav2 pipeline
        Returns:

        """
        # Get the list of files in the local pipeline
        local_files = list(
            map(
                lambda sub_path: sub_path.relative_to(self.tmp_local_unzipped_pipeline_directory.name),
                Path(self.tmp_local_unzipped_pipeline_directory.name).glob("*/**")
            )
        )

        # Get the list of files in the icav2 pipeline
        icav2_pipeline_files = list(
            map(
                lambda sub_path: sub_path.relative_to(self.tmp_icav2_pipeline_directory.name),
                Path(self.tmp_icav2_pipeline_directory.name).glob("*/**")
            )
        )

        # Collect cmp files objects
        self.file_cmp_list_match, self.file_cmp_list_edited, file_cmp_list_errors = cmpfiles(
            self.tmp_local_unzipped_pipeline_directory.name,
            self.tmp_icav2_pipeline_directory.name,
            sorted({*icav2_pipeline_files, *local_files}),
            shallow=False
        )

        # Get the list of missing files
        self.file_cmp_list_missing = list(
            filter(
                lambda file_: not (Path(self.tmp_local_unzipped_pipeline_directory.name) / file_).is_file(),
                file_cmp_list_errors
            )
        )

        # Get the list of new files
        self.file_cmp_list_new = list(
            filter(
                lambda file_: (Path(self.tmp_local_unzipped_pipeline_directory.name) / file_).is_file(),
                file_cmp_list_errors
            )
        )

        # Report the following files match
        matching_files_list_str = '\n'.join(self.file_cmp_list_match)
        logger.info(
            f"The following files match between the locally zipped pipeline and the icav2 pipeline: "
            f"{matching_files_list_str}"
        )

        # Report the following files missing
        file_cmp_missing_list_str = '\n'.join(self.file_cmp_list_missing)
        logger.info(
            f"The following files are missing from the locally zipped pipeline and will be removed from the icav2 pipeline"
            f"{file_cmp_missing_list_str}"
        )

        # Report the following files added
        file_cmp_new_list_str = '\n'.join(self.file_cmp_list_new)
        logger.info(
            f"The following files will be added to the icav2 pipeline"
            f"{file_cmp_new_list_str}"
        )

        # The following files are different, printing the differences
        for file_name in self.file_cmp_list_edited:
            local_file_path = Path(self.tmp_local_unzipped_pipeline_directory.name) / file_name
            icav2_file_path = Path(self.tmp_icav2_pipeline_directory.name) / file_name

            logger.info(f"Comparing local with icav2 for {file_name}")
            if file_name.endswith(".cwl") or file_name.endswith(".yaml"):
                deepdiff_obj: DeepDiff = compare_yaml_files(
                    local_file_path,
                    icav2_file_path
                )

                pprint(deepdiff_obj, indent=4)

            else:
                logger.info(f"Running diff binary command for {file_name}")
                diff_returncode, diff_stdout, diff_stderr = run_subprocess_proc(
                    [
                        "diff", icav2_file_path, local_file_path
                    ],
                    capture_output=True
                )

                logger.info(f"Diff is\n{diff_stdout}")

    def update_pipeline(self):
        # Show what files were not updating
        for file_name in self.file_cmp_list_match:
            logger.info(f"Skipping update of {file_name}")

        # Update mismatched files
        for file_name in self.file_cmp_list_edited:
            logger.info(f"Updating file {file_name}")
            local_file_path = Path(self.tmp_local_unzipped_pipeline_directory.name) / file_name
            update_pipeline_file(self.pipeline_id, file_name, local_file_path)

        # Add new files
        for file_name in self.file_cmp_list_new:
            logger.info(f"Adding file {file_name}")
            local_file_path = Path(self.tmp_local_unzipped_pipeline_directory.name) / file_name
            add_pipeline_file(self.pipeline_id, file_name, local_file_path)

        # Delete missing files
        for file_name in self.file_cmp_list_missing:
            logger.info(f"Deleting file {file_name}")
            delete_pipeline_file(self.pipeline_id, file_name)
