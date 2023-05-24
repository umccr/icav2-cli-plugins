#!/usr/bin/env python

"""
Help out tenant commands
"""
from pathlib import Path
from urllib.parse import urlparse

from ruamel.yaml import YAML

from utils.config_helpers import get_icav2_base_url
from utils.logger import get_logger

logger = get_logger()


def get_tenant_api_key_from_config_file(tenant_config_file: Path) -> str:
    """
    Get the tenant api key
    Returns:

    """
    yaml = YAML()

    with open(tenant_config_file, "r") as file_h:
        return yaml.load(file_h).get("x-api-key")


def get_server_url_from_config_file(tenant_config_file: Path) -> str:
    """
    Get the server api key
    Returns:

    """
    yaml = YAML()

    with open(tenant_config_file, "r") as file_h:
        return yaml.load(file_h).get("server-url", urlparse(get_icav2_base_url()).netloc)


def get_session_file_path_from_config_file(tenant_config_file: Path) -> Path:
    server_url = get_server_url_from_config_file(tenant_config_file)

    return tenant_config_file.parent / f".session.{server_url.split('.')[0]}.yaml"