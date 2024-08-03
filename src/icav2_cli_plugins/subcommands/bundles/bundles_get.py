#!/usr/bin/env python3

"""
List the existing bundles
"""
# Standard imports
import sys
from pathlib import Path
from typing import Optional
import json
from ruamel.yaml import YAML

# Wrapica imports
from wrapica.bundle import (
    Bundle
)

# Utils
from ...utils.bundle_helpers import (
    bundle_to_yaml_obj, bundle_to_dict
)
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class BundlesGet(Command):
    """Usage:
    icav2 bundles get help
    icav2 bundles get <bundle_id_or_name>
                      (--json | --yaml)
                      [--include-metadata]
                      [--output-path <path_to_file>]

Description:
    Get a bundle, the output object has the following attributes:  (comments only available when --yaml is set)
    id: <bundle_id>  # Bundle name
    region: <region_id>  # Region name
    tenant: <tenant_id>  # Tenant name
    pipelines:
      - <pipeline_id>  # pipeline-code
      ...
    data:
      - <data_id>  # Data uri
      ...
    metadata:  (Only included when --include-metadata is set)
      name: <bundle_name>
      short_description: <bundle_short_description>
      version: <bundle_version>
      version_description: <bundle_version_description>

Options:
  --json                       Optional: Return bundle object in json format
  --yaml                       Optional: Return the bundle in yaml format
  --include-metadata           Optional: Include metadata in the bundle object
  --output-path=<path>         Optional: Write out bundle attributes out to a file, otherwise to stdout

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles get abcdefg.12345 --output-yaml bundle.abcdefg.yaml
    """

    bundle_obj: Optional[Bundle]
    is_json: Optional[bool]
    is_yaml: Optional[bool]
    include_metadata: Optional[bool]
    output_path: Optional[Path]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "bundle_obj": DocOptArg(
                cli_arg_keys=["bundle_id_or_name"],
            ),
            "is_json": DocOptArg(
                cli_arg_keys=["--json"],
            ),
            "is_yaml": DocOptArg(
                cli_arg_keys=["--yaml"]
            ),
            "include_metadata": DocOptArg(
                cli_arg_keys=["--include-metadata"]
            ),
            "output_path": DocOptArg(
                cli_arg_keys=["--output-path"],
            )
        }

        super().__init__(command_argv)

    def __call__(self):
        with open(self.output_path, "w") as output_h:
            if self.is_json:
                json.dump(
                    bundle_to_dict(
                        self.bundle_obj,
                        include_metadata=self.include_metadata
                    ),
                    indent=2,
                    fp=output_h
                )
            else:
                yaml = YAML()
                yaml.indent(mapping=2, sequence=4, offset=2)
                yaml.dump(
                    bundle_to_yaml_obj(
                        self.bundle_obj,
                        include_metadata=self.include_metadata
                    ),
                    output_h
                )

    def check_args(self):
        # Check that the parent directory is required for the output path
        if self.output_path is not None and not self.output_path.parent.exists():
            raise FileNotFoundError(f"Parent directory {self.output_path.parent} does not exist")

        # Set self.output_path to stdout if not provided
        if self.output_path is None:
            self.output_path: int = sys.stdout.fileno()
        logger.info("Finished checking args")
