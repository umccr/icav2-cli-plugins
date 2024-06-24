#!/usr/bin/env python3

"""
List the existing bundles
"""

# External imports
from typing import Optional, List, Union

# Wrapica
from wrapica.region import Region
from wrapica.bundle import filter_bundles, Bundle
from wrapica.enums import BundleStatus
from wrapica.user import User

# Utils
from ...utils.bundle_helpers import print_bundles
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

logger = get_logger()


class BundlesList(Command):
    """Usage:
    icav2 bundles list help
    icav2 bundles list [--name <name_or_regex>]
                       [--status <status>]
                       [--creator <creator_id_or_username>]
                       [--region <region_id_or_city_name>]
                       [--json]

Description:
    List available bundles

Options:
  --name=<name>                         Optional, show only bundles that match a certain bundle name,
                                        can use a regex here too
  --status=<status>                     Optional, show only bundles by status (one of DRAFT, RELEASED, DEPRECATED)
  --creator=<creator_id_or_username>    Optional, show only bundles that are created by this user
  --region=<region_id_or_city_name>     Optional, show only bundles of a certain region
  --json                                Return bundle list as json list object to stdout (table by default)

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles list
    """

    bundle_name: Optional[str]
    status: Optional[Union[BundleStatus]]
    creator_obj: Optional[User]
    region: Optional[Region]
    is_json: Optional[bool]


    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "bundle_name": DocOptArg(
                cli_arg_keys=["--name"]
            ),
            "status": DocOptArg(
                cli_arg_keys=["--status"]
            ),
            "creator_obj": DocOptArg(
                cli_arg_keys=["--creator"]
            ),
            "region_obj": DocOptArg(
                cli_arg_keys=["--region"]
            ),
            "is_json": DocOptArg(
                cli_arg_keys=["--json"]
            )
        }

        # Extras
        # The bundle name provided by the user
        self.bundle_obj_list: Optional[List[Bundle]] = None
        super().__init__(command_argv)

    def __call__(self):
        logger.debug("Printing bundles")
        print_bundles(self.bundle_obj_list, json_output=self.is_json)

    def check_args(self):
        # Get bundles list
        self.bundle_obj_list: List[Bundle] = filter_bundles(
            bundle_name=self.bundle_name,
            region_id=self.region.id if self.region is not None else None,
            status=BundleStatus(self.status) if self.status is not None else None,
            creator_id=self.creator_obj.id if self.creator_obj is not None else None
        )

        # Check list
        if len(self.bundle_obj_list) == 0:
            logger.error("No bundles found")
            raise AssertionError
