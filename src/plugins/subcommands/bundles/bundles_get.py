#!/usr/bin/env python3

"""
List the existing bundles
"""
from pathlib import Path
from typing import Optional, List, Dict

from libica.openapi.v2.model.bundle import Bundle
from pandas.io import json

from utils import is_uuid_format
from utils.bundle_helpers import \
    filter_bundles, print_bundles, bundle_to_yaml_obj, get_bundle_dict_object
from utils.errors import InvalidArgumentError
from utils.logger import get_logger

from subcommands import Command
from utils.region_helpers import get_region_id_from_city_name, get_default_region_id, get_region_id_from_input_yaml_list
from utils.user_helpers import get_user_from_user_name

logger = get_logger()


class BundlesGet(Command):
    """Usage:
    icav2 bundles get help
    icav2 bundles get <bundle_id>
                      [--json]
                      [--output-yaml <path_to_yaml>]

Description:
    Get a bundle, if specifying --output-yaml the output object has the following attributes:
    region: <region_id>
    pipelines:
      - pipeline_id: <pipeline_id>
        pipeline_code: <pipeline_code>
      ...
    data:
      - data_id: <data_id>
        data_uri: <data_uri>
      ...

Options:
  --json                       Optional: Return bundle object in json format to stdout
  --output-yaml=<output_yaml>  Optional: Write out bundle attributes into yaml object

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles get abcdefg.12345 --output-yaml bundle.abcdefg.yaml
    """

    def __init__(self, command_argv):
        # The bundle name provided by the user
        self.bundle_id: Optional[str] = None
        self.bundle_obj: Optional[Dict] = None
        self.output_yaml: Optional[Path] = None
        self.json_arg: Optional[bool] = None

        super().__init__(command_argv)

    def __call__(self):
        if self.json_arg:
            print(json.dumps(get_bundle_dict_object(self.bundle_id), indent=2))
        if self.output_yaml is not None:
            logger.info(f"Writing bundle info to {self.output_yaml}")
            with open(self.output_yaml, "w") as yaml_h:
                bundle_to_yaml_obj(self.bundle_id, yaml_h)

    def check_args(self):
        # Check if the bundle name arg exists
        bundle_id_arg = self.args.get("<bundle_id>", None)
        if bundle_id_arg is not None:
            self.bundle_id = bundle_id_arg

        # Check if the json arg exists
        json_arg = self.args.get("--json", None)
        if json_arg is not None and json_arg is not False:
            self.json_arg = True
        else:
            self.json_arg = False

        # Check if the output yaml arg exists AND parent exists
        output_yaml_arg = self.args.get("--output-yaml", None)
        if output_yaml_arg is not None:
            if not Path(output_yaml_arg).parent.is_dir():
                logger.error(f"--output-yaml specified but parent directory of '{output_yaml_arg}' does not exist. "
                             "Please create this directory and try again")
                raise InvalidArgumentError
            self.output_yaml = Path(output_yaml_arg)

        if not self.json_arg and output_yaml_arg is None:
            logger.error("Please specify at least one of --json OR --output-yaml")
            raise InvalidArgumentError

