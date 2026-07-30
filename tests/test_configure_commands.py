#!/usr/bin/env python3
"""
Unit tests for configure set and configure list commands.

Tests interactive prompting with mocked stdin, mocked token generation,
output formatting, empty state handling, and file permissions.

Requirements validated: 8.1, 8.2, 8.4, 8.7
"""

import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from icav2_cli_plugins.subcommands.configure.configure_set import Command as ConfigureSetCommand
from icav2_cli_plugins.subcommands.configure.configure_list import Command as ConfigureListCommand
from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig


# ---------------------------------------------------------------------------
# configure set tests
# ---------------------------------------------------------------------------


class TestConfigureSetSuccess:
    """Test configure set with mocked stdin and mocked token generation."""

    def test_set_with_valid_inputs_writes_profile(self, tmp_path: Path, monkeypatch):
        """
        Mock input() to provide server_url, api_key, project_name.
        Mock TokenManager._generate_token to succeed.
        Verify profile is written to config file correctly.
        Requirement: 8.1, 8.5
        """
        config_path = tmp_path / "config"

        # Sequence of user inputs
        responses = iter([
            "my-server.illumina.com",  # server_url
            "test-api-key-abc123",     # x_api_key
            "my-project",              # project_name
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))

        # Patch CONFIG_FILE_PATH to use tmp_path
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        # Mock _generate_token to succeed (returns a token string)
        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            return_value="mocked-jwt-token-12345",
        ):
            cmd = ConfigureSetCommand(["configure", "set", "dev-profile"])
            cmd()

        # Verify config file exists and contains the correct profile
        assert config_path.exists()
        parser = ConfigParser()
        profiles = parser.parse_file(config_path)
        assert "dev-profile" in profiles
        assert profiles["dev-profile"].server_url == "my-server.illumina.com"
        assert profiles["dev-profile"].x_api_key == "test-api-key-abc123"
        assert profiles["dev-profile"].project_name == "my-project"

    def test_set_token_generation_failure_does_not_modify_config(
        self, tmp_path: Path, monkeypatch, capsys
    ):
        """
        Mock token generation to fail.
        Verify error message and config NOT modified.
        Requirement: 8.6
        """
        config_path = tmp_path / "config"

        responses = iter([
            "ica.illumina.com",
            "bad-api-key",
            "project-name",
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        # Mock _generate_token to raise RuntimeError (simulating API failure)
        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            side_effect=RuntimeError("HTTP 403 Forbidden"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                cmd = ConfigureSetCommand(["configure", "set", "test-profile"])
                cmd()

        assert exc_info.value.code == 1
        # Config file should not exist
        assert not config_path.exists()
        # Error message should mention validation failure
        captured = capsys.readouterr()
        assert "API key validation failed" in captured.err

    def test_set_no_profile_name_defaults_to_default(self, tmp_path: Path, monkeypatch):
        """
        configure set with no profile name defaults to [default].
        Requirement: 8.3
        """
        config_path = tmp_path / "config"

        responses = iter([
            "",               # server_url (empty -> default ica.illumina.com)
            "my-key-xyz",     # x_api_key
            "",               # project_name (empty -> None)
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            return_value="mocked-token",
        ):
            cmd = ConfigureSetCommand(["configure", "set"])
            cmd()

        parser = ConfigParser()
        profiles = parser.parse_file(config_path)
        assert "default" in profiles
        assert profiles["default"].server_url == "ica.illumina.com"
        assert profiles["default"].x_api_key == "my-key-xyz"
        assert profiles["default"].project_name is None

    def test_set_existing_profile_overwrites(self, tmp_path: Path, monkeypatch):
        """
        configure set with a profile name that already exists overwrites it.
        Requirement: 8.8
        """
        config_path = tmp_path / "config"

        # Write an existing config with a profile
        parser = ConfigParser()
        existing = {
            "staging": ProfileConfig(
                name="staging",
                server_url="old-server.com",
                x_api_key="old-key-111",
                project_name="old-project",
            ),
            "default": ProfileConfig(
                name="default",
                server_url="ica.illumina.com",
                x_api_key="default-key",
            ),
        }
        parser.write_file(config_path, existing)

        # Now overwrite "staging"
        responses = iter([
            "new-server.com",       # new server_url
            "new-api-key-222",      # new x_api_key
            "new-project-name",     # new project_name
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            return_value="new-token",
        ):
            cmd = ConfigureSetCommand(["configure", "set", "staging"])
            cmd()

        # Verify overwritten profile
        profiles = parser.parse_file(config_path)
        assert profiles["staging"].server_url == "new-server.com"
        assert profiles["staging"].x_api_key == "new-api-key-222"
        assert profiles["staging"].project_name == "new-project-name"
        # Verify default profile was preserved
        assert "default" in profiles
        assert profiles["default"].x_api_key == "default-key"


# ---------------------------------------------------------------------------
# configure list tests
# ---------------------------------------------------------------------------


class TestConfigureListOutput:
    """Test configure list output format and empty state."""

    def test_list_with_sample_profiles(self, tmp_path: Path, monkeypatch, capsys):
        """
        Write a sample config, run list, verify table output format.
        Requirement: 8.2
        """
        config_path = tmp_path / "config"

        # Write sample profiles
        parser = ConfigParser()
        profiles = {
            "default": ProfileConfig(
                name="default",
                server_url="ica.illumina.com",
                x_api_key="key-default",
            ),
            "production": ProfileConfig(
                name="production",
                server_url="prod.illumina.com",
                x_api_key="key-prod",
            ),
            "staging": ProfileConfig(
                name="staging",
                server_url="staging.illumina.com",
                x_api_key="key-staging",
            ),
        }
        parser.write_file(config_path, profiles)

        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_list.CONFIG_FILE_PATH",
            config_path,
        )

        cmd = ConfigureListCommand([])
        cmd()

        captured = capsys.readouterr()
        output = captured.out

        # Verify table header
        assert "Profile" in output
        assert "Server URL" in output

        # Verify all profiles are listed
        assert "default" in output
        assert "production" in output
        assert "staging" in output

        # Verify server URLs are shown
        assert "ica.illumina.com" in output
        assert "prod.illumina.com" in output
        assert "staging.illumina.com" in output

        # Verify profiles are sorted (default, production, staging)
        default_pos = output.index("default")
        production_pos = output.index("production")
        staging_pos = output.index("staging")
        assert default_pos < production_pos < staging_pos

    def test_list_empty_state_no_config_file(self, tmp_path: Path, monkeypatch, capsys):
        """
        Empty/missing config file produces 'No profiles configured' message.
        Requirement: 8.7
        """
        config_path = tmp_path / "nonexistent_config"

        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_list.CONFIG_FILE_PATH",
            config_path,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd = ConfigureListCommand([])
            cmd()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No profiles configured" in captured.out

    def test_list_empty_config_file(self, tmp_path: Path, monkeypatch, capsys):
        """
        Config file exists but contains no profiles shows empty message.
        Requirement: 8.7
        """
        config_path = tmp_path / "config"
        # Write an empty config (just comments or blank)
        config_path.write_text("# empty config\n", encoding="utf-8")
        os.chmod(config_path, 0o600)

        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_list.CONFIG_FILE_PATH",
            config_path,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd = ConfigureListCommand([])
            cmd()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "No profiles configured" in captured.out


# ---------------------------------------------------------------------------
# File permissions tests
# ---------------------------------------------------------------------------


class TestFilePermissions:
    """Test that config file is created with mode 0600."""

    def test_config_file_permissions_on_create(self, tmp_path: Path, monkeypatch):
        """
        Verify config file is created with mode 0600.
        Requirement: 8.4
        """
        config_path = tmp_path / "config"

        responses = iter([
            "ica.illumina.com",
            "key-for-perms-test",
            "project",
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            return_value="perms-token",
        ):
            cmd = ConfigureSetCommand(["configure", "set", "test"])
            cmd()

        # Check file permissions
        file_mode = config_path.stat().st_mode & 0o777
        assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"

    def test_config_file_permissions_on_overwrite(self, tmp_path: Path, monkeypatch):
        """
        Verify config file retains mode 0600 after overwriting a profile.
        Requirement: 8.4
        """
        config_path = tmp_path / "config"

        # Create initial config
        parser = ConfigParser()
        parser.write_file(
            config_path,
            {"default": ProfileConfig(name="default", x_api_key="old")},
        )

        # Verify permissions were set initially
        assert (config_path.stat().st_mode & 0o777) == 0o600

        # Overwrite the profile
        responses = iter([
            "ica.illumina.com",
            "new-key",
            "",
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            return_value="new-token",
        ):
            cmd = ConfigureSetCommand(["configure", "set"])
            cmd()

        # Verify permissions remain 0600
        file_mode = config_path.stat().st_mode & 0o777
        assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"

    def test_config_parser_write_file_sets_permissions(self, tmp_path: Path):
        """
        Verify ConfigParser.write_file() directly sets mode 0600.
        Requirement: 8.4
        """
        config_path = tmp_path / "direct_write_config"
        parser = ConfigParser()
        profiles = {
            "default": ProfileConfig(
                name="default",
                server_url="ica.illumina.com",
                x_api_key="key-123",
            ),
        }
        parser.write_file(config_path, profiles)

        assert config_path.exists()
        file_mode = config_path.stat().st_mode & 0o777
        assert file_mode == 0o600, f"Expected 0600, got {oct(file_mode)}"
