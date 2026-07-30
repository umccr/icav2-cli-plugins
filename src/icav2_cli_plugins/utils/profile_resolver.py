#!/usr/bin/env python3
"""
Profile resolver for determining the active configuration.

Resolves the active configuration by applying precedence:
1. Explicit env vars (ICAV2_ACCESS_TOKEN, ICAV2_PROJECT_ID, ICAV2_BASE_URL)
2. --profile CLI flag or ICAV2_PROFILE env var
3. ICAV2_TENANT_NAME env var (backward compat, treated as profile name)
4. [default] profile in config file
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from icav2_cli_plugins.utils.config_parser import ConfigParser, ConfigParseError


@dataclass
class ResolvedConfig:
    """Final resolved configuration after applying precedence."""
    profile_name: str
    server_url: str
    base_url: str
    access_token: Optional[str]
    project_id: Optional[str]
    api_key: Optional[str]
    output_format: str


class ProfileResolver:
    """
    Resolves the active configuration by applying precedence:
    1. Explicit env vars (ICAV2_ACCESS_TOKEN, ICAV2_PROJECT_ID, ICAV2_BASE_URL)
    2. --profile CLI flag or ICAV2_PROFILE env var
    3. ICAV2_TENANT_NAME env var (backward compat, treated as profile name)
    4. [default] profile in config file
    """

    def __init__(self, config_path: Path, cli_profile: Optional[str] = None):
        self.config_path = config_path
        self.cli_profile = cli_profile

    def resolve(self) -> ResolvedConfig:
        """Resolve configuration from all sources."""
        # Parse the config file, handling missing/unreadable errors
        parser = ConfigParser()
        try:
            profiles = parser.parse_file(self.config_path)
        except ConfigParseError as e:
            print(
                f"Error: Config file not found at {self.config_path}. "
                f"Run 'icav2 configure set' to create one.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Determine which profile to load
        profile_name = self._determine_profile_name()

        # Handle the case where config exists but has no profiles at all
        if not profiles:
            print(
                "Error: No profiles configured. Run 'icav2 configure set' to create one.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Look up the profile in parsed config
        if profile_name not in profiles:
            available = list(profiles.keys())
            available_str = ", ".join(available)

            # Distinguish between "no default" vs "requested profile not found"
            if profile_name == "default" and not self._has_explicit_profile_source():
                print(
                    f"Error: No default profile configured. "
                    f"Available profiles: {available_str}. "
                    f"Set ICAV2_PROFILE or run 'icav2 configure set'.",
                    file=sys.stderr,
                )
            else:
                print(
                    f"Error: Profile '{profile_name}' not found. "
                    f"Available profiles: {available_str}",
                    file=sys.stderr,
                )
            sys.exit(1)

        profile = profiles[profile_name]

        # Build ResolvedConfig from profile values
        server_url = profile.server_url or "ica.illumina.com"
        base_url = f"https://{server_url}/ica/rest"

        config = ResolvedConfig(
            profile_name=profile_name,
            server_url=server_url,
            base_url=base_url,
            access_token=None,
            project_id=profile.project_id,
            api_key=profile.x_api_key,
            output_format=profile.output_format or "table",
        )

        # Apply environment variable overrides
        config = self._apply_env_overrides(config)

        return config

    def _has_explicit_profile_source(self) -> bool:
        """Check if a profile name was explicitly provided via CLI flag or env vars."""
        if self.cli_profile is not None:
            return True
        if os.environ.get("ICAV2_PROFILE", ""):
            return True
        if os.environ.get("ICAV2_TENANT_NAME", ""):
            return True
        return False

    def _determine_profile_name(self) -> str:
        """Determine which profile to load from config."""
        # 1. --profile CLI flag takes highest precedence
        if self.cli_profile is not None:
            return self.cli_profile

        # 2. ICAV2_PROFILE env var
        icav2_profile = os.environ.get("ICAV2_PROFILE", "")
        if icav2_profile:
            return icav2_profile

        # 3. ICAV2_TENANT_NAME env var (backward compat)
        tenant_name = os.environ.get("ICAV2_TENANT_NAME", "")
        if tenant_name:
            return tenant_name

        # 4. Fall back to default profile
        return "default"

    def _apply_env_overrides(self, config: ResolvedConfig) -> ResolvedConfig:
        """Apply environment variable overrides on top of profile values."""
        # ICAV2_ACCESS_TOKEN overrides token
        access_token = os.environ.get("ICAV2_ACCESS_TOKEN", "")
        if access_token:
            config.access_token = access_token

        # ICAV2_PROJECT_ID overrides project_id
        project_id = os.environ.get("ICAV2_PROJECT_ID", "")
        if project_id:
            config.project_id = project_id

        # ICAV2_BASE_URL overrides base_url
        base_url = os.environ.get("ICAV2_BASE_URL", "")
        if base_url:
            config.base_url = base_url

        return config
