#!/usr/bin/env python3

"""
Add a bundle to a project
"""
# Standard imports
from typing import List, Optional

# Wrapica imports
from wrapica.bundle import (
    Bundle,
    link_bundle_to_project
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

logger = get_logger()


class BundlesAddToProject(Command):
    """Usage:
    icav2 bundles add-bundle-to-project help
    icav2 bundles add-bundle-to-project <bundle_id_or_name>
                                        (--project=<project_name_or_id>)...
    icav2 bundles add-bundle-to-project (--cli-input-yaml=<file>)
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
  --bundle=<bundle_id_or_name>          Required, the bundle id (or bundle name) to be linked to the project(s)
                                        Use as a positional parameter when not using the yaml file,
                                        otherwise, the bundle id is read from the yaml file or can be specified
                                        on the command line with this option
  --project=<project_name_or_id>        Optional, the project to add the bundle to.  This option can be specified
                                        multiple times to add the bundle to multiple projects.
                                        When using the yaml file use the 'projects' key.

  --cli-input-yaml=<file>               Optional, path to input yaml file (see yaml example above)


Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles add-bundle-to-project bundle1234 --project my-project
    icav2 bundles add-bundle-to-project --cli-input-yaml /path/to/input.yaml
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

        # Additional parameters
        self.bundle_region: Optional[Region] = None

        super().__init__(command_argv)

    def __call__(self):
        for project_iter in self.project_obj_list:
            logger.info(f"Linking bundle {self.bundle_obj.id} to project {project_iter.id}")
            link_bundle_to_project(project_iter.id, self.bundle_obj.id)
            logger.info(f"Successfully linked bundle {self.bundle_obj.id} to project {project_iter.id}")

    def check_args(self):

        # Set the bundle region
        self.bundle_region = self.bundle_obj.region

        # Check the bundle status
        if not BundleStatus(self.bundle_obj.status) == BundleStatus.RELEASED:
            logger.error("Bundle must be released before being added to a project")
            raise ValueError

        # Check regions match
        has_errors = False
        for project_obj_iter in self.project_obj_list:
            if not project_obj_iter.region.id == self.bundle_region.id:
                logger.error(
                    f"Cannot add bundle '{self.bundle_obj.id}' "
                    f"to project '{project_obj_iter.id}' as they are in different regions"
                )
                has_errors = True

        if has_errors:
            raise ValueError
