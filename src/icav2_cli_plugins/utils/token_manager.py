#!/usr/bin/env python3
"""
Token manager for access token lifecycle management.

Handles token caching, validation, and refresh per profile.
Cache location: ~/.icav2-cli-plugins/cache/<profile_name>/session.yaml
Refresh threshold: 3600 seconds before expiry
"""

import os
import sys
import time
from typing import Optional
from pathlib import Path

import jwt
import requests
from ruamel.yaml import YAML

from icav2_cli_plugins.utils.globals import TOKEN_REFRESH_THRESHOLD


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

    Cache location: ~/.icav2-cli-plugins/cache/<profile_name>/session.yaml
    Refresh threshold: 3600 seconds before expiry
    """

    def __init__(self, profile_name: str, cache_dir: Path):
        self.profile_name = profile_name
        self.cache_dir = cache_dir
        self._cache_path = cache_dir / profile_name / "session.yaml"

    def get_valid_token(self, api_key: str, base_url: str) -> str:
        """
        Return a valid access token, using cache if fresh enough.
        Generates new token from API key if cache is stale/absent.
        """
        cached_token = self._read_cache()
        if cached_token is not None and self._is_token_fresh(cached_token):
            return cached_token

        # Cache miss or stale token — generate a new one
        new_token = self._generate_token(api_key, base_url)
        self._write_cache(new_token)
        return new_token

    def _read_cache(self) -> Optional[str]:
        """Read cached token from session.yaml."""
        if not self._cache_path.exists():
            return None

        try:
            yaml = YAML()
            with open(self._cache_path, "r") as fh:
                data = yaml.load(fh)

            if not isinstance(data, dict):
                return None

            token = data.get("access_token")
            if token is None or not isinstance(token, str):
                return None

            return token
        except Exception:
            # Malformed YAML or any read error — treat as absent
            return None

    def _write_cache(self, token: str) -> None:
        """Write token to session.yaml with mode 0600."""
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "access_token": token,
            "token_epoch": int(time.time()),
        }

        yaml = YAML()
        with open(self._cache_path, "w") as fh:
            yaml.dump(data, fh)

        # Set file permissions to owner read/write only
        os.chmod(self._cache_path, 0o600)

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
