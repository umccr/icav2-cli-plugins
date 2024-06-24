#!/usr/bin/env python3

"""
Download a CWL or Nextflow pipeline to a CWL file object
"""

# External imports
from pathlib import Path
from typing import Optional
from libica.openapi.v2.model.project_pipeline import ProjectPipeline

# Wrapica imports
from wrapica.pipelines import download_pipeline_to_zip

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


def confirm_download(zip_path: str):
    confirm_update = input(f"Would you like to overwrite '{zip_path}'? (y/yes) (any other key will cancel)")
    if confirm_update.lower() not in ["y", "yes"]:
        logger.info("Exiting without updating the pipeline")
        raise SystemExit


class ProjectPipelinesDownload(Command):
    """Usage:
    icav2 projectpipelines download help
    icav2 projectpipelines download <pipeline>
                                    [--output-dir <output_directory>]
                                    [--force]

Description:
    Download a pipeline from ICAv2 to a local directory.

Options:
    <pipeline>               Required, the pipeline id (or code) of the pipeline to download from
    --output-directory       Optional, if not specified, will be downloaded to the current working directory
    --force                  Optional, if the output zip file already exists, do not ask user for confirmation to overwrite file

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines download my_pipeline.zip
    """

    project_pipeline_obj: ProjectPipeline
    output_dir: Path
    force: bool

    def __init__(self, command_argv):
        # CLI Docopt args
        self._docopt_type_args = {
            "project_pipeline_obj": DocOptArg(
                cli_arg_keys=["<pipeline>"]
            ),
            "output_dir": DocOptArg(
                cli_arg_keys=["--output-directory"]
            ),
            "force": DocOptArg(
                cli_arg_keys=["--force"]
            )
        }

        # Initialise parameters
        self.project_id: Optional[str] = None
        self.output_zip_path: Optional[Path] = None

        super().__init__(command_argv)

    def __call__(self):
        # Check args
        self.check_args()

        # Download the pipeline
        download_pipeline_to_zip(
            pipeline_id=self.project_pipeline_obj.pipeline.id,
            zip_path=self.output_zip_path
        )

    def check_args(self):
        # Get the pipeline id
        self.project_id = get_project_id()
        self.output_zip_path = (self.output_dir / (self.project_pipeline_obj.pipeline.code + ".zip"))

        # Get output dir
        if not self.output_dir.is_dir():
            logger.error(f"Output directory {self.output_dir} does not exist")

        if not self.force and self.output_zip_path.is_file():
            confirm_download(self.output_zip_path)
