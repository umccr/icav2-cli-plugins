#!/usr/bin/env python3

"""
Abort an analysis
"""

# External imports
from typing import Optional

# Wrapica imports
from wrapica.enums import ProjectAnalysisStatus
from wrapica.project_analysis import (
    abort_analysis, AnalysisType
)

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectAnalysesAbort(Command):
    """Usage:
    icav2 projectanalyses abort help
    icav2 projectanalyses abort <analysis_id_or_user_reference>

Description:
    Abort an analysis in a project

Options:
    <analysis_id_or_user_reference>     Required, the id (or user reference) of the analysis.
                                        Note that the user reference must be unique within the project,
                                        If the user reference is not unique, please use an analysis id instead.

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)

Example:
    icav2 projectanalyses abort <analysis_id>
    """

    analysis_obj: Optional[AnalysisType]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docop_type_args = {
            "analysis_obj": DocOptArg(
                cli_arg_keys=["analysis_id_or_user_reference"],
            )
        }

        # Initialise other args
        self.project_id: Optional[str] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Set project id
        self.project_id = get_project_id()

        # Check analysis status is a non-terminal state
        if ProjectAnalysisStatus(self.analysis_obj.status) not in [
            ProjectAnalysisStatus.REQUESTED,
            ProjectAnalysisStatus.QUEUED,
            ProjectAnalysisStatus.INITIALIZING,
            ProjectAnalysisStatus.PREPARING_INPUTS,
            ProjectAnalysisStatus.IN_PROGRESS,
            ProjectAnalysisStatus.GENERATING_OUTPUTS,
            ProjectAnalysisStatus.AWAITING_INPUT
        ]:
            raise ValueError(
                f"Analysis {self.analysis_obj.id} is in a terminal state and cannot be aborted"
            )

    def __call__(self):
        abort_analysis(
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id
        )
