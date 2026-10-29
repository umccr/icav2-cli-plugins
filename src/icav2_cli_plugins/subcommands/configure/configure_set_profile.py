#!/usr/bin/env python3
"""
Configure set-profile command - interactively configure a profile.

Prompts for an existing tenant_name, a project_name, and an output_format,
resolves the project name to a project ID using the referenced tenant's
credentials, and saves the profile (project-scoped configuration) to the
config file.

The profile does NOT store server_url or x_api_key; those live on the tenant
section it references.
"""

import sys

import requests
from docopt import docopt

from icav2_cli_plugins.utils.config_parser import (
    ConfigParser,
    ConfigParseError,
    ProfileConfig,
)
from icav2_cli_plugins.utils.globals import CONFIG_FILE_PATH, VALID_OUTPUT_FORMATS
from icav2_cli_plugins.utils.token_manager import TokenManager


class Command:
    """
Usage:
    icav2 configure set-profile help
    icav2 configure set-profile <profile_name>

Description:
    Interactively configure a profile (project-scoped configuration). Prompts
    for an existing tenant name, a project name, and an output format. Resolves
    the project name to a project ID using the referenced tenant's credentials
    before saving.

    The referenced tenant must already exist (run 'icav2 configure set-tenant'
    first). The profile stores project_id, project_name, tenant_name and
    output_format only; server_url and x_api_key live on the tenant section.

Options:
    <profile_name>          Name of the profile to configure (required)

Examples:
    icav2 configure set-profile production
    """

    def __init__(self, command_argv):
        self.args = docopt(self.__doc__, argv=command_argv)

        # Print help if requested
        if self.args.get("help"):
            print(self.__doc__)
            sys.exit(0)

        self.profile_name = self.args.get("<profile_name>")

    def __call__(self):
        # Load existing config (profiles can only be created once a tenant exists)
        parser = ConfigParser()
        try:
            tenants, profiles = parser.parse_file(CONFIG_FILE_PATH)
        except ConfigParseError:
            tenants, profiles = {}, {}

        # Prompt for the tenant this profile references
        tenant_name = input("Tenant name: ").strip()
        if tenant_name not in tenants:
            available = ", ".join(sorted(tenants.keys())) if tenants else "(none)"
            print(
                f"Error: Tenant '{tenant_name}' is not configured. "
                f"Run 'icav2 configure set-tenant' first. "
                f"Available tenants: {available}",
                file=sys.stderr,
            )
            sys.exit(1)

        tenant = tenants[tenant_name]

        # Prompt for project name and output format
        project_name = input("Project name: ").strip() or None
        output_format = input("Output format [table]: ").strip() or "table"
        if output_format not in VALID_OUTPUT_FORMATS:
            print(
                f"Error: Invalid output_format '{output_format}', "
                f"must be one of {sorted(VALID_OUTPUT_FORMATS)}.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Resolve project name to project ID using the referenced tenant
        project_id = None
        if project_name:
            base_url = f"https://{tenant.server_url}/ica/rest"
            token_manager = TokenManager(
                tenant_name=tenant_name,
                config_path=CONFIG_FILE_PATH,
            )
            try:
                access_token = token_manager.get_valid_token(
                    api_key=tenant.x_api_key,
                    base_url=base_url,
                    cached_token=tenant.access_token,
                )
            except RuntimeError as e:
                print(
                    f"Error: Could not obtain an access token for tenant "
                    f"'{tenant_name}': {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

            project_id = self._resolve_project_id(
                base_url=base_url,
                project_name=project_name,
                access_token=access_token,
            )

        # Create/overwrite the profile
        profiles[self.profile_name] = ProfileConfig(
            name=self.profile_name,
            project_id=project_id,
            project_name=project_name,
            tenant_name=tenant_name,
            output_format=output_format,
        )

        # Write config file (creates file + parent dirs with mode 0600)
        parser.write_file(CONFIG_FILE_PATH, tenants, profiles)

        print(f"Profile '{self.profile_name}' configured successfully.")

    @staticmethod
    def _resolve_project_id(base_url: str, project_name: str, access_token: str) -> str:
        """
        Resolve a project name to its project ID via the ICAv2 API.

        Lists all projects accessible with the given token and matches by name.
        Exits with an error if the project cannot be found.
        """
        url = f"{base_url}/api/projects"
        response = requests.get(
            url,
            headers={
                "Accept": "application/vnd.illumina.v3+json",
                "Authorization": f"Bearer {access_token}",
            },
        )

        if response.status_code != 200:
            print(
                f"Error: Failed to list projects (HTTP {response.status_code}). "
                f"Cannot resolve project name '{project_name}' to an ID.",
                file=sys.stderr,
            )
            sys.exit(1)

        projects = response.json().get("items", [])
        for project in projects:
            if project.get("name") == project_name:
                return project.get("id")

        # Project not found — show available projects to help the user
        available = [p.get("name") for p in projects if p.get("name")]
        print(
            f"Error: Project '{project_name}' not found.",
            file=sys.stderr,
        )
        if available:
            print(
                f"Available projects: {', '.join(sorted(available))}",
                file=sys.stderr,
            )
        sys.exit(1)
