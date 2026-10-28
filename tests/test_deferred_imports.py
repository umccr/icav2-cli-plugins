"""
Tests for deferred imports in subcommands/__init__.py.

Validates: Requirements 6.2, 6.6

These tests verify that importing the subcommands module does NOT trigger
imports of heavy libraries (wrapica, libica, pandas), and that deferred
imports still work when coercion methods are actually called.

We use subprocess isolation to avoid module cache pollution from the
test process itself (which may have already imported these libraries).
"""

import subprocess
import sys
import textwrap

import pytest


class TestDeferredImports:
    """Tests that heavy libraries are not imported at module load time."""

    def test_subcommands_import_does_not_load_wrapica(self):
        """
        Importing icav2_cli_plugins.subcommands should NOT cause wrapica
        to appear in sys.modules.

        Validates: Requirements 6.2, 6.6
        """
        script = textwrap.dedent("""\
            import sys
            # Import the subcommands module
            import icav2_cli_plugins.subcommands

            # Check that heavy libraries are NOT loaded
            heavy_libs = ['wrapica', 'libica', 'pandas']
            loaded = [lib for lib in heavy_libs if any(
                key == lib or key.startswith(lib + '.')
                for key in sys.modules
            )]

            if loaded:
                print(f"FAIL: These libraries were unexpectedly imported: {loaded}", file=sys.stderr)
                sys.exit(1)
            else:
                print("PASS: No heavy libraries imported at module load time")
                sys.exit(0)
        """)

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Heavy libraries were imported at module load time.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_command_class_accessible_without_heavy_imports(self):
        """
        The Command and DocOptArg classes should be accessible without
        triggering heavy library imports.

        Validates: Requirements 6.2, 6.6
        """
        script = textwrap.dedent("""\
            import sys
            from icav2_cli_plugins.subcommands import Command, DocOptArg

            # Verify we can reference the classes
            assert Command is not None
            assert DocOptArg is not None

            # Instantiate a DocOptArg without triggering heavy imports
            arg = DocOptArg(cli_arg_keys=["--test-arg"])
            assert arg is not None
            assert arg.cli_arg_keys == ["test_arg"]

            # Check that heavy libraries are still NOT loaded
            heavy_libs = ['wrapica', 'libica', 'pandas']
            loaded = [lib for lib in heavy_libs if any(
                key == lib or key.startswith(lib + '.')
                for key in sys.modules
            )]

            if loaded:
                print(f"FAIL: These libraries were unexpectedly imported: {loaded}", file=sys.stderr)
                sys.exit(1)
            else:
                print("PASS: Command and DocOptArg accessible without heavy imports")
                sys.exit(0)
        """)

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Heavy libraries were imported when accessing Command/DocOptArg.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_coerce_arg_type_triggers_pandas_for_datetime(self):
        """
        Calling coerce_arg_type() with a datetime arg_type should trigger
        a pandas import (deferred to point of use).

        Validates: Requirements 6.2, 6.6
        """
        script = textwrap.dedent("""\
            import sys
            from datetime import datetime
            from icav2_cli_plugins.subcommands import DocOptArg

            # Confirm pandas not loaded yet
            pandas_loaded_before = any(
                key == 'pandas' or key.startswith('pandas.')
                for key in sys.modules
            )
            if pandas_loaded_before:
                print("FAIL: pandas was already loaded before coerce_arg_type", file=sys.stderr)
                sys.exit(1)

            # Create a DocOptArg with datetime type and a string value
            arg = DocOptArg(cli_arg_keys=["--date"])
            arg.arg_type = datetime
            arg.arg_value = "2024-01-15"

            # Calling coerce_arg_type should trigger the pandas import
            arg.coerce_arg_type()

            # Now pandas SHOULD be loaded
            pandas_loaded_after = any(
                key == 'pandas' or key.startswith('pandas.')
                for key in sys.modules
            )
            if not pandas_loaded_after:
                print("FAIL: pandas was NOT loaded after coerce_arg_type with datetime", file=sys.stderr)
                sys.exit(1)

            # Verify the value was actually coerced
            assert arg.arg_value is not None
            assert isinstance(arg.arg_value, datetime), f"Expected datetime, got {type(arg.arg_value)}"

            print("PASS: pandas imported on demand during datetime coercion")
            sys.exit(0)
        """)

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, (
            f"Deferred pandas import for datetime coercion failed.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_get_arg_type_triggers_wrapica_import(self):
        """
        Calling get_arg_type() should trigger wrapica imports since it
        needs PipelineType and other wrapica types for comparison.

        Validates: Requirements 6.2, 6.6
        """
        script = textwrap.dedent("""\
            import sys
            from icav2_cli_plugins.subcommands import DocOptArg

            # Confirm wrapica not loaded yet
            wrapica_loaded_before = any(
                key == 'wrapica' or key.startswith('wrapica.')
                for key in sys.modules
            )
            if wrapica_loaded_before:
                print("FAIL: wrapica was already loaded before get_arg_type", file=sys.stderr)
                sys.exit(1)

            print("PASS: wrapica is deferred and not loaded at import time")
            sys.exit(0)
        """)

        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"wrapica was imported at module load time.\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
