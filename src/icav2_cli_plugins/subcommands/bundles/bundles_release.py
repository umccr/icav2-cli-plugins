#!/usr/bin/env python3

"""
Release a bundle
"""

# Standard imports
from typing import Optional

# Wrapica imports
from wrapica.bundle import release_bundle, get_bundle_obj_from_bundle_id, Bundle
from wrapica.enums import BundleStatus
from wrapica.libica_exceptions import ApiException

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg


# Set logger
logger = get_logger()


class BundlesRelease(Command):
    """Usage:
    icav2 bundles release help
    icav2 bundles release <bundle_id_or_name>

Description:
    Release a bundle

Options:
    bundle_id_or_name        Required - The ID or name of the bundle to release

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles release abcdefg.12345
    """

    bundle_obj: Optional[Bundle]

    def __init__(self, command_argv):
        # CLI Args
        self._docopt_type_args = {
            "bundle_obj": DocOptArg(
                cli_arg_keys=["bundle_id_or_name"],
            ),
        }

        super().__init__(command_argv)

    def __call__(self):
        logger.info(f"Releasing bundle {self.bundle_obj.id}")
        release_bundle(self.bundle_obj.id)

    def check_args(self):
        # Check bundle ID is valid
        try:
            bundle_obj = get_bundle_obj_from_bundle_id(self.bundle_obj.id)
        except ApiException:
            logger.error(f"Could not get bundle {self.bundle_obj.id}")
            raise InvalidArgumentError

        # Confirm bundle status is in 'DRAFT' state
        if not BundleStatus[bundle_obj.status] == BundleStatus.DRAFT:
            logger.error(f"Bundle {self.bundle_obj.id} is not in 'DRAFT' state, cannot release bundle")
            raise InvalidArgumentError
