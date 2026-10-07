#!/usr/bin/env python

"""
List of globals to use for icav2 cli plugins
"""
import re
from pathlib import Path

DEFAULT_ICAV2_BASE_URL = "https://ica.illumina.com/ica/rest"

ICAV2_CONFIG_FILE_SERVER_URL_KEY = "server-url"
ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY = "access-token"
ICAV2_SESSION_FILE_PROJECT_ID_KEY = "project-id"

ICAV2_CONFIG_FILE_PATH = "{HOME}/.icav2/config.yaml"
ICAV2_SESSION_FILE_PATH = "{HOME}/.icav2/.session.{server_url_prefix}.yaml"

ICAV2_ACCESS_TOKEN_AUDIENCE = "ica"

LIBICAV2_DEFAULT_PAGE_SIZE = 1000

ICAV2_MAX_STEP_CHARACTERS = 23

ICAV2_CLI_PLUGINS_HOME_ENV_VAR = "ICAV2_CLI_PLUGINS_HOME"
ICAV2_CLI_PLUGINS_TENANTS_HOME = "{ICAV2_CLI_PLUGINS_HOME}/tenants/{tenant_name}"
ICAV2_CLI_PLUGINS_TENANT_CONFIG_FILE_PATH = "{ICAV2_CLI_PLUGINS_TENANTS_HOME}/config.yaml"


def get_default_analysis_storage_size():
    """Lazy accessor to avoid loading wrapica at module import time."""
    from wrapica.enums import AnalysisStorageSize
    return AnalysisStorageSize.SMALL

PARAMS_XML_FILE_NAME = "params.xml"

BLANK_PARAMS_XML_V2_FILE_CONTENTS = [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<pd:pipeline xmlns:pd="xsd://www.illumina.com/ica/cp/pipelinedefinition" code="" version="1.0">',
    '    <pd:dataInputs/>',
    '    <pd:steps/>',
    '</pd:pipeline>'
]

GITHUB_RELEASE_DESCRIPTION_REGEX_MATCH = re.compile(
    r"GitHub\sRelease\sURL:\s(.*)"
)

GITHUB_RELEASE_REPO_TAG_REGEX_MATCH = re.compile(
    r"/(.*)/releases/tag/(.*)"
)


# Profile-based configuration constants
ICAV2_CLI_PLUGINS_BASE_DIR = Path.home() / ".icav2-cli-plugins"
CONFIG_FILE_PATH = ICAV2_CLI_PLUGINS_BASE_DIR / "config"
CACHE_DIR = ICAV2_CLI_PLUGINS_BASE_DIR / "cache"
BIN_DIR = ICAV2_CLI_PLUGINS_BASE_DIR / "bin"
LOCAL_BINARY_PATH = BIN_DIR / "_icav2"

PROFILE_NAME_REGEX = r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$'
VALID_OUTPUT_FORMATS = ('table', 'json', 'yaml')
TOKEN_REFRESH_THRESHOLD = 3600
