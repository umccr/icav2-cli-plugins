#!/usr/bin/env python3
"""
Config file parser for INI-style profile configuration.

Handles the AWS CLI-style profile format:
  [default]            -> default profile
  [profile my-tenant]  -> named profile "my-tenant"

Keys: key = value (whitespace trimmed, comments with # or ;)
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, Optional
from pathlib import Path

from icav2_cli_plugins.utils.globals import PROFILE_NAME_REGEX, VALID_OUTPUT_FORMATS


@dataclass
class ProfileConfig:
    """Represents a single parsed profile."""
    name: str
    server_url: str = "ica.illumina.com"
    x_api_key: Optional[str] = None
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    token_tid: Optional[str] = None
    output_format: str = "table"


class ConfigParseError(Exception):
    """Raised when config file contains malformed content."""
    def __init__(self, line_number: int, line_content: str, message: str):
        self.line_number = line_number
        self.line_content = line_content
        super().__init__(f"Line {line_number}: {message}: {line_content!r}")


class ConfigParser:
    """
    Parses ~/.icav2-cli-plugins/config in AWS-style INI format.

    Sections:
      [default]            -> default profile
      [profile my-tenant]  -> named profile "my-tenant"

    Keys: key = value (whitespace trimmed, comments with # or ;)
    """

    # Known keys that map to ProfileConfig fields
    _KNOWN_KEYS = frozenset({
        'server_url', 'x_api_key', 'project_id',
        'project_name', 'token_tid', 'output_format',
    })

    def parse(self, content: str) -> Dict[str, ProfileConfig]:
        """Parse config file content into profile dict."""
        profiles: Dict[str, ProfileConfig] = {}
        # Track raw key-value pairs per section before constructing ProfileConfig
        sections: Dict[str, Dict[str, str]] = {}
        current_section: Optional[str] = None

        lines = content.split('\n')

        for line_num, raw_line in enumerate(lines, start=1):
            # Strip the line for analysis
            line = raw_line.strip()

            # Skip blank lines
            if not line:
                continue

            # Skip comment lines (first non-whitespace is # or ;)
            if line[0] in ('#', ';'):
                continue

            # Check for section header
            if line.startswith('['):
                current_section = self._parse_section_header(line, line_num, raw_line)
                if current_section not in sections:
                    sections[current_section] = {}
                continue

            # Must be a key=value pair
            if '=' not in line:
                raise ConfigParseError(
                    line_number=line_num,
                    line_content=raw_line,
                    message="no '=' delimiter found"
                )

            # Split on first = only
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if current_section is None:
                raise ConfigParseError(
                    line_number=line_num,
                    line_content=raw_line,
                    message="key-value pair found before any section header"
                )

            # Last occurrence wins for duplicate keys
            sections[current_section][key] = value

        # Build ProfileConfig objects from parsed sections
        for section_name, kvs in sections.items():
            # Validate output_format if present
            if 'output_format' in kvs:
                fmt = kvs['output_format']
                if fmt not in VALID_OUTPUT_FORMATS:
                    raise ConfigParseError(
                        line_number=0,
                        line_content=f"output_format = {fmt}",
                        message=f"invalid output_format '{fmt}', must be one of {VALID_OUTPUT_FORMATS}"
                    )

            profiles[section_name] = ProfileConfig(
                name=section_name,
                server_url=kvs.get('server_url', 'ica.illumina.com'),
                x_api_key=kvs.get('x_api_key'),
                project_id=kvs.get('project_id'),
                project_name=kvs.get('project_name'),
                token_tid=kvs.get('token_tid'),
                output_format=kvs.get('output_format', 'table'),
            )

        return profiles

    def _parse_section_header(self, line: str, line_num: int, raw_line: str) -> str:
        """Parse a section header line and return the profile name."""
        # Must end with ]
        if not line.endswith(']'):
            raise ConfigParseError(
                line_number=line_num,
                line_content=raw_line,
                message="invalid section header (missing closing ']')"
            )

        # Extract content between [ and ]
        header_content = line[1:-1].strip()

        # [default] section
        if header_content == 'default':
            return 'default'

        # [profile <name>] section
        if header_content.startswith('profile '):
            profile_name = header_content[len('profile '):].strip()
            if not profile_name:
                raise ConfigParseError(
                    line_number=line_num,
                    line_content=raw_line,
                    message="empty profile name"
                )
            if not re.match(PROFILE_NAME_REGEX, profile_name):
                raise ConfigParseError(
                    line_number=line_num,
                    line_content=raw_line,
                    message=f"invalid profile name '{profile_name}' "
                            f"(must match {PROFILE_NAME_REGEX})"
                )
            return profile_name

        # Unrecognized section header format
        raise ConfigParseError(
            line_number=line_num,
            line_content=raw_line,
            message=f"invalid section header '[{header_content}]' "
                    f"(expected '[default]' or '[profile <name>]')"
        )

    def serialize(self, profiles: Dict[str, ProfileConfig]) -> str:
        """Serialize profiles back to INI format."""
        sections: list[str] = []

        # Determine section ordering: default first, then named profiles alphabetically
        profile_names = sorted(
            (name for name in profiles if name != 'default')
        )
        if 'default' in profiles:
            profile_names = ['default'] + profile_names

        for name in profile_names:
            profile = profiles[name]

            # Build section header
            if name == 'default':
                header = '[default]'
            else:
                header = f'[profile {name}]'

            # Build key-value lines for non-None fields
            lines: list[str] = [header]

            if profile.server_url is not None:
                lines.append(f'server_url = {profile.server_url}')
            if profile.x_api_key is not None:
                lines.append(f'x_api_key = {profile.x_api_key}')
            if profile.project_id is not None:
                lines.append(f'project_id = {profile.project_id}')
            if profile.project_name is not None:
                lines.append(f'project_name = {profile.project_name}')
            if profile.token_tid is not None:
                lines.append(f'token_tid = {profile.token_tid}')
            if profile.output_format is not None:
                lines.append(f'output_format = {profile.output_format}')

            sections.append('\n'.join(lines))

        return '\n\n'.join(sections) + '\n'

    def parse_file(self, path: Path) -> Dict[str, ProfileConfig]:
        """Read and parse a config file from disk."""
        if not path.exists():
            raise ConfigParseError(
                line_number=0,
                line_content="",
                message=f"Config file not found: {path}"
            )
        try:
            content = path.read_text(encoding="utf-8")
        except PermissionError as e:
            raise ConfigParseError(
                line_number=0,
                line_content="",
                message=f"Cannot read config file (permission denied): {path}"
            ) from e
        except OSError as e:
            raise ConfigParseError(
                line_number=0,
                line_content="",
                message=f"Cannot read config file: {path}: {e}"
            ) from e
        return self.parse(content)

    def write_file(self, path: Path, profiles: Dict[str, ProfileConfig]) -> None:
        """Serialize and write profiles to disk with mode 0600."""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.serialize(profiles)
        path.write_text(content, encoding="utf-8")
        os.chmod(path, 0o600)
