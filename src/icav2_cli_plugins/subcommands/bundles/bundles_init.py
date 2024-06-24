#!/usr/bin/env python3

"""
Initialise a bundle
"""

# Standard imports
import json
import sys
from pathlib import Path
from typing import Optional, List
from ruamel.yaml import YAML

# Wrapica
from wrapica.bundle import (
    Bundle,
    generate_empty_bundle,
    add_pipeline_to_bundle,
    add_data_to_bundle,
    get_bundle_obj_from_bundle_name
)
from wrapica.pipelines import (
    Pipeline, get_pipeline_obj_from_pipeline_id
)
from wrapica.region import (
    Region, get_region_obj_from_region_id
)
from wrapica.data import (
    Data
)
from wrapica.region import (
    get_default_region
)

# Utils
from ...utils.bundle_helpers import bundle_to_dict, bundle_to_yaml_obj
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg

logger = get_logger()


class BundlesInit(Command):
    """Usage:
    icav2 bundles init help
    icav2 bundles init <bundle_name>
                       (--short-description=<description>)
                       (--bundle-version=<bundle_version>)
                       (--bundle-version-description=<description>)
                       [--pipeline=<pipeline_id_or_code>]...
                       [--data=<data_id_or_uri>]...
                       [--category=<category>]...
                       [--region <region_id_or_city_name>]
                       [--json | --yaml]
    icav2 bundles init (--cli-input-yaml=<file>)
                       [--bundle-name=<bundle_name>]
                       [--short-description=<description>]
                       [--bundle-version=<bundle_version>]
                       [--bundle-version-description=<description>]
                       [--pipeline=<pipeline_id_or_code>]...
                       [--data=<data_id_or_uri>]...
                       [--category=<category>]...
                       [--region <region_id_or_city_name>]
                       [--json | --yaml]

Description:
    Initialise a bundle, the bundle will be in 'DRAFT' state.

    The cli input yaml file may look like the following
    name: my_first_bundle # Required (can also be specified on the cli)
    region: my-region-id OR my-region-city-name # Optional
    pipelines:  # Optional - list of either a pipeline id or pipeline code
      - a_pipeline_code
      - a1b2c3de-uuid-pipeline-id
    data:  # Optional - list of either a data id or data uri
      - fil.12345567
      - fol.12345678
      - icav2://playground/path-to-file/
      - icav2://project-id/path-to-folder/
    categories:
      - category1
      - category2

    Use either --json or --yaml to specify the output format. If neither --json or --yaml are specified,
    the bundle id will be printed to stdout.


Options:
  --short-description=<description>          Required, a short description for the bundle
  --bundle-version=<bundle_version>          Required, specify the bundle version
  --bundle-version-description=<description> Required, specify a description for the bundle version
  --pipeline=<pipeline_id_or_code>           Optional, specify a pipeline ID or code to add to the bundle
                                             (specify multiple times for multiple pipelines).
                                             Use the 'pipelines' key when using the input yaml file invocation.
  --data=<data_id_or_uri>                    Optional, specify a data ID or URI to add to the bundle
                                             (specify multiple times for multiple data).
                                             Use the 'data' key when using the input yaml file invocation.
  --category=<category>                      Optional, specify a category for the bundle.
                                             (specify multiple times for multiple categories).
                                             Use the 'categories' key when using the input yaml file invocation.
  --region=<region_id_or_city_name>          Optional, specify a region ID or city name if user has access to multiple regions
  --json                                     Optional, return the output in json format
  --yaml                                     Optional, return the output in yaml format

  --cli-input-yaml=<file>                    Optional, path to input yaml file

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles init my-first-bundle --short-description "My very first bundle" --input-yaml file.yaml
    """

    bundle_name: str
    short_description: str
    bundle_version: str
    bundle_version_description: str
    pipeline_obj_list: Optional[List[Pipeline]]
    data_obj_list: Optional[List[Data]]
    categories: Optional[List[str]]
    region: Optional[Region]
    is_json: Optional[bool]
    is_yaml: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "bundle_name": DocOptArg(
                cli_arg_keys=["--bundle-name"],
            ),
            "short_description": DocOptArg(
                cli_arg_keys=["--short-description"]
            ),
            "bundle_version": DocOptArg(
                cli_arg_keys=["--bundle-version"]
            ),
            "bundle_version_description": DocOptArg(
                cli_arg_keys=["--bundle-version-description"]
            ),
            "pipeline_obj_list": DocOptArg(
                cli_arg_keys=["--pipeline"],
                yaml_arg_keys=["pipelines"],
            ),
            "data_obj_list": DocOptArg(
                cli_arg_keys=["--data"],
                yaml_arg_keys=["data"],
            ),
            "categories": DocOptArg(
                cli_arg_keys=["--category"],
                yaml_arg_keys=["categories"],
            ),
            "region": DocOptArg(
                cli_arg_keys=["--region"],
            ),
            "is_json": DocOptArg(
                cli_arg_keys=["--json"]
            ),
            "is_yaml": DocOptArg(
                cli_arg_keys=["--yaml"]
            ),
        }

        # Additional args
        self.bundle_obj: Optional[Bundle] = None

        super().__init__(command_argv)

    def __call__(self):
        # Initialise bundle
        self.bundle_obj: Bundle = generate_empty_bundle(
            bundle_name=self.bundle_name,
            bundle_version=str(self.bundle_version),
            short_description=self.short_description,
            version_comment=self.bundle_version_description,
            region_id=self.region.id,
            categories=self.categories
        )

        # Get bundle id
        self.bundle_id = self.bundle_obj.id
        logger.info(f"Created the bundle {self.bundle_id}")

        # Add pipeline objects to bundle
        if len(self.pipeline_obj_list) is not None and len(self.pipeline_obj_list) > 0:
            logger.info(f"Adding pipelines to bundle {self.bundle_id}")
            for pipeline_obj in self.pipeline_obj_list:
                if add_pipeline_to_bundle(self.bundle_id, pipeline_obj.id):
                    logger.info(f"Successfully linked pipeline {pipeline_obj.id} to {self.bundle_id}")
                else:
                    logger.warning(f"Could not add pipeline {pipeline_obj.id} to bundle {self.bundle_id}")

        # Add data objects to bundle
        if len(self.data_obj_list) is not None:
            logger.info(f"Adding data to bundle {self.bundle_id}")
            data_obj: Data
            for data_obj in self.data_obj_list:
                if add_data_to_bundle(self.bundle_id, data_obj.id):
                    logger.info(f"Successfully linked data {data_obj.id} to {self.bundle_id}")
                else:
                    logger.warning(f"Could not add data {data_obj.id} to bundle {self.bundle_id}")

        with open(sys.stdout.fileno(), "w") as output_h:
            if self.is_json:
                json.dump(
                    bundle_to_dict(
                        self.bundle_obj,
                        include_metadata=True
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
                        include_metadata=True
                    ),
                    output_h
                )

    def check_args(self):
        # Set region
        if self.region is None:
            self.region = get_default_region()

        # Check if we have a bundle of the same name in the same region?
        existing_bundle: Optional[Bundle] = get_bundle_obj_from_bundle_name(self.bundle_name, self.region.id)
        if existing_bundle is not None:
            # Not currently possible, see https://github.com/umccr-illumina/ica_v2/issues/42
            # self.bundle_version = int(existing_bundle.bundle_version) + 1
            if existing_bundle.status == "DRAFT":
                logger.error(f"Got a bundle with the same name in the same region with id '{existing_bundle.id}'")
                logger.error(f"Use "
                             f"'icav2 bundle add-pipeline --pipeline 'my-pipeline-id' <my_bundle_name>' or\n"
                             f"'icav2 bundle add-data --data 'my-data-id' <my_bundle_name>'\n"
                             f"instead to add pipelines or data to this bundle.\n"
                             f"You may also wish to recreate a new bundle with a different name")
                raise AssertionError
            elif existing_bundle.status == "RELEASED":
                logger.error(f"Got a bundle with the same name in the same region with id '{existing_bundle.id}'")
                logger.error("This bundle has been released, please use a new bundle name")
                raise AssertionError

        # Check we got some actual objects
        if (self.pipeline_obj_list is None or len(self.pipeline_obj_list) == 0) \
                and (self.data_obj_list is None or len(self.data_obj_list) == 0):
            logger.warning(
                "Found neither pipelines nor data objects to add to the bundle. "
                "Do you wish to continue to generate an empty bundle?"
            )
            continue_or_exit = input("Continue? [y/n]: ")
            if continue_or_exit.lower() != "y":
                sys.exit(0)
