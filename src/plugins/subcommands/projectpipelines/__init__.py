#!/usr/bin/env python3

"""
Project data
"""

from subcommands import SuperCommand
import sys


class ProjectPipelines(SuperCommand):
    """
Usage:
  icav2 projectpipelines <command> <args...>

Available Commands:
  create      Create a pipeline
  input       Retrieve input parameters of pipeline
  link        Link pipeline to a project
  list        List of pipelines for a project
  start       Start a pipeline
  unlink      Unlink pipeline from a project

Plugin Commands:
  create-cwl-workflow-from-zip             Upload a CWL Workflow to ICAv2 from a local zip path
  create-cwl-workflow-from-github-release  Upload a CWL Workflow to ICAv2 from a GitHub Release
  create-cwl-wes-input-template            Create a template for a CWL pipeline
  start-cwl-wes                            Launch a CWL workflow from a WES yaml

Flags:
  -h, --help   help for projectpipelines

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 projectdata [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):

        if cmd == "create-cwl-workflow-from-zip":
            from subcommands.projectpipelines.create_cwl_workflow_from_zip import ProjectDataCreateCWLWorkflow as subcommand
        if cmd == "create-cwl-workflow-from-github-release":
            from subcommands.projectpipelines.create_cwl_workflow_from_github_release import ProjectDataCreateCWLWorkflowFromGitHubRelease as subcommand
        elif cmd == "create-cwl-wes-input-template":
            from subcommands.projectpipelines.create_wes_input_template import ProjectDataCreateWESInputTemplate as subcommand
        elif cmd == "start-cwl-wes":
            from subcommands.projectpipelines.launch_cwl_wes import ProjectDataStartCWLWES as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)
        # Initialise and return
        return subcommand(command_argv)







