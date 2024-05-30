#!/usr/bin/env python3

"""
Abort an analysis
"""

# External imports
from typing import Optional

# Wrapica imports
from wrapica.project_analysis import abort_analysis

# Import from utils
from ...utils import is_uuid_format
from ...utils.config_helpers import get_project_id
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# locals
from .. import Command

# Get logger
logger = get_logger()


class ProjectAnalysesAbort(Command):
    """Usage:
    icav2 projectanalyses abort help
    icav2 projectanalyses abort <analysis_id>

Description:
    Abort an analysis in a project

Options:
    <analysis_id>               Required, the id of the analysis

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)

Example:
    icav2 projectanalyses abort <analysis_id>
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.project_id: str = get_project_id()
        self.analysis_id: Optional[str] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        if not is_uuid_format(self.analysis_id):
            logger.error(f"Got analysis-id parameter as '{self.analysis_id}' but is not in UUID format")
            raise InvalidArgumentError

    def __call__(self):
        abort_analysis(
            project_id=self.project_id,
            analysis_id=self.analysis_id
        )
