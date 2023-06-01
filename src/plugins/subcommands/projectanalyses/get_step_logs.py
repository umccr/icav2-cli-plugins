#!/usr/bin/env python3

"""
Get the logs of a step

This is entirely the wrong spot for this, but the code was already all here!
"""

import tempfile
import os

from libica.openapi.v2.model.analysis_step_logs import AnalysisStepLogs
from libica.openapi.v2.model.create_cwl_analysis import CreateCwlAnalysis

from utils import is_uuid_format
from utils.config_helpers import get_project_id_from_project_name, \
    get_libicav2_configuration, get_project_id
from utils.errors import InvalidArgumentError

from utils.projectanalysis_helpers import \
    get_workflow_steps, filter_analysis_steps, write_analysis_step_logs

from subcommands import Command
from utils.logger import get_logger
from pathlib import Path
from typing import Optional, Dict, List


logger = get_logger()


class ProjectAnalysesGetStepLogs(Command):
    """Usage:
    icav2 projectanalyses get-analysis-step-logs help
    icav2 projectanalyses get-analysis-step-logs <analysis_id>
                                                 (--step-name=<step_name>)
                                                 (--stdout | --stderr)
                                                 [--output-path=<output_file>]

Description:
    Given an analysis id and project id, print either the log stderr or log stdout to console or to an output file
    The step name can be collected by running cwl-ica icav2-list-analysis-steps.
    You can also use 'cwltool' as the step-name parameter to print the cwltool debug logs.

Options:
    <analysis_id>                              Required, the analysis id you wish to list logs of
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

    def __init__(self, command_argv):
        # Initialise parameters
        self.project_id: Optional[str] = None
        self.analysis_id: Optional[str] = None
        self.step_name: Optional[str] = None
        self.stdout: Optional[bool] = None
        self.stderr: Optional[bool] = None
        self.output_path: Optional[Path] = None

        # Collect args from doc strings
        super().__init__(command_argv)

    def __call__(self):
        logger.info("Collecting workflow and getting log files")
        log_obj = self.get_analysis_logs()
        logger.info("Writing out log files, this may take some time if the analysis is still running")
        self.print_logs(log_obj)

    def check_args(self):
        # Get project id
        self.project_id = get_project_id()
        self.analysis_id = self.args.get("<analysis_id>", None)

        # Check analysis id is not None
        if self.analysis_id is None:
            logger.error("Must specify --analysis-id parameter")
            raise InvalidArgumentError

        if not is_uuid_format(self.analysis_id):
            logger.error(f"Got --analysis-id parameter as {self.analysis_id} but is not in UUID format")
            raise InvalidArgumentError

        # Get analysis storage size
        self.step_name = self.args.get("--step-name", None)

        # Check analysis id is not None
        if self.step_name is None:
            logger.error("Must specify --step-name parameter, please use the cwl-ica icav2-list-analysis-steps"
                         "and use the 'name' attribute of the step youd like to see")
            raise InvalidArgumentError
        if self.step_name == "cwltool":
            self.step_name = "pipeline_runner.0"

        # Check not both stderr and stdout have been specified
        if self.args.get("--stderr", False) and self.args.get("--stdout", False):
            logger.error("Please specify one and only one of --stderr and --stdout")
            raise InvalidArgumentError
        if not self.args.get("--stderr", False) and not self.args.get("--stdout", False):
            logger.error("Please specify one and only one of --stderr and --stdout")
            raise InvalidArgumentError

        # Check if stderr has been specified
        if self.args.get("--stderr", False):
            self.stderr = True
            self.stdout = False
        else:
            self.stderr = False
            self.stdout = True

        # Check output path parent exists
        if self.args.get("--output-path", None) is not None:
            self.output_path = Path(self.args.get("--output-path"))
            if str(self.output_path) == "-":
                # Writing to stdout
                self.output_path = None
            elif not self.output_path.parent.is_dir():
                logger.error(f"Parent of {self.output_path} does not exist, please create it first")
                raise InvalidArgumentError

    def get_analysis_logs(self) -> AnalysisStepLogs:
        # Get workflow steps
        workflow_steps = get_workflow_steps(
            project_id=self.project_id,
            analysis_id=self.analysis_id
        )

        # Get step names
        workflow_step_names = filter_analysis_steps(workflow_steps, True)

        # Check step in list of step names
        matching_workflow_steps = list(filter(lambda x: x.get("name") == self.step_name, workflow_step_names))
        if len(matching_workflow_steps) == 0:
            logger.error(f"Could not find step-name {self.step_name} in analysis id {self.analysis_id}")
            logger.error("Please try running cwl-ica icav2-list-analysis-steps to view list of available step names")
            raise ValueError
        if len(matching_workflow_steps) > 1:
            logger.error(f"Got multiple matches for step-name {self.step_name}")
            raise ValueError

        matching_workflow_step = matching_workflow_steps[0]

        if matching_workflow_step.get("status") in ["WAITING"]:
            logger.error(f"Could not get information about {self.step_name} since it is still waiting to run")
            raise ValueError

        # Get analysis step log object
        log_obj: AnalysisStepLogs = list(
            filter(
                lambda x: x.get("name").split("#", 1)[-1] == matching_workflow_step.get("name"),
                workflow_steps
            )
        )[0].logs

        if len(log_obj.to_dict()) == 0:
            logger.error(f"Could not collect logs for step {matching_workflow_step.get('name')}")
            raise AttributeError

        return log_obj

    def print_logs(self, log_obj: AnalysisStepLogs):

        if self.output_path is not None:
            output_path = self.output_path
        else:
            tmp_obj = tempfile.NamedTemporaryFile()
            output_path = tmp_obj.name

        write_analysis_step_logs(
            log_obj,
            self.project_id,
            "stderr" if self.stderr else "stdout",
            output_path,
            is_cwltool_log=True if self.step_name == "pipeline_runner.0" else False
        )

        if self.output_path is None:
            try:
                with open(output_path, 'r') as f_h:
                    print(f_h.read())
            except BrokenPipeError:
                # Chances are we were piped into head command
                pass
