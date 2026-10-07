#!/usr/bin/env python3
"""
Token manager for access token lifecycle management.

Handles token validation, refresh, and persistence in the config file.
Tokens are stored in the profile's config section (optionally encrypted)
and auto-refreshed when expired or within the refresh threshold.

Refresh threshold: 3600 seconds before expiry
"""

import sys
import time
from typing import Optional
from pathlib import Path

import jwt
import requests

from icav2_cli_plugins.utils.globals import TOKEN_REFRESH_THRESHOLD
from icav2_cli_plugins.utils.api_key_encryption import (
    encrypt_api_key,
    is_encrypted,
    resolve_api_key,
)


def validate_env_token(token: str) -> str:
    """
    Validate a JWT token from ICAV2_ACCESS_TOKEN environment variable.

    Returns the token if valid. Raises SystemExit if expired or malformed.
    Does NOT fall back to profile token - this is a hard error.
    """
    # Try to decode the JWT without signature verification
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=["HS256", "RS256"],
        )
    except (jwt.DecodeError, jwt.InvalidTokenError):
        print(
            "Error: ICAV2_ACCESS_TOKEN is malformed (not a valid JWT). "
            "Unset the variable or provide a valid token.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check for exp claim
    exp = payload.get("exp")
    if exp is None:
        print(
            "Error: ICAV2_ACCESS_TOKEN is missing the 'exp' claim. "
            "Unset the variable or provide a valid token.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check if token is expired
    if exp <= time.time():
        print(
            "Error: ICAV2_ACCESS_TOKEN is expired. "
            "Unset the variable or provide a valid token.",
            file=sys.stderr,
        )
        sys.exit(1)

    return token


class TokenManager:
    """
    Manages access token lifecycle per profile.

    Tokens are stored directly in the config file alongside other profile
    fields (access_token and access_token_expiry). If encryption keys are
    configured, the access token is encrypted at rest just like the API key.

    Refresh threshold: 3600 seconds before expiry.
    """

    def __init__(
        self,
        profile_name: str,
        config_path: Path,
        private_key_path: Optional[Path] = None,
        public_key_path: Optional[Path] = None,
    ):
        self.profile_name = profile_name
        self.config_path = config_path
        self.private_key_path = private_key_path
        self.public_key_path = public_key_path

    def get_valid_token(self, api_key: str, base_url: str, cached_token: Optional[str] = None) -> str:
        """
        Return a valid access token.

        Checks the cached token from config first. If fresh, returns it directly.
        If stale/absent, generates a new one from the API key (decrypting if needed),
        persists the new token back to config (encrypting if keys are available),
        and returns it.

        Args:
            api_key: The stored API key (may be encrypted).
            base_url: The ICAv2 base URL for token generation.
            cached_token: The access_token value from the config (may be encrypted or None).

        Returns:
            A valid plain-text access token ready for use.
        """
        # Try using the cached token from config
        if cached_token is not None:
            plain_token = self._resolve_secret(cached_token)
            if plain_token and self._is_token_fresh(plain_token):
                return plain_token

        # Cached token is stale/absent/invalid — generate a new one
        plain_api_key = self._resolve_secret(api_key)
        new_token = self._generate_token(plain_api_key, base_url)

        # Persist the new token back to the config file
        self._persist_token(new_token)

        return new_token

    def _resolve_secret(self, value: str) -> str:
        """Resolve a secret value, decrypting if necessary."""
        if not is_encrypted(value):
            return value

        try:
            return resolve_api_key(
                stored_value=value,
                private_key_path=self.private_key_path,
            )
        except (FileNotFoundError, ValueError) as e:
            print(
                f"Error: Cannot decrypt value for profile '{self.profile_name}': {e}",
                file=sys.stderr,
            )
            sys.exit(1)

    def _encrypt_if_keys_available(self, plaintext: str) -> str:
        """Encrypt a value if public key is available, otherwise return as-is."""
        if self.public_key_path and self.public_key_path.exists():
            try:
                return encrypt_api_key(plaintext, self.public_key_path)
            except (ValueError, FileNotFoundError):
                # Can't encrypt — store plain
                return plaintext
        return plaintext

    def _is_token_fresh(self, token: str) -> bool:
        """Check if token has >3600 seconds until exp claim."""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
            exp = payload.get("exp")
            if exp is None:
                return False
            return (exp - time.time()) > TOKEN_REFRESH_THRESHOLD
        except (jwt.DecodeError, jwt.InvalidTokenError, KeyError, Exception):
            # Not a valid JWT — treat as stale
            return False

    def _get_token_expiry(self, token: str) -> Optional[int]:
        """Extract the exp claim from a JWT token."""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=["HS256", "RS256"],
            )
            return payload.get("exp")
        except (jwt.DecodeError, jwt.InvalidTokenError):
            return None

    def _generate_token(self, api_key: str, base_url: str) -> str:
        """Generate new access token from API key via ICAv2 API."""
        url = f"{base_url}/api/tokens"

        response = requests.post(
            url,
            headers={
                "Accept": "application/vnd.illumina.v3+json",
                "X-API-Key": api_key,
            },
            data="",
        )

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Failed to generate token for profile '{self.profile_name}' "
                f"at {base_url}: HTTP {response.status_code}"
            )

        response_json = response.json()
        token = response_json.get("token")
        if token is None:
            # Fallback: some API versions use "access_token"
            token = response_json.get("access_token")

        if token is None:
            raise RuntimeError(
                f"Failed to generate token for profile '{self.profile_name}' "
                f"at {base_url}: response did not contain a token"
            )

        return token

    def _persist_token(self, token: str) -> None:
        """
        Write the new token back to the config file for this profile.

        Encrypts the token if encryption keys are available.
        Also stores the expiry epoch for quick checks.
        """
        from icav2_cli_plugins.utils.config_parser import ConfigParser, ConfigParseError

        parser = ConfigParser()

        try:
            profiles = parser.parse_file(self.config_path)
        except ConfigParseError:
            # If config can't be read, skip persistence (token still usable in memory)
            return

        if self.profile_name not in profiles:
            return

        profile = profiles[self.profile_name]

        # Encrypt the token if keys are available
        stored_token = self._encrypt_if_keys_available(token)
        profile.access_token = stored_token

        # Store the expiry epoch as a string for easy comparison
        expiry = self._get_token_expiry(token)
        if expiry is not None:
            profile.access_token_expiry = str(expiry)

        # Write the updated config back
        parser.write_file(self.config_path, profiles)
