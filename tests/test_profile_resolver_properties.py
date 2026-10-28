"""Property-based tests for the profile resolver."""

import os
import string
import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig
from icav2_cli_plugins.utils.globals import VALID_OUTPUT_FORMATS
from icav2_cli_plugins.utils.profile_resolver import ProfileResolver


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Valid profile name: starts with alphanumeric, followed by 0-63 chars of [a-zA-Z0-9_-]
_profile_name_first_char = st.sampled_from(
    string.ascii_letters + string.digits
)
_profile_name_rest_chars = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=0,
    max_size=15,
)

profile_name_strategy = st.builds(
    lambda first, rest: first + rest,
    _profile_name_first_char,
    _profile_name_rest_chars,
)

# Valid output format
output_format_strategy = st.sampled_from(list(VALID_OUTPUT_FORMATS))

# Simple values: short alphanumeric strings safe for INI format
_simple_value = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_.",
    min_size=1,
    max_size=20,
)


@st.composite
def profiles_with_unique_names(draw: st.DrawFn, min_profiles: int = 1, max_profiles: int = 5):
    """Generate a dict of valid profiles with unique names."""
    num_profiles = draw(st.integers(min_value=min_profiles, max_value=max_profiles))
    profiles: dict[str, ProfileConfig] = {}

    # Generate unique profile names
    names: list[str] = []
    for i in range(num_profiles):
        # Use index suffix to ensure uniqueness
        base_name = draw(profile_name_strategy)
        name = f"{base_name}{i}"
        # Ensure it matches the regex (first char must be alphanumeric)
        if not name[0].isalnum():
            name = f"p{name}"
        names.append(name)

    for name in names:
        profiles[name] = ProfileConfig(
            name=name,
            server_url=draw(_simple_value),
            x_api_key=draw(st.one_of(st.none(), _simple_value)),
            project_id=draw(st.one_of(st.none(), _simple_value)),
            project_name=draw(st.one_of(st.none(), _simple_value)),
            token_tid=draw(st.one_of(st.none(), _simple_value)),
            output_format=draw(output_format_strategy),
        )

    return profiles


# ---------------------------------------------------------------------------
# Property 7: Invalid profile name produces error with available profiles
# ---------------------------------------------------------------------------

# Feature: profile-based-config, Property 7: Invalid profile name produces error with available profiles
class TestInvalidProfileError:
    """Property 7: Invalid profile name produces error with available profiles.

    For any config file with N profiles (N >= 1) and any profile name string
    that does not match any profile in the config, attempting to resolve that
    profile SHALL produce an error that contains both the requested profile
    name and all available profile names.

    **Validates: Requirements 2.4**
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(data=st.data())
    def test_invalid_profile_name_produces_error_with_available_profiles(
        self, data, tmp_path, monkeypatch, capsys
    ):
        """
        Generate configs with 1+ valid profiles, request a nonexistent profile name
        via cli_profile parameter, assert that SystemExit is raised and stderr
        contains the requested profile name and all available profile names.

        **Validates: Requirements 2.4**
        """
        # Generate a config with 1+ profiles
        profiles = data.draw(profiles_with_unique_names(min_profiles=1, max_profiles=5))

        existing_names = set(profiles.keys())

        # Generate a profile name that does NOT exist in the config
        requested_name = data.draw(
            profile_name_strategy.filter(
                lambda n: n not in existing_names and n != "default"
            ),
            label="requested_nonexistent_profile_name",
        )

        # Write the config to a temp file
        parser = ConfigParser()
        config_file = tmp_path / f"config_{id(profiles)}"
        parser.write_file(config_file, profiles)

        # Clear any env vars that might interfere
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        # Use cli_profile parameter to request the nonexistent profile
        resolver = ProfileResolver(config_path=config_file, cli_profile=requested_name)

        # Should raise SystemExit (sys.exit(1))
        with pytest.raises(SystemExit) as exc_info:
            resolver.resolve()

        assert exc_info.value.code == 1

        # Capture stderr output
        captured = capsys.readouterr()
        stderr_output = captured.err

        # The error message must contain the requested profile name
        assert requested_name in stderr_output, (
            f"Expected requested profile name '{requested_name}' in stderr, "
            f"got: {stderr_output!r}"
        )

        # The error message must contain all available profile names
        for available_name in existing_names:
            assert available_name in stderr_output, (
                f"Expected available profile name '{available_name}' in stderr, "
                f"got: {stderr_output!r}"
            )

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(data=st.data())
    def test_invalid_profile_via_env_var_produces_error(
        self, data, tmp_path, monkeypatch, capsys
    ):
        """
        When ICAV2_PROFILE is set to a nonexistent profile name, the resolver
        produces an error containing the name and available profiles.

        **Validates: Requirements 2.4**
        """
        # Generate a config with 1+ profiles
        profiles = data.draw(profiles_with_unique_names(min_profiles=1, max_profiles=4))

        existing_names = set(profiles.keys())

        # Generate a profile name that does NOT exist in the config
        requested_name = data.draw(
            profile_name_strategy.filter(
                lambda n: n not in existing_names and n != "default"
            ),
            label="requested_nonexistent_profile_name",
        )

        # Write the config to a temp file
        parser = ConfigParser()
        config_file = tmp_path / f"config_{id(profiles)}"
        parser.write_file(config_file, profiles)

        # Set ICAV2_PROFILE to the nonexistent name
        monkeypatch.setenv("ICAV2_PROFILE", requested_name)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        # Create resolver without cli_profile (rely on env var)
        resolver = ProfileResolver(config_path=config_file, cli_profile=None)

        # Should raise SystemExit (sys.exit(1))
        with pytest.raises(SystemExit) as exc_info:
            resolver.resolve()

        assert exc_info.value.code == 1

        # Capture stderr output
        captured = capsys.readouterr()
        stderr_output = captured.err

        # The error message must contain the requested profile name
        assert requested_name in stderr_output, (
            f"Expected requested profile name '{requested_name}' in stderr, "
            f"got: {stderr_output!r}"
        )

        # The error message must contain all available profile names
        for available_name in existing_names:
            assert available_name in stderr_output, (
                f"Expected available profile name '{available_name}' in stderr, "
                f"got: {stderr_output!r}"
            )


# ---------------------------------------------------------------------------
# Strategies for Property 3
# ---------------------------------------------------------------------------

# Server URL strategy (when present): hostname-like values
_server_url_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-.",
    min_size=3,
    max_size=30,
).filter(lambda s: len(s.strip()) > 0 and s.strip() == s)


@st.composite
def profile_with_optional_defaults(draw: st.DrawFn) -> tuple[str, bool, bool, str | None, str | None]:
    """
    Generate a profile configuration with optional server_url and output_format.

    Returns:
        Tuple of (profile_name, omit_server_url, omit_output_format,
                  server_url_value_if_present, output_format_value_if_present)
    """
    name = draw(st.one_of(st.just("default"), profile_name_strategy))
    omit_server_url = draw(st.booleans())
    omit_output_format = draw(st.booleans())

    # Ensure at least one key is omitted (test is about defaults being applied)
    assume(omit_server_url or omit_output_format)

    server_url_value = None if omit_server_url else draw(_server_url_strategy)
    output_format_value = None if omit_output_format else draw(output_format_strategy)

    return (name, omit_server_url, omit_output_format, server_url_value, output_format_value)


def _build_config_content(
    profile_name: str,
    omit_server_url: bool,
    omit_output_format: bool,
    server_url_value: str | None,
    output_format_value: str | None,
) -> str:
    """Build INI config content with optional keys omitted."""
    if profile_name == "default":
        header = "[default]"
    else:
        header = f"[profile {profile_name}]"

    lines = [header]

    if not omit_server_url and server_url_value is not None:
        lines.append(f"server_url = {server_url_value}")

    if not omit_output_format and output_format_value is not None:
        lines.append(f"output_format = {output_format_value}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Property 3: Default values applied when keys absent
# ---------------------------------------------------------------------------

# Feature: profile-based-config, Property 3: Default values applied when keys absent
class TestDefaultValueResolution:
    """Property 3: Default values applied when keys absent.

    For any profile that omits the server_url key, the resolved server URL
    SHALL be "ica.illumina.com"; and for any profile that omits the
    output_format key, the resolved output format SHALL be "table".

    **Validates: Requirements 1.4, 1.5**
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(data=st.data())
    def test_defaults_applied_when_keys_absent(self, data, monkeypatch, tmp_path):
        """
        Generate profiles missing server_url and/or output_format,
        assert defaults are applied by the ProfileResolver.

        **Validates: Requirements 1.4, 1.5**
        """
        profile_info = data.draw(
            profile_with_optional_defaults(), label="profile_info"
        )
        name, omit_server_url, omit_output_format, server_url_value, output_format_value = profile_info

        # Clear environment variables that could interfere with resolution
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        # Set ICAV2_PROFILE to the generated profile name (unless it's "default")
        if name != "default":
            monkeypatch.setenv("ICAV2_PROFILE", name)

        # Build config content with the keys optionally omitted
        config_content = _build_config_content(
            profile_name=name,
            omit_server_url=omit_server_url,
            omit_output_format=omit_output_format,
            server_url_value=server_url_value,
            output_format_value=output_format_value,
        )

        # Write config to a temp file
        config_file = tmp_path / f"config_{id(config_content)}"
        config_file.write_text(config_content, encoding="utf-8")

        # Resolve the profile using ProfileResolver
        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        # Assert defaults are applied when keys are absent
        if omit_server_url:
            assert resolved.server_url == "ica.illumina.com", (
                f"Expected default server_url 'ica.illumina.com' when key absent, "
                f"got '{resolved.server_url}'"
            )
            assert resolved.base_url == "https://ica.illumina.com/ica/rest", (
                f"Expected default base_url when server_url absent, "
                f"got '{resolved.base_url}'"
            )
        else:
            assert resolved.server_url == server_url_value, (
                f"Expected server_url '{server_url_value}' when key present, "
                f"got '{resolved.server_url}'"
            )
            assert resolved.base_url == f"https://{server_url_value}/ica/rest", (
                f"Expected base_url 'https://{server_url_value}/ica/rest' when server_url present, "
                f"got '{resolved.base_url}'"
            )

        if omit_output_format:
            assert resolved.output_format == "table", (
                f"Expected default output_format 'table' when key absent, "
                f"got '{resolved.output_format}'"
            )
        else:
            assert resolved.output_format == output_format_value, (
                f"Expected output_format '{output_format_value}' when key present, "
                f"got '{resolved.output_format}'"
            )

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(
        profile_name=st.one_of(st.just("default"), profile_name_strategy),
    )
    def test_server_url_defaults_to_ica_illumina_when_absent(
        self, profile_name, monkeypatch, tmp_path
    ):
        """
        When server_url is completely absent from a profile, the resolved
        server_url SHALL be "ica.illumina.com".

        **Validates: Requirements 1.4**
        """
        # Clear environment variables
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        if profile_name != "default":
            monkeypatch.setenv("ICAV2_PROFILE", profile_name)

        # Config with no server_url key at all
        config_content = _build_config_content(
            profile_name=profile_name,
            omit_server_url=True,
            omit_output_format=False,
            server_url_value=None,
            output_format_value="table",
        )

        config_file = tmp_path / f"config_{hash(profile_name)}"
        config_file.write_text(config_content, encoding="utf-8")

        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        assert resolved.server_url == "ica.illumina.com"
        assert resolved.base_url == "https://ica.illumina.com/ica/rest"

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(
        profile_name=st.one_of(st.just("default"), profile_name_strategy),
    )
    def test_output_format_defaults_to_table_when_absent(
        self, profile_name, monkeypatch, tmp_path
    ):
        """
        When output_format is completely absent from a profile, the resolved
        output_format SHALL be "table".

        **Validates: Requirements 1.5**
        """
        # Clear environment variables
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        if profile_name != "default":
            monkeypatch.setenv("ICAV2_PROFILE", profile_name)

        # Config with no output_format key at all
        config_content = _build_config_content(
            profile_name=profile_name,
            omit_server_url=False,
            omit_output_format=True,
            server_url_value="custom.server.com",
            output_format_value=None,
        )

        config_file = tmp_path / f"config_{hash(profile_name)}"
        config_file.write_text(config_content, encoding="utf-8")

        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        assert resolved.output_format == "table"


# ---------------------------------------------------------------------------
# Strategies for Property 4
# ---------------------------------------------------------------------------

# Server URL strategy for Property 4
_server_url_p4 = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_.",
    min_size=3,
    max_size=30,
)


@st.composite
def multi_profile_config(draw: st.DrawFn) -> dict[str, ProfileConfig]:
    """
    Generate a multi-profile config dict that always includes a 'default' profile
    and at least one named profile with unique names.
    """
    # Generate default profile
    default_profile = ProfileConfig(
        name="default",
        server_url=draw(_server_url_p4),
        x_api_key=draw(_simple_value),
        project_id=draw(_simple_value),
        project_name=draw(st.one_of(st.none(), _simple_value)),
        token_tid=draw(st.one_of(st.none(), _simple_value)),
        output_format=draw(output_format_strategy),
    )

    # Generate between 1 and 4 named profiles
    num_named = draw(st.integers(min_value=1, max_value=4))
    profiles: dict[str, ProfileConfig] = {"default": default_profile}

    used_names: set[str] = {"default"}
    for i in range(num_named):
        # Generate a unique profile name
        name = draw(profile_name_strategy)
        # Ensure uniqueness by appending index if collision
        if name in used_names:
            name = f"{name}{i}"
        if name in used_names or name == "default":
            name = f"prof{i}"
        used_names.add(name)

        profiles[name] = ProfileConfig(
            name=name,
            server_url=draw(_server_url_p4),
            x_api_key=draw(_simple_value),
            project_id=draw(_simple_value),
            project_name=draw(st.one_of(st.none(), _simple_value)),
            token_tid=draw(st.one_of(st.none(), _simple_value)),
            output_format=draw(output_format_strategy),
        )

    return profiles


# ---------------------------------------------------------------------------
# Property 4: Profile selection resolves correct profile
# ---------------------------------------------------------------------------

# Feature: profile-based-config, Property 4: Profile selection resolves correct profile
class TestProfileSelectionResolvesCorrectProfile:
    """Property 4: Profile selection resolves correct profile.

    For any config file containing multiple profiles and any valid profile name
    present in that config, setting ICAV2_PROFILE to that name SHALL load exactly
    the key-value pairs from that profile's section, and when ICAV2_PROFILE is unset
    or empty, the [default] profile SHALL be loaded.

    **Validates: Requirements 2.1, 2.2**
    """

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(profiles=multi_profile_config())
    def test_icav2_profile_selects_named_profile(self, profiles, tmp_path, monkeypatch):
        """
        When ICAV2_PROFILE is set to a valid profile name, the resolver loads
        exactly that profile's values.

        **Validates: Requirements 2.1**
        """
        # Write the config to a temp file
        parser = ConfigParser()
        config_file = tmp_path / f"config_{id(profiles)}"
        parser.write_file(config_file, profiles)

        # Pick a named (non-default) profile to select
        named_profiles = [name for name in profiles if name != "default"]
        assume(len(named_profiles) > 0)
        target_name = named_profiles[0]
        target_profile = profiles[target_name]

        # Clear all env vars that could interfere
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        # Set ICAV2_PROFILE to the target profile name
        monkeypatch.setenv("ICAV2_PROFILE", target_name)

        # Resolve config
        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        # Assert the resolved config matches the target profile
        assert resolved.profile_name == target_name
        assert resolved.api_key == target_profile.x_api_key
        assert resolved.project_id == target_profile.project_id
        assert resolved.server_url == target_profile.server_url
        assert resolved.output_format == target_profile.output_format

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(profiles=multi_profile_config())
    def test_unset_icav2_profile_loads_default(self, profiles, tmp_path, monkeypatch):
        """
        When ICAV2_PROFILE is not set (or empty), the [default] profile is loaded.

        **Validates: Requirements 2.2**
        """
        # Write the config to a temp file
        parser = ConfigParser()
        config_file = tmp_path / f"config_{id(profiles)}"
        parser.write_file(config_file, profiles)

        default_profile = profiles["default"]

        # Clear all env vars that could interfere
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        # Resolve config with no ICAV2_PROFILE set
        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        # Assert the resolved config matches the default profile
        assert resolved.profile_name == "default"
        assert resolved.api_key == default_profile.x_api_key
        assert resolved.project_id == default_profile.project_id
        assert resolved.server_url == default_profile.server_url
        assert resolved.output_format == default_profile.output_format

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(profiles=multi_profile_config())
    def test_empty_icav2_profile_loads_default(self, profiles, tmp_path, monkeypatch):
        """
        When ICAV2_PROFILE is set to an empty string, the [default] profile is loaded.

        **Validates: Requirements 2.2**
        """
        # Write the config to a temp file
        parser = ConfigParser()
        config_file = tmp_path / f"config_{id(profiles)}"
        parser.write_file(config_file, profiles)

        default_profile = profiles["default"]

        # Clear all interfering env vars, then set ICAV2_PROFILE to empty
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)
        monkeypatch.setenv("ICAV2_PROFILE", "")

        # Resolve config
        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        # Assert the resolved config matches the default profile
        assert resolved.profile_name == "default"
        assert resolved.api_key == default_profile.x_api_key
        assert resolved.project_id == default_profile.project_id
        assert resolved.server_url == default_profile.server_url
        assert resolved.output_format == default_profile.output_format

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
    )
    @given(profiles=multi_profile_config(), data=st.data())
    def test_each_profile_selectable_by_name(self, profiles, data, tmp_path, monkeypatch):
        """
        For any profile in the config, setting ICAV2_PROFILE to its name loads
        that profile's exact values.

        **Validates: Requirements 2.1, 2.2**
        """
        # Write the config to a temp file
        parser = ConfigParser()
        config_file = tmp_path / f"config_{id(profiles)}"
        parser.write_file(config_file, profiles)

        # Pick any profile name from the config (including 'default')
        target_name = data.draw(st.sampled_from(sorted(profiles.keys())), label="target_profile")
        target_profile = profiles[target_name]

        # Clear all env vars that could interfere
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        # Set ICAV2_PROFILE (or leave unset for "default")
        if target_name == "default":
            # Don't set ICAV2_PROFILE to test default fallback
            pass
        else:
            monkeypatch.setenv("ICAV2_PROFILE", target_name)

        # Resolve config
        resolver = ProfileResolver(config_path=config_file)
        resolved = resolver.resolve()

        # Assert the resolved config matches the target profile
        assert resolved.profile_name == target_name
        assert resolved.api_key == target_profile.x_api_key
        assert resolved.project_id == target_profile.project_id
        assert resolved.server_url == target_profile.server_url
        assert resolved.output_format == target_profile.output_format


# ---------------------------------------------------------------------------
# Helpers for Property 5
# ---------------------------------------------------------------------------

# Server URL strategy for Property 5
_server_url_value = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-.",
    min_size=3,
    max_size=30,
).filter(lambda s: len(s.strip()) > 0)

# Strategy for optional env var values (either set to a non-empty value, or absent)
optional_env_value = st.one_of(
    st.none(),  # env var not set
    _simple_value,  # env var set to a non-empty value
)

# Profile name strategy that excludes "default"
_named_profile_strategy = profile_name_strategy.filter(lambda n: n != "default")


def _write_config_with_profiles(tmp_path: Path, profiles: dict[str, ProfileConfig]) -> Path:
    """Write a config file with given profiles and return its path."""
    config_path = tmp_path / "config"
    parser = ConfigParser()
    parser.write_file(config_path, profiles)
    return config_path


def _build_profile(
    name: str,
    server_url: str = "ica.illumina.com",
    x_api_key: str | None = None,
    project_id: str | None = None,
    project_name: str | None = None,
    output_format: str = "table",
) -> ProfileConfig:
    """Build a ProfileConfig with given values."""
    return ProfileConfig(
        name=name,
        server_url=server_url,
        x_api_key=x_api_key,
        project_id=project_id,
        project_name=project_name,
        output_format=output_format,
    )


# ---------------------------------------------------------------------------
# Feature: profile-based-config, Property 5: Configuration precedence resolution
# ---------------------------------------------------------------------------


class TestPrecedenceResolution:
    """Property 5: Configuration precedence resolution.

    For any combination of environment variables (ICAV2_ACCESS_TOKEN,
    ICAV2_PROJECT_ID, ICAV2_BASE_URL), --profile flag, ICAV2_PROFILE env var,
    ICAV2_TENANT_NAME env var, and [default] profile values, the resolved
    configuration SHALL use the value from the highest-precedence source that
    provides a non-empty value for each configuration key.

    **Validates: Requirements 2.5, 7.4, 9.1, 9.3, 9.4, 9.5, 9.6, 9.7**
    """

    # --- Property 5a: Env var overrides for field values ---

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        profile_project_id=_simple_value,
        profile_server_url=_server_url_value,
        env_access_token=optional_env_value,
        env_project_id=optional_env_value,
        env_base_url=optional_env_value,
    )
    def test_env_var_overrides_profile_values(
        self,
        tmp_path: Path,
        monkeypatch,
        profile_project_id: str,
        profile_server_url: str,
        env_access_token: str | None,
        env_project_id: str | None,
        env_base_url: str | None,
    ):
        """
        When env vars are set, they override corresponding profile values.
        When env vars are not set, profile values are used.

        **Validates: Requirements 2.5, 9.1, 9.3, 9.4**
        """
        # Clear all relevant env vars first
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)

        # Set up profile
        profiles = {
            "default": _build_profile(
                name="default",
                server_url=profile_server_url,
                project_id=profile_project_id,
            ),
        }
        config_path = _write_config_with_profiles(tmp_path, profiles)

        # Set env vars that are provided
        if env_access_token is not None:
            monkeypatch.setenv("ICAV2_ACCESS_TOKEN", env_access_token)
        if env_project_id is not None:
            monkeypatch.setenv("ICAV2_PROJECT_ID", env_project_id)
        if env_base_url is not None:
            monkeypatch.setenv("ICAV2_BASE_URL", env_base_url)

        # Resolve configuration
        resolver = ProfileResolver(config_path=config_path)
        resolved = resolver.resolve()

        # Verify precedence: env vars override profile values
        if env_access_token is not None:
            assert resolved.access_token == env_access_token
        else:
            # Profile does not set access_token, so it should remain None
            assert resolved.access_token is None

        if env_project_id is not None:
            assert resolved.project_id == env_project_id
        else:
            assert resolved.project_id == profile_project_id

        expected_base_url = f"https://{profile_server_url}/ica/rest"
        if env_base_url is not None:
            assert resolved.base_url == env_base_url
        else:
            assert resolved.base_url == expected_base_url

    # --- Property 5b: Profile name precedence ---

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        cli_profile_name=st.one_of(st.none(), _named_profile_strategy),
        env_icav2_profile=st.one_of(st.none(), _named_profile_strategy),
        env_tenant_name=st.one_of(st.none(), _named_profile_strategy),
    )
    def test_profile_name_precedence(
        self,
        tmp_path: Path,
        monkeypatch,
        cli_profile_name: str | None,
        env_icav2_profile: str | None,
        env_tenant_name: str | None,
    ):
        """
        Profile name is resolved in precedence order:
        --profile flag > ICAV2_PROFILE > ICAV2_TENANT_NAME > default

        **Validates: Requirements 7.4, 9.5, 9.6, 9.7**
        """
        # Clear relevant env vars
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)

        # Determine what the expected profile name should be based on precedence
        if cli_profile_name is not None:
            expected_profile = cli_profile_name
        elif env_icav2_profile is not None:
            expected_profile = env_icav2_profile
        elif env_tenant_name is not None:
            expected_profile = env_tenant_name
        else:
            expected_profile = "default"

        # Build a config with all potential profiles so resolution succeeds
        all_names = set()
        if cli_profile_name is not None:
            all_names.add(cli_profile_name)
        if env_icav2_profile is not None:
            all_names.add(env_icav2_profile)
        if env_tenant_name is not None:
            all_names.add(env_tenant_name)
        all_names.add("default")

        # Create distinct project_id per profile to verify correct one is loaded
        profiles = {}
        for name in all_names:
            profiles[name] = _build_profile(
                name=name,
                project_id=f"project-for-{name}",
            )

        config_path = _write_config_with_profiles(tmp_path, profiles)

        # Set env vars
        if env_icav2_profile is not None:
            monkeypatch.setenv("ICAV2_PROFILE", env_icav2_profile)
        if env_tenant_name is not None:
            monkeypatch.setenv("ICAV2_TENANT_NAME", env_tenant_name)

        # Resolve
        resolver = ProfileResolver(config_path=config_path, cli_profile=cli_profile_name)
        resolved = resolver.resolve()

        # Verify the correct profile was selected
        assert resolved.profile_name == expected_profile, (
            f"Expected profile '{expected_profile}' but got '{resolved.profile_name}'. "
            f"cli_profile={cli_profile_name!r}, "
            f"ICAV2_PROFILE={env_icav2_profile!r}, "
            f"ICAV2_TENANT_NAME={env_tenant_name!r}"
        )
        # Verify the values come from the correct profile
        assert resolved.project_id == f"project-for-{expected_profile}"

    # --- Property 5c: ICAV2_PROFILE takes precedence over ICAV2_TENANT_NAME ---

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        profile_name=_named_profile_strategy,
        tenant_name=_named_profile_strategy,
    )
    def test_icav2_profile_over_tenant_name(
        self,
        tmp_path: Path,
        monkeypatch,
        profile_name: str,
        tenant_name: str,
    ):
        """
        When both ICAV2_PROFILE and ICAV2_TENANT_NAME are set,
        ICAV2_PROFILE wins.

        **Validates: Requirements 9.6**
        """
        # Ensure distinct names
        assume(profile_name != tenant_name)

        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        monkeypatch.setenv("ICAV2_PROFILE", profile_name)
        monkeypatch.setenv("ICAV2_TENANT_NAME", tenant_name)

        profiles = {
            profile_name: _build_profile(name=profile_name, project_id="from-profile-env"),
            tenant_name: _build_profile(name=tenant_name, project_id="from-tenant-env"),
            "default": _build_profile(name="default", project_id="from-default"),
        }
        config_path = _write_config_with_profiles(tmp_path, profiles)

        resolver = ProfileResolver(config_path=config_path)
        resolved = resolver.resolve()

        assert resolved.profile_name == profile_name
        assert resolved.project_id == "from-profile-env"

    # --- Property 5d: --profile flag takes precedence over all env vars ---

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        cli_profile=_named_profile_strategy,
        env_profile=_named_profile_strategy,
        env_tenant=_named_profile_strategy,
    )
    def test_cli_profile_flag_highest_precedence_for_profile_name(
        self,
        tmp_path: Path,
        monkeypatch,
        cli_profile: str,
        env_profile: str,
        env_tenant: str,
    ):
        """
        The --profile CLI flag takes highest precedence for profile name selection,
        even when ICAV2_PROFILE and ICAV2_TENANT_NAME are both set.

        **Validates: Requirements 7.4**
        """
        # Ensure distinct names
        assume(cli_profile != env_profile)
        assume(cli_profile != env_tenant)
        assume(env_profile != env_tenant)

        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)

        monkeypatch.setenv("ICAV2_PROFILE", env_profile)
        monkeypatch.setenv("ICAV2_TENANT_NAME", env_tenant)

        profiles = {
            cli_profile: _build_profile(name=cli_profile, project_id="from-cli-flag"),
            env_profile: _build_profile(name=env_profile, project_id="from-profile-env"),
            env_tenant: _build_profile(name=env_tenant, project_id="from-tenant-env"),
            "default": _build_profile(name="default", project_id="from-default"),
        }
        config_path = _write_config_with_profiles(tmp_path, profiles)

        resolver = ProfileResolver(config_path=config_path, cli_profile=cli_profile)
        resolved = resolver.resolve()

        assert resolved.profile_name == cli_profile
        assert resolved.project_id == "from-cli-flag"

    # --- Property 5e: Combined precedence for both profile name and env overrides ---

    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @given(
        cli_profile_name=st.one_of(st.none(), _named_profile_strategy),
        env_project_id=optional_env_value,
        env_base_url=optional_env_value,
        profile_project_id=_simple_value,
        profile_server_url=_server_url_value,
    )
    def test_combined_profile_selection_and_env_overrides(
        self,
        tmp_path: Path,
        monkeypatch,
        cli_profile_name: str | None,
        env_project_id: str | None,
        env_base_url: str | None,
        profile_project_id: str,
        profile_server_url: str,
    ):
        """
        Profile name resolution and env var overrides work together:
        first the correct profile is selected, then env vars override
        individual fields.

        **Validates: Requirements 2.5, 7.4, 9.3, 9.4, 9.7**
        """
        monkeypatch.delenv("ICAV2_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("ICAV2_PROJECT_ID", raising=False)
        monkeypatch.delenv("ICAV2_BASE_URL", raising=False)
        monkeypatch.delenv("ICAV2_PROFILE", raising=False)
        monkeypatch.delenv("ICAV2_TENANT_NAME", raising=False)

        # Determine expected profile
        if cli_profile_name is not None:
            expected_profile = cli_profile_name
        else:
            expected_profile = "default"

        # Build profiles - the selected profile has specific values
        profiles = {"default": _build_profile(
            name="default",
            server_url="default-server.com",
            project_id="default-project-id",
        )}
        if cli_profile_name is not None:
            profiles[cli_profile_name] = _build_profile(
                name=cli_profile_name,
                server_url=profile_server_url,
                project_id=profile_project_id,
            )

        config_path = _write_config_with_profiles(tmp_path, profiles)

        # Set env vars
        if env_project_id is not None:
            monkeypatch.setenv("ICAV2_PROJECT_ID", env_project_id)
        if env_base_url is not None:
            monkeypatch.setenv("ICAV2_BASE_URL", env_base_url)

        resolver = ProfileResolver(config_path=config_path, cli_profile=cli_profile_name)
        resolved = resolver.resolve()

        # Profile selection check
        assert resolved.profile_name == expected_profile

        # Field override checks
        if env_project_id is not None:
            assert resolved.project_id == env_project_id
        else:
            if cli_profile_name is not None:
                assert resolved.project_id == profile_project_id
            else:
                assert resolved.project_id == "default-project-id"

        if env_base_url is not None:
            assert resolved.base_url == env_base_url
        else:
            if cli_profile_name is not None:
                expected_url = f"https://{profile_server_url}/ica/rest"
            else:
                expected_url = "https://default-server.com/ica/rest"
            assert resolved.base_url == expected_url
