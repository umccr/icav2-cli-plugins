#!/usr/bin/env python3

"""
Configuration helpers

From collecting configuration from ~/.session.ica.yaml through ruamel to creating configuration object for libicav2
"""
import os
from collections import OrderedDict

from libica.openapi.v2.api.project_api import ProjectApi

from ruamel.yaml import YAML
from pathlib import Path

from datetime import datetime

from jwt import decode, InvalidTokenError

from utils.globals import ICAV2_SESSION_FILE_PATH, ICAV2_ACCESS_TOKEN_AUDIENCE, \
    DEFAULT_ICAV2_BASE_URL, ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY, ICAV2_SESSION_FILE_PROJECT_ID_KEY
from utils.logger import get_logger
from libica.openapi.v2 import Configuration, ApiClient, ApiException
from typing import Optional, List

from utils.subprocess_handler import run_subprocess_proc

logger = get_logger()

LIBICAV2_CONFIGURATION: Optional[Configuration] = None


def get_session_file_path() -> Path:
    """
    Get path for session file and assert file exists
    :return:
    """
    session_file_path: Path = Path(ICAV2_SESSION_FILE_PATH.format(
        HOME=os.environ["HOME"]
    ))

    if not session_file_path.is_file():
        logger.error(f"Could not get file path {session_file_path}")
        raise FileNotFoundError

    return session_file_path


def read_session_file() -> OrderedDict:
    """
    Get the contents of the session file (~/.icav2/.session.ica.yaml)
    :return:
    """

    logger.debug("Reading in the session file")
    yaml = YAML()

    with open(get_session_file_path(), "r") as file_h:
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
        else:
            access_token = refresh_access_token()

    return access_token


def get_project_id(raise_if_not_found: bool = True) -> Optional[str]:
    project_id = os.environ.get("ICAV2_PROJECT_ID")
    if project_id is None:
        logger.debug("Env var ICAV2_PROJECT_ID was empty, getting project id from session file")
        try:
            project_id = get_project_id_from_session_file()
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


def get_project_id_from_session_file() -> str:
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
    :param access_token:
    :return:
    """
    current_epoch_time = int(datetime.now().strftime("%s"))

    if get_jwt_token_obj(access_token, ICAV2_ACCESS_TOKEN_AUDIENCE).get("exp") < current_epoch_time:
        logger.debug("Token has expired")
        return False
    return True


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


def set_libicav2_configuration():
    # Use the global attribute to set the object from within the function
    global LIBICAV2_CONFIGURATION

    logger.debug("Setting the libicav2 configuration object")

    host = os.environ.get("ICAV2_BASE_URL", DEFAULT_ICAV2_BASE_URL)
    access_token = os.environ.get("ICAV2_ACCESS_TOKEN", None)

    if access_token is None or check_access_token_expiry(access_token):
        access_token = get_access_token_from_session_file()

    LIBICAV2_CONFIGURATION = Configuration(
        host=host,
        access_token=access_token
    )


def get_libicav2_configuration() -> Configuration:
    if LIBICAV2_CONFIGURATION is None:
        set_libicav2_configuration()

    return LIBICAV2_CONFIGURATION


def get_project_id_from_project_name(project_name: str) -> str:
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectApi(api_client)
        include_hidden_projects = True  # bool, none_type | Include hidden projects. (optional) if omitted the server will use the default value of False
        # Dont expect over 1000 projects tbh
        page_size = 1000  # str | The amount of rows to return. Use in combination with the offset or cursor parameter to get subsequent results. (optional)

        # example passing only required values which don't have defaults set
        # and optional values
        try:
            # Retrieve a list of projects.
            api_response = api_instance.get_projects(
                search=project_name,
                include_hidden_projects=include_hidden_projects,
                page_size=str(page_size)
            )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectApi->get_projects: %s\n" % e)

    project_list: List = api_response.items
    project_list = list(filter(lambda x: x.name == project_name, project_list))

    if len(project_list) == 0:
        raise ValueError(f"Could not find project '{project_name}'")
    elif len(project_list) == 1:
        return project_list[0].id
    else:
        raise ValueError(f"Got multiple IDs for project name {project_name}")
