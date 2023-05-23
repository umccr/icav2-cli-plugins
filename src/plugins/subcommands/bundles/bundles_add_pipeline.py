#!/usr/bin/env python3

"""
Add a pipeline object (or list of pipeline objects) to a bundle
"""
from pathlib import Path
from typing import List, Optional, Union

from libica.openapi.v2.model.pipeline import Pipeline

from subcommands import Command
from utils.bundle_helpers import add_pipeline_to_bundle, read_input_yaml_file, get_pipelines_from_input_yaml_list
from utils.config_helpers import get_project_id
from utils.errors import InvalidArgumentError
from utils.logger import get_logger
from utils.projectpipeline_helpers import get_pipeline_id_from_pipeline_code

logger = get_logger()


class BundlesAddPipeline(Command):
    """Usage:
    icav2 bundles add-pipeline help
    icav2 bundles add-pipeline <bundle_id>
                               (--input-yaml=<bundle.yaml> | --pipeline-id=<pipeline_id> | --pipeline-code=<pipeline_code>)

Description:
    Add a released pipeline to a bundle

    The yaml file may look like the following, in this subcommand however, we only look at the 'pipelines' key
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
  --pipeline-id=<pipeline-id>           Optional, the pipeline id to add to the bundle
  --pipeline-code=<pipeline-code>       Optional, the pipeline code to add to the bundle

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest

Example:
    icav2 bundles add-pipeline-to-bundle --input-yaml path-to-input.yaml
    """

    def __init__(self, command_argv):
        # The bundle name provided by the user
        self.bundle_id: Optional[str] = None

        self.pipeline_id: Optional[Union[str | List[Pipeline]]] = None
        self.input_yaml: Optional[Path] = None

        super().__init__(command_argv)

    def __call__(self):
        if isinstance(self.pipeline_id, List):
            pipeline: Pipeline
            for pipeline in self.pipeline_id:
                # Add pipeline to the bundle
                add_pipeline_to_bundle(
                    bundle_id=self.bundle_id,
                    pipeline_id=pipeline.id
                )
        else:
            # Add pipeline to the bundle
            add_pipeline_to_bundle(
                bundle_id=self.bundle_id,
                pipeline_id=self.pipeline_id
            )

    def check_args(self):
        # Check the bundle name arg exists
        bundle_id_arg = self.args.get("<bundle_id>", None)
        if bundle_id_arg is None:
            logger.error("Could not get arg <bundle_id>")
            raise InvalidArgumentError

        self.bundle_id = bundle_id_arg

        # Read the bundle object from input yaml parameter (if specified)
        input_yaml_arg = self.args.get("--input-yaml", None)
        if input_yaml_arg is not None:
            if not Path(input_yaml_arg).is_file():
                logger.error(f"Could not file file {input_yaml_arg}", None)
                raise FileNotFoundError
            self.input_yaml = Path(input_yaml_arg)
            yaml_obj = read_input_yaml_file(self.input_yaml)
            # Get the pipeline and data objects
            self.pipeline_id: List[Pipeline] = get_pipelines_from_input_yaml_list(yaml_obj)

        pipeline_id_arg = self.args.get("--pipeline-id", None)
        pipeline_code_arg = self.args.get("--pipeline-code", None)

        if pipeline_id_arg is not None:
            self.pipeline_id = pipeline_id_arg

        if pipeline_code_arg is not None:
            self.pipeline_id = get_pipeline_id_from_pipeline_code(get_project_id(), pipeline_code_arg)
