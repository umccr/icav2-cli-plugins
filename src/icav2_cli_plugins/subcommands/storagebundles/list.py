#!/usr/bin/env python3

"""
List the storage bundles available to the user in this tenant
"""

# External imports
import json
import sys
from typing import List, Optional

# Utils
from ...utils import to_jsonable_dict
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


def get_storage_bundles() -> List:
    """
    Retrieve the list of storage bundles available to the user.

    wrapica does not (yet) provide a wrapper for storage bundles, so we call
    the libica v3 StorageBundleApi directly using the wrapica configuration
    (which reads ICAV2_ACCESS_TOKEN / ICAV2_BASE_URL from the environment).
    """
    from libica.openapi.v3 import ApiClient, ApiException
    from libica.openapi.v3.api.storage_bundle_api import StorageBundleApi
    from wrapica.utils.configuration import get_icav2_configuration

    with ApiClient(get_icav2_configuration()) as api_client:
        api_instance = StorageBundleApi(api_client)

    try:
        api_response = api_instance.get_storage_bundles()
    except ApiException as e:
        logger.error("Exception when calling StorageBundleApi->get_storage_bundles: %s\n" % e)
        raise ApiException

    return api_response.items


class StorageBundlesList(Command):
    """Usage:
    icav2 storagebundles list help
    icav2 storagebundles list [--json | --yaml]

Description:
    List the storage bundles available to the user in this tenant.

Options:
    --json                  Optional, print the output in json format
    --yaml                  Optional, print the output in yaml format

    If neither --json nor --yaml is specified, the output is printed as a table.

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)

Example:
    icav2 storagebundles list
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
        storage_bundles = get_storage_bundles()

        storage_bundle_dicts = list(
            map(
                to_jsonable_dict,
                storage_bundles
            )
        )

        if self.is_json:
            print(json.dumps(storage_bundle_dicts, indent=4))
            return

        if self.is_yaml:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.dump(storage_bundle_dicts, sys.stdout)
            return

        # Default: table output with the most relevant columns
        import pandas as pd
        storage_bundle_df = pd.DataFrame(
            list(
                map(
                    lambda bundle_iter: {
                        "id": bundle_iter.id,
                        "bundle_name": bundle_iter.bundle_name,
                        "entitlement_name": bundle_iter.entitlement_name,
                        "region_city_name": (
                            bundle_iter.region.city_name
                            if bundle_iter.region is not None else None
                        ),
                    },
                    storage_bundles
                )
            )
        )

        try:
            storage_bundle_df.to_markdown(sys.stdout, index=False)
            print()
        except BrokenPipeError:
            pass
