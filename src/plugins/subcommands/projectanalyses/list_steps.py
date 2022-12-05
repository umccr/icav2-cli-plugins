#!/usr/bin/env python3

"""
List steps of an analysis

This is entirely the wrong spot for this, but the code was already all here!

"""

import json
import os

from utils import is_project_id_format
from utils.config_helpers import get_project_id

from utils.projectanalysis_helpers import \
    get_workflow_steps, filter_analysis_steps

from subcommands import Command
from utils.logger import get_logger
from argparse import ArgumentError
from typing import Optional, Dict, List


logger = get_logger()


class ProjectAnalysesListAnalysisSteps(Command):
    """Usage:
    icav2 projectanalyses list-analysis-steps help
    icav2 projectanalyses list-analysis-steps (<analysis_id>)
                                              [--show-technical-steps]

Description:
    List analysis steps

Options:
    <analysis_id>                              Required, the id of the analysis
    --show-technical-steps                     Optional, Also list technical steps

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)


Example:
    icav2 projectanalyses list-analysis-steps <analysis_id>
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.project_id: Optional[str] = None
        self.analysis_id: Optional[str] = None
        self.show_technical_steps: Optional[bool] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Get project id
        self.project_id = get_project_id()

        # Get analysis storage size
        self.analysis_id = self.args.get("<analysis_id>", None)

        # Check analysis id is not None
        if self.analysis_id is None:
            logger.error("Must specify analysis-id positional argument")
            raise ArgumentError

        if not is_project_id_format(self.analysis_id):
            logger.error(f"Got --analysis-id parameter as {self.analysis_id} but is not in UUID format")
            raise ArgumentError

        # Check if show technical steps has been specified
        if self.args.get("--show-technical-steps", False):
            self.show_technical_steps = True
        else:
            self.show_technical_steps = False

    def get_analysis_steps(self) -> List[Dict]:
        # Get workflow steps
        workflow_steps = get_workflow_steps(
            project_id=self.project_id,
            analysis_id=self.analysis_id
        )

        return filter_analysis_steps(workflow_steps, self.show_technical_steps)

    def __call__(self):
        analysis_steps = self.get_analysis_steps()
        print(json.dumps(analysis_steps, indent=2))
