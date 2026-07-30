#!/usr/bin/env python3
"""
Unit tests for the ConfigureSet command.

Tests interactive prompting, API key validation, profile creation/overwrite,
and config file handling.
"""

import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from icav2_cli_plugins.subcommands.configure.configure_set import Command
from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig


class TestCommandInit:
    """Tests for Command argument parsing."""

    def test_defaults_to_default_profile(self):
        cmd = Command(["configure", "set"])
        assert cmd.profile_name == "default"

    def test_accepts_named_profile(self):
        cmd = Command(["configure", "set", "production"])
        assert cmd.profile_name == "production"

    def test_help_exits_cleanly(self):
        with pytest.raises(SystemExit) as exc_info:
            Command(["configure", "set", "help"])
        assert exc_info.value.code == 0


class TestCommandCall:
    """Tests for Command.__call__() interactive flow."""

    def test_successful_profile_creation(self, tmp_path: Path):
        """Successful flow: prompts, validates key, writes config."""
        config_path = tmp_path / "config"

        inputs = iter([
            "ica.illumina.com",  # server_url
            "my-api-key-123",    # x_api_key
            "my-project",        # project_name
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "generated-token"}

        cmd = Command(["configure", "set", "myprofile"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd()

        # Verify config was written
        assert config_path.exists()
        parser = ConfigParser()
        profiles = parser.parse_file(config_path)
        assert "myprofile" in profiles
        assert profiles["myprofile"].server_url == "ica.illumina.com"
        assert profiles["myprofile"].x_api_key == "my-api-key-123"
        assert profiles["myprofile"].project_name == "my-project"

    def test_default_profile_when_no_name(self, tmp_path: Path):
        """When no profile name given, writes to [default] section."""
        config_path = tmp_path / "config"

        inputs = iter([
            "",                  # server_url (empty -> default)
            "api-key-456",       # x_api_key
            "",                  # project_name (empty -> None)
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "tok"}

        cmd = Command(["configure", "set"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd()

        parser = ConfigParser()
        profiles = parser.parse_file(config_path)
        assert "default" in profiles
        assert profiles["default"].server_url == "ica.illumina.com"
        assert profiles["default"].x_api_key == "api-key-456"
        assert profiles["default"].project_name is None

    def test_api_key_validation_failure_exits(self, tmp_path: Path, capsys):
        """When API key validation fails, exit without writing config."""
        config_path = tmp_path / "config"

        inputs = iter([
            "ica.illumina.com",
            "bad-api-key",
            "project",
        ])

        mock_response = MagicMock()
        mock_response.status_code = 403  # Unauthorized

        cmd = Command(["configure", "set", "test-profile"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response), \
             pytest.raises(SystemExit) as exc_info:
            cmd()

        assert exc_info.value.code == 1
        # Config file should NOT have been created
        assert not config_path.exists()
        captured = capsys.readouterr()
        assert "API key validation failed" in captured.err

    def test_empty_api_key_exits(self, tmp_path: Path, capsys):
        """When user provides empty API key, exit with error."""
        config_path = tmp_path / "config"

        inputs = iter([
            "ica.illumina.com",
            "",                  # empty api key
            "project",
        ])

        cmd = Command(["configure", "set"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             pytest.raises(SystemExit) as exc_info:
            cmd()

        assert exc_info.value.code == 1
        assert not config_path.exists()
        captured = capsys.readouterr()
        assert "API key is required" in captured.err

    def test_overwrites_existing_profile(self, tmp_path: Path):
        """When profile already exists, overwrite it with new values."""
        config_path = tmp_path / "config"

        # Write an existing config with a profile
        parser = ConfigParser()
        existing_profiles = {
            "myprofile": ProfileConfig(
                name="myprofile",
                server_url="old-server.com",
                x_api_key="old-key",
                project_name="old-project",
            )
        }
        parser.write_file(config_path, existing_profiles)

        inputs = iter([
            "new-server.com",
            "new-api-key",
            "new-project",
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "new-token"}

        cmd = Command(["configure", "set", "myprofile"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd()

        profiles = parser.parse_file(config_path)
        assert profiles["myprofile"].server_url == "new-server.com"
        assert profiles["myprofile"].x_api_key == "new-api-key"
        assert profiles["myprofile"].project_name == "new-project"

    def test_preserves_other_profiles_on_overwrite(self, tmp_path: Path):
        """When overwriting a profile, other profiles are preserved."""
        config_path = tmp_path / "config"

        parser = ConfigParser()
        existing_profiles = {
            "default": ProfileConfig(
                name="default",
                server_url="ica.illumina.com",
                x_api_key="default-key",
            ),
            "other": ProfileConfig(
                name="other",
                server_url="other.com",
                x_api_key="other-key",
            ),
        }
        parser.write_file(config_path, existing_profiles)

        inputs = iter([
            "ica.illumina.com",
            "new-default-key",
            "",
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "tok"}

        cmd = Command(["configure", "set"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd()

        profiles = parser.parse_file(config_path)
        # Default was overwritten
        assert profiles["default"].x_api_key == "new-default-key"
        # Other profile preserved
        assert "other" in profiles
        assert profiles["other"].x_api_key == "other-key"

    def test_creates_parent_directories(self, tmp_path: Path):
        """Config file and parent dirs are created if they don't exist."""
        config_path = tmp_path / "nested" / "dir" / "config"

        inputs = iter([
            "ica.illumina.com",
            "key-123",
            "",
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "tok"}

        cmd = Command(["configure", "set"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd()

        assert config_path.exists()
        # Verify file mode is 0600
        mode = config_path.stat().st_mode & 0o777
        assert mode == 0o600
