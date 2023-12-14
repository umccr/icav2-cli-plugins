#!/usr/bin/env python

"""
Helpers for pipeline functions
"""
# External imports
from pathlib import Path
from typing import List
from deepdiff import DeepDiff
from ruamel.yaml import YAML

# Libica
from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.pipeline_api import PipelineApi
from libica.openapi.v2.model.pipeline import Pipeline

# Utils
from .config_helpers import get_libicav2_configuration
from .errors import PipelineNotFoundError
from .logger import get_logger

# Set logger
logger = get_logger()


def get_pipeline_from_pipeline_id(pipeline_id: str) -> Pipeline:
    """
    Get the pipeline from the pipeline id
    :param pipeline_id:
    :return:
    """
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = PipelineApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a pipeline.
        api_response: Pipeline = api_instance.get_pipeline(pipeline_id)
        return api_response
    except ApiException as e:
        logger.error("Exception when calling PipelineApi->get_pipeline: %s\n" % e)
        raise ApiException


def list_all_pipelines() -> List[Pipeline]:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = PipelineApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Retrieve a list of pipelines.
        pipelines: List[Pipeline] = api_instance.get_pipelines().items
    except ApiException as e:
        logger.error("Could not get pipeline list")
        raise ApiException

    return pipelines


def get_pipeline_id_from_pipeline_code(pipeline_code: str) -> str:
    try:
        return next(
            filter(
                lambda pipeline: pipeline.code == pipeline_code,
                list_all_pipelines()
            )
        ).id
    except StopIteration:
        logger.error(f"Could not get pipeline id from pipeline code {pipeline_code}")
        raise PipelineNotFoundError


def compare_yaml_files(path_a: Path, path_b: Path) -> DeepDiff:
    """
    Read in each yaml file and print the differences
    Use https://stackoverflow.com/a/72142230 here
    Args:
        path_a:
        path_b:

    Returns:

    """
    yaml_a = YAML()
    yaml_b = YAML()

    with open(path_a, 'r') as path_a_h:
        yaml_a_dict = yaml_a.load(path_a_h)

    with open(path_b, 'r') as path_b_h:
        yaml_b_dict = yaml_b.load(path_b_h)

    return DeepDiff(yaml_a_dict, yaml_b_dict)
