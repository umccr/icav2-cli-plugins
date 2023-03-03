#!/usr/bin/env python3

"""
Create a download script that creates a suite of presigned urls to be downloaded
encoded into a base64 script
"""
import json
import shutil

from argparse import ArgumentError
import os
import stat
from base64 import b64encode
from datetime import datetime
from pathlib import Path
from re import Pattern
from typing import List, Optional, Match
import re
from tempfile import NamedTemporaryFile
from fileinput import FileInput

import pandas as pd

from humanfriendly import format_size

from libica.openapi.v2.model.project_data import ProjectData

from utils.config_helpers import get_project_id
from utils.datetime_helpers import file_friendly_datetime_format, calculate_presigned_url_expiry
from utils.encryption_helpers import encrypt_presigned_url_with_public_key, encrypt_presigned_url_with_keybase
from utils.logger import get_logger

from subcommands import Command
from utils.projectdata_helpers import check_is_directory, find_data_recursively, bulk_presign_directory, \
    get_data_obj_from_project_id_and_path
from utils.subprocess_handler import run_subprocess_proc
from utils.template_helpers import get_templates_dir

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
    icav2 projectdata create-download-script <data_path>
                                             (--name <name_of_script>)
                                             [--output-directory /path/to/output/]
                                             [--public-key <public_key_path> | --keybase-username <keybase_username> | --keybase-team <keybase_team} ]
                                             [--file-regex <regex>]

Description:
    Create a script to download a folder from icav2.
    This will generate a script that contains a list of presigned urls to download from.

    If a public key or keybase username is specified, the presigned urls will be encrypted.


Options:
    <data_path>                                        Required, path to icav2 data folder you wish to download from

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
    If --keybase-username or --keybase-team is specified, one MUST have keybase cli installed.
    If --public-key is specified, openssl must be installed.

Examples: icav2 projectdata create-download-script /test_data/outputs/
    icav2 projectdata create-download-script /test_data/outputs/ --name test-data-outputs --keybase-username alexiswl --file-regex '*.bam'
    """

    def __init__(self, command_argv):
        # Get the command args
        self.project_id: Optional[str] = None

        self.data_path: Optional[Path] = None
        self.data_id: Optional[ProjectData] = None

        self.name: Optional[str] = None

        self.date: Optional[datetime] = None

        self.output_file_path = None

        self.is_encrypted: Optional[bool] = None

        self.is_keybase: Optional[bool] = None
        self.is_keybase_team: Optional[bool] = None
        self.keybase_name: Optional[str] = None
        self.public_key: Optional[Path] = None

        self.file_regex: Optional[Pattern] = None

        self.data_list: Optional[List[ProjectData]] = None

        self.jq_array: Optional[List[str]] = None

        self.total_diskspace: Optional[int] = None

        super().__init__(command_argv)

    def check_args(self):
        # Steps
        # Get project id
        self.project_id = get_project_id()

        # Check data path arg
        data_path_arg = self.args.get("<data_path>", None)
        if data_path_arg is None:
            logger.error("Could not get arg for <data_path>")
            raise ArgumentError
        self.data_path = Path(data_path_arg)

        # check data_path is real and accessible in project id
        if not check_is_directory(self.project_id, str(self.data_path) + "/"):
            logger.error(f"Could not find data path {self.data_path} in project '{self.project_id}'")
            raise ArgumentError

        self.data_id = get_data_obj_from_project_id_and_path(
            project_id=self.project_id,
            data_path=str(self.data_path) + "/"
        )

        # Get name
        name_arg = self.args.get("--name", None)
        if name_arg is None:
            logger.error("Could not get arg for --name")
            raise ArgumentError
        # Check --name matches file friendly regex
        if re.fullmatch(r"[\w.\-_]+", name_arg) is None:
            logger.error("Please ensure --name argument contains only the characters 'A-Za-z0-9.-_'")
            raise ArgumentError
        self.name = name_arg

        # Get output directory
        output_directory_arg = self.args.get("--output-directory", None)
        if output_directory_arg is None:
            output_directory_arg = os.getcwd()
        elif not Path(output_directory_arg).is_dir():
            logger.error(f"--output-directory specified as '{output_directory_arg}' but directory does not exist")
            raise ArgumentError

        # Get date
        self.date = datetime.utcnow()

        # Set output file path
        self.output_file_path = Path(output_directory_arg) / f"icav2-download-script-{self.name}-{file_friendly_datetime_format(self.date)}.sh"

        # Check if encrypted
        public_key_arg = self.args.get("--public-key", None)
        keybase_username_arg = self.args.get("--keybase-username", None)
        keybase_team_arg = self.args.get("--keybase-team", None)
        if len(
            list(
                filter(
                    lambda x: x is not None,
                    [public_key_arg, keybase_username_arg, keybase_team_arg]
                )
            )
        ) > 1:
            logger.error("Please specify no more than one of --public-key, --keybase-username or --keybase-team")
            raise ArgumentError
        if public_key_arg is not None:
            if not Path(public_key_arg).is_file():
                logger.error(f"--public-key value specified as '{public_key_arg}' but file does not exist")
                raise ArgumentError
            self.public_key = Path(public_key_arg)
            self.is_encrypted = True
        if keybase_username_arg is not None:
            self.is_keybase = True
            self.is_keybase_team = False
            self.keybase_name = keybase_username_arg
            self.is_encrypted = True
        if keybase_team_arg is not None:
            self.is_keybase = True
            self.is_keybase_team = True
            self.keybase_name = keybase_team_arg
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
                raise ArgumentError

        # Get the file regex
        file_regex_arg = self.args.get("--file-regex", None)
        if file_regex_arg is not None:
            self.file_regex = re.compile(file_regex_arg)

    def __call__(self):
        # Find all files in data_path and collect presigned urls and map to paths
        self.data_list = find_data_recursively(
            project_id=self.project_id,
            parent_folder_path=str(self.data_path) + "/",
            data_type="FILE",
            name=".*"
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
            logger.error(f"No files to presign in directory '{self.data_path}' after using file regex '{self.file_regex}'")
            raise FileNotFoundError

        # Bulk presign the directory
        presigned_directory_df = pd.DataFrame(
            bulk_presign_directory(
                project_id=self.project_id,
                folder_path=str(self.data_path) + "/",
                folder_id=self.data_id.data.id
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
            "DATE": file_friendly_datetime_format(self.date),
            "EXPIRY_DATE": file_friendly_datetime_format(calculate_presigned_url_expiry(self.date)),
            "EXPIRY_DATE_EPOCH": calculate_presigned_url_expiry(self.date).strftime('%s'),
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
