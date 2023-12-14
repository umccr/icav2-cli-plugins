#!/usr/bin/env python3

"""
Update a project pipeline by

1. User provides a local zip file of the pipeline
2. A pipeline-id or code
3. We then extract local zip file, and download all pipeline files from the server
4. Compare each with filecmp report, and confirm with user that they would like to update the pipeline
5. Each file in the pipeline is updated
"""
import sys
# External imports
from filecmp import cmpfiles
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory
from typing import Optional, List
from zipfile import ZipFile
from deepdiff import DeepDiff
from libica.openapi.v2.model.pipeline_file import PipelineFile

# Utils
from ...utils import is_uuid_format
from ...utils.config_helpers import get_project_id
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.projectpipeline_helpers import (
    download_pipeline_to_directory, update_pipeline_file,
    add_pipeline_file, delete_pipeline_file, list_pipeline_files
)
from ...utils.pipeline_helpers import (
    compare_yaml_files,
    get_pipeline_id_from_pipeline_code,
    get_pipeline_from_pipeline_id
)
from ...utils.subprocess_handler import run_subprocess_proc

# Locals
from .. import Command

# Get logger
logger = get_logger()


def confirm_pipeline_update():
    confirm_update = input("Would you like to continue with the pipeline update? (y/yes) (any other key will cancel)")
    if confirm_update.lower() not in ["y", "yes"]:
        logger.info("Exiting without updating the pipeline")
        raise SystemExit


class ProjectPipelinesUpdate(Command):
    """Usage:
    icav2 projectpipelines update help
    icav2 projectpipelines update <zipped_pipeline_path> <pipeline_id> [--force]

Description:
    Update a pipeline on ICAv2. The zipped workflow can be created with cwl-ica icav2-zip-workflow

Options:
    <zipped_pipeline_path>   Required, the path to the zip file containing the pipeline.
    <pipeline_id>            Required, the id (or code) of the pipeline to update
    --force                  Optional, don't ask user for confirmation

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines update my_pipeline.zip uuid-1234-5678-9101
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.project_id: Optional[str] = None
        self.pipeline_id: Optional[str] = None
        self.zipped_pipeline_path: Optional[Path] = None

        # Local dirs
        self.tmp_local_unzipped_pipeline_directory_obj: Optional[TemporaryDirectory] = None
        self.tmp_local_unzipped_pipeline_directory: Optional[Path] = None
        self.tmp_icav2_pipeline_directory_obj: Optional[TemporaryDirectory] = None
        self.tmp_icav2_pipeline_directory: Optional[Path] = None

        # Force
        self.force: Optional[bool] = False

        # File comparisons
        self.file_cmp_list_match: Optional[List[Path]] = None
        self.file_cmp_list_edited: Optional[List[Path]] = None
        self.file_cmp_list_missing: Optional[List[Path]] = None
        self.file_cmp_list_new: Optional[List] = None

        # Pipeline file mapping
        self.pipeline_file_mapping: Optional[List[PipelineFile]] = None

        super().__init__(command_argv)

    def __call__(self):
        logger.warning("Pipeline files API does NOT collect main file, 'workflow.cwl', hence any changes to workflow.cwl are ignored.")
        # Compare files
        self.compare_pipeline_files()

        # Check if there are any changes
        if (
            len(self.file_cmp_list_edited) == 0 and
            len(self.file_cmp_list_missing) == 0 and
            len(self.file_cmp_list_new) == 0
        ):
            logger.info("No changes detected, exiting")
            sys.exit(0)

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
        self.project_id = get_project_id()
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

        # Set pipeline file mapping
        self.pipeline_file_mapping = list_pipeline_files(self.project_id, self.pipeline_id)

    def unzip_pipeline(self):
        # Create a temporary directory
        self.tmp_local_unzipped_pipeline_directory_obj = TemporaryDirectory()
        self.tmp_local_unzipped_pipeline_directory = Path(self.tmp_local_unzipped_pipeline_directory_obj.name) / self.zipped_pipeline_path.stem

        # Unzip the pipeline
        logger.info(f"Unzipping {self.zipped_pipeline_path} to {self.tmp_local_unzipped_pipeline_directory}")
        ZipFile(self.zipped_pipeline_path).extractall(self.tmp_local_unzipped_pipeline_directory_obj.name)

        # Check subdirectory
        if not self.tmp_local_unzipped_pipeline_directory.is_dir():
            logger.error(f"Pipeline zip file {self.zipped_pipeline_path} does not contain a subdirectory")
            raise InvalidArgumentError

    def pull_pipeline_from_icav2(self):
        # Create a temporary directory
        self.tmp_icav2_pipeline_directory_obj = TemporaryDirectory()
        self.tmp_icav2_pipeline_directory = Path(self.tmp_icav2_pipeline_directory_obj.name)

        # Get the pipeline
        logger.info(f"Downloading pipeline {self.pipeline_id} to {self.tmp_icav2_pipeline_directory}")
        download_pipeline_to_directory(self.project_id, self.pipeline_id, self.tmp_icav2_pipeline_directory)

    def compare_pipeline_files(self):
        """
        Compare the files in the local pipeline with the files in the icav2 pipeline
        Returns:

        """
        # Get the list of files in the local pipeline
        local_files = list(
            map(
                lambda sub_path: sub_path.relative_to(self.tmp_local_unzipped_pipeline_directory),
                filter(
                    lambda file_: (
                        file_.is_file() and
                        # FIXME - waiting on https://github.com/umccr-illumina/ica_v2/issues/162 and then can remove the
                        # and not == workflow.cwl clause
                        not file_.absolute() == Path(self.tmp_local_unzipped_pipeline_directory) / 'workflow.cwl'
                    ),
                    Path(self.tmp_local_unzipped_pipeline_directory).rglob("*")
                )
            )
        )

        # Get the list of files in the icav2 pipeline
        icav2_pipeline_files = list(
            map(
                lambda sub_path: sub_path.relative_to(self.tmp_icav2_pipeline_directory),
                filter(
                    lambda file_: file_.is_file(),
                    self.tmp_icav2_pipeline_directory.rglob("*")
                )
            )
        )

        # Collect cmp files objects
        self.file_cmp_list_match, self.file_cmp_list_edited, file_cmp_list_errors = cmpfiles(
            self.tmp_local_unzipped_pipeline_directory,
            self.tmp_icav2_pipeline_directory,
            sorted({*icav2_pipeline_files, *local_files}),
            shallow=False
        )

        # Get the list of missing files
        self.file_cmp_list_missing = list(
            filter(
                lambda file_: not (self.tmp_local_unzipped_pipeline_directory / file_).is_file(),
                file_cmp_list_errors
            )
        )

        # Get the list of new files
        self.file_cmp_list_new = list(
            filter(
                lambda file_: (self.tmp_local_unzipped_pipeline_directory / file_).is_file(),
                file_cmp_list_errors
            )
        )

        # Report the following files match
        matching_files_list_str = '\n'.join(map(str, self.file_cmp_list_match))
        if len(self.file_cmp_list_match) > 0:
            logger.info(
                f"The following files match between the locally zipped pipeline and the icav2 pipeline:\n"
                f"{matching_files_list_str}"
            )

        # Report the following files missing
        file_cmp_missing_list_str = '\n'.join(map(str, self.file_cmp_list_missing))
        if len(self.file_cmp_list_missing) > 0:
            logger.info(
                f"The following files are missing from the locally zipped "
                f"pipeline and will be removed from the icav2 pipeline:\n "
                f"{file_cmp_missing_list_str}"
            )

        # Report the following files added
        file_cmp_new_list_str = '\n'.join(map(str, self.file_cmp_list_new))
        if len(self.file_cmp_list_new) > 0:
            logger.info(
                f"The following files will be added to the icav2 pipeline:\n"
                f"{file_cmp_new_list_str}"
            )

        # The following files are different, printing the differences
        file_path: Path
        for file_path in self.file_cmp_list_edited:
            local_file_path = self.tmp_local_unzipped_pipeline_directory / file_path
            icav2_file_path = self.tmp_icav2_pipeline_directory / file_path

            logger.info(f"Comparing local with icav2 for {file_path}")
            if file_path.name.endswith(".cwl") or file_path.name.endswith(".yaml"):
                deepdiff_obj: DeepDiff = compare_yaml_files(
                    icav2_file_path,
                    local_file_path
                )

                pprint(deepdiff_obj, indent=4)

            else:
                logger.info(f"Running diff binary command for {file_path}")
                diff_returncode, diff_stdout, diff_stderr = run_subprocess_proc(
                    [
                        "diff", icav2_file_path, local_file_path
                    ],
                    capture_output=True
                )

                logger.info(f"Diff is\n{diff_stdout}")

    def get_file_id_from_file_name(self, file_name: str) -> str:
        try:
            file_id = next(
                filter(
                    lambda file_: file_.name == file_name,
                    self.pipeline_file_mapping
                )
            ).id
        except StopIteration:
            logger.error(f"Could not get file id for file name '{file_name}'")
            raise StopIteration
        return file_id

    def update_pipeline(self):
        # Show what files were not updating
        for file_name in self.file_cmp_list_match:
            logger.info(f"Skipping update of {file_name}")

        # Update mismatched files
        for file_name in self.file_cmp_list_edited:
            logger.info(f"Updating file {file_name}")
            local_file_path = self.tmp_local_unzipped_pipeline_directory / file_name
            file_id = self.get_file_id_from_file_name(file_name)
            update_pipeline_file(self.project_id, self.pipeline_id, file_id, file_name, local_file_path)

        # Add new files
        for file_name in self.file_cmp_list_new:
            logger.info(f"Adding file {file_name}")
            file_path = self.tmp_local_unzipped_pipeline_directory / file_name
            add_pipeline_file(self.project_id, self.pipeline_id, file_name, file_path)

        # Delete missing files
        for file_name in self.file_cmp_list_missing:
            logger.info(f"Deleting file {file_name}")
            file_id = self.get_file_id_from_file_name(file_name)
            delete_pipeline_file(self.project_id, self.pipeline_id, file_id)
