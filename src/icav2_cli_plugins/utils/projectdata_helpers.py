#!/usr/bin/env python

"""
List of useful functions for cli helpers in ICAv2

* list_data_non_recursively()
* find_data()
* get_file_download_url()
"""

# External imports
import os
from subprocess import SubprocessError
from typing import List, Optional, Dict
from pathlib import Path
import math

# Wrapica imports
from wrapica.project_data import ProjectData
from wrapica.user import get_user_obj_from_user_id

# Local imports
from .logger import get_logger
from .subprocess_handler import run_subprocess_proc


# Set logger
logger = get_logger()


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
        user = get_user_obj_from_user_id(creator_id)
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


def run_s3_sync_command(
        aws_env_vars: Dict,
        aws_s3_sync_args: Optional[List[str]],
        aws_s3_path: str,
        upload: Optional[bool] = False,
        download: Optional[bool] = True,
        upload_path: Optional[Path] = None,
        download_path: Optional[Path] = None
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

    aws_s3_command: List[str] = ["aws", "s3", "sync"]

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
    if aws_s3_sync_args is not None:
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



