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

# Utils imports
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger
from ...utils.projectpipeline_helpers import get_cwl_analysis_output_json

# Locals
from .. import Command


# Set logger
logger = get_logger()


class ProjectAnalysesGetCWLAnalysisOutputJson(Command):
    """Usage:
    icav2 projectanalyses help
    icav2 projectanalyses get-cwl-analysis-output-json <analysis_id>

Description:
    Given an analysis ID, show the output json at
    Future enhancements of this command will allow a user to 'defererence' the input json.

Options:
    <analysis_id>            Required, the analysis id

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectanalyses get-cwl-analysis-output-json abc--123456789
    """

    def __init__(self, command_argv):
        # Get the command args
        self.analysis_id: Optional[str] = None
        self.project_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        analysis_output_json: Dict = self.get_analysis_output_json()
        print(
            json.dumps(analysis_output_json, indent=4)
        )

    def check_args(self):
        self.analysis_id = self.args.get("<analysis_id>", None)

        if self.analysis_id is None:
            logger.error("Please specify the analysis id")
            raise InvalidArgumentError

        self.project_id = get_project_id()

    def get_analysis_output_json(self):
        return get_cwl_analysis_output_json(
            project_id=self.project_id,
            analysis_id=self.analysis_id
        )

