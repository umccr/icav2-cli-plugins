#!/usr/bin/env python3

"""
Get output json

# FIXME - the output json is not the same as we should expect.
# FIXME - see https://github.com/umccr-illumina/ica_v2/issues/185

Instead we should do the following

Collect the output json from stdout of the cwltool step.

Rename the 'data/out/' location steps based on the outputs API -
but this needs to wait for https://github.com/umccr-illumina/ica_v2/issues/182
to also be solved

"""
# External data
import json
from typing import Optional, Dict

# Wrapica imports
from wrapica.libica_models import Analysis
from wrapica.project_analysis import get_cwl_analysis_output_json

# Utils imports
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class ProjectAnalysesGetCWLAnalysisOutputJson(Command):
    """Usage:
    icav2 projectanalyses help
    icav2 projectanalyses get-cwl-analysis-output-json <analysis_id_or_user_reference>

Description:
    Given an analysis ID, show the output json of the analysis.

Options:
    <analysis_id_or_user_reference>    Required, the analysis id or user reference

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectanalyses get-cwl-analysis-output-json abc--123456789
    """

    analysis_obj: Analysis

    def __init__(self, command_argv):
        # CLI Args
        self._docopt_type_args = {
            "analysis_obj": DocOptArg(
                cli_arg_keys=["analysis_id_or_user_reference"],
            )
        }

        # Initialise the other args
        self.project_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        analysis_output_json: Dict = self.get_analysis_output_json()
        print(
            json.dumps(analysis_output_json, indent=4)
        )

    def check_args(self):
        # Set the project id
        self.project_id = get_project_id()

    def get_analysis_output_json(self):
        return get_cwl_analysis_output_json(
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id
        )
