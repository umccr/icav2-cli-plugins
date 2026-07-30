"""Property-based tests for the config file parser."""

import re
import string

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from icav2_cli_plugins.utils.config_parser import ConfigParser, ConfigParseError, ProfileConfig
from icav2_cli_plugins.utils.globals import PROFILE_NAME_REGEX, VALID_OUTPUT_FORMATS


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Strategy for generating valid simple values (no newlines, no leading/trailing whitespace issues)
simple_value_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S"),
        blacklist_characters="\n\r#;[]=",
    ),
    min_size=1,
    max_size=50,
).map(str.strip).filter(lambda s: len(s) > 0)

# Valid profile name: starts with alphanumeric, followed by 0-63 chars of [a-zA-Z0-9_-]
_profile_name_first_char = st.sampled_from(
    string.ascii_letters + string.digits
)
_profile_name_rest_chars = st.text(
    alphabet=string.ascii_letters + string.digits + "_-",
    min_size=0,
    max_size=63,
)

profile_name_strategy = st.builds(
    lambda first, rest: first + rest,
    _profile_name_first_char,
    _profile_name_rest_chars,
)

# Valid output format: one of the allowed values
output_format_strategy = st.sampled_from(list(VALID_OUTPUT_FORMATS))

# Optional string fields: non-empty strings safe for INI format, or None
_safe_value_chars = st.characters(
    whitelist_categories=("L", "N", "P", "S"),
    blacklist_characters="\n\r#;[]=",
)

optional_string_strategy = st.one_of(
    st.none(),
    st.text(_safe_value_chars, min_size=1, max_size=100).map(str.strip).filter(
        lambda s: len(s) > 0
    ),
)

# Server URL strategy: non-empty string safe for INI format
server_url_strategy = st.text(
    _safe_value_chars,
    min_size=1,
    max_size=100,
).map(str.strip).filter(lambda s: len(s) > 0)


def profile_config_strategy(name_strategy=profile_name_strategy):
    """Strategy for generating valid ProfileConfig objects."""
    return st.builds(
        ProfileConfig,
        name=name_strategy,
        server_url=server_url_strategy,
        x_api_key=optional_string_strategy,
        project_id=optional_string_strategy,
        project_name=optional_string_strategy,
        token_tid=optional_string_strategy,
        output_format=output_format_strategy,
    )


def profiles_dict_strategy():
    """
    Strategy for generating a valid Dict[str, ProfileConfig].

    May include a 'default' profile and/or named profiles.
    At least one profile is always generated.
    """
    # Generate named profiles with unique names
    named_profiles = st.lists(
        profile_config_strategy(),
        min_size=0,
        max_size=5,
        unique_by=lambda p: p.name,
    )

    # Optionally include a default profile
    default_profile = st.one_of(
        st.none(),
        profile_config_strategy(name_strategy=st.just("default")),
    )

    return st.builds(
        _build_profiles_dict,
        named_profiles,
        default_profile,
    ).filter(lambda d: len(d) > 0)  # at least one profile


def _build_profiles_dict(named_profiles, default_profile):
    """Build a dict of profiles from generated components."""
    result = {}
    if default_profile is not None:
        result["default"] = default_profile
    for p in named_profiles:
        # Ensure named profiles don't collide with 'default'
        if p.name != "default":
            result[p.name] = p
    return result


# ---------------------------------------------------------------------------
# Property 1: Config file round-trip
# ---------------------------------------------------------------------------

# Feature: profile-based-config, Property 1: Config file round-trip
class TestConfigRoundTrip:
    """Property 1: Config file round-trip.

    For any valid set of profile configurations (with valid profile names,
    supported keys, and valid values), serializing to INI format and then
    parsing the result SHALL produce a configuration object with identical
    section names, keys, and values as the original.

    **Validates: Requirements 3.6, 3.1, 3.3, 3.5, 1.1, 1.2**
    """

    @settings(max_examples=100)
    @given(profiles=profiles_dict_strategy())
    def test_round_trip_preserves_all_profiles(self, profiles):
        """Serialize then parse produces identical ProfileConfig objects."""
        parser = ConfigParser()

        # Serialize profiles to INI format
        serialized = parser.serialize(profiles)

        # Parse the serialized content back
        parsed = parser.parse(serialized)

        # Assert the round-trip produces identical profile names
        assert set(parsed.keys()) == set(profiles.keys()), (
            f"Profile names differ: parsed={set(parsed.keys())}, "
            f"original={set(profiles.keys())}"
        )

        # Assert each profile has identical field values
        for name, original_profile in profiles.items():
            parsed_profile = parsed[name]
            assert parsed_profile.name == original_profile.name, (
                f"Profile '{name}' name mismatch: "
                f"parsed={parsed_profile.name!r}, original={original_profile.name!r}"
            )
            assert parsed_profile.server_url == original_profile.server_url, (
                f"Profile '{name}' server_url mismatch: "
                f"parsed={parsed_profile.server_url!r}, original={original_profile.server_url!r}"
            )
            assert parsed_profile.x_api_key == original_profile.x_api_key, (
                f"Profile '{name}' x_api_key mismatch: "
                f"parsed={parsed_profile.x_api_key!r}, original={original_profile.x_api_key!r}"
            )
            assert parsed_profile.project_id == original_profile.project_id, (
                f"Profile '{name}' project_id mismatch: "
                f"parsed={parsed_profile.project_id!r}, original={original_profile.project_id!r}"
            )
            assert parsed_profile.project_name == original_profile.project_name, (
                f"Profile '{name}' project_name mismatch: "
                f"parsed={parsed_profile.project_name!r}, original={original_profile.project_name!r}"
            )
            assert parsed_profile.token_tid == original_profile.token_tid, (
                f"Profile '{name}' token_tid mismatch: "
                f"parsed={parsed_profile.token_tid!r}, original={original_profile.token_tid!r}"
            )
            assert parsed_profile.output_format == original_profile.output_format, (
                f"Profile '{name}' output_format mismatch: "
                f"parsed={parsed_profile.output_format!r}, original={original_profile.output_format!r}"
            )


# Known keys from ProfileConfig (excluding output_format which has validation)
DUPLICABLE_KEYS = ["server_url", "x_api_key", "project_id", "project_name", "token_tid"]


# Feature: profile-based-config, Property 9: Duplicate keys resolve to last occurrence
class TestDuplicateKeyResolution:
    """Property 9: Duplicate keys resolve to last occurrence.

    For any config file section containing the same key K appearing N times
    (N >= 2) with values V1, V2, ..., Vn, the parsed section SHALL have K
    mapped to Vn (the last occurrence).

    Validates: Requirements 3.8
    """

    @settings(max_examples=100)
    @given(
        key=st.sampled_from(DUPLICABLE_KEYS),
        values=st.lists(simple_value_strategy, min_size=2, max_size=5),
    )
    def test_duplicate_keys_last_value_wins_default_section(self, key: str, values: list[str]):
        """In a [default] section with duplicate keys, the last value wins."""
        # Build config content with the same key repeated multiple times
        lines = ["[default]"]
        for value in values:
            lines.append(f"{key} = {value}")

        content = "\n".join(lines) + "\n"
        parser = ConfigParser()
        profiles = parser.parse(content)

        assert "default" in profiles
        profile = profiles["default"]
        # The last value should win
        assert getattr(profile, key) == values[-1]

    @settings(max_examples=100)
    @given(
        key=st.sampled_from(DUPLICABLE_KEYS),
        values=st.lists(simple_value_strategy, min_size=2, max_size=5),
        profile_name=st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]{0,10}", fullmatch=True),
    )
    def test_duplicate_keys_last_value_wins_named_profile(
        self, key: str, values: list[str], profile_name: str
    ):
        """In a [profile <name>] section with duplicate keys, the last value wins."""
        # Build config content with the same key repeated multiple times
        lines = [f"[profile {profile_name}]"]
        for value in values:
            lines.append(f"{key} = {value}")

        content = "\n".join(lines) + "\n"
        parser = ConfigParser()
        profiles = parser.parse(content)

        assert profile_name in profiles
        profile = profiles[profile_name]
        # The last value should win
        assert getattr(profile, key) == values[-1]

    @settings(max_examples=100)
    @given(
        key=st.sampled_from(DUPLICABLE_KEYS),
        values=st.lists(simple_value_strategy, min_size=2, max_size=5),
        interleaved_keys=st.lists(
            st.tuples(
                st.sampled_from(DUPLICABLE_KEYS),
                simple_value_strategy,
            ),
            min_size=0,
            max_size=3,
        ),
    )
    def test_duplicate_keys_with_interleaved_other_keys(
        self, key: str, values: list[str], interleaved_keys: list[tuple[str, str]]
    ):
        """Duplicate keys resolve to last occurrence even with other keys interleaved."""
        # Filter out interleaved keys that match our duplicate key
        other_keys = [(k, v) for k, v in interleaved_keys if k != key]

        # Build config with duplicates of `key` interleaved with other keys
        lines = ["[default]"]
        for i, value in enumerate(values):
            lines.append(f"{key} = {value}")
            # Insert some other keys between duplicates
            if i < len(other_keys):
                k, v = other_keys[i]
                lines.append(f"{k} = {v}")

        content = "\n".join(lines) + "\n"
        parser = ConfigParser()
        profiles = parser.parse(content)

        assert "default" in profiles
        profile = profiles["default"]
        # The last value of the duplicate key should win
        assert getattr(profile, key) == values[-1]


# Feature: profile-based-config, Property 8: Output format validation
class TestOutputFormatValidation:
    """
    Property 8: Output format validation

    For any string value assigned to the output_format key, the config parser
    SHALL accept it if and only if it is one of table, json, or yaml.

    Validates: Requirements 1.6
    """

    @given(output_format=st.text(min_size=1))
    @settings(max_examples=200)
    def test_output_format_accepted_iff_valid(self, output_format: str):
        """
        Generate arbitrary strings for output_format, assert accepted iff in {table, json, yaml}.
        """
        # Skip strings containing characters that would break INI parsing
        assume('\n' not in output_format)
        assume('\r' not in output_format)
        assume('=' not in output_format)
        assume('#' not in output_format)
        assume(';' not in output_format)
        assume('[' not in output_format)
        assume(']' not in output_format)
        # Value must be non-empty after strip and equal to its stripped form
        # (the parser strips whitespace from values)
        assume(output_format.strip() == output_format)
        assume(len(output_format) > 0)

        parser = ConfigParser()
        config_content = f"[default]\noutput_format = {output_format}\n"

        if output_format in VALID_OUTPUT_FORMATS:
            # Valid formats should parse successfully
            result = parser.parse(config_content)
            assert 'default' in result
            assert result['default'].output_format == output_format
        else:
            # Invalid formats should raise ConfigParseError
            with pytest.raises(ConfigParseError) as exc_info:
                parser.parse(config_content)
            assert 'output_format' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()

    @given(valid_format=st.sampled_from(list(VALID_OUTPUT_FORMATS)))
    @settings(max_examples=100)
    def test_all_valid_formats_accepted(self, valid_format: str):
        """
        All valid output formats (table, json, yaml) are always accepted.
        """
        parser = ConfigParser()
        config_content = f"[default]\noutput_format = {valid_format}\n"

        result = parser.parse(config_content)
        assert 'default' in result
        assert result['default'].output_format == valid_format


# Feature: profile-based-config, Property 10: Malformed lines produce parse errors with line info
class TestMalformedLineDetection:
    """Property 10: Malformed lines produce parse errors with line info.

    For any line in a config file that is not blank, not a comment (starting
    with # or ;), not a section header (starting with [), and does not contain
    a '=' delimiter, the parser SHALL raise a ConfigParseError that includes
    the line number.

    Validates: Requirements 3.7
    """

    @staticmethod
    def _malformed_line_strategy():
        """
        Generate a line that is:
        - Not blank (has at least one non-whitespace character)
        - Not a comment (does not start with # or ;)
        - Not a section header (does not start with [)
        - Does not contain an = delimiter
        """
        return st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N", "P", "S", "Z"),
                blacklist_characters="\n\r\x00",
            ),
            min_size=1,
            max_size=80,
        ).filter(
            lambda s: (
                s.strip() != ""  # Not blank
                and not s.lstrip().startswith("#")  # Not a comment with #
                and not s.lstrip().startswith(";")  # Not a comment with ;
                and not s.lstrip().startswith("[")  # Not a section header
                and "=" not in s  # No = delimiter
            )
        )

    @settings(max_examples=100)
    @given(data=st.data())
    def test_malformed_line_raises_config_parse_error(self, data):
        """A malformed line after a valid section header raises ConfigParseError with correct line number."""
        malformed_line = data.draw(self._malformed_line_strategy(), label="malformed_line")
        line_offset = data.draw(st.integers(min_value=0, max_value=5), label="blank_line_offset")

        # Build config content: a valid section header, optional blank lines, then the malformed line
        lines = ["[default]"]
        for _ in range(line_offset):
            lines.append("")
        lines.append(malformed_line)

        content = "\n".join(lines)

        # The malformed line is at position: 1 (header) + line_offset (blanks) + 1
        expected_line_number = line_offset + 2

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse(content)

        # Verify the error includes the correct line number
        assert exc_info.value.line_number == expected_line_number

    @settings(max_examples=100)
    @given(data=st.data())
    def test_malformed_line_error_contains_line_content(self, data):
        """ConfigParseError includes the content of the malformed line."""
        malformed_line = data.draw(self._malformed_line_strategy(), label="malformed_line")

        # Simple config: section header then malformed line
        content = f"[default]\n{malformed_line}"

        parser = ConfigParser()

        with pytest.raises(ConfigParseError) as exc_info:
            parser.parse(content)

        # The line_content attribute should contain the malformed line
        assert exc_info.value.line_content == malformed_line


# --- Strategies for Property 2 (comment invariance) ---

from hypothesis import HealthCheck

# Simple short profile names for fast generation
_short_profile_name = st.from_regex(r"[a-zA-Z][a-zA-Z0-9_-]{0,7}", fullmatch=True)

# Simple values: short alphanumeric strings (fast to generate)
_simple_value_p2 = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789-_.",
    min_size=1,
    max_size=20,
)


@st.composite
def profile_dicts(draw: st.DrawFn) -> dict[str, ProfileConfig]:
    """Generate a dict of valid profiles for Property 2 testing."""
    has_default = draw(st.booleans())
    num_named = draw(st.integers(min_value=0, max_value=2))

    profiles: dict[str, ProfileConfig] = {}

    if has_default:
        profiles["default"] = ProfileConfig(
            name="default",
            server_url=draw(_simple_value_p2),
            x_api_key=draw(st.one_of(st.none(), _simple_value_p2)),
            project_id=draw(st.one_of(st.none(), _simple_value_p2)),
            project_name=draw(st.one_of(st.none(), _simple_value_p2)),
            token_tid=draw(st.one_of(st.none(), _simple_value_p2)),
            output_format=draw(st.sampled_from(VALID_OUTPUT_FORMATS)),
        )

    # Generate unique named profiles using index suffixes to avoid collisions
    for i in range(num_named):
        base_name = draw(_short_profile_name)
        name = f"{base_name}{i}"
        if name == "default":
            name = f"p{name}"
        profiles[name] = ProfileConfig(
            name=name,
            server_url=draw(_simple_value_p2),
            x_api_key=draw(st.one_of(st.none(), _simple_value_p2)),
            project_id=draw(st.one_of(st.none(), _simple_value_p2)),
            project_name=draw(st.one_of(st.none(), _simple_value_p2)),
            token_tid=draw(st.one_of(st.none(), _simple_value_p2)),
            output_format=draw(st.sampled_from(VALID_OUTPUT_FORMATS)),
        )

    # Ensure at least one profile exists
    if not profiles:
        profiles["default"] = ProfileConfig(
            name="default",
            server_url=draw(_simple_value_p2),
            x_api_key=draw(st.one_of(st.none(), _simple_value_p2)),
            project_id=draw(st.one_of(st.none(), _simple_value_p2)),
            project_name=draw(st.one_of(st.none(), _simple_value_p2)),
            token_tid=draw(st.one_of(st.none(), _simple_value_p2)),
            output_format=draw(st.sampled_from(VALID_OUTPUT_FORMATS)),
        )

    return profiles


# Comment line strategy: short text for fast generation
_comment_text_p2 = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.,!?",
    min_size=0,
    max_size=30,
)


@st.composite
def comment_lines(draw: st.DrawFn) -> str:
    """Generate a valid comment line starting with # or ;."""
    prefix = draw(st.sampled_from(["#", ";"]))
    text = draw(_comment_text_p2)
    return f"{prefix} {text}"


# Feature: profile-based-config, Property 2: Comments do not affect parse result
class TestCommentInvariance:
    """Property 2: Comments do not affect parse result.

    For any valid config file content and any set of comment lines
    (lines starting with # or ;), inserting those comment lines at
    any position in the config file shall produce the same parsed
    result as parsing the config without comments.

    Validates: Requirements 3.2
    """

    @given(
        profiles=profile_dicts(),
        comments=st.lists(comment_lines(), min_size=1, max_size=5),
        positions=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=1, max_size=5),
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_comments_do_not_affect_parse_result(
        self,
        profiles: dict[str, ProfileConfig],
        comments: list[str],
        positions: list[float],
    ):
        """
        **Validates: Requirements 3.2**

        Inserting comment lines at arbitrary positions in valid config
        content produces the same parse result as the original without comments.
        """
        parser = ConfigParser()

        # Serialize the profiles to get valid config content
        original_content = parser.serialize(profiles)

        # Parse the original content (without extra comments)
        original_result = parser.parse(original_content)

        # Insert comments at random positions in the content lines
        lines = original_content.split("\n")

        # Determine insertion positions based on float fractions
        for i, comment in enumerate(comments):
            # Use position fraction to determine where to insert
            pos_frac = positions[i % len(positions)]
            insert_idx = int(pos_frac * (len(lines) + 1))
            insert_idx = min(insert_idx, len(lines))
            lines.insert(insert_idx, comment)

        content_with_comments = "\n".join(lines)

        # Parse the content with comments inserted
        result_with_comments = parser.parse(content_with_comments)

        # The results should be identical
        assert result_with_comments.keys() == original_result.keys(), (
            f"Profile names differ: {result_with_comments.keys()} != {original_result.keys()}"
        )

        for profile_name in original_result:
            orig = original_result[profile_name]
            commented = result_with_comments[profile_name]
            assert orig.name == commented.name
            assert orig.server_url == commented.server_url
            assert orig.x_api_key == commented.x_api_key
            assert orig.project_id == commented.project_id
            assert orig.project_name == commented.project_name
            assert orig.token_tid == commented.token_tid
            assert orig.output_format == commented.output_format
