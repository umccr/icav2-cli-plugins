#!/usr/bin/env python3

"""
Get the default region for the user
"""

# External imports
import json
import sys
from typing import Optional

# Utils
from ...utils import to_jsonable_dict
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class RegionsGetDefaultRegion(Command):
    """Usage:
    icav2 regions get-default-region help
    icav2 regions get-default-region [--json | --yaml]

Description:
    Get the default region for the user.

    A default region can only be determined if the user has access to exactly one region.
    If the user has access to multiple regions, this command will error.

Options:
    --json                  Optional, print the full region object in json format
    --yaml                  Optional, print the full region object in yaml format

    If neither --json nor --yaml is specified, the region id is printed to stdout.

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)

Example:
    icav2 regions get-default-region
    """

    is_json: Optional[bool]
    is_yaml: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "is_json": DocOptArg(
                cli_arg_keys=["--json"],
            ),
            "is_yaml": DocOptArg(
                cli_arg_keys=["--yaml"],
            ),
        }

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Nothing to validate
        pass

    def __call__(self):
        # Lazy imports
        from wrapica.region import get_default_region

        try:
            region = get_default_region()
        except Exception as e:
            logger.error(f"Could not determine the default region: {e}")
            raise InvalidArgumentError

        if self.is_json:
            print(json.dumps(to_jsonable_dict(region), indent=4))
            return

        if self.is_yaml:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.dump(to_jsonable_dict(region), sys.stdout)
            return

        # Default: just print the region id
        print(region.id)
