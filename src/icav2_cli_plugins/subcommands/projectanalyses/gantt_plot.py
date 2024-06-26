#!/usr/bin/env python3

"""
Create a gantt plot for an analysis run
"""

# Standard imports
from pathlib import Path
from typing import Optional, List

# Wrapica
from wrapica.project_analysis import (
    AnalysisStep, AnalysisType,
    get_analysis_steps
)

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.gantt_plot_helpers import (
    filter_workflow_steps_df, analysis_steps_list_to_df, plot_workflow_steps_df,
    add_task_duration_columns, add_task_colour_column
)
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class ProjectAnalysesGanttPlot(Command):
    """Usage:
    icav2 projectanalyses gantt-plot help
    icav2 projectanalyses gantt-plot <analysis_id_or_user_reference>
                                     [--output-path <output_plot_path>]

Description:
    Create a gantt plot for an analysis run

Options:
    <analysis_id_or_user_reference>            Required, the id or user reference of the analysis
                                               Note that the user reference must be unique within the project,
                                               If the user reference is not unique, please use an analysis id instead.
    --output-path <output_plot_path>           Optional, The output path (should end in .png), otherwise the output is <analysis_id>.gantt.png

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)


Example:
    icav2 projectanalyses gantt-plot abc12345 --output-path gantt.png
    """

    analysis_obj: AnalysisType
    output_path: Path

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "analysis_obj": DocOptArg(
                cli_arg_keys=["analysis_id_or_user_reference"],
            ),
            "output_path": DocOptArg(
                cli_arg_keys=["--output-path"],
            )
        }

        # Initialise parameters
        self.project_id: Optional[str] = None
        self.output_path: Optional[Path] = None
        self.workflow_steps: Optional[List[AnalysisStep]] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Set project id
        self.project_id = get_project_id()
        # Check if output path is specified
        # If so, check its parent exists
        if self.output_path is not None:
            if not self.output_path.parent.is_dir():
                logger.error("Could not confirm parent directory of output path exists")
                raise NotADirectoryError
            if not self.output_path.suffix == ".png":
                logger.error("--output-path should have a suffix .png")
                raise InvalidArgumentError
        else:
            self.output_path = Path.cwd() / f"{self.analysis_obj.id}.png"

        # Get analysis workflow steps
        self.workflow_steps = get_analysis_steps(
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id
        )

    def __call__(self):
        self.plot_workflow_steps()

    def plot_workflow_steps(self):
        """
        Plot the workflow steps and write to output path
        Returns:

        """
        # Get a dataframe from a list of analysis step objects
        workflow_steps_df = analysis_steps_list_to_df(self.workflow_steps)

        # Squish the executors together
        workflow_steps_df = filter_workflow_steps_df(workflow_steps_df)

        # Add in the duration columns
        workflow_steps_df = add_task_duration_columns(workflow_steps_df)

        # Add in the colour column
        workflow_steps_df = add_task_colour_column(workflow_steps_df)

        # Plot steps df
        plot_workflow_steps_df(
            workflow_steps_df=workflow_steps_df,
            output_path=self.output_path,
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id
        )
