#!/usr/bin/env python3

import os
from pathlib import Path

from utils.globals import ICAV2_CLI_PLUGINS_HOME_ENV_VAR
from utils.logger import get_logger

logger = get_logger()


def get_icav2_plugins_home_dir():
    if (icav2_plugins_dir := os.environ.get(ICAV2_CLI_PLUGINS_HOME_ENV_VAR, None)) is None:
        logger.error("Could not get env var '{ICAV2_CLI_PLUGINS_HOME_ENV_VAR}'")
        raise EnvironmentError

    return Path(icav2_plugins_dir)


def get_plugins_directory():
    return get_icav2_plugins_home_dir() / "plugins"


def get_tenants_directory():
    return get_icav2_plugins_home_dir() / "tenants"
