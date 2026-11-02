#!/usr/bin/env python3
"""
Configure set-tenant command - interactively configure a tenant.

Prompts for server_url and x_api_key, validates the API key by attempting
token generation, optionally encrypts the API key and access token if
encryption keys are available, and saves the tenant (user-scoped
configuration) to the config file.

Unlike 'configure set', this command does NOT prompt for a project name; it
only sets up the user-scoped tenant section. Use 'configure set-profile' to
create a project-scoped profile that references this tenant.
"""

import sys
from pathlib import Path

from docopt import docopt

from icav2_cli_plugins.utils.api_key_encryption import (
    DEFAULT_PRIVATE_KEY_PATH,
    DEFAULT_PUBLIC_KEY_PATH,
    encrypt_api_key,
    is_encrypted,
)
from icav2_cli_plugins.utils.config_parser import (
    ConfigParser,
    ConfigParseError,
    TenantConfig,
)
from icav2_cli_plugins.utils.globals import CONFIG_FILE_PATH
from icav2_cli_plugins.utils.token_manager import TokenManager


class Command:
    """
Usage:
    icav2 configure set-tenant help
    icav2 configure set-tenant <tenant_name> [--no-encrypt] [--public-key=<path>] [--private-key=<path>]

Description:
    Interactively configure a tenant (user-scoped configuration). Prompts for
    server_url and x_api_key. Validates the API key by generating an access
    token, then stores the tenant section. The access token is user-scoped and
    shared across every profile that references this tenant.

    This command does NOT prompt for a project name. Use
    'icav2 configure set-profile' to create a project-scoped profile.

    If encryption keys exist at ~/.icav2-cli-plugins/keys/ (or are specified
    via --public-key/--private-key), the API key and access token will be
    encrypted before storing in the config file. Use --no-encrypt to store in
    plain text.

Options:
    <tenant_name>           Name of the tenant to configure (required)
    --no-encrypt            Store secrets in plain text even if encryption keys exist
    --public-key=<path>     Path to public key for encryption
    --private-key=<path>    Path to private key (stored in tenant for decryption)

Examples:
    icav2 configure set-tenant my-tenant
    icav2 configure set-tenant my-tenant --no-encrypt
    """

    def __init__(self, command_argv):
        self.args = docopt(self.__doc__, argv=command_argv)

        # Print help if requested
        if self.args.get("help"):
            print(self.__doc__)
            sys.exit(0)

        self.tenant_name = self.args.get("<tenant_name>")
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
        # Prompt interactively for tenant values
        server_url = input("ICA server URL [ica.illumina.com]: ").strip() or "ica.illumina.com"
        x_api_key = input("ICA API key: ").strip()

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
            tenant_name=self.tenant_name,
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
                "Tenant was not saved.",
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

        # Encrypt the access token if keys are available
        stored_access_token = access_token
        if encryption_public_key and self.public_key_path.exists():
            try:
                stored_access_token = encrypt_api_key(access_token, self.public_key_path)
            except (ValueError, FileNotFoundError):
                pass  # Store plain if encryption fails

        # Extract token expiry from the JWT
        access_token_expiry = None
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
            tenants, profiles = parser.parse_file(CONFIG_FILE_PATH)
        except ConfigParseError:
            tenants, profiles = {}, {}

        # Create/overwrite the tenant
        tenants[self.tenant_name] = TenantConfig(
            name=self.tenant_name,
            server_url=server_url,
            x_api_key=stored_api_key,
            encryption_public_key=encryption_public_key,
            encryption_private_key=encryption_private_key,
            access_token=stored_access_token,
            access_token_expiry=access_token_expiry,
        )

        # Write config file (creates file + parent dirs with mode 0600)
        parser.write_file(CONFIG_FILE_PATH, tenants, profiles)

        print(f"Tenant '{self.tenant_name}' configured successfully.")
        if is_encrypted(stored_api_key):
            print("API key is stored encrypted.")
        if is_encrypted(stored_access_token):
            print("Access token is stored encrypted.")
