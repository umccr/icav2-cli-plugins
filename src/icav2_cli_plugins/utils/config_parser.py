#!/usr/bin/env python3
"""
Config file parser for INI-style two-level configuration.

Handles the AWS CLI-style config format with two kinds of sections:
  [tenant my-tenant]   -> user-scoped tenant configuration
  [default]            -> default profile
  [profile my-profile] -> named profile "my-profile"

A profile is project-scoped and points at a tenant via its tenant_name key.
The tenant carries the user-scoped secrets (API key, access token, encryption
keys) that are shared across every project/profile in that tenant.

Keys: key = value (whitespace trimmed, comments with # or ;)
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from pathlib import Path

from icav2_cli_plugins.utils.globals import PROFILE_NAME_REGEX, VALID_OUTPUT_FORMATS


@dataclass
class TenantConfig:
    """Represents a single parsed tenant (user-scoped configuration)."""
    name: str
    server_url: str = "ica.illumina.com"
    x_api_key: Optional[str] = None
    encryption_public_key: Optional[str] = None
    encryption_private_key: Optional[str] = None
    access_token: Optional[str] = None
    access_token_expiry: Optional[str] = None


@dataclass
class ProfileConfig:
    """Represents a single parsed profile (project-scoped configuration)."""
    name: str
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    tenant_name: Optional[str] = None
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
      [tenant my-tenant]   -> tenant configuration
      [default]            -> default profile
      [profile my-profile] -> named profile "my-profile"

    Keys: key = value (whitespace trimmed, comments with # or ;)
    """

    # Known keys that map to TenantConfig fields
    _TENANT_KEYS = frozenset({
        'server_url', 'x_api_key',
        'encryption_public_key', 'encryption_private_key',
        'access_token', 'access_token_expiry',
    })

    # Known keys that map to ProfileConfig fields
    _PROFILE_KEYS = frozenset({
        'project_id', 'project_name', 'tenant_name', 'output_format',
    })

    def parse(self, content: str) -> Tuple[Dict[str, TenantConfig], Dict[str, ProfileConfig]]:
        """Parse config file content into (tenants, profiles) dicts."""
        tenants: Dict[str, TenantConfig] = {}
        profiles: Dict[str, ProfileConfig] = {}

        # Track raw key-value pairs per section. Keyed by a (kind, name) tuple
        # where kind is 'tenant' or 'profile'.
        sections: Dict[Tuple[str, str], Dict[str, str]] = {}
        # Preserve insertion order of section keys
        section_order: list[Tuple[str, str]] = []
        current_section: Optional[Tuple[str, str]] = None

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
                    section_order.append(current_section)
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

        # Build TenantConfig / ProfileConfig objects from parsed sections
        for section_key in section_order:
            kind, section_name = section_key
            kvs = sections[section_key]

            if kind == 'tenant':
                tenants[section_name] = TenantConfig(
                    name=section_name,
                    server_url=kvs.get('server_url', 'ica.illumina.com'),
                    x_api_key=kvs.get('x_api_key'),
                    encryption_public_key=kvs.get('encryption_public_key'),
                    encryption_private_key=kvs.get('encryption_private_key'),
                    access_token=kvs.get('access_token'),
                    access_token_expiry=kvs.get('access_token_expiry'),
                )
                continue

            # Profile section — validate output_format if present
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
                project_id=kvs.get('project_id'),
                project_name=kvs.get('project_name'),
                tenant_name=kvs.get('tenant_name'),
                output_format=kvs.get('output_format', 'table'),
            )

        return tenants, profiles

    def _parse_section_header(
        self, line: str, line_num: int, raw_line: str
    ) -> Tuple[str, str]:
        """
        Parse a section header line and return a (kind, name) tuple.

        kind is one of 'tenant' or 'profile'.
        """
        # Must end with ]
        if not line.endswith(']'):
            raise ConfigParseError(
                line_number=line_num,
                line_content=raw_line,
                message="invalid section header (missing closing ']')"
            )

        # Extract content between [ and ]
        header_content = line[1:-1].strip()

        # [tenant <name>] section
        if header_content.startswith('tenant '):
            tenant_name = header_content[len('tenant '):].strip()
            if not tenant_name:
                raise ConfigParseError(
                    line_number=line_num,
                    line_content=raw_line,
                    message="empty tenant name"
                )
            if not re.match(PROFILE_NAME_REGEX, tenant_name):
                raise ConfigParseError(
                    line_number=line_num,
                    line_content=raw_line,
                    message=f"invalid tenant name '{tenant_name}' "
                            f"(must match {PROFILE_NAME_REGEX})"
                )
            return ('tenant', tenant_name)

        # [default] section
        if header_content == 'default':
            return ('profile', 'default')

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
            return ('profile', profile_name)

        # Unrecognized section header format
        raise ConfigParseError(
            line_number=line_num,
            line_content=raw_line,
            message=f"invalid section header '[{header_content}]' "
                    f"(expected '[tenant <name>]', '[default]' or '[profile <name>]')"
        )

    def serialize(
        self,
        tenants: Dict[str, TenantConfig],
        profiles: Dict[str, ProfileConfig],
    ) -> str:
        """Serialize tenants and profiles back to INI format."""
        sections: list[str] = []

        # Tenant sections first, alphabetical
        for name in sorted(tenants):
            tenant = tenants[name]
            lines: list[str] = [f'[tenant {name}]']

            if tenant.server_url is not None:
                lines.append(f'server_url = {tenant.server_url}')
            if tenant.x_api_key is not None:
                lines.append(f'x_api_key = {tenant.x_api_key}')
            if tenant.encryption_public_key is not None:
                lines.append(f'encryption_public_key = {tenant.encryption_public_key}')
            if tenant.encryption_private_key is not None:
                lines.append(f'encryption_private_key = {tenant.encryption_private_key}')
            if tenant.access_token is not None:
                lines.append(f'access_token = {tenant.access_token}')
            if tenant.access_token_expiry is not None:
                lines.append(f'access_token_expiry = {tenant.access_token_expiry}')

            sections.append('\n'.join(lines))

        # Profile sections: default first, then named profiles alphabetically
        profile_names = sorted(name for name in profiles if name != 'default')
        if 'default' in profiles:
            profile_names = ['default'] + profile_names

        for name in profile_names:
            profile = profiles[name]

            if name == 'default':
                header = '[default]'
            else:
                header = f'[profile {name}]'

            lines = [header]

            if profile.project_id is not None:
                lines.append(f'project_id = {profile.project_id}')
            if profile.project_name is not None:
                lines.append(f'project_name = {profile.project_name}')
            if profile.tenant_name is not None:
                lines.append(f'tenant_name = {profile.tenant_name}')
            if profile.output_format is not None:
                lines.append(f'output_format = {profile.output_format}')

            sections.append('\n'.join(lines))

        return '\n\n'.join(sections) + '\n'

    def parse_file(
        self, path: Path
    ) -> Tuple[Dict[str, TenantConfig], Dict[str, ProfileConfig]]:
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

    def write_file(
        self,
        path: Path,
        tenants: Dict[str, TenantConfig],
        profiles: Dict[str, ProfileConfig],
    ) -> None:
        """Serialize and write tenants + profiles to disk with mode 0600."""
        path.parent.mkdir(parents=True, exist_ok=True)
        content = self.serialize(tenants, profiles)
        path.write_text(content, encoding="utf-8")
        os.chmod(path, 0o600)
