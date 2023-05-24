#!/usr/bin/env python3

"""
Add a data object (or list of data objects) to a bundle
"""
from pathlib import Path
from typing import List, Optional, Union

from libica.openapi.v2.model.data import Data

from subcommands import Command
from utils.bundle_helpers import read_input_yaml_file, \
    add_data_to_bundle, get_data_objs_from_input_yaml_list, get_bundle_from_id
from utils.errors import InvalidArgumentError
from utils.logger import get_logger
from utils.projectdata_helpers import convert_icav2_uri_to_data_obj

logger = get_logger()


class BundlesAddData(Command):
    """Usage:
    icav2 bundles add-data help
    icav2 bundles add-data <bundle_id>
                           (--input-yaml=<bundle.yaml> | --data-id=<data_id> | --data-uri=<data_uri>)

Description:
    Add data to a bundle

    The yaml file may look like the following, in this subcommand however, we only look at the 'data' key
    region:
      id: abcdefg
    pipelines:
      - pipeline-code: abcdeg
      - pipeline-id: a1b2c3de-uuid
    data:
      - data-id: fil.12345567
      - data-id: fol.12345678
      - data-uri: icav2://playground/path-to-file/
      - data-uri: icav2://playground/path-to-folder/


Options:
  --input-yaml=<file>                   Optional, path to input yaml file.
  --data-id=<data-id>                   Optional, the data id to add to the bundle
  --data-uri=<data-uri>                 Optional, the data uri to add to the bundle

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles add-data-to-bundle --input-yaml path-to-input.yaml
    """

    def __init__(self, command_argv):
        # The bundle name provided by the user
        self.bundle_id: Optional[str] = None
        self.bundle_region: Optional[str] = None

        self.data_id: Optional[Union[str | List[Data]]] = None
        self.input_yaml: Optional[Path] = None

        super().__init__(command_argv)

    def __call__(self):
        if isinstance(self.data_id, List):
            data: Data
            for data in self.data_id:
                # Add data to the bundle
                add_data_to_bundle(
                    bundle_id=self.bundle_id,
                    data_id=data.id,
                    data_region_id=data.details.region.id
                )
        else:
            # Add data to the bundle
            add_data_to_bundle(
                bundle_id=self.bundle_id,
                data_id=self.data_id
            )

    def check_args(self):
        # Check the bundle name arg exists
        bundle_id_arg = self.args.get("<bundle_id>", None)
        if bundle_id_arg is None:
            logger.error("Could not get arg <bundle_id>")
            raise InvalidArgumentError

        self.bundle_id = bundle_id_arg
        self.bundle_region = get_bundle_from_id(self.bundle_id).region.id

        # Read the bundle object from input yaml parameter (if specified)
        input_yaml_arg = self.args.get("--input-yaml", None)
        if input_yaml_arg is not None:
            if not Path(input_yaml_arg).is_file():
                logger.error(f"Could not file file {input_yaml_arg}", None)
                raise FileNotFoundError
            self.input_yaml = Path(input_yaml_arg)
            yaml_obj = read_input_yaml_file(self.input_yaml)
            # Get the data and data objects
            self.data_id: List[Data] = get_data_objs_from_input_yaml_list(yaml_obj, self.bundle_region)

        data_id_arg = self.args.get("--data-id", None)
        data_uri_arg = self.args.get("--data-uri", None)

        if data_id_arg is not None:
            self.data_id = data_id_arg

        if data_uri_arg is not None:
            self.data_id = convert_icav2_uri_to_data_obj(data_uri_arg)
