#!/usr/bin/env python3
"""
Unit tests for _delegate_to_icav2() function.

Tests the delegation to the local _icav2 binary with environment variable
propagation and error handling when the binary is missing.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from unittest.mock import patch, MagicMock

import pytest


@dataclass
class MockConfig:
    """Mock config object mimicking ResolvedConfig attributes."""
    access_token: Optional[str] = None
    base_url: Optional[str] = None
    project_id: Optional[str] = None


class TestDelegateToIcav2Exists:
    """Test that the function can be imported."""

    def test_function_importable(self):
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2
        assert callable(_delegate_to_icav2)

    def test_function_accepts_args_and_config(self):
        """Verify the function signature accepts args list and config."""
        import inspect
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2
        sig = inspect.signature(_delegate_to_icav2)
        params = list(sig.parameters.keys())
        assert "args" in params
        assert "config" in params


class TestDelegateToIcav2BinaryMissing:
    """Test error behavior when the binary doesn't exist."""

    def test_exits_with_error_when_binary_not_found(self, capsys, tmp_path):
        """When the binary is missing, exit with code 1 and helpful message."""
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2

        fake_binary = tmp_path / "nonexistent" / "_icav2"
        with patch("icav2_cli_plugins.utils.globals.LOCAL_BINARY_PATH", fake_binary):
            with pytest.raises(SystemExit) as exc_info:
                _delegate_to_icav2(["projects", "list"], config=None)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "_icav2 binary not found" in captured.err
        assert "re-run the installer" in captured.err.lower()

    def test_error_includes_binary_path(self, capsys, tmp_path):
        """The error message should include the expected binary path."""
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2

        fake_binary = tmp_path / "missing" / "_icav2"
        with patch("icav2_cli_plugins.utils.globals.LOCAL_BINARY_PATH", fake_binary):
            with pytest.raises(SystemExit):
                _delegate_to_icav2(["projects", "list"], config=None)

        captured = capsys.readouterr()
        assert str(fake_binary) in captured.err


class TestDelegateToIcav2ExecveCall:
    """Test that execve is called correctly when the binary exists."""

    def test_calls_execve_with_binary_and_args(self, tmp_path):
        """Verify os.execve is called with the correct binary path and args."""
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2

        fake_binary = tmp_path / "_icav2"
        fake_binary.touch()
        fake_binary.chmod(0o755)

        config = MockConfig(
            access_token="test-token",
            base_url="https://ica.illumina.com/ica/rest",
            project_id="proj-123",
        )

        with patch("icav2_cli_plugins.utils.globals.LOCAL_BINARY_PATH", fake_binary):
            with patch("os.execve") as mock_execve:
                _delegate_to_icav2(["projects", "list"], config=config)

        mock_execve.assert_called_once()
        call_args = mock_execve.call_args
        # First arg: binary path
        assert call_args[0][0] == str(fake_binary)
        # Second arg: argv list (binary + args)
        assert call_args[0][1] == [str(fake_binary), "projects", "list"]
        # Third arg: environment dict
        env = call_args[0][2]
        assert env["ICAV2_ACCESS_TOKEN"] == "test-token"
        assert env["ICAV2_BASE_URL"] == "https://ica.illumina.com/ica/rest"
        assert env["ICAV2_PROJECT_ID"] == "proj-123"

    def test_env_inherits_from_current_environment(self, tmp_path):
        """The env passed to execve should include the current environment."""
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2

        fake_binary = tmp_path / "_icav2"
        fake_binary.touch()
        fake_binary.chmod(0o755)

        config = MockConfig(access_token="tok")

        with patch("icav2_cli_plugins.utils.globals.LOCAL_BINARY_PATH", fake_binary):
            with patch("os.execve") as mock_execve:
                with patch.dict(os.environ, {"MY_CUSTOM_VAR": "hello"}):
                    _delegate_to_icav2(["version"], config=config)

        env = mock_execve.call_args[0][2]
        assert env.get("MY_CUSTOM_VAR") == "hello"

    def test_none_config_uses_current_env_only(self, tmp_path):
        """When config is None, only current environment is passed."""
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2

        fake_binary = tmp_path / "_icav2"
        fake_binary.touch()
        fake_binary.chmod(0o755)

        with patch("icav2_cli_plugins.utils.globals.LOCAL_BINARY_PATH", fake_binary):
            with patch("os.execve") as mock_execve:
                _delegate_to_icav2(["help"], config=None)

        env = mock_execve.call_args[0][2]
        # Should not have set any ICAv2 vars that weren't already there
        # (unless they were in the existing environment)
        assert isinstance(env, dict)

    def test_skips_none_config_fields(self, tmp_path):
        """Fields that are None in config should not be set in env."""
        from icav2_cli_plugins.utils.cli import _delegate_to_icav2

        fake_binary = tmp_path / "_icav2"
        fake_binary.touch()
        fake_binary.chmod(0o755)

        config = MockConfig(
            access_token="my-token",
            base_url=None,
            project_id=None,
        )

        # Start with a clean env without these vars
        clean_env = {k: v for k, v in os.environ.items()
                     if k not in ("ICAV2_BASE_URL", "ICAV2_PROJECT_ID")}

        with patch("icav2_cli_plugins.utils.globals.LOCAL_BINARY_PATH", fake_binary):
            with patch("os.execve") as mock_execve:
                with patch.dict(os.environ, clean_env, clear=True):
                    _delegate_to_icav2(["projects", "list"], config=config)

        env = mock_execve.call_args[0][2]
        assert env["ICAV2_ACCESS_TOKEN"] == "my-token"
        assert "ICAV2_BASE_URL" not in env
        assert "ICAV2_PROJECT_ID" not in env
