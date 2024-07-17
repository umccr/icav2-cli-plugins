#!/usr/bin/env python3

"""
Get the logs of a step

This is entirely the wrong spot for this, but the code was already all here!
"""
# Standard imports
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Wrapica imports
from wrapica.enums import AnalysisLogStreamName, ProjectAnalysisStepStatus
from wrapica.project_analysis import (
    AnalysisType,
    AnalysisStepLogs,
    get_analysis_steps,
    write_analysis_step_logs,
    analysis_step_to_dict
)

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectAnalysesGetStepLogs(Command):
    """Usage:
    icav2 projectanalyses get-analysis-step-logs help
    icav2 projectanalyses get-analysis-step-logs <analysis_id_or_user_reference>
                                                 (--step-name=<step_name>)
                                                 (--stdout | --stderr)
                                                 [--output-path=<output_file>]

Description:
    Given an analysis id and project id, print either the log stderr or log stdout to console or to an output file
    The step name can be collected by running cwl-ica icav2-list-analysis-steps.
    You can also use 'cwltool' as the step-name parameter to print the cwltool debug logs.

Options:
    <analysis_id_or_user_reference>            Required, the analysis id you wish to list logs of
    --step-name=<step_name>                    Required, the name of the step, use 'cwltool' to get the cwltool debug logs (maps to technical step id pipeline_runner.0)
    --stdout                                   Optional, get the stdout of a step
    --stderr                                   Optional, get the stderr of a step
                                               Must specify one (and only one of) --stdout and --stderr
    --output-path=<output_file>                Write output to file, otherwise written to stdout / console

Environment:
    ICAV2_ACCESS_TOKEN (optional, defaults to value in ~/.icav2/session.ica.yaml)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)
    ICAV2_PROJECT_ID (optional, defaults to value in ~/.icav2/session.ica.yaml)


Example:
    icav2 projectanalyses get-analysis-step-logs abcd12345 --step-name bclconvert_run_step --stdout
    icav2 projectanalyses get-analysis-step-logs abcd12345 --step-name cwltool --stderr --output-path cwltool-debug-logs.txt
    """

    analysis_obj: AnalysisType
    step_name: str
    stdout: bool
    stderr: bool
    output_path: Path

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "analysis_obj": DocOptArg(
                cli_arg_keys=["analysis_id_or_user_reference"],
            ),
            "step_name": DocOptArg(
                cli_arg_keys=["--step-name"],
            ),
            "stdout": DocOptArg(
                cli_arg_keys=["--stdout"]
            ),
            "stderr": DocOptArg(
                cli_arg_keys=["--stderr"]
            ),
            "output_path": DocOptArg(
                cli_arg_keys=["--output-path"],
            )
        }

        # Initialise parameters
        self.project_id: Optional[str] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def __call__(self):
        # Get then analysis logs
        logger.info("Collecting workflow and getting log files")
        log_obj = self.get_analysis_logs()
        logger.info("Writing out log files, this may take some time if the analysis is still running")
        self.print_logs(log_obj)

    def check_args(self):
        # Check project id
        self.project_id: str = get_project_id()

        # Check analysis id is not None
        if self.step_name == "cwltool":
            self.step_name = "pipeline_runner.0"

        # Check output path parent exists
        if self.output_path is not None and isinstance(self.output_path, Path) and not str(self.output_path) == "-":
            if not self.output_path.parent.is_dir():
                logger.error(f"Parent of {self.output_path} does not exist, please create it first")
                raise NotADirectoryError
        else:
            self.output_path: Path | int = sys.stdout.fileno()

    def get_analysis_logs(self) -> AnalysisStepLogs:
        # Get workflow steps
        workflow_steps = get_analysis_steps(
            project_id=self.project_id,
            analysis_id=self.analysis_obj.id,
            include_technical_steps=True
        )

        # Get step names
        workflow_steps_as_dict = list(
            map(analysis_step_to_dict, workflow_steps)
        )

        # Check step in list of step names
        matching_workflow_steps = list(filter(lambda x: x.get("name") == self.step_name, workflow_steps_as_dict))
        if len(matching_workflow_steps) == 0:
            logger.error(f"Could not find step-name {self.step_name} in analysis id {self.analysis_obj.id}")
            logger.error("Please try running cwl-ica icav2-list-analysis-steps to view list of available step names")
            raise ValueError
        if len(matching_workflow_steps) > 1:
            logger.error(f"Got multiple matches for step-name {self.step_name}")
            raise ValueError

        matching_workflow_step = matching_workflow_steps[0]

        if ProjectAnalysisStepStatus(matching_workflow_step.get("status")) == ProjectAnalysisStepStatus.WAITING:
            logger.error(f"Could not get information about {self.step_name} since it is still waiting to run")
            raise ValueError

        # Get analysis step log object
        log_obj: AnalysisStepLogs = list(
            filter(
                lambda workflow_steps_iter: (
                    workflow_steps_iter.get("name").split("#", 1)[-1] == matching_workflow_step.get("name")
                ),
                workflow_steps
            )
        )[0].logs

        if len(log_obj.to_dict()) == 0:
            logger.error(f"Could not collect logs for step {matching_workflow_step.get('name')}")
            raise AttributeError

        return log_obj

    def print_logs(self, log_obj: AnalysisStepLogs):
        # Write logs to file or stdout
        if (
                self.output_path is not None and
                not str(self.output_path) == "-" and
                not isinstance(self.output_path, int)
        ):
            output_path = self.output_path
        # Stdout, we download first and then print
        else:
            tmp_obj = tempfile.NamedTemporaryFile()
            output_path: Path = Path(tmp_obj.name)

        # Write logs
        write_analysis_step_logs(
            project_id=self.project_id,
            step_logs=log_obj,
            log_name=AnalysisLogStreamName.STDERR if self.stderr else AnalysisLogStreamName.STDOUT,
            output_path=output_path,
            is_cwltool_log=True if self.step_name == "pipeline_runner.0" else False
        )

        # Print logs
        try:
            with open(output_path, 'r') as f_h:
                print(f_h.read())
        except BrokenPipeError:
            # Chances are we were piped into head command
            pass
