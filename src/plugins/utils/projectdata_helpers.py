#!/usr/bin/env python

"""
List of useful functions for cli helpers in ICAv2

* list_data_non_recursively()
* find_data()
* get_file_download_url()
"""
import os
import re
from subprocess import SubprocessError
from typing import List, Optional, Dict
import json
from pathlib import Path
import math
from urllib.parse import urlparse

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.model.create_temporary_credentials import CreateTemporaryCredentials
from libica.openapi.v2.model.temp_credentials import TempCredentials
from libica.openapi.v2.model.create_data import CreateData
from libica.openapi.v2.model.project_data import ProjectData
from libica.openapi.v2.api.project_data_api import ProjectDataApi
from utils import is_uuid_format

from utils.config_helpers import get_libicav2_configuration, get_project_id_from_project_name
from utils.globals import LIBICAV2_DEFAULT_PAGE_SIZE
from utils.logger import get_logger
from utils.subprocess_handler import run_subprocess_proc

from utils.user_helpers import get_user_from_user_id

logger = get_logger()


def get_data_obj_from_project_id_and_path(project_id: str, data_path: str) -> ProjectData:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    file_path = [
        data_path,
    ]  # [str] | The paths of the files to filter on. (optional)
    file_path_match_mode = "FULL_CASE_INSENSITIVE"  # str | How the file paths are filtered:   - STARTS_WITH_CASE_INSENSITIVE: Filters the file path to start with the value of the 'filePath' parameter, regardless of upper/lower casing. This allows e.g. listing all data in a folder and all it's sub-folders (recursively).  - FULL_CASE_INSENSITIVE: Filters the file path to fully match the value of the 'filePath' parameter, regardless of upper/lower casing. Note that this can result in multiple results if e.g. two files exist with the same filename but different casing (abc.txt and ABC.txt). (optional) if omitted the server will use the default value of "STARTS_WITH_CASE_INSENSITIVE"
    data_type = "FOLDER" if data_path.endswith("/") else "FILE"
    parent_folder_path = str(Path(data_path).parent) + "/"
    page_size = 1000  # str | The amount of rows to return. Use in combination with the offset or cursor parameter to get subsequent results. (optional)

    # Make sure parent folder path is not '//'
    if parent_folder_path == "//":
        parent_folder_path = "/"

    # example passing only required values which don't have defaults set
    try:
        # Retrieve the list of project data.
        api_response = api_instance.get_project_data_list(
            project_id,
            file_path=file_path,
            file_path_match_mode=file_path_match_mode,
            type=data_type,
            parent_folder_path=parent_folder_path,
            page_size=str(page_size)
        )
    except ApiException as e:
        raise ValueError("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)

    project_data_list = api_response.items
    if len(project_data_list) == 0:
        raise FileNotFoundError(f"Could not find the file/directory {data_path} in project {project_id}")
    elif len(project_data_list) == 1:
        return project_data_list[0]
    else:
        raise FileNotFoundError(f"Found multiple results for {data_path} in project {project_id}")


def bulk_presign_directory(project_id: str, folder_path: str, folder_id: str) -> List[Dict]:
    """
    Given a folder ID, return a relative path and presigned URL for every file in the directory
    :param folder_path: /path/to/directory (used to create relative paths to the directory)
    :param folder_id: fol.123456
    :return: [
        {
          "path": "subdirectory/filename.txt",
          "presigned_url": "https://..."
        },
        {
        }
    ]
    """
    import pandas as pd

    # Folder df map
    data_ids_df = pd.DataFrame(
        map(
            lambda x: {
                "data_type": x.data.details.data_type,
                "data_id": x.data.id,
                "path": x.data.details.path
            },
            find_data_recursively(
                project_id=project_id,
                parent_folder_path=folder_path,
                data_type="FILE",
                name=".*"
            )
        )
    )

    # Get list of data ids
    data_ids = data_ids_df["data_id"]

    # Get configuration
    configuration = get_libicav2_configuration()

    # Launch get ids
    returncode, stdout, stderr = run_subprocess_proc(
        [
            "curl", "--fail", "--silent", "--location", "--show-error",
            "--request", "POST",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
            "--header", "Content-Type: application/vnd.illumina.v3+json",
            "--data", str(json.dumps({"dataIds": data_ids.tolist()})),
            "--url", f"{configuration.host}/api/projects/{project_id}/data:createDownloadUrls"
        ],
        capture_output=True
    )
    if not returncode == 0:
        logger.error(f"Could not get list of presigned urls for data path {folder_path}")
        logger.error(f"Stderr was:{stderr}")
        raise ChildProcessError

    # Stdout items is a list of dicts with the following attributes
    # dataId
    # urn
    # url
    # So need to remap path from data Id

    # Map IDs to paths to get presigned urls
    paths_urls_df = pd.merge(
        data_ids_df,
        pd.DataFrame(
            json.loads(stdout).get("items")
        ),
        left_on="data_id",
        right_on="dataId"
    ).rename(
        columns={"url": "presigned_url"},
    )[["path", "data_id", "presigned_url"]]

    # Get path as a relative path to the input folder path
    paths_urls_df["path"] = paths_urls_df["path"].apply(lambda x: str(Path(x).relative_to(folder_path)))

    return paths_urls_df


def list_data_non_recursively(project_id: str, parent_folder_id: Optional[str] = None, parent_folder_path: Optional[str] = None, sort: Optional[str] = "") -> List[ProjectData]:
    """
    List data non recursively
    :return:
    """
    # Check one of parent_folder_id and parent_folder_path is specified
    if parent_folder_id is None and parent_folder_path is None:
        logger.error("Must specify one of parent_folder_id and parent_folder_path")
        raise AssertionError
    elif parent_folder_id is not None and parent_folder_path is not None:
        logger.error("Must specify only one of parent_folder_id and parent_folder_path")
        raise AssertionError

    parent_folder_ids = [parent_folder_id] if parent_folder_id is not None else []

    # Collect api instance
    with ApiClient(get_libicav2_configuration()) as api_client:
        api_instance = ProjectDataApi(api_client)

    # Set other parameters
    page_size = LIBICAV2_DEFAULT_PAGE_SIZE
    page_offset = 0

    # Initialise data ids - we may need to extend the items multiple times
    data_ids: List[ProjectData] = []

    while True:
        # Attempt to collect all data ids
        try:
            # Retrieve the list of project data
            api_response = api_instance.get_project_data_list(
                project_id=project_id,
                parent_folder_id=parent_folder_ids,
                parent_folder_path=parent_folder_path,
                page_size=str(page_size),
                page_offset=str(page_offset),
                sort=sort
            )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)

        # Extend items list
        data_ids.extend(api_response.items)

        # Check page offset and page size against total item count
        if page_offset + page_size > api_response.total_item_count:
            break
        page_offset += page_size

    return data_ids


def check_is_directory(project_id: str, folder_path: str) -> bool:
    """
    Check folder path is a directory
    :param project_id:
    :param folder_path:
    :return:
    """
    if not folder_path.endswith("/"):
        logger.error(f"Folder {folder_path} must end with '/'")
        raise ValueError
    try:
        # Try to get data object from project id and path
        get_data_obj_from_project_id_and_path(project_id, folder_path)
    except (ValueError, FileNotFoundError):
        return False
    else:
        return True


def check_is_file(project_id: str, file_path: str) -> bool:
    if file_path.endswith("/"):
        logger.error(f"File path {file_path} must not end with '/'")
        raise ValueError
    try:
        # Try to get data object from project id and path
        get_data_obj_from_project_id_and_path(project_id, file_path)
    except (ValueError, FileNotFoundError):
        return False
    else:
        return True


def find_data_recursively(project_id: str,
                          parent_folder_id: Optional[str] = None, parent_folder_path: Optional[str] = None,
                          name: Optional[str] = "", data_type: Optional[str] = None,
                          mindepth: Optional[int] = None, maxdepth: Optional[int] = None) -> List[ProjectData]:
    """
    Run a find on a data name
    :return:
    """
    # Matched data items thing we return
    matched_data_items: List[ProjectData] = []

    # Get top level items
    data_items: List[ProjectData] = list_data_non_recursively(project_id, parent_folder_path=parent_folder_path)

    # Check if we can pull out any items in the top directory
    if mindepth is None or mindepth <= 0:
        name_regex_obj = re.compile(name)
        for data_item in data_items:
            data_item_match = name_regex_obj.match(data_item.data.details.name)
            if data_type is not None and not data_item.data.details.data_type == data_type:
                continue
            if data_item_match is not None:
                matched_data_items.append(data_item)

    # Otherwise look recursively
    if maxdepth is None or not maxdepth <= 0:
        # Listing subfolders
        subfolders = filter(
            lambda x: x.data.details.data_type == "FOLDER",
            data_items
        )
        for subfolder in subfolders:
            matched_data_items.extend(
                find_data_recursively(
                    project_id=project_id,
                    parent_folder_id=subfolder.data.id,
                    parent_folder_path=subfolder.data.details.path,
                    name=name,
                    data_type=data_type,
                    mindepth=mindepth-1 if mindepth is not None else None,
                    maxdepth=maxdepth-1 if maxdepth is not None else None
                )
            )

    return matched_data_items


def create_data_download_url(project_id: str, data_id: str) -> str:
    """
    Create a data download url for a file item
    :param project_id:
    :param data_id:
    :return:
    """

    # Get configuration
    configuration = get_libicav2_configuration()

    # Use curl command for this POST request
    curl_command_list = [
        "curl",
        "--fail", "--silent", "--location",
        "--request", "POST",
        "--url", f"{configuration.host}/api/projects/{project_id}/data/{data_id}:createDownloadUrl",
        "--header", "Accept: application/vnd.illumina.v3+json",
        "--header", f"Authorization: Bearer {configuration.access_token}",
        "--data", ""
    ]

    # Run the curl command through subprocess.run
    curl_download_returncode, curl_download_stdout, curl_download_stderr = \
        run_subprocess_proc(curl_command_list, capture_output=True)

    if not curl_download_returncode == 0:
        logger.error(f"Could not create a download url for project id '{project_id}', data id '{data_id}'")
        raise ValueError

    return json.loads(curl_download_stdout).get("url")


def get_aws_credentials_access(project_id: str, data_id: str) -> Dict:
    """
    Get AWS credentials access
    :param project_id:
    :param data_id:
    :return:
    """

    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    create_temporary_credentials = CreateTemporaryCredentials()

    # example passing only required values which don't have defaults set
    try:
        # Retrieve temporary credentials for this data.
        api_response: TempCredentials = api_instance.create_temporary_credentials_for_data(
            project_id, data_id, create_temporary_credentials=create_temporary_credentials
        )
    except ApiException as e:
        logger.warning("Exception when calling ProjectDataApi->create_temporary_credentials_for_data: %s\n" % e)
        raise ValueError

    return api_response.aws_temp_credentials


def create_data_in_project(project_id: str, data_path: str) -> ProjectData:
    """
    Create data in project
    :param project_id:
    :param data_path:
    :return:
    """

    # Get data path
    if data_path.endswith("/"):
        data_type = "FOLDER"
    else:
        data_type = "FILE"

    # Get other attributes
    name = Path(data_path).name
    folder_path = str(Path(data_path).parent) + "/"

    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

    try:
        api_response: ProjectData = api_instance.create_data_in_project(
            project_id=project_id,
            create_data=CreateData(
                name=name,
                folder_path=folder_path,
                data_type=data_type
            )
        )
    except ApiException as e:
        logger.error("Exception when calling ProjectDataApi->create_data_in_project: %s\n" % e)
        raise ValueError

    return api_response


def list_files_short(data_items: List[ProjectData]) -> None:
    """
    List all the files and folders in the directory
    :return:
    """

    # Iterate through each item and print
    for data_item in data_items:
        print(data_item.data.details.path)


def list_files_long(data_items: List[ProjectData]):
    """
    Use pandas to list
    :param data_items:
    :return:
    """

    # Import pandas
    # (this takes a few seconds which is why we don't do it at the top)
    import pandas as pd
    from tabulate import tabulate

    # Read in data items as a data frame
    data_items_df = pd.DataFrame(
        [
            {
                "id": data_item.data.id,
                "path": data_item.data.details.path,
                "owning_project_id": data_item.data.details.owning_project_id,
                "owning_project_name": data_item.data.details.owning_project_name,
                "creator_id": data_item.data.details.get("creator_id", None),
                "modification_time_stamp": data_item.data.details.time_modified,
                "size_kb": round(float(data_item.data.details.get("file_size_in_bytes", 0)) / math.pow(2, 10), 2)
            }
            for data_item in data_items
        ]
    )

    # Get users
    creator_ids = list(data_items_df["creator_id"].unique())
    creator_dict = {
        None: ""
    }

    # Iterate through unique creator ids and collect names
    for creator_id in creator_ids:
        if creator_id is None:
            continue
        # Get user from user ids
        user = get_user_from_user_id(creator_id)
        # Set value as firstname ' ' lastname
        creator_dict[user.id] = f"{user.firstname} {user.lastname}"

    data_items_df["creator_user"] = data_items_df["creator_id"].apply(
        lambda x: creator_dict.get(x, None)
    )

    data_items_df_formatted = data_items_df[[
        "size_kb",
        "creator_id",
        "creator_user",
        "modification_time_stamp",
        "owning_project_name",
        "path"
    ]]

    print(
        f"total {data_items_df['size_kb'].sum()} Kb"
    )
    print(
        tabulate(data_items_df_formatted, headers=data_items_df_formatted.columns, showindex=False)
    )


def write_url_contents_to_stdout(download_url: str):
    """
    Stream outputs to stdout
    :param download_url:
    :return:
    """
    run_subprocess_proc(
        [
            "wget",
            "--quiet",
            "--output-document", "/dev/stdout",
            download_url
        ],
        bufsize=0
    )


def view_in_browser(download_url):
    """
    Run browser, downloadurl
    :param download_url:
    :return:
    """
    browser_returncode, browser_stdout, browser_stderr = run_subprocess_proc(
        [
            os.environ["BROWSER"],
            download_url
        ],
        capture_output=True
    )

    if not browser_returncode == 0:
        logger.error("Could not open file in browser")
        logger.error(f"Stdout was '{browser_stdout}'")
        logger.error(f"Stderr was '{browser_stderr}'")
        raise SubprocessError


def run_s3_sync_command(aws_env_vars: Dict, aws_s3_sync_args: List,
                        aws_s3_path: str,
                        upload: Optional[bool] = False, download: Optional[bool] = True,
                        upload_path: Optional[Path] = None, download_path: Optional[Path] = None
                        ) -> bool:
    """
    Run the aws s3 command through the subprocess tool
    :param aws_env_vars:
    :param aws_s3_sync_args:
    :param aws_s3_path:
    :param upload:
    :param download:
    :param upload_path:
    :param download_path:
    :return:
    """

    if not upload and not download:
        logger.error("Something has gone wrong here, please specify one (and only one) of upload or download")
        raise ValueError
    if upload and download:
        logger.error("Something has gone wrong here, please specify one (and only one) of upload or download")
        raise ValueError

    if upload and not upload_path:
        logger.error("Must specify upload path parameter when upload is true")
        raise ValueError
    if download and not download_path:
        logger.error("Must specify download path parameter when download is true")
        raise ValueError

    aws_s3_command: List = ["aws", "s3", "sync"]

    # Are we uploading or downloading
    # (changes the order of the positional parameters)
    if upload:
        aws_s3_command.extend(
            [str(upload_path) + "/", aws_s3_path]
        )
    else:
        aws_s3_command.extend(
            [aws_s3_path, str(download_path) + "/"]
        )

    # Extend with aws s3 sync args
    aws_s3_command.extend(
        aws_s3_sync_args
    )

    aws_s3_command = list(map(str, aws_s3_command))

    logger.debug(
        f"Running aws s3 sync command as '{' '.join(aws_s3_command)}'"
    )

    new_env = os.environ.copy()

    new_env.update(
        {
            "AWS_ACCESS_KEY_ID": aws_env_vars.get("access_key"),
            "AWS_SECRET_ACCESS_KEY": aws_env_vars.get("secret_key"),
            "AWS_SESSION_TOKEN": aws_env_vars.get("session_token"),
            "AWS_REGION": aws_env_vars.get("region")
        }
    )

    aws_s3_sync_command_returncode, _, _ = run_subprocess_proc(
        aws_s3_command,
        env=new_env
    )

    if not aws_s3_sync_command_returncode == 0:
        logger.error("aws s3 sync command returned non-zero exit code. "
                     "Please run with the --verbose aws s3 sync option to investigate further")
        return False

    return True


def get_s3_sync_script(aws_env_vars: Dict, aws_s3_sync_args: List,
                       aws_s3_path: str,
                       upload: Optional[bool] = False, download: Optional[bool] = False,
                       upload_path: Optional[Path] = None, download_path: Optional[Path] = None) -> str:
    """
    Create a s3 sync script
    :param aws_env_vars:
        Contains access tokens in dict
    :param aws_s3_sync_args:
        Contains s3 sync args in list
    :param aws_s3_path:
        The AWS S3 path
    :param upload:
        Are we uploading to icav2?
    :param upload_path:
    :param download:
        Are we download to icav2?
    :param download_path:
    :return:
    """

    if not upload and not download:
        logger.error("Something has gone wrong here, please specify one (and only one) of upload or download")
        raise ValueError
    if upload and download:
        logger.error("Something has gone wrong here, please specify one (and only one) of upload or download")
        raise ValueError

    if upload and not upload_path:
        logger.error("Must specify upload path parameter when upload is true")
        raise ValueError
    if download and not download_path:
        logger.error("Must specify download path parameter when download is true")
        raise ValueError

    # Get first lines
    initial_template = f"""
#!/usr/bin/env bash

# Fail if aws s3 sync command fails 
set -e

AWS_ACCESS_KEY_ID={aws_env_vars.get("access_key")} \\
AWS_SECRET_ACCESS_KEY={aws_env_vars.get("secret_key")} \\
AWS_SESSION_TOKEN={aws_env_vars.get("session_token")} \\
AWS_REGION={aws_env_vars.get("region")} \\
    """

    # Get next lines
    if upload:
        aws_cli_line = f"aws s3 sync {upload_path} {aws_s3_path}"
    else:  # Download is true
        aws_cli_line = f"aws s3 sync {aws_s3_path} {download_path}"

    # Get s3 sync args if they exist
    if len(aws_s3_sync_args) > 0:
        aws_cli_line += " \\\n"

    for index, aws_s3_sync_arg in enumerate(aws_s3_sync_args):
        aws_cli_line += f"  {aws_s3_sync_arg} "
        if not index == len(aws_s3_sync_args) - 1:
            # Add \ to signify more arguments to come
            aws_cli_line += " \\\n"

    # Add final line
    aws_cli_line += "\n"

    return initial_template + aws_cli_line


def convert_icav2_uri_to_data_obj(uri: str) -> ProjectData:
    # Parse obj
    uri_obj = urlparse(uri)

    # Get project name or id
    project_name_or_id = uri_obj.netloc

    # Get data path
    data_path = uri_obj.path

    # Get project id
    if is_uuid_format(project_name_or_id):
        project_id = project_name_or_id
    else:
        project_id = get_project_id_from_project_name(project_name_or_id)

    # Get data path
    return get_data_obj_from_project_id_and_path(project_id, data_path)
