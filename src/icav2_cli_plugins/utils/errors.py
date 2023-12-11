#!/usr/bin/env python

"""
Check errors
"""


class InvalidArgumentError(Exception):
    """
    The argument key or value is
    """
    pass


class PipelineNotFoundError(Exception):
    """
    The pipeline does not exist
    """
    pass