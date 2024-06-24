#!/usr/bin/env python3

"""
List projects a pipeline resides in
"""
# External imports
import json
from typing import Optional, List, Dict

# Wrapica imports
from wrapica.project import list_projects, Project
from wrapica.pipelines import Pipeline
from wrapica.project_pipelines import list_project_pipelines

# Utils
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ListProjects(Command):
    """Usage:
    icav2 pipelines list-projects help
    icav2 pipelines list-projects <pipeline_id_or_code>
                                  [--json] 
                                  [--include-bundle-linked]
                                  [--include-hidden-projects]

Description:
    List projects a pipeline belongs to.

    Use case 1:
    This can be used as a pre-step to icav2 projectpipeline update, when one is not sure which project context
    to enter before updating a pipeline (for this use case do NOT use --include-bundle-linked since this will also
    output projects where the pipeline is linked to).
    If no projects show up, see if any projects show up when using --include-bundle-linked. If using this option
    does show projects, then this pipeline has already been released and cannot be edited.
    If multiple projects show up without the --include-bundle-linked option, then any of these projects can edit this pipeline.


    Use case 2:
    Finding out which projects a pipeline is linked to.

Options:
    <pipeline_id_or_code>        Required, the id (or code) of the pipeline to update
    --include-hidden-projects    Optional, search hidden projects
    --json                       Optional, output in json format
    --include-bundle-linked      Optional, include projects that have the pipeline linked via a bundle

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 pipelines list-projects abcd-efgh-ijkl-mnop
    """

    pipeline_obj: Optional[Pipeline]
    include_hidden_projects: Optional[bool]
    is_json: Optional[bool]
    include_bundle_linked: Optional[bool]

    def __init__(self, command_argv):
        # CLI Args
        self._docopt_type_args = {
            "pipeline_obj": DocOptArg(
                cli_arg_keys=["pipeline_id_or_code"]
            ),
            "include_hidden_projects": DocOptArg(
                cli_arg_keys=["--include-hidden-projects"],
            ),
            "is_json": DocOptArg(
                cli_arg_keys=["--json"],
            ),
            "include_bundle_linked": DocOptArg(
                cli_arg_keys=["--include-bundle-linked"],
            )
        }

        # Initialise parameters
        self.projects: Optional[List[Project]] = None

        super().__init__(command_argv)

    def __call__(self):
        # Update pipeline
        self.filter_projects()

        # End script
        if len(self.projects) == 0:
            logger.error(f"Could not find a single project that contains the pipeline id '{self.pipeline_obj.id}'")
            raise ValueError

        if self.is_json:
            print(
                json.dumps(
                    list(
                        map(
                            lambda project_: {
                                "project_id": project_.id,
                                "project_name": project_.name
                            },
                            self.projects
                        )
                    ),
                    indent=4
                )
            )
        else:
            print(f"The following projects contain the pipeline id: '{self.pipeline_obj.id}'")
            for project in self.projects:
                print(f"* Project ID: {project.id} / Project Name: {project.name}")

    def check_args(self):
        # Get projects
        self.projects = list_projects(include_hidden_projects=self.include_hidden_projects)

    def select_linked_pipeline(self, project_pipeline_dict: Dict) -> bool:
        """
        Select linked pipeline
        :return:
        """
        if self.include_bundle_linked:
            return True
        else:
            return len(project_pipeline_dict.get("bundleLinks").get("items")) == 0

    def filter_projects(self):
        new_projects = []
        for project in self.projects:
            try:
                next(
                    filter(
                        lambda project_pipeline: (
                            project_pipeline.pipeline.id == self.pipeline_obj.id and
                            self.select_linked_pipeline(project_pipeline)
                        ),
                        list_project_pipelines(project_id=project.id)
                    )
                )
            except StopIteration:
                continue
            else:
                new_projects.append(project)

        self.projects = new_projects
