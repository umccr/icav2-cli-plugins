#!/usr/bin/env python3

"""
List steps of an analysis

This is entirely the wrong spot for this, but the code was already all here!

"""

# External imports
import sys
from datetime import datetime
from typing import Optional, List
import pandas as pd

# Wrapica
from wrapica.enums import ProjectAnalysisStatus, ProjectAnalysisSortParameters
from wrapica.pipelines import Pipeline
from wrapica.project_analysis import list_analyses

# Import from utils
from ...utils.config_helpers import get_project_id, set_project_id_env_var
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()

# Set the project id env var
set_project_id_env_var()


class ProjectAnalysesListV2(Command):
    """Usage:
    icav2 projectanalyses list-v2 help
    icav2 projectanalyses list-v2 [-l | --long-listing]
                                  [-t | --time-modified]
                                  [-s | --status-sort]
                                  [-r | --reverse]
                                  [--max-items=<max_items>]
                                  [--pipeline=<pipeline_id_or_code>]
                                  [--user-reference=<user_reference> | --user-reference-regex=<user_reference_regex>]
                                  [--status-filter=<status>]
                                  [--creation-date-before=<creation_date_before>]
                                  [--creation-date-after=<creation_date_after>]
                                  [--modification-date-before=<modification_date_before>]
                                  [--modification-date-after=<modification_date_after>]


Description:
    List analysis in a project.

    Note only --user-reference and --status-filter will filter on the actual endpoint call.
    The other filters will be applied after all matching analyses are returned.

Options:

    Output options:
    -l, --long-listing                Optional, use long-listing format to show owner, modification timestamp and size
    -t, --time-modified               Optional, sort items by time modified
    -s, --status-sort                 Optional, sort items by status. -sort suffix to avoid conflict with --status-filter
    -r, --reverse                     Optional, reverse order
    --max-items=<max_items>           Optional, limit the number of items returned

    Filtering options:
    --pipeline=<pipeline_id_or_code>                        Optional, filter by the pipeline id or code
    --user-reference=<user_reference>                       Optional, filter by the user reference
    --user-reference-regex=<user_reference_regex>           Optional, filter by the user reference regex
    --status-filter=<status_filter>                         Optional, filter by the status (-filter added to end of parameter name to avoid conflict with --status-sort)
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

    long_listing: Optional[bool]
    time_modified: Optional[bool]
    status_sort: Optional[bool]
    reverse: Optional[bool]
    max_items: Optional[bool]

    pipeline: Optional[Pipeline]
    user_reference: Optional[str]
    status_filter: Optional[ProjectAnalysisStatus]
    creation_date_before: Optional[datetime]
    creation_date_after: Optional[datetime]
    modification_date_before: Optional[datetime]
    modification_date_after: Optional[datetime]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "long_listing": DocOptArg(
                cli_arg_keys=["--long-listing"]
            ),
            "time_modified": DocOptArg(
                cli_arg_keys=["--time-modified"]
            ),
            "status_sort": DocOptArg(
                cli_arg_keys=["--status-sort"]
            ),
            "reverse": DocOptArg(
                cli_arg_keys=["--reverse"]
            ),
            "max_items": DocOptArg(
                cli_arg_keys=["--max-items"]
            ),
            "pipeline": DocOptArg(
                cli_arg_keys=["pipeline"]
            ),
            "user_reference": DocOptArg(
                cli_arg_keys=["--user-reference"]
            ),
            "status_filter": DocOptArg(
                cli_arg_keys="--status-filter"
            ),
            "creation_date_before": DocOptArg(
                cli_arg_keys=["creation_date_before"]
            ),
            "creation_date_after": DocOptArg(
                cli_arg_keys=["creation_date_after"]
            ),
            "modification_date_before": DocOptArg(
                cli_arg_keys=["modification_date_before"]
            ),
            "modification_date_after": DocOptArg(
                cli_arg_keys=["modification_date_after"]
            )
        }

        # Initialise non cli attributes
        self.project_id: str = get_project_id()
        self.sort: Optional[List[ProjectAnalysisSortParameters]] = []

        # Filter parameters
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
        if self.status_filter:
            if self.reverse:
                self.sort.append(ProjectAnalysisSortParameters.STATUS_DESC)
            else:
                self.sort.append(ProjectAnalysisSortParameters.STATUS)

    def __call__(self):
        analysis_list = list_analyses(
            project_id=self.project_id,
            pipeline_id=self.pipeline.obj if self.pipeline is not None else None,
            user_reference=self.user_reference,
            status=self.status_filter,
            creation_date_before=self.creation_date_before,
            creation_date_after=self.creation_date_after,
            modification_date_before=self.modification_date_before,
            modification_date_after=self.modification_date_after,
            sort=self.sort,
            max_items=self.max_items
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
                            "pipeline_code": analysis_iter.pipeline.code,
                        }
                    ),
                    analysis_list
                )
            )
        )

        # Drop columns if not long listing
        if not self.long_listing:
            analysis_df = analysis_df.drop(columns=["time_created", "time_modified", "pipeline_code"])

        column_dtypes = analysis_df.dtypes.to_frame().reset_index()
        column_dtypes.columns = ["Column", "Type"]

        for analysis_df_column_name in analysis_df.columns.tolist():
            if column_dtypes.query(f"Column=='{analysis_df_column_name}'")["Type"].item().type == pd.Timestamp:
                analysis_df[analysis_df_column_name] = analysis_df[analysis_df_column_name].apply(
                    lambda dt: dt.strftime("%Y%m%dT%H%M%SZ"))

        # Print to stdout
        analysis_df.to_markdown(sys.stdout, index=False)

        # Add an extra line to stdout
        print()
