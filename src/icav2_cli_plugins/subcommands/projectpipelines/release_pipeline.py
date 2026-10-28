#!/usr/bin/env python3

"""
'Release' a project pipeline
"""

# Standard imports
from typing import Optional

# Wrapica imports
from wrapica.project_pipelines import (
    ProjectPipeline,
    release_project_pipeline
)
from wrapica.user import (
    User,
    get_user_id_from_configuration, get_user_obj_from_user_id
)

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectPipelineReleasePipeline(Command):
    """Usage:
    icav2 projectpipelines release help
    icav2 projectpipelines release <pipeline>


Description:
    Release a pipeline (changes pipeline status from draft to release)

Options:
    <pipeline>           Required, the id (or name) of the pipeline to be released

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines release 6ec0a125-4e80-44f4-8312-0976a8bcd5d5
    """

    project_pipeline_obj: ProjectPipeline

    def __init__(self, command_argv):
        # Set the docopt args
        self._docopt_type_args = {
            "project_pipeline_obj": DocOptArg(
                cli_arg_keys=["<pipeline>"],
            )
        }

        # Initialise parameters
        self.project_id: Optional[str] = None
        self.pipeline_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        release_project_pipeline(self.project_id, self.pipeline_id)

    def check_args(self):
        # Get the project id
        self.project_id = get_project_id()

        # Set the pipeline id
        self.pipeline_id = str(self.project_pipeline_obj.pipeline.id)
