#!/usr/bin/env python3

"""
Test all of the commands in the config helpers python script
"""
import unittest.mock

from unittest.mock import patch, mock_open, MagicMock

from utils.globals import DEFAULT_ICAV2_BASE_URL, ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY
from utils.config_helpers import read_session_file, get_session_file_path, get_access_token_from_session_file, \
    check_access_token_expiry, get_libicav2_configuration

from libica.openapi.v2 import Configuration

from uuid import uuid4

from pathlib import Path

import os

from utils.logger import get_logger

logger = get_logger()

# Some globals
MY_PROJECT_ID = str(uuid4())
MY_HOME_DIR = Path("/path/to/home")

MOCK_SESSION_FILE_CONTENT = f"""
access-token: {os.environ.get("ICAV2_ACCESS_TOKEN", None)}
project-id: {MY_PROJECT_ID}
"""


class TestSessionPath(unittest.TestCase):
    @patch(
        "pathlib.Path.is_file",
        new_callable=MagicMock
    )
    @patch.dict(
        os.environ, {
            "HOME": str(MY_HOME_DIR)
        }
    )
    def test_get_session_file_path(self, magic_mock):
        assert get_session_file_path() == MY_HOME_DIR / ".icav2" / ".session.ica.yaml"

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=MOCK_SESSION_FILE_CONTENT
    )
    def test_read_session_file(self, mock_open):
        assert read_session_file().get("project-id") == MY_PROJECT_ID


class TestAccessToken(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=MOCK_SESSION_FILE_CONTENT
    )
    @patch.dict(
        os.environ, {
            "HOME": str(MY_HOME_DIR)
        }
    )
    def setUp(self, mock_open) -> None:
        pass

    def test_check_access_token_expiry(self):
        # Collect the access token
        not_access_token_expired = check_access_token_expiry(read_session_file().get(ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY))

        # Ensure it has returned true
        assert not_access_token_expired

    def test_get_access_token_from_session_file(self):
        # Collect the access token from the mock session file
        access_token = get_access_token_from_session_file(refresh=False)

        assert access_token == read_session_file().get(ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY)


# class test output configuration object
class TestLibicav2Configuration(unittest.TestCase):
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data=MOCK_SESSION_FILE_CONTENT
    )
    @patch.dict(
        os.environ, {
            "HOME": str(MY_HOME_DIR)
        }
    )
    def setUp(self, mock_open) -> None:
        pass

    def test_get_libicav2_configuration(self):
        self.assertEqual(
            get_libicav2_configuration().host,
            Configuration(
                host=DEFAULT_ICAV2_BASE_URL,
                access_token=read_session_file().get(ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY)
            ).host
        )
        self.assertEqual(
            get_libicav2_configuration().access_token,
            Configuration(
                host=DEFAULT_ICAV2_BASE_URL,
                access_token=read_session_file().get(ICAV2_SESSION_FILE_ACCESS_TOKEN_KEY)
            ).access_token
        )

