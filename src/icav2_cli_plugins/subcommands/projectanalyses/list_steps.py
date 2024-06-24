#!/usr/bin/env python3

"""
List steps of an analysis

This is entirely the wrong spot for this, but the code was already all here!

"""

# External imports
import json
from typing import Optional, Dict, List

# Wrapica
from wrapica.project_analysis import get_analysis_steps, Analysis

# Import from utils
from ...utils.config_helpers import get_project_id
from ...utils.projectanalysis_helpers import filter_analysis_steps
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectAnalysesListAnalysisSteps(Command):
    """Usage:
    icav2 projectanalyses list-analysis-steps help
    icav2 projectanalyses list-analysis-steps <analysis_id_or_user_reference>
                                              [--show-technical-steps]

Description:
    List analysis steps

Options:
    <analysis_id_or_user_reference>            Required, the id of the analysis
                                               Note that the user reference must be unique within the project,
                                               If the user reference is not unique, please use an analysis id instead.
    --show-technical-steps                     Optional, Also list technical steps

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)


Example:
    icav2 projectanalyses list-analysis-steps <analysis_id>
    """

    analysis_obj: Analysis
    is_show_technical_steps: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "analysis_obj": DocOptArg(
                cli_arg_keys=["analysis_id_or_user_reference"],
            ),
            "is_show_technical_steps": DocOptArg(
                cli_arg_keys=["--show-technical-steps"],
            ),
        }

        self.project_id: Optional[str] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Collect other args
        self.project_id = get_project_id()

    def get_analysis_steps(self) -> List[Dict]:
        # Get workflow steps
        workflow_steps = get_analysis_steps(
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id
        )

        return filter_analysis_steps(workflow_steps, self.is_show_technical_steps)

    def __call__(self):
        analysis_steps = self.get_analysis_steps()
        print(json.dumps(analysis_steps, indent=2))
