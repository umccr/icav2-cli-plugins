#!/usr/bin/env python3

"""
Get input json
"""
import json
from utils.errors import InvalidArgumentError
from typing import Optional, Dict

from utils.config_helpers import get_project_id
from utils.logger import get_logger
from subcommands import Command
from utils.projectpipeline_helpers import get_cwl_analysis_input_json

logger = get_logger()


class ProjectAnalysesGetCWLAnalysisInputJson(Command):
    """Usage:
    icav2 projectanalyses help
    icav2 projectanalyses get-cwl-analysis-input-json <analysis_id>

Description:
    Given an analysis ID, show the input json used to launch the pipeline.
    Future enhancements of this command will allow a user to 'defererence' the input json.

Options:
    <analysis_id>            Required, the analysis id

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectanalyses get-cwl-analysis-input-json abc--123456789
    """

    def __init__(self, command_argv):
        # Get the command args
        self.analysis_id: Optional[str] = None
        self.project_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        analysis_input_json: Dict = self.get_analysis_input_json()
        print(
            json.dumps(analysis_input_json, indent=4)
        )

    def check_args(self):
        self.analysis_id = self.args.get("<analysis_id>", None)

        if self.analysis_id is None:
            logger.error("Please specify the analysis id")
            raise InvalidArgumentError

        self.project_id = get_project_id()

    def get_analysis_input_json(self):
        return get_cwl_analysis_input_json(
            project_id=self.project_id,
            analysis_id=self.analysis_id
        )

