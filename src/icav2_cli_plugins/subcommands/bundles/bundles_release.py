#!/usr/bin/env python3

"""
Release a bundle
"""

# External imports
from typing import Optional

# Libica
from libica.openapi.v2 import ApiException

# Utils
from ...utils.bundle_helpers import get_bundle_from_id, release_bundle
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# Local
from .. import Command

logger = get_logger()


class BundlesRelease(Command):
    """Usage:
    icav2 bundles release help
    icav2 bundles release <bundle_id>

Description:
    Release a bundle

Options:

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles release abcdefg.12345
    """

    def __init__(self, command_argv):
        # The bundle name provided by the user
        self.bundle_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        logger.info(f"Releasing bundle {self.bundle_id}")
        release_bundle(self.bundle_id)

    def check_args(self):
        # Check the bundle name arg exists
        bundle_id_arg = self.args.get("<bundle_id>", None)
        if bundle_id_arg is None:
            logger.error("Could not get arg <bundle_id>")
            raise InvalidArgumentError

        self.bundle_id = bundle_id_arg

        # Check bundle ID is valid
        try:
            get_bundle_from_id(self.bundle_id)
        except ApiException:
            logger.error(f"Could not get bundle {self.bundle_id}")
            raise InvalidArgumentError

