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
  archive              archive data
  create               Create data id for a project
  delete               delete data
  download             Download a file/folder
  downloadurl          get download url
  folderuploadsession  Get details of a folder upload
  get                  Get details of a data
  link                 Link data to a project
  list                 List data
  mount                Mount project data
  temporarycredentials fetch temporal credentials for data
  unarchive            unarchive data
  unlink               Unlink data to a project
  unmount              Unmount project data
  update               Updates the details of a data
  upload               Upload a file/folder

Plugin Commands:
  create-cwl-workflow-from-zip      Upload a CWL Workflow to ICAv2
  create-cwl-wes-input-template     Create a template for a CWL pipeline
  start-cwl-wes                     Launch a CWL workflow from a WES yaml

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







