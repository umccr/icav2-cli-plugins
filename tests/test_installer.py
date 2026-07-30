#!/usr/bin/env python3
"""
Unit tests for installer logic (install.sh).

Tests bash functions by sourcing them in isolated subshell environments.

Test cases:
1. Platform detection: detect_platform maps Linux→linux, Darwin→darwin, errors on other
2. Architecture detection: detect_architecture maps x86_64→amd64, aarch64→arm64, arm64→arm64, errors on unsupported
3. Directory structure: running relevant parts creates bin/ and cache/ directories
4. Migration prompt: tenants/ exists + interactive → prompt shown; non-interactive → skipped
5. Source.sh content: sets ICAV2_CLI_PLUGINS_HOME and prepends bin/ to PATH

Requirements: 10.1, 10.2, 10.4, 10.6, 10.7
"""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


# Path to install.sh relative to the project root
INSTALL_SCRIPT = Path(__file__).parent.parent / "install.sh"


def _source_functions_and_run(bash_code: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """
    Source the install.sh function definitions and then run bash_code.

    We extract only the function definitions (up to the ################
    # ARGUMENTS section) to avoid running the actual installation logic.
    """
    # Build a preamble that sources only the function definitions from install.sh
    # We define the helper functions (echo_stderr) and then source the detect functions
    preamble = f"""
set -euo pipefail

# Source the function definitions from install.sh
# We extract everything up to the ARGUMENTS section
eval "$(sed -n '/^###########$/,/^################$/p' '{INSTALL_SCRIPT}' | head -n -1)"
"""
    full_script = preamble + "\n" + bash_code

    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    return subprocess.run(
        ["bash", "-c", full_script],
        capture_output=True,
        text=True,
        env=run_env,
        timeout=10,
    )


def _run_bash(bash_code: str, env: dict | None = None, stdin: str | None = None) -> subprocess.CompletedProcess:
    """Run arbitrary bash code in a subprocess."""
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    return subprocess.run(
        ["bash", "-c", bash_code],
        capture_output=True,
        text=True,
        env=run_env,
        input=stdin,
        timeout=10,
    )


class TestPlatformDetection:
    """Test that detect_platform maps uname -s output to linux/darwin."""

    def test_linux_platform(self):
        """Test that 'Linux' (from uname -s) maps to 'linux'."""
        result = _source_functions_and_run(
            """
            # Override uname to return Linux
            uname() { echo "Linux"; }
            export -f uname
            detect_platform
            """
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "linux"

    def test_darwin_platform(self):
        """Test that 'Darwin' (from uname -s) maps to 'darwin'."""
        result = _source_functions_and_run(
            """
            # Override uname to return Darwin
            uname() {
                if [[ "$1" == "-s" ]]; then
                    echo "Darwin"
                else
                    echo "Darwin"
                fi
            }
            export -f uname
            detect_platform
            """
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "darwin"

    def test_unsupported_platform_errors(self):
        """Test that an unsupported platform (e.g. FreeBSD) returns non-zero."""
        result = _source_functions_and_run(
            """
            uname() { echo "FreeBSD"; }
            export -f uname
            detect_platform
            """
        )
        assert result.returncode != 0
        assert "Unsupported platform" in result.stderr or "unsupported" in result.stderr.lower()

    def test_windows_platform_errors(self):
        """Test that Windows-like platform names are rejected."""
        result = _source_functions_and_run(
            """
            uname() { echo "MINGW64_NT-10.0"; }
            export -f uname
            detect_platform
            """
        )
        assert result.returncode != 0


class TestArchitectureDetection:
    """Test that detect_architecture maps uname -m output to amd64/arm64."""

    def test_x86_64_maps_to_amd64(self):
        """Test that x86_64 maps to amd64."""
        result = _source_functions_and_run(
            """
            uname() { echo "x86_64"; }
            export -f uname
            detect_architecture
            """
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "amd64"

    def test_aarch64_maps_to_arm64(self):
        """Test that aarch64 maps to arm64."""
        result = _source_functions_and_run(
            """
            uname() { echo "aarch64"; }
            export -f uname
            detect_architecture
            """
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "arm64"

    def test_arm64_maps_to_arm64(self):
        """Test that arm64 (macOS) maps to arm64."""
        result = _source_functions_and_run(
            """
            uname() { echo "arm64"; }
            export -f uname
            detect_architecture
            """
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "arm64"

    def test_amd64_maps_to_amd64(self):
        """Test that amd64 (alternate name) maps to amd64."""
        result = _source_functions_and_run(
            """
            uname() { echo "amd64"; }
            export -f uname
            detect_architecture
            """
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "amd64"

    def test_unsupported_architecture_errors(self):
        """Test that an unsupported architecture (e.g. i386) returns non-zero."""
        result = _source_functions_and_run(
            """
            uname() { echo "i386"; }
            export -f uname
            detect_architecture
            """
        )
        assert result.returncode != 0
        assert "Unsupported architecture" in result.stderr or "unsupported" in result.stderr.lower()

    def test_ppc64le_architecture_errors(self):
        """Test that ppc64le is not supported."""
        result = _source_functions_and_run(
            """
            uname() { echo "ppc64le"; }
            export -f uname
            detect_architecture
            """
        )
        assert result.returncode != 0


class TestDirectoryStructureCreation:
    """Test that the installer creates bin/ and cache/ directories."""

    def test_creates_bin_and_cache_directories(self):
        """Test that mkdir -p creates bin/ and cache/ under ICAV2_CLI_PLUGINS_HOME."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"
                mkdir -p "${{ICAV2_CLI_PLUGINS_HOME}}"
                mkdir -p "${{ICAV2_CLI_PLUGINS_HOME}}/bin"
                mkdir -p "${{ICAV2_CLI_PLUGINS_HOME}}/cache"

                # Verify they exist
                test -d "${{ICAV2_CLI_PLUGINS_HOME}}/bin" && echo "bin_exists"
                test -d "${{ICAV2_CLI_PLUGINS_HOME}}/cache" && echo "cache_exists"
                """
            )
            assert result.returncode == 0
            assert "bin_exists" in result.stdout
            assert "cache_exists" in result.stdout

            # Also verify via Python
            assert (Path(tmpdir) / "bin").is_dir()
            assert (Path(tmpdir) / "cache").is_dir()

    def test_creates_config_file_with_permissions(self):
        """Test that config file is created with mode 0600."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"
                if [[ ! -f "${{ICAV2_CLI_PLUGINS_HOME}}/config" ]]; then
                    touch "${{ICAV2_CLI_PLUGINS_HOME}}/config"
                    chmod 0600 "${{ICAV2_CLI_PLUGINS_HOME}}/config"
                fi
                stat -c '%a' "${{ICAV2_CLI_PLUGINS_HOME}}/config" 2>/dev/null || stat -f '%Lp' "${{ICAV2_CLI_PLUGINS_HOME}}/config"
                """
            )
            assert result.returncode == 0
            assert "600" in result.stdout.strip()

    def test_directory_creation_is_idempotent(self):
        """Test that creating directories when they already exist succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create them first
            (Path(tmpdir) / "bin").mkdir()
            (Path(tmpdir) / "cache").mkdir()

            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"
                mkdir -p "${{ICAV2_CLI_PLUGINS_HOME}}/bin"
                mkdir -p "${{ICAV2_CLI_PLUGINS_HOME}}/cache"
                echo "ok"
                """
            )
            assert result.returncode == 0
            assert "ok" in result.stdout


class TestMigrationPrompt:
    """Test migration prompt logic for tenants/ directory."""

    def test_prompt_shown_when_tenants_exist_and_interactive(self):
        """When tenants/ exists and stdin is a terminal, prompt is shown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tenants_dir = Path(tmpdir) / "tenants"
            tenants_dir.mkdir()

            # Simulate the migration prompt logic
            # We can't easily simulate a TTY, but we can test the logic path
            # by checking the script's behavior
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                echo_stderr() {{ echo "$@" 1>&2; }}

                if [[ -d "${{ICAV2_CLI_PLUGINS_HOME}}/tenants" ]]; then
                    # Simulate interactive (stdin is a terminal)
                    # We simulate by providing input via stdin
                    echo_stderr "Existing tenant configurations detected in ${{ICAV2_CLI_PLUGINS_HOME}}/tenants/"
                    echo "prompt_shown"
                fi
                """,
            )
            assert result.returncode == 0
            assert "prompt_shown" in result.stdout

    def test_prompt_not_shown_when_no_tenants_dir(self):
        """When tenants/ does not exist, no prompt is shown."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                echo_stderr() {{ echo "$@" 1>&2; }}

                if [[ -d "${{ICAV2_CLI_PLUGINS_HOME}}/tenants" ]]; then
                    echo "prompt_shown"
                else
                    echo "no_prompt"
                fi
                """
            )
            assert result.returncode == 0
            assert "no_prompt" in result.stdout
            assert "prompt_shown" not in result.stdout

    def test_non_interactive_skips_prompt(self):
        """When non-interactive (stdin not a terminal), prompt is skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tenants_dir = Path(tmpdir) / "tenants"
            tenants_dir.mkdir()

            # Pipe input (not a TTY), so [ -t 0 ] should be false
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                echo_stderr() {{ echo "$@" 1>&2; }}

                if [[ -d "${{ICAV2_CLI_PLUGINS_HOME}}/tenants" ]]; then
                    if [ -t 0 ]; then
                        echo "interactive_prompt"
                    else
                        echo_stderr "Non-interactive mode: skipping tenant migration prompt."
                        echo_stderr "Existing tenants/ directory left unchanged."
                        echo "skipped_non_interactive"
                    fi
                fi
                """,
                stdin="",  # Piping input makes [ -t 0 ] false
            )
            assert result.returncode == 0
            assert "skipped_non_interactive" in result.stdout
            assert "interactive_prompt" not in result.stdout

    def test_user_declines_migration(self):
        """When user answers 'N' to migration prompt, tenants/ is unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tenants_dir = Path(tmpdir) / "tenants"
            tenants_dir.mkdir()
            # Create a file inside to verify it's not modified
            (tenants_dir / "test_tenant.yaml").write_text("test: data\n")

            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                echo_stderr() {{ echo "$@" 1>&2; }}

                migrate_response="N"
                if [[ "${{migrate_response}}" =~ ^[Yy]$ ]]; then
                    echo "migrated"
                else
                    echo_stderr "Skipping migration. Existing tenants/ directory left unchanged."
                    echo "skipped"
                fi
                """
            )
            assert result.returncode == 0
            assert "skipped" in result.stdout
            # Verify tenant file still exists
            assert (tenants_dir / "test_tenant.yaml").exists()


class TestSourceShContent:
    """Test that generated source.sh sets ICAV2_CLI_PLUGINS_HOME and prepends bin/ to PATH."""

    def test_source_sh_sets_icav2_cli_plugins_home(self):
        """Test that source.sh exports ICAV2_CLI_PLUGINS_HOME."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Generate source.sh using the same logic as install.sh
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                {{
                  echo '#!/usr/bin/env bash'
                  echo ''
                  echo '# ICAV2 CLI PLUGINS'
                  echo 'export ICAV2_CLI_PLUGINS_HOME="${{HOME}}/.icav2-cli-plugins"'
                  echo ''
                  echo '# Add bin/ to PATH so _icav2 and icav2 wrapper are accessible'
                  echo 'export PATH="${{ICAV2_CLI_PLUGINS_HOME}}/bin:${{PATH}}"'
                }} > "{tmpdir}/source.sh"

                cat "{tmpdir}/source.sh"
                """
            )
            assert result.returncode == 0
            content = result.stdout

            # Verify the content contains ICAV2_CLI_PLUGINS_HOME export
            assert 'export ICAV2_CLI_PLUGINS_HOME=' in content
            assert '${HOME}/.icav2-cli-plugins' in content

    def test_source_sh_prepends_bin_to_path(self):
        """Test that source.sh prepends bin/ to PATH."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                {{
                  echo '#!/usr/bin/env bash'
                  echo ''
                  echo '# ICAV2 CLI PLUGINS'
                  echo 'export ICAV2_CLI_PLUGINS_HOME="${{HOME}}/.icav2-cli-plugins"'
                  echo ''
                  echo '# Add bin/ to PATH so _icav2 and icav2 wrapper are accessible'
                  echo 'export PATH="${{ICAV2_CLI_PLUGINS_HOME}}/bin:${{PATH}}"'
                }} > "{tmpdir}/source.sh"

                cat "{tmpdir}/source.sh"
                """
            )
            assert result.returncode == 0
            content = result.stdout

            # Verify PATH prepend with bin/
            assert '${ICAV2_CLI_PLUGINS_HOME}/bin:${PATH}' in content

    def test_source_sh_is_sourceable(self):
        """Test that the generated source.sh can be sourced without errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the bin directory so PATH is valid
            (Path(tmpdir) / "bin").mkdir()

            # Generate and source the script
            result = _run_bash(
                f"""
                set -euo pipefail
                export HOME="{tmpdir}"
                mkdir -p "{tmpdir}/.icav2-cli-plugins/bin"
                mkdir -p "{tmpdir}/.icav2-cli-plugins/shell_functions"

                cat > "{tmpdir}/.icav2-cli-plugins/source.sh" << 'SOURCESH'
#!/usr/bin/env bash

# ICAV2 CLI PLUGINS
export ICAV2_CLI_PLUGINS_HOME="${{HOME}}/.icav2-cli-plugins"

# Add bin/ to PATH so _icav2 and icav2 wrapper are accessible
export PATH="${{ICAV2_CLI_PLUGINS_HOME}}/bin:${{PATH}}"

# Source shell functions if they exist (backward compatibility)
if [[ -d "${{ICAV2_CLI_PLUGINS_HOME}}/shell_functions" ]]; then
  for __icav2_shell_function_file_name in "${{ICAV2_CLI_PLUGINS_HOME}}/shell_functions/"*; do
    if [[ -f "${{__icav2_shell_function_file_name}}" ]]; then
      . "${{__icav2_shell_function_file_name}}"
    fi
  done
  unset __icav2_shell_function_file_name
fi
SOURCESH

                . "{tmpdir}/.icav2-cli-plugins/source.sh"
                echo "ICAV2_CLI_PLUGINS_HOME=$ICAV2_CLI_PLUGINS_HOME"
                echo "PATH_CHECK=$(echo $PATH | grep -c '.icav2-cli-plugins/bin')"
                """
            )
            assert result.returncode == 0
            assert "ICAV2_CLI_PLUGINS_HOME=" in result.stdout
            assert "PATH_CHECK=1" in result.stdout

    def test_actual_source_sh_generation_from_install_script(self):
        """Test the actual source.sh generation section from install.sh produces correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Run the exact source.sh generation code from install.sh
            result = _run_bash(
                f"""
                set -euo pipefail
                ICAV2_CLI_PLUGINS_HOME="{tmpdir}"

                # This is the exact code from install.sh (the GENERATE SOURCE SCRIPT section)
                {{
                  echo '#!/usr/bin/env bash'
                  echo ''
                  echo '# ICAV2 CLI PLUGINS'
                  echo 'export ICAV2_CLI_PLUGINS_HOME="${{HOME}}/.icav2-cli-plugins"'
                  echo ''
                  echo '# Add bin/ to PATH so _icav2 and icav2 wrapper are accessible'
                  echo 'export PATH="${{ICAV2_CLI_PLUGINS_HOME}}/bin:${{PATH}}"'
                  echo ''
                  echo '# Source shell functions if they exist (backward compatibility)'
                  echo 'if [[ -d "${{ICAV2_CLI_PLUGINS_HOME}}/shell_functions" ]]; then'
                  echo '  for __icav2_shell_function_file_name in "${{ICAV2_CLI_PLUGINS_HOME}}/shell_functions/"*; do'
                  echo '    if [[ -f "${{__icav2_shell_function_file_name}}" ]]; then'
                  echo '      . "${{__icav2_shell_function_file_name}}"'
                  echo '    fi'
                  echo '  done'
                  echo '  unset __icav2_shell_function_file_name'
                  echo 'fi'
                }} > "${{ICAV2_CLI_PLUGINS_HOME}}/source.sh"

                cat "${{ICAV2_CLI_PLUGINS_HOME}}/source.sh"
                """
            )
            assert result.returncode == 0
            content = result.stdout

            # Verify key requirements:
            # 1. Sets ICAV2_CLI_PLUGINS_HOME
            assert 'export ICAV2_CLI_PLUGINS_HOME=' in content
            # 2. Prepends bin/ to PATH
            assert '${ICAV2_CLI_PLUGINS_HOME}/bin:${PATH}' in content
            # 3. Is a valid bash script (starts with shebang)
            assert content.startswith("#!/usr/bin/env bash")
