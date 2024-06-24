#!/usr/bin/env python3

"""
Configuration helpers

From collecting configuration from ~/.session.ica.yaml through ruamel to creating configuration object for libicav2
"""
# External data
import os
from base64 import b64decode
from collections import OrderedDict
import json
from ruamel.yaml import YAML
from pathlib import Path
from datetime import datetime
from jwt import decode, InvalidTokenError
from typing import Optional
from urllib.parse import urlparse

# Libica
from libica.openapi.v2 import Configuration

# Locals
from .globals import (
    ICAV2_CONFIG_FILE_PATH, ICAV2_SESSION_FILE_PATH, ICAV2_ACCESS_TOKEN_AUDIENCE,
    DEFAULT_ICAV2_BASE_URL, ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY, ICAV2_SESSION_FILE_PROJECT_ID_KEY,
    ICAV2_CONFIG_FILE_SERVER_URL_KEY, ICAV2_CLI_PLUGINS_TENANTS_HOME, ICAV2_CLI_PLUGINS_TENANT_CONFIG_FILE_PATH
)
from .subprocess_handler import run_subprocess_proc
from .logger import get_logger

# Set logger
logger = get_logger()

# GLobals
LIBICAV2_CONFIGURATION: Optional[Configuration] = None


def get_config_file_path() -> Path:
    """
    Get path for the config file and asser it exists
    :return:
    """
    logger.error("Trying to retrieve the path of the icav2 config file, we don't use this when using the icav2-cli-plugins repo")
    raise NotImplementedError


def get_tenant_config_file_path(tenant_name: str, raise_if_not_found: bool = True) -> Path:
    """
    Get path for the tenant config file and assert it exists
    :return:
    """
    tenant_config_file_path: Path = Path(
        ICAV2_CLI_PLUGINS_TENANT_CONFIG_FILE_PATH.format(
            ICAV2_CLI_PLUGINS_TENANTS_HOME=ICAV2_CLI_PLUGINS_TENANTS_HOME.format(
                ICAV2_CLI_PLUGINS_HOME=os.environ["ICAV2_CLI_PLUGINS_HOME"],
                tenant_name=tenant_name
            )
        )
    )

    if not tenant_config_file_path.is_file() and raise_if_not_found:
        logger.error(f"Could not get file path {tenant_config_file_path}")
        raise FileNotFoundError

    return tenant_config_file_path


def read_config_file(tenant_name: Optional[str] = None) -> OrderedDict:
    """
    Get the contents of the session file (~/.icav2/config.ica.yaml)
    :return:
    """

    if tenant_name is not None:
        config_file_path = get_tenant_config_file_path(tenant_name)
    else:
        config_file_path = get_config_file_path()

    logger.debug("Reading in the config file")
    yaml = YAML()

    with open(config_file_path, "r") as file_h:
        data = yaml.load(file_h)

    return data


def get_session_file_path() -> Path:
    """
    Get path for session file and assert file exists
    :return:
    """
    logger.error("Trying to retrieve the path of the icav2 session file, we don't use this when using the icav2-cli-plugins repo")
    raise NotImplementedError


def read_session_file() -> OrderedDict:
    """
    Get the contents of the session file (~/.icav2/.session.ica.yaml)
    :return:
    """
    logger.error("Trying to get information from the icav2 session file, we don't use this when using the icav2-cli-plugins repo")
    raise NotImplementedError


def read_tenant_session_file(tenant_name: str) -> OrderedDict:
    """
    Get the contents of the tenant session file (~/.icav2-cli-plugins/tenants/.session.ica.yaml)
    :param tenant_name:
    :return:
    """

    logger.debug("Reading in the tenant session file")
    yaml = YAML()

    tenant_session_file_path: Path = Path(
        ICAV2_CLI_PLUGINS_TENANTS_HOME.format(
            ICAV2_CLI_PLUGINS_HOME=os.environ["ICAV2_CLI_PLUGINS_HOME"],
            tenant_name=tenant_name
        )
    ) / (
        ".session.{server_url_prefix}.yaml".format(
            server_url_prefix=urlparse(
                get_icav2_base_url(tenant_name=tenant_name)
            ).netloc.split(".")[0]
        )
    )

    if not tenant_session_file_path.is_file():
        logger.error(f"Could not get file path {tenant_session_file_path}")
        raise FileNotFoundError

    with open(tenant_session_file_path, "r") as file_h:
        data = yaml.load(file_h)

    return data


def get_access_token_from_session_file(refresh: bool = True) -> str:
    """
    Collect the contents of the access token
    :return:
    """
    session_data: OrderedDict = read_session_file()

    access_token: str = session_data.get(ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY, None)

    if access_token is None:
        logger.error("Could not get access token from session file")
        raise KeyError

    if not check_access_token_expiry(access_token):
        if not refresh:
            logger.error(f"Could not refresh access token in session file {ICAV2_SESSION_FILE_PATH}")
            raise KeyError
        else:
            access_token = refresh_access_token()

    return access_token


def get_tenant(raise_if_not_found: bool = True) -> Optional[str]:
    if os.environ.get("ICAV2_TENANT_NAME") is not None:
        return os.environ.get("ICAV2_TENANT_NAME")
    elif os.environ.get("ICAV2_DEFAULT_TENANT_NAME") is not None:
        return os.environ.get("ICAV2_DEFAULT_TENANT_NAME")
    elif (Path(os.environ.get("ICAV2_CLI_PLUGINS_HOME")) / "tenants" / "default_tenant.txt").is_file():
        with open(Path(os.environ.get("ICAV2_CLI_PLUGINS_HOME")) / "tenants" / "default_tenant.txt", "r") as file_h:
            return file_h.read().strip()
    if not raise_if_not_found:
        return None
    logger.error("Could not get tenant name from environment variables or default tenant file.")
    raise AssertionError


def get_project_id(raise_if_not_found: bool = True) -> Optional[str]:
    project_id = os.environ.get("ICAV2_PROJECT_ID")
    if project_id is None:
        tenant_name = get_tenant(raise_if_not_found=raise_if_not_found)
        logger.debug("Env var ICAV2_PROJECT_ID was empty, getting project id from session file")
        try:
            project_id = get_project_id_from_session_file(tenant_name)
        except KeyError:
            if not raise_if_not_found:
                return None
            logger.error("Please either set ICAV2_PROJECT_ID in your environment or "
                         "set the project id in the session file.  "
                         "You can set the environment variable by running "
                         "\"icav2 projects enter 'project-name'\" and set the "
                         "project id in the session file by running "
                         "\"icav2 projects enter --global 'project-name'\"")
            raise AssertionError
    return project_id


def set_project_id_env_var(project_id: Optional[str] = None):
    # Set the environment variable, useful for wrapica configurations
    # That do not know about the session files.
    # This should be done at the top of every script that requires the project id
    if project_id is None:
        project_id = get_project_id()
    os.environ["ICAV2_PROJECT_ID"] = project_id


def get_project_id_from_session_file(tenant_name: Optional[str] = None) -> str:
    if tenant_name is not None:
        session_data: OrderedDict = read_tenant_session_file(tenant_name)
    else:
        session_data: OrderedDict = read_session_file()

    project_id: str = session_data.get(ICAV2_SESSION_FILE_PROJECT_ID_KEY, None)

    if project_id is None:
        logger.error("Could not get project id from session file")
        raise KeyError

    return project_id


def get_jwt_token_obj(jwt_token, audience):
    """
    Get the jwt token object through the pyjwt package
    :param jwt_token: The jwt token in base64url format
    :param audience: The Audeince to use for the token, defaults to 'ica'
    :return:
    """
    try:
        token_object = decode(jwt_token,
                              options={
                                         "verify_signature": False,
                                         "require_exp": True
                                       },
                              audience=[audience],
                              algorithms="RS256",
                              )
    except InvalidTokenError:
        raise InvalidTokenError

    return token_object


def check_access_token_expiry(access_token: str) -> bool:
    """
    Check access token hasn't expired
    True if has not expired, otherwise false
    :param access_token:
    :return:
    """
    current_epoch_time = int(datetime.now().strftime("%s"))

    if current_epoch_time < get_jwt_token_obj(access_token, ICAV2_ACCESS_TOKEN_AUDIENCE).get("exp"):
        return True

    # Otherwise
    logger.info("Token has expired")
    return False


def refresh_access_token() -> str:
    """
    Run standard command to get a new token in the session file
    :return:
    """
    project_list_returncode, project_list_stdout, project_list_stderr = \
        run_subprocess_proc(["icav2", "projects", "list"], capture_output=True)

    if not project_list_returncode == 0:
        logger.error("Couldn't run a simple icav2 command to refresh the token")
        raise ChildProcessError

    # Get the newly refreshed token
    return get_access_token_from_session_file(refresh=False)


def get_icav2_base_url(tenant_name: Optional[str] = None):
    """
    Collect the icav2 base url for the configuration
    Likely 'https://ica.illumina.com/ica/rest'
    :return:
    """
    # Check env
    icav2_base_url_env = os.environ.get("ICAV2_BASE_URL", None)
    if icav2_base_url_env is not None:
        return icav2_base_url_env

    # Read config file
    config_yaml_dict = read_config_file(tenant_name=tenant_name)
    if ICAV2_CONFIG_FILE_SERVER_URL_KEY in config_yaml_dict.keys():
        return f"https://{config_yaml_dict[ICAV2_CONFIG_FILE_SERVER_URL_KEY]}/ica/rest"
    else:
        logger.warning("Could not get server-url from config yaml")

    return DEFAULT_ICAV2_BASE_URL


def set_libicav2_configuration():
    # Use the global attribute to set the object from within the function
    global LIBICAV2_CONFIGURATION

    logger.debug("Setting the libicav2 configuration object")

    host = get_icav2_base_url(tenant_name=get_tenant(raise_if_not_found=False))
    access_token = os.environ.get("ICAV2_ACCESS_TOKEN", None)

    if access_token is None or not check_access_token_expiry(access_token):
        access_token = get_access_token_from_session_file()

    LIBICAV2_CONFIGURATION = Configuration(
        host=host,
        access_token=access_token
    )


def get_libicav2_configuration() -> Configuration:
    if LIBICAV2_CONFIGURATION is None:
        set_libicav2_configuration()

    return LIBICAV2_CONFIGURATION


def create_access_token_from_api_key(api_key: str) -> str:
    get_api_key_returncode, get_api_key_stdout, get_api_key_stderr = run_subprocess_proc(
        [
            "curl", "--fail", "--silent", "--location", "--show-error",
            "--url", f"{get_icav2_base_url(tenant_name=get_tenant(raise_if_not_found=False))}/api/tokens",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"X-API-Key: {api_key}",
            "--data", ""
        ],
        capture_output=True
    )

    if not get_api_key_returncode == 0:
        logger.error("Unable to create an api key, error was")
        logger.error(get_api_key_stderr)
        raise ValueError

    return json.loads(get_api_key_stdout).get("token")


def get_project_id_from_project_name_curl(base_url: str, project_name: str, access_token: str) -> str:
    """
    Quick use of curl when the access token is not yet set in the configuration file (tenants init)
    Args:
        access_token:

    Returns:

    """

    list_projects_returncode, list_projects_stdout, list_projects_stderr = run_subprocess_proc(
        [
            "curl", "--fail", "--location", "--silent",
            "--request", "GET",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {access_token}",
            "--url", f"{base_url}/api/projects/"
        ],
        capture_output=True
    )

    if not list_projects_returncode == 0:
        logger.error("Unable to list projects, error was")
        logger.error(list_projects_stderr)
        raise ValueError

    project_list = json.loads(list_projects_stdout).get("items")

    for project in project_list:
        if project.get("name") == project_name:
            return project.get("id")

    logger.error(f"Could not find project '{project_name}'")
    raise ValueError


def get_project_name_from_project_id_curl(base_url, project_id: str, access_token: str) -> str:
    """
    Quick use of curl when the access token is not yet set in the configuration file (tenants init)
    Args:
        access_token:

    Returns:

    """

    get_project_returncode, get_project_stdout, get_project_stderr = run_subprocess_proc(
        [
            "curl", "--fail", "--location", "--silent",
            "--request", "GET",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {access_token}",
            "--url", f"{base_url}/api/projects/{project_id}"
        ],
        capture_output=True
    )

    if not get_project_returncode == 0:
        logger.error("Unable to get projects, error was")
        logger.error(get_project_stderr)
        raise ValueError

    return json.loads(get_project_stdout).get("name")


def get_tenant_id_from_b64_tid(tenant_id):
    # Very confusing way but we need the negative modulo
    num_equals = (4 - len(tenant_id) % 4) % 4

    return b64decode(tenant_id + ("=" * num_equals)).decode().split(":")[-1]


