#!/usr/bin/env python3

"""
Get input json
"""
# External imports
import json
from typing import Optional, Dict

# Wrapica imports
from wrapica.project_analysis import get_cwl_analysis_input_json, Analysis, get_analysis_obj_from_analysis_id

# Utils
from ...utils.config_helpers import get_project_id, set_project_id_env_var
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectAnalysesGetCWLAnalysisInputJson(Command):
    """Usage:
    icav2 projectanalyses help
    icav2 projectanalyses get-cwl-analysis-input-json <analysis_id_or_user_reference>

Description:
    Given an analysis ID, show the input json used to launch the pipeline.
    Future enhancements of this command will allow a user to 'defererence' the input json.

Options:
    <analysis_id_or_user_reference>            Required, the id (or user reference) of the analysis.
                                               Note that the user reference must be unique within the project,
                                               If the user reference is not unique, please use an analysis id instead.

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectanalyses get-cwl-analysis-input-json abc--123456789
    """

    analysis_obj: Analysis

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "analysis_obj": DocOptArg(
                cli_arg_keys=["analysis_id_or_user_reference"],
            )
        }
        # Collect other args
        self.project_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        analysis_input_json: Dict = self.get_analysis_input_json()
        print(
            json.dumps(
                analysis_input_json,
                indent=4
            )
        )

    def check_args(self):
        # Set the project id
        self.project_id = get_project_id()

    def get_analysis_input_json(self):
        return get_cwl_analysis_input_json(
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id
        )
