#!/usr/bin/env python3

"""
List the existing bundles
"""

# External imports
from typing import Optional, List

# Libica
from libica.openapi.v2.model.bundle import Bundle

# Utils
from ...utils import is_uuid_format
from ...utils.bundle_helpers import \
    filter_bundles, print_bundles
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.region_helpers import get_region_id_from_city_name
from ...utils.user_helpers import get_user_from_user_name

# Locals
from .. import Command

logger = get_logger()


class BundlesList(Command):
    """Usage:
    icav2 bundles list help
    icav2 bundles list [--bundle-name <name>]
                       [--status <status>]
                       [--creator=<creator_id_or_username>]
                       [--region <region_id_or_city_name>]

Description:
    List available bundles

Options:
  --status=<status>                     Optional, show only bundles by status (one of DRAFT, RELEASED, DEPRECATED)
  --bundle-name=<name>                  Optional, show only bundles that match a certain bundle name
  --creator=<creator_id_or_username>    Optional, show only bundles that are created by this user
  --region=<region_id_or_city_name>     Optional, show only bundles of a certain region
  --json                                Return bundle list as json list object to stdout (table by default)

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles list
    """

    def __init__(self, command_argv):
        # The bundle name provided by the user
        self.bundles_list: Optional[List[Bundle]] = None
        self.bundle_name: Optional[str] = None
        self.status: Optional[str] = None
        self.creator_id: Optional[str] = None
        self.region: Optional[str] = None
        self.json: Optional[bool] = None

        super().__init__(command_argv)

    def __call__(self):
        print_bundles(self.bundles_list, json_output=self.json)

    def check_args(self):
        # Check if the bundle name arg exists
        bundle_name_arg = self.args.get("--bundle-name", None)
        if bundle_name_arg is not None:
            self.bundle_name = bundle_name_arg

        # Check if the status arg exists
        status_arg = self.args.get("--status", None)
        if status_arg is not None:
            if status_arg.upper() not in ["DRAFT", "RELEASED", "DEPRECATED"]:
                logger.error("Please ensure status arg is one of 'DRAFT', 'RELEASED', 'DEPRECATED'")
                raise InvalidArgumentError
            self.status = status_arg

        # Check if the creator arg exists
        creator_arg = self.args.get("--creator", None)
        if creator_arg is not None:
            if is_uuid_format(creator_arg):
                self.creator_id = creator_arg
            else:
                self.creator_id = get_user_from_user_name(creator_arg).id

        # Check if the region arg exists
        region_arg = self.args.get("--region", None)
        if region_arg is not None:
            if is_uuid_format(region_arg):
                self.region_id = region_arg
            else:
                self.region_id = get_region_id_from_city_name(region_arg)

        # Check if json command exists
        json_arg = self.args.get("--json", None)
        if json_arg is not None:
            self.json = True
        else:
            self.json = False

        # Get bundles list
        self.bundles_list: List[Bundle] = filter_bundles(
            bundle_name=self.bundle_name,
            region_id=self.region,
            status=self.status,
            creator_id=self.creator_id
        )

        # Check list
        if self.bundles_list == 0:
            logger.error("No bundles found")
            raise AssertionError
