#!/usr/bin/env python

"""
List of globals to use for icav2 cli plugins
"""
from enum import Enum

DEFAULT_ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY = "access-token"
ICAV2_SESSION_FILE_PROJECT_ID_KEY = "project-id"

ICAV2_SESSION_FILE_PATH = "{HOME}/.icav2/.session.ica.yaml"

ICAV2_ACCESS_TOKEN_AUDIENCE = "ica"

LIBICAV2_DEFAULT_PAGE_SIZE = 1000

ICAV2_MAX_STEP_CHARACTERS = 23


class ICAv2AnalysisStorageSize(Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE = ICAv2AnalysisStorageSize.SMALL
