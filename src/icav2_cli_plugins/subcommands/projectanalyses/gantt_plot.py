#!/usr/bin/env python3

"""
Create a gantt plot for an analysis run
"""

# External imports
from pathlib import Path
from typing import Optional, List

# Libica
from libica.openapi.v2.model.analysis_step import AnalysisStep

# Utils
from ...utils import is_uuid_format
from ...utils.config_helpers import get_project_id
from ...utils.gantt_plot_helpers import (
    filter_workflow_steps_df, analysis_list_to_df, plot_workflow_steps_df,
    add_task_duration_columns, add_task_colour_column
)
from ...utils.projectanalysis_helpers import (
    get_workflow_steps, filter_analysis_steps
)
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# Locals
from .. import Command



logger = get_logger()


class ProjectAnalysesGanttPlot(Command):
    """Usage:
    icav2 projectanalyses gantt-plot help
    icav2 projectanalyses gantt-plot <analysis_id>
                                     [--output-path <output_plot_path>]

Description:
    Create a gantt plot for an analysis run

Options:
    <analysis_id>                              Required, the id of the analysis
    --output-path <output_plot_path>           Optional, The output path (should end in .png), otherwise the output is <analysis_id>.gantt.png

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, set as ~/.icav2/.session.ica.yaml if not set)


Example:
    icav2 projectanalyses gantt-plot abc12345 --output-path gantt.png
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.project_id: Optional[str] = None
        self.analysis_id: Optional[str] = None
        self.output_path: Optional[Path] = None

        self.workflow_steps: Optional[List[AnalysisStep]] = None

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
            raise InvalidArgumentError

        if not is_uuid_format(self.analysis_id):
            logger.error(f"Got --analysis-id parameter as {self.analysis_id} but is not in UUID format")
            raise InvalidArgumentError

        # Check if show technical steps has been specified
        if self.args.get("--output-path", None):
            self.output_path = Path(self.args.get("--output-path"))
            # Check output path is not a directory
            if self.output_path.is_dir():
                logger.error(f"--output-path should specify path to a file, but {self.output_path} is a directory")
                raise InvalidArgumentError
            if not self.output_path.parent.is_dir():
                logger.error(f"--output-path parent should exist, please create directory {self.output_path.parent} first")
                raise InvalidArgumentError
            # Ensure the output path has a png suffix
            if not self.output_path.suffix == ".png":
                logger.error("--output-path should have a suffix .png")
                raise InvalidArgumentError
        else:
            self.output_path = self.args.get(Path.cwd() / f"{self.analysis_id}.png")

        self.workflow_steps = get_workflow_steps(
            project_id=self.project_id,
            analysis_id=self.analysis_id
        )

    def __call__(self):
        self.plot_workflow_steps()

    def plot_workflow_steps(self):
        """
        Plot the workflow steps and write to output path
        Returns:

        """
        # Get a dataframe from a list of analysis step objects
        workflow_steps_df = analysis_list_to_df(self.workflow_steps)

        # Squish the executors together
        workflow_steps_df = filter_workflow_steps_df(workflow_steps_df)

        # Add in the duration columns
        workflow_steps_df = add_task_duration_columns(workflow_steps_df)

        # Add in the colour column
        workflow_steps_df = add_task_colour_column(workflow_steps_df)

        # Plot steps df
        plot_workflow_steps_df(workflow_steps_df, self.output_path, self.analysis_id)





