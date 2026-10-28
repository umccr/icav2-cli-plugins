#!/usr/bin/env python3
"""
Configure generate-keys command - generate RSA key pair for API key encryption.

Creates an RSA-4096 key pair at ~/.icav2-cli-plugins/keys/ (or a custom path)
for encrypting API keys stored in the config file.
"""

import sys
from getpass import getpass
from pathlib import Path

from docopt import docopt

from icav2_cli_plugins.utils.api_key_encryption import (
    DEFAULT_PRIVATE_KEY_PATH,
    DEFAULT_PUBLIC_KEY_PATH,
    generate_key_pair,
)


class Command:
    """
Usage:
    icav2 configure generate-keys help
    icav2 configure generate-keys [--private-key=<path>] [--public-key=<path>] [--no-passphrase]

Description:
    Generate an RSA key pair for encrypting API keys in the config file.

    By default, keys are stored at:
      Private: ~/.icav2-cli-plugins/keys/id_rsa
      Public:  ~/.icav2-cli-plugins/keys/id_rsa.pub

    The private key can optionally be protected with a passphrase.
    You will be prompted for a passphrase unless --no-passphrase is specified.

Options:
    --private-key=<path>    Path to write the private key [default: ~/.icav2-cli-plugins/keys/id_rsa]
    --public-key=<path>     Path to write the public key [default: ~/.icav2-cli-plugins/keys/id_rsa.pub]
    --no-passphrase         Do not protect the private key with a passphrase

Examples:
    icav2 configure generate-keys
    icav2 configure generate-keys --no-passphrase
    icav2 configure generate-keys --private-key=~/.ssh/icav2_rsa --public-key=~/.ssh/icav2_rsa.pub
    """

    def __init__(self, command_argv):
        self.args = docopt(self.__doc__, argv=command_argv)

        # Print help if requested
        if self.args.get("help"):
            print(self.__doc__)
            sys.exit(0)

        # Resolve key paths
        private_key_arg = self.args.get("--private-key")
        public_key_arg = self.args.get("--public-key")

        self.private_key_path = (
            Path(private_key_arg).expanduser()
            if private_key_arg
            else DEFAULT_PRIVATE_KEY_PATH
        )
        self.public_key_path = (
            Path(public_key_arg).expanduser()
            if public_key_arg
            else DEFAULT_PUBLIC_KEY_PATH
        )
        self.no_passphrase = self.args.get("--no-passphrase", False)

    def __call__(self):
        # Prompt for passphrase unless --no-passphrase is specified
        passphrase = None
        if not self.no_passphrase:
            passphrase = self._prompt_passphrase()

        # Generate the key pair
        try:
            private_path, public_path = generate_key_pair(
                private_key_path=self.private_key_path,
                public_key_path=self.public_key_path,
                passphrase=passphrase,
            )
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        # Report success
        print(f"RSA key pair generated successfully:")
        print(f"  Private key: {private_path} (mode 0600)")
        print(f"  Public key:  {public_path} (mode 0644)")
        print()
        if passphrase:
            print("The private key is protected with a passphrase.")
            print("You will be prompted for it when decrypting API keys.")
        else:
            print("The private key is NOT passphrase-protected.")
            print("Consider using a passphrase for additional security.")
        print()
        print("To encrypt API keys during profile setup, run:")
        print("  icav2 configure set <profile_name>")
        print()
        print("Encryption keys will be detected automatically from the default location.")

    @staticmethod
    def _prompt_passphrase() -> str | None:
        """Prompt for a passphrase with confirmation."""
        try:
            passphrase = getpass("Enter passphrase for private key (empty for no passphrase): ")
            if not passphrase:
                return None
            confirm = getpass("Confirm passphrase: ")
            if passphrase != confirm:
                print("Error: Passphrases do not match.", file=sys.stderr)
                sys.exit(1)
            return passphrase
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.", file=sys.stderr)
            sys.exit(1)
