#!/usr/bin/env python3

"""
List steps of an analysis

This is entirely the wrong spot for this, but the code was already all here!

"""

# External imports
import json
import sys
from datetime import datetime
from typing import Optional, Dict, List
import pandas as pd

from wrapica.enums import ProjectAnalysisStatusValues, ProjectAnalysisSortParameters
from wrapica.project_analysis.functions.project_analyses_functions import list_analyses


# Import from utils
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# locals
from .. import Command

# Get logger
logger = get_logger()


class ProjectAnalysesListV2(Command):
    """Usage:
    icav2 projectanalyses list-v2 help
    icav2 projectanalyses list-v2 [-l | --long-listing]
                                  [-t | --time-modified]
                                  [-s | --status]
                                  [-r | --reverse]
                                  [--pipeline=<pipeline_id_or_code>]
                                  [--user-reference-regex=<user_reference_regex>]
                                  [--status=<status>]
                                  [--creation-date-before=<creation_date_before>]
                                  [--creation-date-after=<creation_date_after>]
                                  [--modification-date-before=<modification_date_before>]
                                  [--modification-date-after=<modification_date_after>]


Description:
    List analysis in a project

Options:

    Output options:
    -l, --long-listing                Optional, use long-listing format to show owner, modification timestamp and size
    -t, --time-modified               Optional, sort items by time modified
    -s, --status                      Optional, sort items by status
    -r, --reverse                     Optional, reverse order

    Filtering options:
    --pipeline=<pipeline_id_or_code>                        Optional, filter by the pipeline id or code
    --user-reference-regex=<user_reference_regex>           Optional, filter by the user reference regex
    --status-filter=<status_filter>                         Optional, filter by the status (-filter added to end of parameter name to avoid conflict with --status)
    --creation-date-before=<creation_date_before>           Optional, filter by the creation date before
    --creation-date-after=<creation_date_after>             Optional, filter by the creation date after
    --modification-date-before=<modification_date_before>   Optional, filter by the modification date before
    --modification-date-after=<modification_date_after>     Optional, filter by the modification date after

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)

Example:
    icav2 projectanalyses list-v2
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.project_id: str = get_project_id()

        # Output parameters
        self.long_listing: Optional[bool] = False
        self.time_modified: Optional[bool] = False
        self.status: Optional[bool] = False
        self.reverse: Optional[bool] = False
        self.sort: Optional[List[ProjectAnalysisSortParameters]] = []

        # Filter parameters
        self.pipeline_id: Optional[str] = None
        self.user_reference_regex: Optional[str] = None
        self.status_filter: Optional[ProjectAnalysisStatusValues] = None
        self.creation_date_before: Optional[datetime] = None
        self.creation_date_after: Optional[datetime] = None
        self.modification_date_before: Optional[datetime] = None
        self.modification_date_after: Optional[datetime] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    # No arguments to check
    def check_args(self):
        # Check sort parameters
        # Check for time modified arg
        if self.time_modified:
            if self.reverse:
                self.sort.append(ProjectAnalysisSortParameters.END_DATE_DESC)
            else:
                self.sort.append(ProjectAnalysisSortParameters.END_DATE)
        # Check user reference
        if self.status:
            if self.reverse:
                self.sort.append(ProjectAnalysisSortParameters.STATUS_DESC)
            else:
                self.sort.append(ProjectAnalysisSortParameters.STATUS)

    def __call__(self):
        analysis_list = list_analyses(
            project_id=self.project_id,
            pipeline_id=self.pipeline_id,
            user_reference_regex=self.user_reference_regex,
            status=self.status,
            creation_date_before=self.creation_date_before,
            creation_date_after=self.creation_date_after,
            modification_date_before=self.modification_date_before,
            modification_date_after=self.modification_date_after,
            sort=self.sort
        )

        # Convert to dataframe
        analysis_df = pd.DataFrame(
            list(
                map(
                    lambda analysis_iter: (
                        {
                            "id": analysis_iter.id,
                            "user_reference": analysis_iter.user_reference,
                            "status": analysis_iter.status,
                            "time_created": analysis_iter.time_created,
                            "time_modified": analysis_iter.time_modified,
                            "pipeline_id": analysis_iter.pipeline.id,
                        }
                    ),
                    analysis_list
                )
            )
        )

        # Drop columns if not long listing
        if not self.long_listing:
            analysis_df = analysis_df.drop(columns=["time_created", "time_modified", "pipeline_id"])

        # Print to stdout
        analysis_df.to_markdown(sys.stdout, index=False)

        # Add an extra line to stdout
        print()
