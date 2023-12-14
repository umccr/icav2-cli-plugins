#!/usr/bin/env python3

"""
List projects a pipeline resides in
"""
import json
# External imports
from typing import Optional, List, Dict
from libica.openapi.v2.model.project import Project

# Utils
from ...utils import is_uuid_format
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.pipeline_helpers import get_pipeline_id_from_pipeline_code
from ...utils.project_helpers import list_projects
from ...utils.projectpipeline_helpers import list_project_pipelines

# Locals
from .. import Command

# Get logger
logger = get_logger()


class ListProjects(Command):
    """Usage:
    icav2 pipelines list-projects help
    icav2 pipelines list-projects <pipeline_id>  
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
    <pipeline_id>                Required, the id (or code) of the pipeline to update
    --include-hidden-projects    Optional, search hidden projects
    --json                       Optional, output in json format
    --include-bundle-linked      Optional, include projects that have the pipeline linked via a bundle

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 pipelines list-projects abcd-efgh-ijkl-mnop
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.projects: Optional[List[Project]] = None
        self.pipeline_id: Optional[str] = None
        self.include_hidden_projects: Optional[bool] = None
        self.json: Optional[bool] = None
        self.bundle_linked: Optional[bool] = False

        super().__init__(command_argv)

    def __call__(self):
        # Update pipeline
        self.filter_projects()

        # End script
        if len(self.projects) == 0:
            logger.error(f"Could not find a single project that contains the pipeline id '{self.pipeline_id}'")
            raise ValueError

        if self.json:
            print(
                json.dumps(
                    list(
                        map(
                            lambda project_: {"project_id": project_.id, "project_name": project_.name},
                            self.projects
                        )
                    ),
                    indent=4
                )
            )
        else:
            print(f"The following projects contain the pipeline id: '{self.pipeline_id}'")
            for project in self.projects:
                print(f"* Project ID: {project.id} / Project Name: {project.name}")

    def get_pipeline_id(self):
        pipeline_id_arg = self.args.get("<pipeline_id>", None)
        if pipeline_id_arg is None:
            logger.error("Please specify a pipeline id or code")
            raise InvalidArgumentError

        # Get pipeline id (if in code format)
        if is_uuid_format(pipeline_id_arg):
            pipeline_id = pipeline_id_arg
        else:
            pipeline_id = get_pipeline_id_from_pipeline_code(pipeline_id_arg)

        return pipeline_id

    def check_args(self):
        # Get the pipeline id
        self.pipeline_id = self.get_pipeline_id()

        # Check parameters
        self.include_hidden_projects = self.args.get("--include-hidden-projects", False)
        self.json = self.args.get("--json", False)
        self.bundle_linked = self.args.get("--include-bundle-linked", False)

        # Get projects
        self.projects = list_projects(include_hidden_projects=self.include_hidden_projects)

    def select_linked_pipeline(self, project_pipeline_dict: Dict) -> bool:
        """
        Select linked pipeline
        :return:
        """
        if self.bundle_linked:
            return True
        else:
            return len(project_pipeline_dict.get("bundleLinks").get("items")) == 0

    def filter_projects(self):
        new_projects = []
        for project in self.projects:
            try:
                next(
                    filter(
                        lambda project_pipeline: project_pipeline.get("pipeline").get("id") == self.pipeline_id and
                                                 self.select_linked_pipeline(project_pipeline),
                        list_project_pipelines(project_id=project.id)
                    )
                )
            except StopIteration:
                continue
            else:
                new_projects.append(project)

        self.projects = new_projects
