#!/usr/bin/env python3
"""
Unit tests for the ProfileResolver class.

Tests the precedence chain:
1. --profile CLI flag
2. ICAV2_PROFILE env var
3. ICAV2_TENANT_NAME env var
4. [default] profile
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch
import tempfile

from icav2_cli_plugins.utils.profile_resolver import ProfileResolver, ResolvedConfig


# Sample config file content for tests
SAMPLE_CONFIG = """\
[default]
server_url = ica.illumina.com
x_api_key = default-api-key
project_id = default-project-id
output_format = table

[profile staging]
server_url = staging.illumina.com
x_api_key = staging-api-key
project_id = staging-project-id
output_format = json

[profile production]
server_url = prod.illumina.com
x_api_key = prod-api-key
project_id = prod-project-id
output_format = yaml
"""

MINIMAL_CONFIG = """\
[default]
x_api_key = my-key
"""


class TestDetermineProfileName(unittest.TestCase):
    """Tests for _determine_profile_name() precedence."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        self.tmp.write(SAMPLE_CONFIG)
        self.tmp.close()
        self.config_path = Path(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_cli_profile_takes_highest_precedence(self):
        """--profile flag overrides all env vars."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile="staging")
        with patch.dict(os.environ, {"ICAV2_PROFILE": "production", "ICAV2_TENANT_NAME": "other"}):
            name = resolver._determine_profile_name()
        self.assertEqual(name, "staging")

    def test_icav2_profile_env_takes_second_precedence(self):
        """ICAV2_PROFILE env var used when no --profile flag."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        with patch.dict(os.environ, {"ICAV2_PROFILE": "production", "ICAV2_TENANT_NAME": "other"}):
            name = resolver._determine_profile_name()
        self.assertEqual(name, "production")

    def test_icav2_tenant_name_env_takes_third_precedence(self):
        """ICAV2_TENANT_NAME used when no --profile flag and no ICAV2_PROFILE."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        env = {"ICAV2_TENANT_NAME": "staging"}
        # Ensure ICAV2_PROFILE is not set
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("ICAV2_PROFILE", None)
            name = resolver._determine_profile_name()
        self.assertEqual(name, "staging")

    def test_defaults_to_default_profile(self):
        """Falls back to 'default' when no flag or env vars."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        with patch.dict(os.environ, {}, clear=True):
            name = resolver._determine_profile_name()
        self.assertEqual(name, "default")

    def test_empty_icav2_profile_is_ignored(self):
        """Empty ICAV2_PROFILE is treated as unset."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        with patch.dict(os.environ, {"ICAV2_PROFILE": ""}, clear=True):
            name = resolver._determine_profile_name()
        self.assertEqual(name, "default")

    def test_empty_icav2_tenant_name_is_ignored(self):
        """Empty ICAV2_TENANT_NAME is treated as unset."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        with patch.dict(os.environ, {"ICAV2_TENANT_NAME": ""}, clear=True):
            name = resolver._determine_profile_name()
        self.assertEqual(name, "default")


class TestResolve(unittest.TestCase):
    """Tests for resolve() method."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        self.tmp.write(SAMPLE_CONFIG)
        self.tmp.close()
        self.config_path = Path(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_resolve_default_profile(self):
        """Resolves the default profile correctly."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        with patch.dict(os.environ, {}, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.profile_name, "default")
        self.assertEqual(config.server_url, "ica.illumina.com")
        self.assertEqual(config.base_url, "https://ica.illumina.com/ica/rest")
        self.assertIsNone(config.access_token)
        self.assertEqual(config.project_id, "default-project-id")
        self.assertEqual(config.api_key, "default-api-key")
        self.assertEqual(config.output_format, "table")

    def test_resolve_named_profile_via_cli_flag(self):
        """Resolves a named profile when --profile is set."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile="staging")
        with patch.dict(os.environ, {}, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.profile_name, "staging")
        self.assertEqual(config.server_url, "staging.illumina.com")
        self.assertEqual(config.base_url, "https://staging.illumina.com/ica/rest")
        self.assertEqual(config.project_id, "staging-project-id")
        self.assertEqual(config.api_key, "staging-api-key")
        self.assertEqual(config.output_format, "json")

    def test_resolve_profile_not_found_exits_with_error(self):
        """sys.exit(1) called for missing profile with available profiles listed."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile="nonexistent")
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                resolver.resolve()
        self.assertEqual(ctx.exception.code, 1)

    def test_resolve_constructs_base_url_from_server_url(self):
        """base_url is https://{server_url}/ica/rest."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile="production")
        with patch.dict(os.environ, {}, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.base_url, "https://prod.illumina.com/ica/rest")

    def test_resolve_defaults_server_url(self):
        """If server_url absent, defaults to ica.illumina.com."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(MINIMAL_CONFIG)
        tmp.close()
        try:
            resolver = ProfileResolver(config_path=Path(tmp.name), cli_profile=None)
            with patch.dict(os.environ, {}, clear=True):
                config = resolver.resolve()
            self.assertEqual(config.server_url, "ica.illumina.com")
            self.assertEqual(config.base_url, "https://ica.illumina.com/ica/rest")
        finally:
            os.unlink(tmp.name)

    def test_resolve_defaults_output_format(self):
        """If output_format absent, defaults to 'table'."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(MINIMAL_CONFIG)
        tmp.close()
        try:
            resolver = ProfileResolver(config_path=Path(tmp.name), cli_profile=None)
            with patch.dict(os.environ, {}, clear=True):
                config = resolver.resolve()
            self.assertEqual(config.output_format, "table")
        finally:
            os.unlink(tmp.name)


class TestApplyEnvOverrides(unittest.TestCase):
    """Tests for _apply_env_overrides() method."""

    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        self.tmp.write(SAMPLE_CONFIG)
        self.tmp.close()
        self.config_path = Path(self.tmp.name)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_access_token_override(self):
        """ICAV2_ACCESS_TOKEN env var overrides access_token."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        env = {"ICAV2_ACCESS_TOKEN": "env-token-123"}
        with patch.dict(os.environ, env, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.access_token, "env-token-123")

    def test_project_id_override(self):
        """ICAV2_PROJECT_ID env var overrides project_id."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        env = {"ICAV2_PROJECT_ID": "env-project-id"}
        with patch.dict(os.environ, env, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.project_id, "env-project-id")

    def test_base_url_override(self):
        """ICAV2_BASE_URL env var overrides base_url."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        env = {"ICAV2_BASE_URL": "https://custom.example.com/api"}
        with patch.dict(os.environ, env, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.base_url, "https://custom.example.com/api")

    def test_empty_env_vars_do_not_override(self):
        """Empty env vars should not override profile values."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        env = {
            "ICAV2_ACCESS_TOKEN": "",
            "ICAV2_PROJECT_ID": "",
            "ICAV2_BASE_URL": "",
        }
        with patch.dict(os.environ, env, clear=True):
            config = resolver.resolve()
        self.assertIsNone(config.access_token)
        self.assertEqual(config.project_id, "default-project-id")
        self.assertEqual(config.base_url, "https://ica.illumina.com/ica/rest")

    def test_all_overrides_together(self):
        """All env overrides applied simultaneously."""
        resolver = ProfileResolver(config_path=self.config_path, cli_profile=None)
        env = {
            "ICAV2_ACCESS_TOKEN": "token-from-env",
            "ICAV2_PROJECT_ID": "project-from-env",
            "ICAV2_BASE_URL": "https://override.example.com/rest",
        }
        with patch.dict(os.environ, env, clear=True):
            config = resolver.resolve()
        self.assertEqual(config.access_token, "token-from-env")
        self.assertEqual(config.project_id, "project-from-env")
        self.assertEqual(config.base_url, "https://override.example.com/rest")


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling in resolve() method."""

    def test_config_file_missing_exits_with_error(self):
        """sys.exit(1) when config file does not exist."""
        resolver = ProfileResolver(
            config_path=Path("/nonexistent/path/config"),
            cli_profile=None,
        )
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit) as ctx:
                resolver.resolve()
        self.assertEqual(ctx.exception.code, 1)

    def test_config_file_missing_prints_actionable_message(self):
        """Error message includes path and suggests 'icav2 configure set'."""
        import io
        resolver = ProfileResolver(
            config_path=Path("/nonexistent/path/config"),
            cli_profile=None,
        )
        with patch.dict(os.environ, {}, clear=True):
            with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                with self.assertRaises(SystemExit):
                    resolver.resolve()
        output = mock_stderr.getvalue()
        self.assertIn("/nonexistent/path/config", output)
        self.assertIn("icav2 configure set", output)

    def test_profile_not_found_prints_available_profiles(self):
        """Error message lists available profiles when requested profile not found."""
        import io
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(SAMPLE_CONFIG)
        tmp.close()
        try:
            resolver = ProfileResolver(
                config_path=Path(tmp.name),
                cli_profile="nonexistent",
            )
            with patch.dict(os.environ, {}, clear=True):
                with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                    with self.assertRaises(SystemExit):
                        resolver.resolve()
            output = mock_stderr.getvalue()
            self.assertIn("nonexistent", output)
            self.assertIn("Available profiles", output)
            # Should list the actual profiles
            self.assertIn("default", output)
            self.assertIn("staging", output)
            self.assertIn("production", output)
        finally:
            os.unlink(tmp.name)

    def test_no_default_profile_and_no_env_var_exits_with_error(self):
        """sys.exit(1) when no default profile exists and no env vars set."""
        # Config with only named profiles, no [default]
        config_content = """\
[profile staging]
server_url = staging.illumina.com
x_api_key = staging-key
"""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(config_content)
        tmp.close()
        try:
            resolver = ProfileResolver(
                config_path=Path(tmp.name),
                cli_profile=None,
            )
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SystemExit) as ctx:
                    resolver.resolve()
            self.assertEqual(ctx.exception.code, 1)
        finally:
            os.unlink(tmp.name)

    def test_no_default_profile_prints_available_and_suggestion(self):
        """Error message suggests setting ICAV2_PROFILE or running configure set."""
        import io
        config_content = """\
[profile staging]
server_url = staging.illumina.com
x_api_key = staging-key

[profile production]
server_url = prod.illumina.com
x_api_key = prod-key
"""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(config_content)
        tmp.close()
        try:
            resolver = ProfileResolver(
                config_path=Path(tmp.name),
                cli_profile=None,
            )
            with patch.dict(os.environ, {}, clear=True):
                with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                    with self.assertRaises(SystemExit):
                        resolver.resolve()
            output = mock_stderr.getvalue()
            self.assertIn("No default profile configured", output)
            self.assertIn("staging", output)
            self.assertIn("production", output)
            self.assertIn("ICAV2_PROFILE", output)
            self.assertIn("icav2 configure set", output)
        finally:
            os.unlink(tmp.name)

    def test_empty_config_file_exits_with_no_profiles_error(self):
        """sys.exit(1) when config file has no profiles at all."""
        # Config file that exists but has no sections (only comments/blank lines)
        config_content = "# This config file is empty\n\n"
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(config_content)
        tmp.close()
        try:
            resolver = ProfileResolver(
                config_path=Path(tmp.name),
                cli_profile=None,
            )
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SystemExit) as ctx:
                    resolver.resolve()
            self.assertEqual(ctx.exception.code, 1)
        finally:
            os.unlink(tmp.name)

    def test_empty_config_file_prints_no_profiles_message(self):
        """Error message tells user to run 'icav2 configure set' when no profiles."""
        import io
        config_content = "# Empty config\n"
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(config_content)
        tmp.close()
        try:
            resolver = ProfileResolver(
                config_path=Path(tmp.name),
                cli_profile=None,
            )
            with patch.dict(os.environ, {}, clear=True):
                with patch('sys.stderr', new_callable=io.StringIO) as mock_stderr:
                    with self.assertRaises(SystemExit):
                        resolver.resolve()
            output = mock_stderr.getvalue()
            self.assertIn("No profiles configured", output)
            self.assertIn("icav2 configure set", output)
        finally:
            os.unlink(tmp.name)

    def test_config_file_unreadable_exits_with_error(self):
        """sys.exit(1) when config file exists but is not readable."""
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.config', delete=False)
        tmp.write(SAMPLE_CONFIG)
        tmp.close()
        # Remove read permissions
        os.chmod(tmp.name, 0o000)
        try:
            resolver = ProfileResolver(
                config_path=Path(tmp.name),
                cli_profile=None,
            )
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(SystemExit) as ctx:
                    resolver.resolve()
            self.assertEqual(ctx.exception.code, 1)
        finally:
            # Restore permissions for cleanup
            os.chmod(tmp.name, 0o600)
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
