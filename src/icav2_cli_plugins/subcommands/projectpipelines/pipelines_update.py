#!/usr/bin/env python3

"""
Update a project pipeline by

1. User provides a local zip file of the pipeline
2. A pipeline-id or name
3. We then extract local zip file, and download all pipeline files from the server
4. Compare each with filecmp report, and confirm with user that they would like to update the pipeline
5. Each file in the pipeline is updated
"""
# External imports
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, List, cast

# Libica model imports
from libica.openapi.v3 import ProjectPipelineV4

# Wrapica imports
from wrapica.enums import PipelineStatus
from wrapica.pipelines import (
    PipelineFile,
)
from wrapica.project_pipelines import (
    ProjectPipelineType, pipeline_update_from_zip
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
    <pipeline_id>            Required, the id (or name) of the pipeline to update
    --force                  Optional, don't ask user for confirmation

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines update my_pipeline.zip uuid-1234-5678-9101
    """

    zipped_pipeline_path: Path
    project_pipeline_obj: ProjectPipelineType
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
        self.force: bool = False

        # File comparisons
        self.file_cmp_list_match: Optional[List[Path]] = None
        self.file_cmp_list_edited: Optional[List[Path]] = None
        self.file_cmp_list_missing: Optional[List[Path]] = None
        self.file_cmp_list_new: Optional[List[Path]] = None

        # Pipeline file mapping
        self.pipeline_file_mapping: Optional[List[PipelineFile]] = None

        # Get the user obj
        self.user_obj: Optional[User]

        super().__init__(command_argv)

    def __call__(self):
        # Update pipeline
        pipeline_update_from_zip(
            cast(str, self.project_id),
            self.project_pipeline_obj.pipeline.id,
            self.zipped_pipeline_path,
            self.force
        )

        # End script
        logger.info(f"Pipeline {self.pipeline_id} has been successfully updated!")

    def check_args(self):
        # Get the pipeline id
        self.project_id = get_project_id()

        # Coerce to a v4 pipeline
        self.project_pipeline_obj: ProjectPipelineV4

        # Set the pipeline id, referred to in a few sections
        self.pipeline_id = str(self.project_pipeline_obj.pipeline.id)

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

    def check_is_editable(self):
        # Check pipeline status
        if not self.pipeline_status == PipelineStatus.DRAFT:
            logger.error(f"Pipeline '{self.project_pipeline_obj.pipeline.id}' is not in DRAFT status")
            logger.error(f"Cannot edit pipeline in '{self.pipeline_status.value}' status")
            sys.exit(1)

        logger.info(f"Pipeline '{self.project_pipeline_obj.pipeline.id}' is editable")
