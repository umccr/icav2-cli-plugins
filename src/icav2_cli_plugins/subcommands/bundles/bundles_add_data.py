#!/usr/bin/env python3

"""
Add a data object (or list of data objects) to a bundle
"""
# Standard imports
import sys
from typing import List, Optional

# Wrapica imports
from wrapica.enums import BundleStatus
from wrapica.project import check_project_has_data_sharing_enabled
from wrapica.data import Data
from wrapica.bundle import (
    Bundle,
    add_data_to_bundle
)
from wrapica.region import Region

# Utils
from ...utils import is_interactive
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class BundlesAddData(Command):
    """Usage:
    icav2 bundles add-data help
    icav2 bundles add-data <bundle_id_or_name>
                           (--data=<data_id_or_uri>)...
    icav2 bundles add-data (--cli-input-yaml=<file>)
                           [--bundle=<bundle_id_or_name>]
                           [--data=<data_id_or_uri>]...

Description:
    Add data to a bundle

    The cli-input-yaml file may look like the following

    bundle: my_bundle_name or bundle-id
    data:
      - fil.12345567
      - fol.12345678
      - icav2://playground/path-to-file/
      - icav2://playground/path-to-folder/


Options:
  --bundle=<bundle_id_or_name>          Required, the bundle id (or bundle name) to add the data to
                                        Use as a positional parameter when not using the yaml file,
                                        otherwise, the bundle id is read from the yaml file or can be specified
                                        on the command line with this option
  --data=<data_id_or_uri>               Required, the data to add to the bundle, can also be specified in the yaml file.
                                        This option can be specified multiple times if multiple data items are to be added
                                        to the bundle. Use the 'data' key in the yaml file.

 --cli-input-yaml=<file>               Optional, path to input yaml file (see yaml example above)



Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles add-data-to-bundle my_bundle --data fil.12345678
    icav2 bundles add-data-to-bundle --cli-input-yaml /path/to/input.yaml
    """

    bundle_obj: Bundle
    data_obj_list: List[Data]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "bundle_obj": DocOptArg(
                cli_arg_keys=["bundle_id_or_name", "bundle"],
            ),
            "data_obj_list": DocOptArg(
                cli_arg_keys=["data"]
            )
        }

        # Additional parameters
        self.bundle_obj: Optional[Bundle] = None
        self.bundle_region: Optional[Region] = None

        super().__init__(command_argv)

    def __call__(self):
        data_obj: Data
        for data_obj in self.data_obj_list:
            # Add data to the bundle
            add_data_to_bundle(
                bundle_id=self.bundle_obj.id,
                data_id=data_obj.id
            )

    def check_args(self):
        # Set the bundle region
        self.bundle_region = self.bundle_obj.region

        # Check the data list is not empty
        if len(self.data_obj_list) == 0:
            logger.error("Please specify one or more data items")
            raise InvalidArgumentError

        # Check bundle status
        if BundleStatus[self.bundle_obj.status] == BundleStatus.RELEASED and is_interactive():
            logger.warning("Bundle is already released, are you sure you wish to add data to it?")
            continue_or_exit = input("Continue? (y/n): ")
            if continue_or_exit.lower() != "y":
                sys.exit(0)

        # Check projects have data sharing enabled
        self.check_projects_have_data_sharing_enabled()

        # Check data region matches bundle region
        self.check_data_region_matches_bundle_region()

    def check_projects_have_data_sharing_enabled(self):
        # Check if the project has data sharing enabled
        # Check the owning project id
        # For each of the data objects allows sharing enabled
        project_list = list(
            set(
                map(
                    lambda data_iter: data_iter.details.owning_project_id,
                    self.data_obj_list
                )
            )
        )

        has_errors = False
        for project_id in project_list:
            if not check_project_has_data_sharing_enabled(project_id):
                logger.error(
                    f"Cannot add data to bundle {self.bundle_obj.id}"
                    f"as the project {project_id} does not have data sharing enabled"
                )
                has_errors = True
        if has_errors:
            raise ValueError

    def check_data_region_matches_bundle_region(self):
        # Check if the data region matches the bundle region
        for project_data_obj in self.data_obj_list:
            if project_data_obj.data.region.id != self.bundle_region.id:
                logger.error(
                    f"Cannot add data to bundle"
                    f"as the data region {project_data_obj.data.region.city_name} does not match the bundle region {self.bundle_region.city_name}"
                )
                raise ValueError
