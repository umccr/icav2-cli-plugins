#!/usr/bin/env python3

"""
Project data
"""

from .. import SuperCommand
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
  create-cwl-pipeline-from-zip             Upload a CWL Workflow to ICAv2 from a local zip path
  create-cwl-pipeline-from-github-release  Upload a CWL Workflow to ICAv2 from a GitHub Release
  create-nextflow-pipeline-from-nf-core    Upload a nf-core pipeline to ICAv2
  create-nextflow-pipeline-from-zip        Upload a nextflow pipeline from a zip file
  create-wes-input-template                Create a template for an ICAv2 pipeline
  start-wes                                Launch an ICAv2 Pipeline from a WES yaml
  update                                   Update a projectpipeline
  download                                 Download a projectpipeline to a zip file
  release                                  Release a projectpipeline

Flags:
  -h, --help   help for projectpipelines

Global Flags:
  -t, --access-token string    JWT used to call rest service
  -o, --output-format string   output format (default "table")
  -s, --server-url string      server url to direct commands
  -k, --x-api-key string       api key used to call rest service

Use "icav2 projectpipelines [command] --help" for more information about a command.
    """

    def __init__(self, command_argv):
        super().__init__(command_argv)

    def get_subcommand_obj(self, cmd, command_argv):

        if cmd == "create-cwl-pipeline-from-zip":
            from .create_cwl_workflow_from_zip import ProjectPipelinesCreateCWLWorkflow as subcommand
        elif cmd == "create-cwl-pipeline-from-github-release":
            from .create_cwl_pipeline_from_github_release import ProjectPipelinesCreateCWLWorkflowFromGitHubRelease as subcommand
        elif cmd == "create-nextflow-pipeline-from-nf-core":
            from .create_nextflow_pipeline_from_nf_core import ProjectPipelinesCreateNextflowPipelineFromNfCore as subcommand
        elif cmd == "create-nextflow-pipeline-from-zip":
            from .create_nextflow_pipeline_from_zip import ProjectPipelinesCreateNextflowPipelineFromZip as subcommand
        elif cmd == "create-wes-input-template":
            from .create_wes_input_template import ProjectPipelinesCreateWESInputTemplate as subcommand
        elif cmd == "start-wes":
            from .launch_wes import ProjectPipelinesStartWES as subcommand
        elif cmd == "update":
            from .pipelines_update import ProjectPipelinesUpdate as subcommand
        elif cmd == "download":
            from .download_pipeline import ProjectPipelinesDownload as subcommand
        elif cmd == "release":
            from .release_pipeline import ProjectPipelineReleasePipeline as subcommand
        else:
            print(self.__doc__)
            print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
            sys.exit(1)
        # Initialise and return
        return subcommand(command_argv)







