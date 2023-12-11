#!/usr/bin/env python3

"""
Add a bundle to a project
"""
from pathlib import Path
from typing import List, Optional

from .. import Command
from ...utils import is_uuid_format
from ...utils.bundle_helpers import read_input_yaml_file, \
    get_bundle_from_id, add_bundle_to_project, \
    get_project_ids_from_yaml_obj
from ...utils.config_helpers import get_project_id_from_project_name
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.region_helpers import get_project_region_id_from_project_id

logger = get_logger()


class BundlesAddToProject(Command):
    """Usage:
    icav2 bundles add-bundle-to-project help
    icav2 bundles add-bundle-to-project <bundle_id>
                                        (--input-yaml=<bundle.yaml> | --project=<project_name_or_id>)

Description:
    Add bundle to a project. Bundle MUST be released

    The input yaml may contain one of the following attributes:
    Where the projects key is a list.
    Each list attribute may be a string or a dict containing either the project_id, project_name or project key
    projects:
      - project: <project_name_or_id>
      OR
      - <project_name_or_id>

    If you have only one project to link to, you wish to may specify the project on the commandline instead.

    In order to add a bundle to a project, you will need admin access to the project.


Options:
  --input-yaml=<file>                   Optional, path to input yaml file.
  --project=<project_name_or_id         Optional, the project to add the bundle to

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles add-bundle-to-project bundle1234 --input-yaml path-to-input.yaml
    icav2 bundles add-bundle-to-project bundle1234 --project my-project
    """

    def __init__(self, command_argv):
        # The bundle id to link to the user
        self.project_ids: Optional[List] = None
        self.bundle_id: Optional[str] = None
        self.bundle_region: Optional[str] = None
        self.input_yaml: Optional[Path] = None

        super().__init__(command_argv)

    def __call__(self):
        for project_id in self.project_ids:
            if not get_project_region_id_from_project_id(project_id) == self.bundle_region:
                logger.warning(f"Cannot add bundle '{self.bundle_id}' "
                               f"to project '{project_id}' as they are in different region")
            add_bundle_to_project(project_id, self.bundle_id)

    def check_args(self):
        # Check the bundle name arg exists
        bundle_id_arg = self.args.get("<bundle_id>", None)
        if bundle_id_arg is None:
            logger.error("Could not get arg <bundle_id>")
            raise InvalidArgumentError

        self.bundle_id = bundle_id_arg
        self.bundle_region = get_bundle_from_id(self.bundle_id).region.id

        # Check the bundle status
        if not get_bundle_from_id(self.bundle_id).status.lower() == "released":
            logger.error("Bundle must be released before being added to a project")
            raise InvalidArgumentError

        # Check input yaml arg AND project arg

        # Read the bundle object from input yaml parameter (if specified)
        input_yaml_arg = self.args.get("--input-yaml", None)
        # Check if the project arg
        project_arg = self.args.get("--project")

        if input_yaml_arg is not None and project_arg is not None:
            logger.error("Please specify one (and only one) of --input-yaml and --project")
            raise InvalidArgumentError
        elif input_yaml_arg is None and project_arg is None:
            logger.error("Please specify one (and only one) of --input-yaml and --project")
            raise InvalidArgumentError

        if input_yaml_arg is not None:
            if not Path(input_yaml_arg).is_file():
                logger.error(f"Could not file file {input_yaml_arg}", None)
                raise FileNotFoundError
            self.input_yaml = Path(input_yaml_arg)
            yaml_obj = read_input_yaml_file(self.input_yaml)
            self.project_ids = get_project_ids_from_yaml_obj(yaml_obj.get("projects"))

        if project_arg is not None:
            if is_uuid_format(project_arg):
                self.project_ids = [project_arg]
            else:
                self.project_ids = [get_project_id_from_project_name(project_arg)]
