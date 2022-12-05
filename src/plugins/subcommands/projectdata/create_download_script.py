#!/usr/bin/env python3

"""
Create a download script that creates a suite of presigned urls to be downloaded
encoded into a base64 script
"""

import logging

from argparse import ArgumentError
import os
from typing import List, Optional
import math

from libica.openapi.v2.model.project_data import ProjectData

from utils.config_helpers import get_project_id_from_session_file, get_project_id
from utils.projectdata_helpers import check_is_directory, list_data_non_recursively, list_files_short, list_files_long
from utils.logger import get_logger
from utils.user_helpers import get_user_from_user_id

from base64 import encode

from subcommands import Command

logger = get_logger()


class CreateDownloadScript(Command):
    """Usage:
    icav2 projectdata createdownloadscript help
    icav2 projectdata createdownloadscript <data_path> <download_path>
    """

