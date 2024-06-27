#!/usr/bin/env python3

"""
Remove a bundle from a project
"""

# Standard imports
from typing import List, Optional

# Wrapica imports
from wrapica.bundle import (
    Bundle,
    link_bundle_to_project, list_bundles_in_project, unlink_bundle_from_project
)
from wrapica.project import (
    Project
)
from wrapica.region import (
    Region
)
from wrapica.enums import BundleStatus

# Utils
from ...utils.logger import get_logger

# Local imports
from .. import Command, DocOptArg


# Get logger
logger = get_logger()


class BundlesRemoveFromProject(Command):
    """Usage:
    icav2 bundles remove-bundle-from-project help
    icav2 bundles remove-bundle-from-project <bundle_id_or_name>
                                             (--project=<project_name_or_id>)...
    icav2 bundles remove-bundle-from-project (--cli-input-yaml=<file>)
                                             [--bundle=<bundle_id_or_name>]
                                             [--project=<project_name_or_id>]...


Description:
    Add bundle to a project. Bundle MUST be released

    The cli input yaml may look like the following

    bundle: my_bundle_name or bundle-id
    projects:
      - my_project_id_1
      - my_project_name_2

    If you have only one project to link to, you wish to may specify the project on the commandline instead.

    In order to add a bundle to a project, you will need admin access to the project.


Options:
  --bundle=<bundle_id_or_name>          Required, the bundle id (or bundle name) to be remove from the project(s)
                                        Use as a positional parameter when not using the yaml file,
                                        otherwise, the bundle id is read from the yaml file or can be specified
                                        on the command line with this option
  --project=<project_name_or_id>        Optional, the project(s) to remove the bundle from.  This option can be specified
                                        multiple times to remove the bundle from multiple projects.
                                        When using the yaml file use the 'projects' key.

  --cli-input-yaml=<file>               Optional, path to input yaml file (see yaml example above)


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles remove-bundle-from-project bundle1234 --project my-project
    icav2 bundles remove-bundle-from-project --cli-input-yaml /path/to/input.yaml
    """

    bundle_obj: Bundle
    project_obj_list: List[Project]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "bundle_obj": DocOptArg(
                cli_arg_keys=["bundle_id_or_name", "bundle"],
            ),
            "project_obj_list": DocOptArg(
                cli_arg_keys=["project"],
                yaml_arg_keys=["projects"]
            )
        }

        super().__init__(command_argv)

    def __call__(self):
        for project_iter in self.project_obj_list:
            logger.info(f"Removing bundle {self.bundle_obj.id} from project {project_iter.id}")
            unlink_bundle_from_project(
                project_id=project_iter.id,
                bundle_id=self.bundle_obj.id
            )
            logger.info(f"Successfully unlinked bundle {self.bundle_obj.id} from project {project_iter.id}")

    def check_args(self):
        # Check the bundle is in the project
        projects_with_bundle = []
        for project_obj in self.project_obj_list:
            for bundle in list_bundles_in_project(project_id=project_obj.id):
                if bundle.id == self.bundle_obj.id:
                    break
            else:
                logger.info(f"Could not find bundle {self.bundle_obj.id} in project {project_obj.id}, skipping this project")
                continue
            projects_with_bundle.append(project_obj)

        self.project_obj_list = projects_with_bundle
