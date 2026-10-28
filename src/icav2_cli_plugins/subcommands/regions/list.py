#!/usr/bin/env python3

"""
List the regions available to the user in this tenant
"""

# External imports
import json
import sys
from typing import Optional

# Utils
from ...utils import to_jsonable_dict
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class RegionsList(Command):
    """Usage:
    icav2 regions list help
    icav2 regions list [--json | --yaml]

Description:
    List the regions available to the user in this tenant.

Options:
    --json                  Optional, print the output in json format
    --yaml                  Optional, print the output in yaml format

    If neither --json nor --yaml is specified, the output is printed as a table.

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)

Example:
    icav2 regions list
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
        from wrapica.region import get_regions

        regions = get_regions()

        region_dicts = list(
            map(
                to_jsonable_dict,
                regions
            )
        )

        if self.is_json:
            print(json.dumps(region_dicts, indent=4))
            return

        if self.is_yaml:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.dump(region_dicts, sys.stdout)
            return

        # Default: table output with the most relevant columns
        import pandas as pd
        region_df = pd.DataFrame(
            list(
                map(
                    lambda region_iter: {
                        "id": region_iter.id,
                        "code": region_iter.code,
                        "city_name": region_iter.city_name,
                        "country": (
                            region_iter.country.name
                            if region_iter.country is not None else None
                        ),
                    },
                    regions
                )
            )
        )

        try:
            region_df.to_markdown(sys.stdout, index=False)
            print()
        except BrokenPipeError:
            pass
