#!/usr/bin/env python3

"""
Initialise a bundle
"""

from pathlib import Path
from typing import Optional, List

from libica.openapi.v2.model.bundle import Bundle
from libica.openapi.v2.model.data import Data
from libica.openapi.v2.model.pipeline import Pipeline

from utils import is_uuid_format
from utils.bundle_helpers import read_input_yaml_file, get_pipelines_from_input_yaml_list, \
    get_data_objs_from_input_yaml_list, create_bundle, add_data_to_bundle, add_pipeline_to_bundle, get_bundle_from_name
from utils.errors import InvalidArgumentError
from utils.logger import get_logger

from subcommands import Command
from utils.region_helpers import get_region_id_from_city_name, get_default_region_id, get_region_id_from_input_yaml_list

logger = get_logger()


class BundlesInit(Command):
    """Usage:
    icav2 bundles init help
    icav2 bundles init <bundle_name>
                       (--short-description <description)
                       (--input-yaml <bundle.yaml>)
                       [--region <region_id_or_city_name>]
                       [--json]

Description:
    Initialise a bundle through a yaml file.

    The yaml file contains the following keys:
      * region: (optional)
        * A string containing either the region id or city-name
      * pipelines
        * A list of pipeline ids or codes to add to the bundle
        * Where each item in the list must contain one of the following keys
          * pipeline_id
          * pipeline_code
      * data
        * A list of data paths or ids to add to the bundle
        * Where each item in the list must contain one of the following keys
          * data_id  (accessed by the Data/ endpoint by default) (iterates through available regions to find data id)
          * data_uri (icav2://project-name-or-id/path-to-data/) (accessed from the projectdata endpoint)
      * analyses  :construction:
        * A list of analysis ids to add to the bundle
        * Where each item in the list must contain one of the following keys
          * analysis_id  (required)
          * pipeline_only (optional boolean)
          * data_only (optional boolean)
          * inputs_only (optional boolean)
          * outputs_only (optional boolean)

    The yaml file may look like the following
    region:
      id: abcdefg
    pipelines:
      - pipeline_code: abcdeg
      - pipeline_id: a1b2c3de-uuid
    data:
      - data_id: fil.12345567
      - data_id: fol.12345678
      - data_uri: icav2://playground/path-to-file/
      - data_uri: icav2://playground/path-to-folder/


Options:
  --short-description=<description>     Required, a short description for the bundle
  --region=<region_id_or_city_name>     Optional, specify a region ID or city name if user has access to multiple regions
                                        One may also specify the region id / city name in the input yaml.
  --input-yaml=<file>                   Required, path to input yaml file
  --json                                Return bundle as json object to stdout

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles init my-first-bundle --short-description "My very first bundle" --input-yaml file.yaml
    """

    def __init__(self, command_argv):
        # The bundle name provided by the user
        self.bundle_name: Optional[str] = None
        self.bundle_id: Optional[str] = None

        # Regino
        self.region_id: Optional[str] = None

        self.short_description: Optional[str] = None
        self.input_yaml: Optional[Path] = None
        self.release_version: Optional[int] = 1

        # Get the pipeline inputs
        self.pipeline_objs: Optional[List[Pipeline]] = None
        self.data_objs: Optional[List[Data]] = None

        super().__init__(command_argv)

    def __call__(self):
        # Initialise bundle
        bundle_obj: Bundle = create_bundle(
            bundle_name=self.bundle_name,
            region_id=self.region_id,
            bundle_description=self.short_description,
            bundle_release_version=str(self.release_version)
        )

        # Get bundle id
        self.bundle_id = bundle_obj.id
        logger.info(f"Created the bundle {self.bundle_id}")

        # Add pipeline objects to bundle
        if len(self.pipeline_objs) is not None:
            logger.info(f"Adding pipelines to bundle {self.bundle_id}")
            for pipeline_obj in self.pipeline_objs:
                if add_pipeline_to_bundle(self.bundle_id, pipeline_obj.id):
                    logger.info(f"Successfully linked pipeline {pipeline_obj.id} to {bundle_obj.id}")

        # Add data objects to bundle
        if len(self.data_objs) is not None:
            logger.info(f"Adding data to bundle {self.bundle_id}")
            data_obj: Data
            for data_obj in self.data_objs:
                if add_data_to_bundle(self.bundle_id, data_obj.id, data_obj.details.region.id):
                    logger.info(f"Successfully linked data {data_obj.id} to {bundle_obj.id}")

    def check_args(self):
        # Check the bundle name arg exists
        bundle_name_arg = self.args.get("<bundle_name>", None)
        if bundle_name_arg is None:
            logger.error("Could not get arg <bundle_name>")
            raise InvalidArgumentError

        self.bundle_name = bundle_name_arg

        short_description_arg = self.args.get("--short-description", None)
        self.short_description = short_description_arg

        # Read the bundle object
        input_yaml_arg = self.args.get("--input-yaml", None)
        if input_yaml_arg is None:
            logger.error("Please ensure --input-yaml arg is specified")
            raise InvalidArgumentError
        if not Path(input_yaml_arg).is_file():
            logger.error(f"Could not file file {input_yaml_arg}", None)
            raise FileNotFoundError

        self.input_yaml = Path(input_yaml_arg)
        yaml_obj = read_input_yaml_file(self.input_yaml)

        # Get the bundle's region ID
        region_arg = self.args.get("--region", None)
        if region_arg is not None and is_uuid_format(region_arg):
            self.region_id = region_arg
        elif region_arg is not None and not is_uuid_format(region_arg):
            self.region_id = get_region_id_from_city_name(region_arg)
        elif "region" in yaml_obj.keys():
            self.region_id = get_region_id_from_input_yaml_list(yaml_obj)
        else:
            self.region_id = get_default_region_id()

        # Check if we have a bundle of the same name in the same region?
        existing_bundle: Optional[Bundle] = get_bundle_from_name(self.bundle_name, self.region_id)
        if existing_bundle is not None:
            # Not currently possible, see https://github.com/umccr-illumina/ica_v2/issues/42
            # self.release_version = int(existing_bundle.release_version) + 1
            if existing_bundle.status == "DRAFT":
                logger.error(f"Got a bundle with the same name in the same region with id '{existing_bundle.id}'")
                logger.error(f"Use "
                             f"'icav2 add-pipeline {existing_bundle.id} --input-yaml {self.input_yaml}' or\n"
                             f"'icav2 add-data --input-yaml {self.input_yaml}'\n"
                             f"instead to add pipelines or data to this bundle.\n"
                             f"You may also wish to recreate a new bundle with a different name")
                raise AssertionError
            elif existing_bundle.status == "RELEASED":
                logger.error(f"Got a bundle with the same name in the same region with id '{existing_bundle.id}'")
                logger.error("This bundle has been released, please use a new bundle name")
                raise AssertionError

        # Get the pipeline and data objects
        self.pipeline_objs = get_pipelines_from_input_yaml_list(yaml_obj)
        self.data_objs = get_data_objs_from_input_yaml_list(yaml_obj, region_id=self.region_id)

        # Check we got some actual objects
        if (self.pipeline_objs is None or len(self.pipeline_objs) == 0) \
                and (self.data_objs is None or len(self.data_objs) == 0):
            logger.error("Found neither pipelines nor data objects in input yaml")
            raise ValueError

