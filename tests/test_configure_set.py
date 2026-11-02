#!/usr/bin/env python3
"""
Unit tests for the (deprecated) ConfigureSet command.

Tests interactive prompting, API key validation, config creation/overwrite,
config file handling, and that the deprecation warning is emitted while the
command still writes a usable two-level config.
"""

import os
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from icav2_cli_plugins.subcommands.configure.configure_set import Command
from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig, TenantConfig


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

    @pytest.fixture(autouse=True)
    def _disable_auto_encryption(self, tmp_path, monkeypatch):
        """Prevent tests from auto-encrypting by pointing to non-existent keys."""
        fake_pub = tmp_path / "nonexistent_keys" / "id_rsa.pub"
        fake_priv = tmp_path / "nonexistent_keys" / "id_rsa"
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.DEFAULT_PUBLIC_KEY_PATH",
            fake_pub,
        )
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.DEFAULT_PRIVATE_KEY_PATH",
            fake_priv,
        )

    def test_successful_profile_creation(self, tmp_path: Path, capsys):
        """Successful flow: prompts, validates key, writes tenant + profile."""
        config_path = tmp_path / "config"

        inputs = iter([
            "ica.illumina.com",  # server_url
            "my-api-key-123",    # x_api_key
            "my-tenant",         # tenant_name
            "my-project",        # project_name
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "generated-token"}

        # Mock the project list API call for resolving project name -> ID
        mock_projects_response = MagicMock()
        mock_projects_response.status_code = 200
        mock_projects_response.json.return_value = {
            "items": [{"name": "my-project", "id": "proj-uuid-123"}]
        }

        cmd = Command(["configure", "set", "myprofile"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.requests.get", return_value=mock_projects_response):
            cmd()

        # Deprecation warning emitted on stderr
        captured = capsys.readouterr()
        assert "deprecated" in captured.err

        # Verify config was written with a tenant + profile
        assert config_path.exists()
        parser = ConfigParser()
        tenants, profiles = parser.parse_file(config_path)
        assert "my-tenant" in tenants
        assert tenants["my-tenant"].server_url == "ica.illumina.com"
        assert tenants["my-tenant"].x_api_key == "my-api-key-123"
        assert "myprofile" in profiles
        assert profiles["myprofile"].project_name == "my-project"
        assert profiles["myprofile"].project_id == "proj-uuid-123"
        assert profiles["myprofile"].tenant_name == "my-tenant"

    def test_default_profile_when_no_name(self, tmp_path: Path):
        """When no profile name given, writes to [default] section."""
        config_path = tmp_path / "config"

        inputs = iter([
            "",                  # server_url (empty -> default)
            "api-key-456",       # x_api_key
            "",                  # tenant_name (empty -> None, falls back to profile name)
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
        tenants, profiles = parser.parse_file(config_path)
        assert "default" in profiles
        # No explicit tenant -> tenant named after the profile
        assert "default" in tenants
        assert tenants["default"].server_url == "ica.illumina.com"
        assert tenants["default"].x_api_key == "api-key-456"
        assert profiles["default"].project_name is None
        assert profiles["default"].tenant_name == "default"

    def test_api_key_validation_failure_exits(self, tmp_path: Path, capsys):
        """When API key validation fails, exit without writing config."""
        config_path = tmp_path / "config"

        inputs = iter([
            "ica.illumina.com",
            "bad-api-key",
            "my-tenant",
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
            "my-tenant",
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

        # Write an existing config with a tenant + profile
        parser = ConfigParser()
        existing_tenants = {
            "old-tenant": TenantConfig(
                name="old-tenant",
                server_url="old-server.com",
                x_api_key="old-key",
            )
        }
        existing_profiles = {
            "myprofile": ProfileConfig(
                name="myprofile",
                project_name="old-project",
                tenant_name="old-tenant",
            )
        }
        parser.write_file(config_path, existing_tenants, existing_profiles)

        inputs = iter([
            "new-server.com",
            "new-api-key",
            "new-tenant",
            "new-project",
        ])

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "new-token"}

        mock_projects_response = MagicMock()
        mock_projects_response.status_code = 200
        mock_projects_response.json.return_value = {
            "items": [{"name": "new-project", "id": "proj-new-uuid"}]
        }

        cmd = Command(["configure", "set", "myprofile"])

        with patch("builtins.input", lambda prompt: next(inputs)), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH", config_path), \
             patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response), \
             patch("icav2_cli_plugins.subcommands.configure.configure_set.requests.get", return_value=mock_projects_response):
            cmd()

        tenants, profiles = parser.parse_file(config_path)
        assert tenants["new-tenant"].server_url == "new-server.com"
        assert tenants["new-tenant"].x_api_key == "new-api-key"
        assert profiles["myprofile"].project_name == "new-project"
        assert profiles["myprofile"].project_id == "proj-new-uuid"
        assert profiles["myprofile"].tenant_name == "new-tenant"

    def test_preserves_other_profiles_on_overwrite(self, tmp_path: Path):
        """When overwriting a profile, other profiles are preserved."""
        config_path = tmp_path / "config"

        parser = ConfigParser()
        existing_tenants = {
            "default": TenantConfig(
                name="default",
                server_url="ica.illumina.com",
                x_api_key="default-key",
            ),
            "other": TenantConfig(
                name="other",
                server_url="other.com",
                x_api_key="other-key",
            ),
        }
        existing_profiles = {
            "default": ProfileConfig(name="default", tenant_name="default"),
            "other": ProfileConfig(name="other", tenant_name="other"),
        }
        parser.write_file(config_path, existing_tenants, existing_profiles)

        inputs = iter([
            "ica.illumina.com",
            "new-default-key",
            "",                  # tenant_name (empty -> falls back to profile name 'default')
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

        tenants, profiles = parser.parse_file(config_path)
        # Default tenant was overwritten
        assert tenants["default"].x_api_key == "new-default-key"
        # Other profile + tenant preserved
        assert "other" in profiles
        assert "other" in tenants
        assert tenants["other"].x_api_key == "other-key"

    def test_creates_parent_directories(self, tmp_path: Path):
        """Config file and parent dirs are created if they don't exist."""
        config_path = tmp_path / "nested" / "dir" / "config"

        inputs = iter([
            "ica.illumina.com",
            "key-123",
            "",                  # tenant_name (empty -> falls back to profile name)
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

        assert config_path.exists()
        # Verify file mode is 0600
        mode = config_path.stat().st_mode & 0o777
        assert mode == 0o600
