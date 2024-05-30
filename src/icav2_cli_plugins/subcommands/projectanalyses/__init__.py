#!/usr/bin/env python3

"""
Project data
"""

# External
import sys

# Interal
from .. import SuperCommand


class ProjectAnalyses(SuperCommand):
    """
Usage:
  icav2 projectanalyses <command> <args...>

CLI Commands:
  get         Get the details of an analysis
  input       Retrieve input of analyses commands
  list        List of analyses for a project
  output      Retrieve output of analyses commands
  update      Update tags of analyses

Plugin Commands:
  list-v2                          A better implementation of the 'list' command
  get-cwl-analysis-input-json      Get input json for cwl analysis
  get-cwl-analysis-output-json     Get output json for cwl analysis
  list-analysis-steps              List the steps for a cwl analysis
  get-analysis-step-logs           Get the log outputs for a cwl analysis step
  gantt-plot                       Create a gantt-plot for analysis
  abort                            Abort an analysis

Flags:
  -h, --help   help for projectanalyses

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 projectanalyses [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):

        if cmd == "get-cwl-analysis-input-json":
            from .get_input_json import ProjectAnalysesGetCWLAnalysisInputJson as subcommand
        elif cmd == "get-cwl-analysis-output-json":
            from .get_output_json import ProjectAnalysesGetCWLAnalysisOutputJson as subcommand
        elif cmd == "list-analysis-steps":
            from .list_steps import ProjectAnalysesListAnalysisSteps as subcommand
        elif cmd == "get-analysis-step-logs":
            from .get_step_logs import ProjectAnalysesGetStepLogs as subcommand
        elif cmd == "gantt-plot":
            from .gantt_plot import ProjectAnalysesGanttPlot as subcommand
        elif cmd == "abort":
            from .abort import ProjectAnalysesAbort as subcommand
        elif cmd == "list-v2":
            from .list_v2 import ProjectAnalysesListV2 as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)

        # Initialise and return
        return subcommand(command_argv)
