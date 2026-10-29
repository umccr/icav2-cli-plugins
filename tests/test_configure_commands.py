#!/usr/bin/env python3
"""
Unit tests for the configure command group (two-level config).

Covers:
  - configure set-tenant   (writes a [tenant] section with token + expiry)
  - configure set-profile  (references an existing tenant; errors otherwise)
  - configure export       (emits exactly four export lines)
  - configure set          (deprecated; still writes a usable config)
  - configure list         (two-level listing + empty state)
  - tokens export          (deprecated; still prints the token)

Token generation (requests.post) and project-id resolution (requests.get)
are mocked; no live network is used. tmp_path holds the config file.
"""

import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import jwt
import pytest

from icav2_cli_plugins.subcommands.configure.configure_set import Command as ConfigureSetCommand
from icav2_cli_plugins.subcommands.configure.configure_set_tenant import Command as ConfigureSetTenantCommand
from icav2_cli_plugins.subcommands.configure.configure_set_profile import Command as ConfigureSetProfileCommand
from icav2_cli_plugins.subcommands.configure.configure_export import Command as ConfigureExportCommand
from icav2_cli_plugins.subcommands.configure.configure_list import Command as ConfigureListCommand
from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig, TenantConfig


def _make_jwt(exp: int) -> str:
    """Helper: create a JWT with the given exp claim."""
    return jwt.encode({"exp": exp, "iss": "test"}, "secret", algorithm="HS256")


# ---------------------------------------------------------------------------
# configure set-tenant tests
# ---------------------------------------------------------------------------


class TestConfigureSetTenant:

    @pytest.fixture(autouse=True)
    def _disable_auto_encryption(self, tmp_path, monkeypatch):
        fake_pub = tmp_path / "nonexistent_keys" / "id_rsa.pub"
        fake_priv = tmp_path / "nonexistent_keys" / "id_rsa"
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set_tenant.DEFAULT_PUBLIC_KEY_PATH",
            fake_pub,
        )
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set_tenant.DEFAULT_PRIVATE_KEY_PATH",
            fake_priv,
        )

    def test_set_tenant_writes_tenant_section(self, tmp_path: Path, monkeypatch):
        """set-tenant writes a [tenant] section with token + expiry, no project fields."""
        config_path = tmp_path / "config"
        exp = int(time.time()) + 7200
        token = _make_jwt(exp)

        responses = iter([
            "ica.illumina.com",   # server_url
            "my-api-key",         # x_api_key
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set_tenant.CONFIG_FILE_PATH",
            config_path,
        )

        mock_response = MagicMock(status_code=200, json=MagicMock(return_value={"token": token}))

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd = ConfigureSetTenantCommand(["configure", "set-tenant", "my-tenant"])
            cmd()

        parser = ConfigParser()
        tenants, profiles = parser.parse_file(config_path)
        assert "my-tenant" in tenants
        tenant = tenants["my-tenant"]
        assert tenant.server_url == "ica.illumina.com"
        assert tenant.x_api_key == "my-api-key"
        assert tenant.access_token == token
        assert tenant.access_token_expiry == str(exp)
        # No profiles / project fields written
        assert profiles == {}

    def test_set_tenant_defaults_to_default(self, tmp_path: Path, monkeypatch):
        config_path = tmp_path / "config"
        token = _make_jwt(int(time.time()) + 7200)

        responses = iter(["", "key-abc"])  # server_url default, api key
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set_tenant.CONFIG_FILE_PATH",
            config_path,
        )
        mock_response = MagicMock(status_code=200, json=MagicMock(return_value={"token": token}))

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            cmd = ConfigureSetTenantCommand(["configure", "set-tenant"])
            cmd()

        parser = ConfigParser()
        tenants, _profiles = parser.parse_file(config_path)
        assert "default" in tenants
        assert tenants["default"].server_url == "ica.illumina.com"


# ---------------------------------------------------------------------------
# configure set-profile tests
# ---------------------------------------------------------------------------


class TestConfigureSetProfile:

    def _write_tenant(self, config_path: Path, token: str) -> None:
        parser = ConfigParser()
        tenants = {
            "my-tenant": TenantConfig(
                name="my-tenant",
                server_url="ica.illumina.com",
                x_api_key="tenant-key",
                access_token=token,
            )
        }
        parser.write_file(config_path, tenants, {})

    def test_set_profile_unknown_tenant_errors(self, tmp_path: Path, monkeypatch, capsys):
        """Entering an unconfigured tenant exits with a stderr listing available tenants."""
        config_path = tmp_path / "config"
        token = _make_jwt(int(time.time()) + 7200)
        self._write_tenant(config_path, token)

        responses = iter(["does-not-exist"])  # tenant_name
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set_profile.CONFIG_FILE_PATH",
            config_path,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd = ConfigureSetProfileCommand(["configure", "set-profile", "prod"])
            cmd()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "does-not-exist" in captured.err
        assert "my-tenant" in captured.err  # available tenant listed

    def test_set_profile_writes_profile(self, tmp_path: Path, monkeypatch):
        """Valid tenant -> writes a profile with project fields, tenant_name, output_format."""
        config_path = tmp_path / "config"
        token = _make_jwt(int(time.time()) + 7200)
        self._write_tenant(config_path, token)

        responses = iter([
            "my-tenant",     # tenant_name
            "my-project",    # project_name
            "json",          # output_format
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set_profile.CONFIG_FILE_PATH",
            config_path,
        )

        mock_get = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"items": [{"name": "my-project", "id": "proj-uuid-123"}]}),
        )

        with patch(
            "icav2_cli_plugins.subcommands.configure.configure_set_profile.requests.get",
            return_value=mock_get,
        ):
            cmd = ConfigureSetProfileCommand(["configure", "set-profile", "prod"])
            cmd()

        parser = ConfigParser()
        tenants, profiles = parser.parse_file(config_path)
        assert "prod" in profiles
        profile = profiles["prod"]
        assert profile.project_id == "proj-uuid-123"
        assert profile.project_name == "my-project"
        assert profile.tenant_name == "my-tenant"
        assert profile.output_format == "json"
        # No server_url / x_api_key on the profile object
        assert not hasattr(profile, "server_url")
        assert not hasattr(profile, "x_api_key")


# ---------------------------------------------------------------------------
# configure export tests
# ---------------------------------------------------------------------------


class TestConfigureExport:

    def test_export_prints_four_lines(self, tmp_path: Path, monkeypatch, capsys):
        """export prints exactly four export lines with derived base url."""
        config_path = tmp_path / "config"
        token = _make_jwt(int(time.time()) + 7200)

        parser = ConfigParser()
        tenants = {
            "my-tenant": TenantConfig(
                name="my-tenant",
                server_url="ica.illumina.com",
                x_api_key="tenant-key",
                access_token=token,
            )
        }
        profiles = {
            "prod": ProfileConfig(
                name="prod",
                project_id="proj-uuid-123",
                project_name="my-project",
                tenant_name="my-tenant",
            )
        }
        parser.write_file(config_path, tenants, profiles)

        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_export.CONFIG_FILE_PATH",
            config_path,
        )
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        cmd = ConfigureExportCommand(["configure", "export", "prod"])
        cmd()

        captured = capsys.readouterr()
        lines = [ln for ln in captured.out.splitlines() if ln.strip()]
        assert lines == [
            "export ICAV2_SERVER_URL=ica.illumina.com",
            "export ICAV2_BASE_URL=https://ica.illumina.com/ica/rest",
            "export ICAV2_PROJECT_ID=proj-uuid-123",
            f"export ICAV2_ACCESS_TOKEN={token}",
        ]


# ---------------------------------------------------------------------------
# configure set (deprecated) tests
# ---------------------------------------------------------------------------


class TestConfigureSetDeprecated:

    @pytest.fixture(autouse=True)
    def _disable_auto_encryption(self, tmp_path, monkeypatch):
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

    def test_set_warns_and_writes_config(self, tmp_path: Path, monkeypatch, capsys):
        config_path = tmp_path / "config"

        responses = iter([
            "ica.illumina.com",  # server_url
            "test-api-key",      # x_api_key
            "my-tenant",         # tenant_name
            "my-project",        # project_name
        ])
        monkeypatch.setattr("builtins.input", lambda prompt: next(responses))
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_set.CONFIG_FILE_PATH",
            config_path,
        )

        with patch.object(
            __import__("icav2_cli_plugins.utils.token_manager", fromlist=["TokenManager"]).TokenManager,
            "_generate_token",
            return_value="mocked-jwt-token-12345",
        ), patch(
            "icav2_cli_plugins.subcommands.configure.configure_set.requests.get",
        ) as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"items": [{"name": "my-project", "id": "proj-uuid-123"}]}),
            )
            cmd = ConfigureSetCommand(["configure", "set", "dev-profile"])
            cmd()

        captured = capsys.readouterr()
        assert "deprecated" in captured.err

        parser = ConfigParser()
        tenants, profiles = parser.parse_file(config_path)
        assert "my-tenant" in tenants
        assert tenants["my-tenant"].x_api_key == "test-api-key"
        assert "dev-profile" in profiles
        assert profiles["dev-profile"].project_id == "proj-uuid-123"
        assert profiles["dev-profile"].tenant_name == "my-tenant"


# ---------------------------------------------------------------------------
# configure list tests
# ---------------------------------------------------------------------------


class TestConfigureListOutput:

    def test_list_with_sample_config(self, tmp_path: Path, monkeypatch, capsys):
        config_path = tmp_path / "config"

        parser = ConfigParser()
        tenants = {
            "prod-tenant": TenantConfig(name="prod-tenant", server_url="prod.illumina.com"),
            "dev-tenant": TenantConfig(name="dev-tenant", server_url="ica.illumina.com"),
        }
        profiles = {
            "default": ProfileConfig(name="default", tenant_name="dev-tenant", project_name="dev-proj"),
            "production": ProfileConfig(name="production", tenant_name="prod-tenant", project_name="prod-proj"),
        }
        parser.write_file(config_path, tenants, profiles)

        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_list.CONFIG_FILE_PATH",
            config_path,
        )

        cmd = ConfigureListCommand([])
        cmd()

        output = capsys.readouterr().out
        assert "Tenant" in output
        assert "Profile" in output
        assert "prod-tenant" in output
        assert "dev-tenant" in output
        assert "default" in output
        assert "production" in output
        # Profile references its tenant
        assert "prod.illumina.com" in output

    def test_list_empty_state_no_config_file(self, tmp_path: Path, monkeypatch, capsys):
        config_path = tmp_path / "nonexistent_config"
        monkeypatch.setattr(
            "icav2_cli_plugins.subcommands.configure.configure_list.CONFIG_FILE_PATH",
            config_path,
        )

        with pytest.raises(SystemExit) as exc_info:
            cmd = ConfigureListCommand([])
            cmd()

        assert exc_info.value.code == 0
        assert "No profiles configured" in capsys.readouterr().out

    def test_list_empty_config_file(self, tmp_path: Path, monkeypatch, capsys):
        config_path = tmp_path / "config"
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
        assert "No profiles configured" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# tokens export (deprecated) tests
# ---------------------------------------------------------------------------


class TestTokensExportDeprecated:

    def test_tokens_export_warns_but_prints_token(self, monkeypatch, capsys):
        from icav2_cli_plugins.subcommands.tokens.export import TokensExport

        monkeypatch.setenv("ICAV2_ACCESS_TOKEN", "my-resolved-token")

        cmd = TokensExport(["tokens", "export"])
        cmd()

        captured = capsys.readouterr()
        assert "deprecated" in captured.err
        assert "my-resolved-token" in captured.out
