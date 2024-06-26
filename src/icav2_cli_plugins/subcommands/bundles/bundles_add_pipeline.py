#!/usr/bin/env python3

"""
Add a pipeline object (or list of pipeline objects) to a bundle
"""
# External imports
import sys
from typing import List, Optional


# Wrapica imports
from wrapica.bundle import (
    Bundle,
    add_pipeline_to_bundle
)
from wrapica.enums import PipelineStatus, BundleStatus
from wrapica.pipelines import (
    PipelineType
)

# Utils
from ...utils import is_interactive
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg

logger = get_logger()


class BundlesAddPipeline(Command):
    """Usage:
    icav2 bundles add-pipeline help
    icav2 bundles add-pipeline <bundle_id_or_name>
                               (--pipeline=<pipeline_id_or_code>...)
    icav2 bundles add-pipeline (--cli-input-yaml=<file>)
                               [--bundle=<bundle_id_or_name>]
                               [--pipeline=<pipeline_id_or_code>]...

Description:
    Add a released pipeline to a bundle

    The cli-input-yaml may look like the following
    bundle: my_bundle_id
    pipelines:
      - my_pipeline_code_or_id

Options:
  --bundle=<bundle_id_or_name>          Required, the bundle id (or bundle name) to add the pipeline to
                                        Use as a positional parameter when not using the yaml file,
                                        otherwise, the bundle id is read from the yaml file or can be specified
                                        on the command line with this option
  --pipeline=<pipeline_id_or_code>      Required, the pipeline id or code to add to the bundle,
                                        can be specified either on the command line or through the input yaml file.
                                        When specified in the yaml file, the key should be 'pipelines'

  --cli-input-yaml=<file>               Optional, path to input yaml file (see yaml example above)

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles add-pipeline my_bundle --pipeline my_pipeline_code
    icav2 bundles add-pipeline --cli-input-yaml /path/to/input.yaml
    """

    bundle_obj: Optional[Bundle]
    pipeline_obj_list: List[PipelineType]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "bundle_obj": DocOptArg(
                cli_arg_keys=["bundle_id_or_name", "bundle"],
            ),
            "pipeline_obj_list": DocOptArg(
                cli_arg_keys=["pipeline"],
                yaml_arg_keys=["pipelines"],
            )
        }

        super().__init__(command_argv)

    def __call__(self):
        for pipeline in self.pipeline_obj_list:
            # Add pipeline to the bundle
            add_pipeline_to_bundle(
                bundle_id=self.bundle_obj.id,
                pipeline_id=pipeline.id
            )

    def check_args(self):
        # Check bundle status
        if (
                BundleStatus(self.bundle_obj.status) == BundleStatus.RELEASED
                and is_interactive()
        ):
            logger.warning("Bundle is already released, are you sure you wish to add data to it?")
            continue_or_exit = input("Continue? (y/n): ")
            if continue_or_exit.lower() != "y":
                sys.exit(0)

        # Check each pipeline has been released
        has_errors = False
        for pipeline_obj in self.pipeline_obj_list:
            if not PipelineStatus(pipeline_obj.status) == PipelineStatus.RELEASED:
                logger.error(
                    f"Pipeline {pipeline_obj.id} is not released, only released pipelines can be added to a bundle"
                )
                has_errors = True
        if has_errors:
            raise ValueError("One or more pipelines has not yet been released")