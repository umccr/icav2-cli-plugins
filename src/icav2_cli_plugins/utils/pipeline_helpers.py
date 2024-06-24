#!/usr/bin/env python

"""
Helpers for pipeline functions
"""
# External imports
from pathlib import Path
from deepdiff import DeepDiff
from ruamel.yaml import YAML

# Utils
from .logger import get_logger

# Set logger
logger = get_logger()


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
