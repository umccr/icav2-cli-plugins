#!/usr/bin/env python3
"""
Unit tests for CLI lazy import and startup performance.

Tests that:
- help/version commands do not import heavy libraries
- --profile flag is parsed correctly from global args
- Unknown commands are delegated (would go to _icav2 binary)

Requirements: 6.4, 6.5, 6.7
"""

import sys
import subprocess
import pytest


# Heavy libraries that should NOT be imported during help/version
HEAVY_LIBRARIES = [
    "wrapica",
    "libica",
    "pandas",
    "cwl_utils",
    "cwltool",
    "nf_core",
    "matplotlib",
    "bs4",  # beautifulsoup4 imports as bs4
]


def _remove_heavy_libs_from_sys_modules():
    """Remove heavy libs from sys.modules to start with a clean state."""
    for lib in HEAVY_LIBRARIES:
        # Remove the lib and any submodules
        keys_to_remove = [k for k in sys.modules if k == lib or k.startswith(f"{lib}.")]
        for key in keys_to_remove:
            del sys.modules[key]


class TestHelpDoesNotImportHeavyLibraries:
    """Test that running 'help' does not import heavy libraries."""

    def test_help_no_heavy_imports(self, monkeypatch):
        """After running help command, verify heavy libs NOT in sys.modules."""
        # Clean state
        _remove_heavy_libs_from_sys_modules()

        # Simulate running: icav2-cli-plugins help
        monkeypatch.setattr(sys, "argv", ["icav2-cli-plugins", "help"])

        # Need to re-import dispatch fresh to avoid stale module state
        from icav2_cli_plugins.utils.cli import _dispatch

        with pytest.raises(SystemExit) as exc_info:
            _dispatch()

        assert exc_info.value.code == 0

        # Check that heavy libraries were NOT imported
        for lib in HEAVY_LIBRARIES:
            matching_modules = [k for k in sys.modules if k == lib or k.startswith(f"{lib}.")]
            assert matching_modules == [], (
                f"Heavy library '{lib}' was imported during 'help' command: {matching_modules}"
            )


class TestVersionDoesNotImportHeavyLibraries:
    """Test that running 'version' does not import heavy libraries."""

    def test_version_no_heavy_imports(self, monkeypatch):
        """After running version command, verify heavy libs NOT in sys.modules."""
        # Clean state
        _remove_heavy_libs_from_sys_modules()

        # Simulate running: icav2-cli-plugins version
        monkeypatch.setattr(sys, "argv", ["icav2-cli-plugins", "version"])

        from icav2_cli_plugins.utils.cli import _dispatch

        with pytest.raises(SystemExit) as exc_info:
            _dispatch()

        assert exc_info.value.code == 0

        # Check that heavy libraries were NOT imported
        for lib in HEAVY_LIBRARIES:
            matching_modules = [k for k in sys.modules if k == lib or k.startswith(f"{lib}.")]
            assert matching_modules == [], (
                f"Heavy library '{lib}' was imported during 'version' command: {matching_modules}"
            )


class TestProfileFlagParsing:
    """Test that the --profile flag is parsed correctly."""

    def test_profile_flag_parsed_from_global_args(self, monkeypatch):
        """Test that --profile flag value is correctly extracted from global args."""
        from docopt import docopt
        from icav2_cli_plugins.utils.cli import __doc__ as cli_doc
        from icav2_cli_plugins.utils import version

        # Simulate: icav2-cli-plugins --profile my-tenant help
        argv = ["--profile", "my-tenant", "help"]
        global_args = docopt(cli_doc, argv, version=version, options_first=True)

        assert global_args.get("--profile") == "my-tenant"

    def test_profile_flag_none_when_absent(self, monkeypatch):
        """Test that --profile is None when not provided."""
        from docopt import docopt
        from icav2_cli_plugins.utils.cli import __doc__ as cli_doc
        from icav2_cli_plugins.utils import version

        # Simulate: icav2-cli-plugins help
        argv = ["help"]
        global_args = docopt(cli_doc, argv, version=version, options_first=True)

        assert global_args.get("--profile") is None

    def test_profile_flag_with_various_names(self, monkeypatch):
        """Test --profile works with different valid profile name formats."""
        from docopt import docopt
        from icav2_cli_plugins.utils.cli import __doc__ as cli_doc
        from icav2_cli_plugins.utils import version

        test_profiles = ["default", "my-tenant", "prod_us", "tenant123"]

        for profile_name in test_profiles:
            argv = ["--profile", profile_name, "help"]
            global_args = docopt(cli_doc, argv, version=version, options_first=True)
            assert global_args.get("--profile") == profile_name, (
                f"Expected profile '{profile_name}', got '{global_args.get('--profile')}'"
            )


class TestUnknownCommandDelegation:
    """Test that unknown commands would be delegated to _icav2 binary."""

    def test_unknown_command_attempts_delegation(self, monkeypatch):
        """Test that an unknown command tries to delegate to _icav2 binary.

        Since the _icav2 binary won't exist in test environment, and
        _resolve_profile_and_token will fail without config, we verify
        the command routing logic recognizes it's not a plugin command.
        """
        from icav2_cli_plugins.utils.cli import COMMAND_MODULE_MAP

        unknown_commands = ["projects", "data", "unknown-cmd", "list"]

        for cmd in unknown_commands:
            assert cmd not in COMMAND_MODULE_MAP, (
                f"Command '{cmd}' should not be in COMMAND_MODULE_MAP "
                f"(it should be delegated to _icav2)"
            )

    def test_known_commands_are_in_module_map(self):
        """Test that plugin commands are properly registered."""
        from icav2_cli_plugins.utils.cli import COMMAND_MODULE_MAP

        expected_commands = [
            "bundles",
            "pipelines",
            "projectanalyses",
            "projectdata",
            "projectpipelines",
            "tenants",
            "configure",
        ]

        for cmd in expected_commands:
            assert cmd in COMMAND_MODULE_MAP, (
                f"Plugin command '{cmd}' should be in COMMAND_MODULE_MAP"
            )

    def test_lazy_import_returns_none_for_unknown(self):
        """Test that lazy_import_command returns None for unknown commands."""
        from icav2_cli_plugins.utils.cli import lazy_import_command

        result = lazy_import_command("nonexistent-command")
        assert result is None

    def test_lazy_import_returns_module_for_known(self):
        """Test that lazy_import_command returns a module for known commands."""
        from icav2_cli_plugins.utils.cli import lazy_import_command

        # configure is a lightweight module we can safely import in tests
        result = lazy_import_command("configure")
        assert result is not None
        assert hasattr(result, "get_configure_subcommand")


class TestHelpVersionOutput:
    """Test that help and version produce expected output."""

    def test_help_prints_usage(self, monkeypatch, capsys):
        """Test that help command prints CLI usage documentation."""
        monkeypatch.setattr(sys, "argv", ["icav2-cli-plugins", "help"])

        from icav2_cli_plugins.utils.cli import _dispatch

        with pytest.raises(SystemExit) as exc_info:
            _dispatch()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        # Should contain usage information
        assert "Usage:" in captured.out or "icav2-cli-plugins" in captured.out

    def test_version_prints_version_string(self, monkeypatch, capsys):
        """Test that version command prints the version string."""
        monkeypatch.setattr(sys, "argv", ["icav2-cli-plugins", "version"])

        from icav2_cli_plugins.utils.cli import _dispatch
        from icav2_cli_plugins.utils import version

        with pytest.raises(SystemExit) as exc_info:
            _dispatch()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert version in captured.out
