#!/usr/bin/env python3
"""
Configure set command - interactively configure a profile.

Prompts for server_url, x_api_key, tenant_name, and project_name,
validates the API key by attempting token generation, optionally encrypts
the API key if encryption keys are available, resolves the project name
to a project ID, and saves the profile to the config file.
"""

import sys
from pathlib import Path

import requests
from docopt import docopt

from icav2_cli_plugins.utils.api_key_encryption import (
    DEFAULT_PRIVATE_KEY_PATH,
    DEFAULT_PUBLIC_KEY_PATH,
    encrypt_api_key,
    is_encrypted,
)
from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig, ConfigParseError
from icav2_cli_plugins.utils.globals import CONFIG_FILE_PATH
from icav2_cli_plugins.utils.token_manager import TokenManager


class Command:
    """
Usage:
    icav2 configure set help
    icav2 configure set [<profile_name>] [--no-encrypt] [--public-key=<path>] [--private-key=<path>]

Description:
    Interactively configure a profile. Prompts for server_url, x_api_key,
    tenant_name, and project_name. Validates the API key and resolves the
    project name to a project ID before saving.

    If encryption keys exist at ~/.icav2-cli-plugins/keys/ (or are specified
    via --public-key/--private-key), the API key will be encrypted before
    storing in the config file. Use --no-encrypt to store in plain text.

Options:
    <profile_name>          Name of the profile to configure (defaults to 'default')
    --no-encrypt            Store API key in plain text even if encryption keys exist
    --public-key=<path>     Path to public key for encryption
    --private-key=<path>    Path to private key (stored in profile for decryption)

Examples:
    icav2 configure set
    icav2 configure set production
    icav2 configure set production --no-encrypt
    icav2 configure set --public-key=~/.ssh/icav2_rsa.pub --private-key=~/.ssh/icav2_rsa
    """

    def __init__(self, command_argv):
        self.args = docopt(self.__doc__, argv=command_argv)

        # Print help if requested
        if self.args.get("help"):
            print(self.__doc__)
            sys.exit(0)

        self.profile_name = self.args.get("<profile_name>") or "default"
        self.no_encrypt = self.args.get("--no-encrypt", False)

        # Resolve encryption key paths
        public_key_arg = self.args.get("--public-key")
        private_key_arg = self.args.get("--private-key")

        self.public_key_path = (
            Path(public_key_arg).expanduser()
            if public_key_arg
            else DEFAULT_PUBLIC_KEY_PATH
        )
        self.private_key_path = (
            Path(private_key_arg).expanduser()
            if private_key_arg
            else DEFAULT_PRIVATE_KEY_PATH
        )

    def __call__(self):
        # Prompt interactively for profile values
        server_url = input("ICA server URL [ica.illumina.com]: ").strip() or "ica.illumina.com"
        x_api_key = input("ICA API key: ").strip()
        tenant_name = input("Tenant name: ").strip() or None
        project_name = input("Project name: ").strip() or None

        # Validate that an API key was provided
        if not x_api_key:
            print(
                "Error: API key is required.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Validate the API key by attempting token generation
        base_url = f"https://{server_url}/ica/rest"
        token_manager = TokenManager(
            profile_name=self.profile_name,
            config_path=CONFIG_FILE_PATH,
        )

        try:
            access_token = token_manager._generate_token(api_key=x_api_key, base_url=base_url)
        except RuntimeError as e:
            print(
                f"Error: API key validation failed - {e}",
                file=sys.stderr,
            )
            print(
                "The provided API key could not be validated. "
                "Profile was not saved.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Determine whether to encrypt the API key
        stored_api_key = x_api_key
        encryption_public_key = None
        encryption_private_key = None

        if not self.no_encrypt and self.public_key_path.exists():
            try:
                stored_api_key = encrypt_api_key(x_api_key, self.public_key_path)
                encryption_public_key = str(self.public_key_path)
                encryption_private_key = str(self.private_key_path)
                print(f"API key encrypted with {self.public_key_path}")
            except (ValueError, FileNotFoundError) as e:
                print(
                    f"Warning: Could not encrypt API key ({e}). Storing in plain text.",
                    file=sys.stderr,
                )
        elif not self.no_encrypt and not self.public_key_path.exists():
            print(
                "Tip: Run 'icav2 configure generate-keys' to enable API key encryption.",
                file=sys.stderr,
            )

        # Resolve project name to project ID if a project name was provided
        project_id = None
        if project_name:
            project_id = self._resolve_project_id(
                base_url=base_url,
                project_name=project_name,
                access_token=access_token,
            )

        # Encrypt the access token if keys are available
        stored_access_token = access_token
        access_token_expiry = None
        if encryption_public_key and self.public_key_path.exists():
            try:
                stored_access_token = encrypt_api_key(access_token, self.public_key_path)
            except (ValueError, FileNotFoundError):
                pass  # Store plain if encryption fails

        # Extract token expiry
        try:
            import jwt as pyjwt
            payload = pyjwt.decode(
                access_token,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
            exp = payload.get("exp")
            if exp is not None:
                access_token_expiry = str(exp)
        except Exception:
            pass

        # Load existing config (or start fresh if file doesn't exist)
        parser = ConfigParser()
        try:
            profiles = parser.parse_file(CONFIG_FILE_PATH)
        except ConfigParseError:
            # File doesn't exist or is empty — start with an empty dict
            profiles = {}

        # Create/overwrite the profile
        profiles[self.profile_name] = ProfileConfig(
            name=self.profile_name,
            server_url=server_url,
            x_api_key=stored_api_key,
            project_id=project_id,
            project_name=project_name,
            tenant_name=tenant_name,
            encryption_public_key=encryption_public_key,
            encryption_private_key=encryption_private_key,
            access_token=stored_access_token,
            access_token_expiry=access_token_expiry,
        )

        # Write config file (creates file + parent dirs with mode 0600)
        parser.write_file(CONFIG_FILE_PATH, profiles)

        print(f"Profile '{self.profile_name}' configured successfully.")
        if is_encrypted(stored_api_key):
            print("API key is stored encrypted.")
        if is_encrypted(stored_access_token):
            print("Access token is stored encrypted.")

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
