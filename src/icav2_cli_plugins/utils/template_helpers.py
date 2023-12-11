#!/usr/bin/env python

# Local imports
from .plugin_helpers import get_plugins_directory


def get_templates_dir():
    """
    Return the template directory under plugins / templates/
    :return:
    """
    return get_plugins_directory() / "templates"
