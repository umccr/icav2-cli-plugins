#!/usr/bin/env python3

"""
List the storage configurations available to the user in this tenant
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


def get_storage_configurations() -> List:
    """
    Retrieve the full list of storage configuration objects available to the user.

    The wrapica get_storage_configuration_list helper only returns a reduced
    id/bucketName/keyPrefix mapping, so we call the libica v3
    StorageConfigurationApi directly to obtain the full objects (matching the
    output of the native 'icav2 storageconfigurations list' command).
    """
    from libica.openapi.v3 import ApiClient, ApiException
    from libica.openapi.v3.api.storage_configuration_api import StorageConfigurationApi
    from wrapica.utils.configuration import get_icav2_configuration

    with ApiClient(get_icav2_configuration()) as api_client:
        api_instance = StorageConfigurationApi(api_client)

    try:
        api_response = api_instance.get_storage_configurations()
    except ApiException as e:
        logger.error("Exception when calling StorageConfigurationApi->get_storage_configurations: %s\n" % e)
        raise ApiException

    return api_response.items


class StorageConfigurationsList(Command):
    """Usage:
    icav2 storageconfigurations list help
    icav2 storageconfigurations list [--json | --yaml]

Description:
    List the storage configurations available to the user in this tenant.

Options:
    --json                  Optional, print the output in json format
    --yaml                  Optional, print the output in yaml format

    If neither --json nor --yaml is specified, the output is printed as a table.

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)

Example:
    icav2 storageconfigurations list
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
        storage_configurations = get_storage_configurations()

        storage_configuration_dicts = list(
            map(
                to_jsonable_dict,
                storage_configurations
            )
        )

        if self.is_json:
            print(json.dumps(storage_configuration_dicts, indent=4))
            return

        if self.is_yaml:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.dump(storage_configuration_dicts, sys.stdout)
            return

        # Default: table output with the most relevant columns
        import pandas as pd
        storage_configuration_df = pd.DataFrame(
            list(
                map(
                    lambda config_iter: {
                        "id": config_iter.id,
                        "name": config_iter.name,
                        "type": config_iter.type,
                        "status": config_iter.status,
                        "region_city_name": (
                            config_iter.region.city_name
                            if config_iter.region is not None else None
                        ),
                        "is_default": config_iter.is_default,
                    },
                    storage_configurations
                )
            )
        )

        try:
            storage_configuration_df.to_markdown(sys.stdout, index=False)
            print()
        except BrokenPipeError:
            pass
