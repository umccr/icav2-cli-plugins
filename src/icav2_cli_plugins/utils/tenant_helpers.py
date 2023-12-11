#!/usr/bin/env python

"""
Help out tenant commands
"""

# External imports
import json
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse
from ruamel.yaml import YAML

# Libica imports
from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.project_api import ProjectApi
from libica.openapi.v2.model.project import Project
from libica.openapi.v2.model.project_paged_list import ProjectPagedList

# Local imports
from .config_helpers import get_icav2_base_url, get_libicav2_configuration
from .logger import get_logger
from .subprocess_handler import run_subprocess_proc

# Set logger
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


def get_project_list_curl(base_url: str, access_token: str) -> Optional[List[Dict]]:
    curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc([
            "curl",
            "--fail-with-body",
            "--silent",
            "--location",
            "--show-error",
            "--request", "GET",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {access_token}",
            "--url", f"{base_url}/api/projects"
        ],
        capture_output=True
    )

    if not curl_returncode == 0:
        logger.error("Could not list projects")
        raise ChildProcessError

    return json.loads(curl_stdout).get("items")


def get_tenant_name_from_project_list(base_url: str, access_token: str) -> Optional[str]:
    """
    Assumes tenant has at least one project
    Returns:
      Tenant name if we have a project otherwise none
    """

    project_list = get_project_list_curl(base_url, access_token)

    if len(project_list) == 0:
        logger.warning("No projects available, could not get tenant name according to the api")
        return None

    for project in project_list:
        if project.get("tenantName") is not None:
            return project.get("tenantName")

    logger.warning("No project had the tenantName attribute.")
    return None


def get_tenant_id_from_project_list(base_url, access_token) -> Optional[str]:
    """
        Assumes tenant has at least one project
        Returns:
          Tenant name if we have a project otherwise none
        """

    project_list = get_project_list_curl(base_url, access_token)

    if len(project_list) == 0:
        logger.warning("No projects available, could not get tenant name according to the api")
        return None

    for project in project_list:
        if project.get("tenantId") is not None:
            return project.get("tenantId")

    logger.warning("No project had the tenantId attribute.")
    return None
