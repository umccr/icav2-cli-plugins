#!/usr/bin/env python3

"""
'Release' a project pipeline
"""

# External data
from typing import Optional

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger
from ...utils.projectpipeline_helpers import release_pipeline, get_project_pipeline
from ...utils.user_helpers import get_username_from_configuration

# Locals
from .. import Command

# Get logger
logger = get_logger()


class ProjectPipelineReleasePipeline(Command):
    """Usage:
    icav2 projectpipelines release help
    icav2 projectpipelines release <pipeline_id>


Description:
    Release a pipeline (changes pipeline status from draft to release)

Options:
    <pipeline_id>           Required, the id of the pipeline to be released

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines release 6ec0a125-4e80-44f4-8312-0976a8bcd5d5
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.pipeline_id: Optional[str] = None
        self.project_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        release_pipeline(self.project_id, self.pipeline_id)

    def check_args(self):

        # Get the project id
        self.project_id = get_project_id()

        # Get the pipeline id
        pipeline_id_arg = self.args.get("<pipeline_id>", None)

        if pipeline_id_arg is None:
            logger.error("Please specify the pipeline id")
            raise InvalidArgumentError

        self.pipeline_id = pipeline_id_arg

        # Check pipeline id belongs to owner
        username = get_username_from_configuration()

        if not username == get_project_pipeline(self.project_id, self.pipeline_id).pipeline.owner_id:
            logger.error("This pipeline does not belong to you, you cannot release it")

