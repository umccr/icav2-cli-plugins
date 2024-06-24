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
import sys
from filecmp import cmpfiles
from pathlib import Path
from pprint import pprint
from tempfile import TemporaryDirectory
from typing import Optional, List
from zipfile import ZipFile
from deepdiff import DeepDiff

# Wrapica imports
from wrapica.enums import PipelineStatus
from wrapica.pipelines import (
    PipelineFile,
    list_pipeline_files, download_pipeline_to_directory
)
from wrapica.project_pipelines import (
    ProjectPipeline,
    update_pipeline_file, add_pipeline_file, delete_pipeline_file
)
from wrapica.user import (
    User,
    get_user_obj_from_user_id,
    get_user_id_from_configuration
)

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.pipeline_helpers import compare_yaml_files
from ...utils.subprocess_handler import run_subprocess_proc

# Locals
from .. import Command, DocOptArg

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
    icav2 projectpipelines update <zipped_pipeline_path> <pipeline> [--force]

Description:
    Update a pipeline on ICAv2. The zipped workflow can be created with either
    1. cwl-ica icav2-zip-workflow
    2. nf-core download <pipeline_name> --revision <pipeline_revision> --outdir <pipeline_dir> --compress zip

    It is expected for CWL workflows, that the workflow.cwl file is in the top directory of the zip file.
    For Nextflow workflows, the main.nf file is expected in the top directory of the zip file, along with nextflow.config.

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

    zipped_pipeline_path: Path
    project_pipeline_obj: ProjectPipeline
    force: bool

    def __init__(self, command_argv):
        self._docopt_type_args = {
            "zipped_pipeline_path": DocOptArg(
                cli_arg_keys=["<zipped_pipeline_path>"]
            ),
            "project_pipeline_obj": DocOptArg(
                cli_arg_keys=["<pipeline>"]
            ),
            "force": DocOptArg(
                cli_arg_keys=["--force"]
            )
        }

        # Initialise parameters
        self.project_id: Optional[str] = None
        self.pipeline_id: Optional[str] = None
        self.pipeline_status: Optional[PipelineStatus] = None

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

        # Get the user obj
        self.user_obj: Optional[User]

        super().__init__(command_argv)

    def __call__(self):
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

    def check_args(self):
        # Get the pipeline id
        self.project_id = get_project_id()

        # Set the pipeline id, referred to in a few sections
        self.pipeline_id = self.project_pipeline_obj.pipeline.id

        # Check the pipeline is an editable pipeline
        self.pipeline_status = PipelineStatus(self.project_pipeline_obj.pipeline.status)

        # Get the user object
        self.user_obj: User = get_user_obj_from_user_id(get_user_id_from_configuration())

        # Check the pipeline is editable on ICAv2
        self.check_is_editable()

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
        self.pipeline_file_mapping = list_pipeline_files(self.pipeline_id)

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
        download_pipeline_to_directory(self.pipeline_id, self.tmp_icav2_pipeline_directory)

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
                        file_.is_file()
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
            update_pipeline_file(self.project_id, self.pipeline_id, file_id, local_file_path)

        # Add new files
        for file_name in self.file_cmp_list_new:
            logger.info(f"Adding file {file_name}")
            file_path = self.tmp_local_unzipped_pipeline_directory / file_name
            add_pipeline_file(self.project_id, self.pipeline_id, file_path)

        # Delete missing files
        for file_name in self.file_cmp_list_missing:
            logger.info(f"Deleting file {file_name}")
            file_id = self.get_file_id_from_file_name(file_name)
            delete_pipeline_file(self.project_id, self.pipeline_id, file_id)

    def check_is_editable(self):
        # Check pipeline status
        if not self.pipeline_status == PipelineStatus.DRAFT:
            logger.error(f"Pipeline '{self.project_pipeline_obj.pipeline.id}' is not in DRAFT status")
            logger.error(f"Cannot edit pipeline in '{self.pipeline_status.value}' status")
            sys.exit(1)

        # Check user
        if not self.project_pipeline_obj.pipeline.owner_id == self.user_obj.id:
            logger.error(f"Pipeline '{self.project_pipeline_obj.id}' is not owned by user '{self.user_obj.id}'")
            sys.exit(1)

        logger.info(f"Pipeline '{self.project_pipeline_obj.id}' is editable")
