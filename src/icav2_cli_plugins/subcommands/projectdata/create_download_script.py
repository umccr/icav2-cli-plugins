#!/usr/bin/env python3

"""
Create a download script that creates a suite of presigned urls to be downloaded
encoded into a base64 script
"""

# External imports
import json
import shutil
import os
import stat
from base64 import b64encode
from datetime import datetime, timezone
from pathlib import Path
from re import Pattern
from typing import List, Optional, Match, Union
import re
from tempfile import NamedTemporaryFile
from fileinput import FileInput
import pandas as pd
from humanfriendly import format_size

# Wrapica
from wrapica.enums import DataType
from wrapica.project_data import (
    ProjectData,
    presign_folder,
    find_project_data_bulk
)

# Import utils
from ...utils.config_helpers import get_project_id
from ...utils.datetime_helpers import (
    file_friendly_datetime_format, calculate_presigned_url_expiry
)
from ...utils.encryption_helpers import (
    encrypt_presigned_url_with_public_key, encrypt_presigned_url_with_keybase
)
from ...utils.logger import get_logger
from ...utils.subprocess_handler import run_subprocess_proc
from ...utils.template_helpers import get_templates_dir
from ...utils.errors import InvalidArgumentError

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()

# Expects user to have generated a private/public key pair with
# $ openssl genrsa -out key.pem 4096  # Key generation
# $ openssl rsa -in key.pem -outform PEM -out priv.pem  # Write out private key
# $ openssl rsa -in key.pem -outform PEM -pubout -out public.pem  # Write out public key
# We can encrypt each presigned url with the users public key with the following command
# $ openssl pkeyutl -encrypt -inkey public.pem -keyform PEM -pubin <<< "${presigned_url}" | base64
# The script generated then takes the users private key as input and decrypts with
# openssl pkeyutl -decrypt -inkey priv.pem -keyform PEM <<< "$(base64 -d "${encrypted_presigned_url})"
# For keybase, things are a little easier
# We can encrypt each presigned url with the following command
# keybase encrypt <username> <<< "${presigned_url}" | base64


class CreateDownloadScript(Command):
    """Usage:
    icav2 projectdata create-download-script help
    icav2 projectdata create-download-script <data>
                                             (--name <name_of_script>)
                                             [--output-directory /path/to/output/]
                                             [--public-key <public_key_path> | --keybase-username <keybase_username> | --keybase-team <keybase_team} ]
                                             [--file-regex <regex>]

Description:
    Create a script to download a folder from icav2.
    This will generate a script that contains a list of presigned urls to download from.

    If a public key or keybase username is specified, the presigned urls will be encrypted.


Options:
    <data>                                             Required, path to icav2 data folder you wish to download from,
                                                       May also specify a folder id or an icav2 uri

    --name <name>                                      Descriptor of the data being downloaded

    --output-directory </path/to/output/dir/>          Directory to place the output file ($PWD by default)

    --public-key </path/to/output/key.pem>             Path to a public key (PEM) used to encrypt the data via
                                                       openssl pkeyutl -encrypt -keyform PEM -inkey /path/to/public-key
    --keybase-username <your-username>                 Collects the public key for a keybase user to encrypt data
    --keybase-team <your-team>                         Collects the public key for a keybase team to encrypt data

    --file-regex <regex>                               Only add files to the download script that match a regex

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Required, taken from "$HOME/.icav2/.session.ica.yaml" if not set


Extras:
    If --keybase-username or --keybase-team is specified, user MUST have keybase cli installed.
    If --public-key is specified, openssl must be installed.

Examples: icav2 projectdata create-download-script /test_data/outputs/
    icav2 projectdata create-download-script /test_data/outputs/ --name test-data-outputs --keybase-username alexiswl --file-regex '*.bam'
    """

    project_data_obj: Optional[ProjectData]
    name: Optional[str]
    output_directory: Optional[Path]
    public_key: Optional[Path]
    keybase_username: Optional[str]
    keybase_team: Optional[str]
    file_regex: Optional[Union[str, Pattern]]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "project_data_obj": DocOptArg(
                cli_arg_keys=["data"]
            ),
            "name": DocOptArg(
                cli_arg_keys=["name"]
            ),
            "output_directory": DocOptArg(
                cli_arg_keys=["--output-directory"]
            ),
            "public_key": DocOptArg(
                cli_arg_keys=["--public-key"]
            ),
            "keybase_username": DocOptArg(
                cli_arg_keys=["--keybase-username"]
            ),
            "keybase_team": DocOptArg(
                cli_arg_keys=["--keybase-team"]
            ),
            "file_regex": DocOptArg(
                cli_arg_keys=["--file-regex"]
            )
        }

        # Additional attributes
        self.project_id: Optional[str] = None
        self.data_path: Optional[Path] = None
        self.current_timestamp: Optional[datetime] = None
        self.output_file_path = None
        self.is_encrypted: Optional[bool] = None
        self.is_keybase: Optional[bool] = None
        self.is_keybase_team: Optional[bool] = None
        self.keybase_name: Optional[str] = None
        self.data_list: Optional[List[ProjectData]] = None
        self.jq_array: Optional[List[str]] = None
        self.total_diskspace: Optional[int] = None

        super().__init__(command_argv)

    def check_args(self):
        # Check arguments

        # Get project id
        self.project_id = get_project_id()

        # Check data is a folder
        if self.project_data_obj is not None:
            if not DataType(self.project_data_obj.data.details.data_type) == DataType.FOLDER:
                logger.error(f"Data '{self.project_data_obj.data.details.path}' is not a folder")
                raise ValueError

            # Set data path
            self.data_path = Path(self.project_data_obj.data.details.path)
        else:
            logger.error(
                "Cannot set data parameter to '/' directory, we cannot get AWS sync credentials from the top directory")
            raise InvalidArgumentError

        # Check --name matches file friendly regex
        if re.fullmatch(r"[\w.\-_]+", self.name) is None:
            logger.error("Please ensure --name argument contains only the characters 'A-Za-z0-9.-_'")
            raise InvalidArgumentError

        # Get output directory
        if self.output_directory is None:
            self.output_directory = Path(os.getcwd())
        elif not self.output_directory.is_dir():
            logger.error(f"--output-directory specified as '{self.output_directory}' but directory does not exist")
            raise InvalidArgumentError

        # Get date
        self.current_timestamp = datetime.now(timezone.utc)

        # Set output file path
        self.output_file_path = Path(self.output_directory) / f"icav2-download-script-{self.name}-{file_friendly_datetime_format(self.current_timestamp)}.sh"

        # Check if encrypted
        if len(
            list(
                filter(
                    lambda x: x is not None,
                    [self.public_key, self.keybase_username, self.keybase_team]
                )
            )
        ) > 1:
            logger.error("Please specify no more than one of --public-key, --keybase-username or --keybase-team")
            raise InvalidArgumentError
        if self.public_key is not None:
            if not self.public_key.is_file():
                logger.error(f"--public-key value specified as '{self.public_key}' but file does not exist")
                raise InvalidArgumentError
            self.is_encrypted = True
        if self.keybase_username is not None:
            self.is_keybase = True
            self.is_keybase_team = False
            self.keybase_name = self.keybase_username
            self.is_encrypted = True
        if self.keybase_team is not None:
            self.is_keybase = True
            self.is_keybase_team = True
            self.keybase_name = self.keybase_team
            self.is_encrypted = True

        # check keybase cli is set if --keybase-* is set
        if self.is_keybase:
            returncode, _, _ = run_subprocess_proc(
                ["which", "keybase"],
                capture_output=True
            )

            if not returncode == 0:
                logger.error(
                    "Cannot find keybase binary but --keybase-username or --keybase-team was selected"
                )
                raise InvalidArgumentError

        # Get the file regex
        self.file_regex = re.compile(self.file_regex)

    def __call__(self):
        # Find all files in data_path and collect presigned urls and map to paths
        self.data_list = find_project_data_bulk(
            project_id=self.project_id,
            parent_folder_path=self.data_path,
            data_type=DataType.FILE
        )

        # Check data list is non-empty
        if len(self.data_list) == 0:
            logger.error(f"No files to presign in directory '{self.data_path}'")
            raise FileNotFoundError

        # Update data list if file regex is not None
        if self.file_regex is not None:
            self.data_list = list(
                filter(
                    lambda x: self.file_regex.match(x.name),
                    self.data_list
                )
            )

        # Check data list is non-empty
        if len(self.data_list) == 0:
            logger.error(
                f"No files to presign in directory '{self.data_path}' "
                f"after using file regex '{self.file_regex}'"
            )
            raise FileNotFoundError

        # Bulk presign the directory
        presigned_directory_df = pd.DataFrame(
            presign_folder(
                project_id=self.project_id,
                folder_path=self.data_path
            )
        )

        presigned_directory_df["etag"] = presigned_directory_df.apply(
            lambda row: next(
                map(
                    lambda filtered_data_item: filtered_data_item.data.details.object_e_tag,
                    filter(
                        lambda data_item: str(Path(data_item.data.details.path).relative_to(self.data_path)) == row.path,
                        self.data_list
                    )
                )
            ),
            axis="columns"
        )

        presigned_directory_df["file_size"] = presigned_directory_df.apply(
            lambda row: next(
                map(
                    lambda filtered_data_item: filtered_data_item.data.details.file_size_in_bytes,
                    filter(
                        lambda data_item: str(Path(data_item.data.details.path).relative_to(self.data_path)) == row.path,
                        self.data_list
                    )
                )
            ),
            axis="columns"
        )

        if self.is_encrypted:
            if self.public_key is not None:
                presigned_directory_df["presigned_url"] = presigned_directory_df["presigned_url"].apply(
                    lambda x: encrypt_presigned_url_with_public_key(
                        x, self.public_key
                    )
                )
            else:
                presigned_directory_df["presigned_url"] = presigned_directory_df["presigned_url"].apply(
                    lambda x: encrypt_presigned_url_with_keybase(
                        x,
                        keybase_name=self.keybase_name,
                        is_keybase_team=self.is_keybase_team
                    )
                )

        self.total_diskspace = presigned_directory_df["file_size"].sum()

        # For each item in the data list collect a presigned url
        self.jq_array: List[str] = list(
            map(
                lambda row: f"    \"{str(b64encode(json.dumps(row, separators=(',', ':')).encode()).decode())}\" \\\n",
                json.loads(
                    presigned_directory_df[["presigned_url", "path", "etag", "file_size"]].to_json(orient='records')
                )
            )
        )

        # Copy template and substitute values in template via FileInput
        input_template_obj = NamedTemporaryFile(prefix="icav2-download-script-template")

        # write output file as icav2-download-script-<name>-<date>.sh
        shutil.copy2(get_templates_dir() / "create-download-script.sh", input_template_obj.name)

        # Update template
        self.find_replace_values_in_template(Path(input_template_obj.name))

        # Copy over template
        shutil.copy2(input_template_obj.name, self.output_file_path)

        # Convert to executable
        output_file_stat = os.stat(self.output_file_path)
        os.chmod(self.output_file_path, output_file_stat.st_mode | stat.S_IEXEC)

        logger.info(
            f"Created download script at {self.output_file_path}"
        )

    def find_replace_values_in_template(self, file_path: Path):
        """
        The following values need to be replaced
        __IS_ENCRYPTED__ <boolean true if one of --public-key-, keybase-user, or keybase-team is specified> otherwise false
        __KEYBASE_USERNAME__  <--keybase-username or --keybase-team> otherwise 'null'
        __NAME__ with <--name> parameter
        __DATE__ with <%YYYY-%mm-%dd-%HH%MM%SS%>
        __EXPIRY_DATE__ <%YYYY-MM-DD-HHMMSS%>
        __EXPIRY_DATE_EPOCH__ <Int epoch time>
        __REQUIRED_DISK_SPACE__ <sum bytes of all files)
        __PRESIGNED_URL_BASE64_ARRAY_JQ_LIST__ <array of presigned url base64 dicts>
        :return:
        """

        match_keys = {
            "IS_ENCRYPTED": str(self.is_encrypted).lower(),
            "KEYBASE_USERNAME": self.keybase_name,
            "NAME": self.name,
            "DATE": file_friendly_datetime_format(self.current_timestamp),
            "EXPIRY_DATE": file_friendly_datetime_format(calculate_presigned_url_expiry(self.current_timestamp)),
            "EXPIRY_DATE_EPOCH": calculate_presigned_url_expiry(self.current_timestamp).strftime('%s'),
            "REQUIRED_DISK_SPACE": format_size(self.total_diskspace, binary=True),
            "PRESIGNED_URL_BASE64_ARRAY_JQ_LIST": "".join(self.jq_array)
        }

        match_placeholder = re.compile(r"(<__([\w_]+)__>)")

        with FileInput(file_path, inplace=True) as _input:
            for line in _input:
                line_strip = line.rstrip()
                line_matches: Optional[List[Match]] = match_placeholder.findall(line_strip)
                if len(line_matches) == 0:
                    print(line_strip)
                    continue

                for line_match in line_matches:
                    line_strip = line_strip.replace(
                        str(line_match[0]),
                        str(match_keys[line_match[1]])
                    )
                print(line_strip)
