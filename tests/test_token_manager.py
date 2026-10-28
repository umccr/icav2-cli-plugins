#!/usr/bin/env python3
"""
Unit tests for TokenManager.

Tests token freshness checking, generation, persistence to config, and
the encrypted token lifecycle.
"""

import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import jwt
import pytest

from icav2_cli_plugins.utils.token_manager import TokenManager
from icav2_cli_plugins.utils.config_parser import ConfigParser, ProfileConfig


def _make_jwt(exp: int, extra_claims: dict | None = None) -> str:
    """Helper: create a JWT with given exp claim."""
    payload = {"exp": exp, "iss": "test"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, "secret", algorithm="HS256")


def _write_config(path: Path, profiles: dict[str, ProfileConfig]) -> None:
    """Helper: write a config file with given profiles."""
    parser = ConfigParser()
    parser.write_file(path, profiles)


class TestTokenManagerInit:
    def test_stores_profile_name(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("prod", config_path)
        assert tm.profile_name == "prod"

    def test_stores_config_path(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        assert tm.config_path == config_path

    def test_stores_key_paths(self, tmp_path: Path):
        config_path = tmp_path / "config"
        priv = tmp_path / "id_rsa"
        pub = tmp_path / "id_rsa.pub"
        tm = TokenManager("test", config_path, private_key_path=priv, public_key_path=pub)
        assert tm.private_key_path == priv
        assert tm.public_key_path == pub


class TestIsTokenFresh:
    def test_fresh_token(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        # Token expires in 2 hours (7200 seconds) — well above threshold
        exp = int(time.time()) + 7200
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is True

    def test_stale_token_at_threshold(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        # Token expires exactly at threshold (3600 seconds)
        exp = int(time.time()) + 3600
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is False

    def test_stale_token_below_threshold(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        # Token expires in 1800 seconds — below threshold
        exp = int(time.time()) + 1800
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is False

    def test_expired_token(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        # Already expired
        exp = int(time.time()) - 100
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is False

    def test_invalid_jwt(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        assert tm._is_token_fresh("not-a-jwt") is False

    def test_jwt_without_exp_claim(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("test", config_path)
        # JWT without exp claim
        token = jwt.encode({"iss": "test"}, "secret", algorithm="HS256")
        assert tm._is_token_fresh(token) is False


class TestGenerateToken:
    def test_successful_generation(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("prod", config_path)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "new-access-token"}

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response) as mock_post:
            result = tm._generate_token("my-api-key", "https://ica.illumina.com/ica/rest")

        assert result == "new-access-token"
        mock_post.assert_called_once_with(
            "https://ica.illumina.com/ica/rest/api/tokens",
            headers={
                "Accept": "application/vnd.illumina.v3+json",
                "X-API-Key": "my-api-key",
            },
            data="",
        )

    def test_falls_back_to_access_token_key(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("prod", config_path)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"access_token": "fallback-token"}

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            result = tm._generate_token("key", "https://ica.illumina.com/ica/rest")

        assert result == "fallback-token"

    def test_raises_on_http_error(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("prod", config_path)

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to generate token.*prod"):
                tm._generate_token("bad-key", "https://ica.illumina.com/ica/rest")

    def test_raises_when_no_token_in_response(self, tmp_path: Path):
        config_path = tmp_path / "config"
        tm = TokenManager("prod", config_path)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"something_else": "value"}

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="response did not contain a token"):
                tm._generate_token("key", "https://ica.illumina.com/ica/rest")


class TestGetValidToken:
    def test_returns_cached_fresh_token(self, tmp_path: Path):
        config_path = tmp_path / "config"

        # Create a fresh token
        exp = int(time.time()) + 7200
        fresh_token = _make_jwt(exp)

        # Write config with the cached token
        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
                access_token=fresh_token,
                access_token_expiry=str(exp),
            )
        })

        tm = TokenManager("default", config_path)

        # Should return cached token without calling _generate_token
        with patch.object(tm, "_generate_token") as mock_gen:
            result = tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=fresh_token,
            )

        assert result == fresh_token
        mock_gen.assert_not_called()

    def test_generates_new_when_cache_stale(self, tmp_path: Path):
        config_path = tmp_path / "config"

        # Create a stale token (below threshold)
        exp = int(time.time()) + 1000
        stale_token = _make_jwt(exp)

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
                access_token=stale_token,
                access_token_expiry=str(exp),
            )
        })

        tm = TokenManager("default", config_path)

        # Should generate a new token
        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token) as mock_gen:
            result = tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=stale_token,
            )

        assert result == new_token
        mock_gen.assert_called_once_with("api-key", "https://ica.illumina.com/ica/rest")

    def test_generates_new_when_no_cached_token(self, tmp_path: Path):
        config_path = tmp_path / "config"

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
            )
        })

        tm = TokenManager("default", config_path)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token) as mock_gen:
            result = tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=None,
            )

        assert result == new_token
        mock_gen.assert_called_once()

    def test_persists_token_to_config_after_generation(self, tmp_path: Path):
        config_path = tmp_path / "config"

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
            )
        })

        tm = TokenManager("default", config_path)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token):
            tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=None,
            )

        # Verify the token was persisted back to config
        parser = ConfigParser()
        profiles = parser.parse_file(config_path)
        assert profiles["default"].access_token == new_token
        assert profiles["default"].access_token_expiry == str(new_exp)

    def test_config_permissions_after_persist(self, tmp_path: Path):
        config_path = tmp_path / "config"

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
            )
        })

        tm = TokenManager("default", config_path)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token):
            tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=None,
            )

        # Verify permissions
        import stat
        mode = config_path.stat().st_mode & 0o777
        assert mode == 0o600


class TestGetValidTokenWithEncryption:
    """Tests for token encryption/decryption during get_valid_token."""

    def test_encrypted_cached_token_is_decrypted(self, tmp_path: Path):
        """A cached encrypted token is decrypted and returned if fresh."""
        from icav2_cli_plugins.utils.api_key_encryption import (
            generate_key_pair, encrypt_api_key,
        )

        config_path = tmp_path / "config"
        priv_key = tmp_path / "id_rsa"
        pub_key = tmp_path / "id_rsa.pub"
        generate_key_pair(priv_key, pub_key)

        # Create a fresh token and encrypt it
        exp = int(time.time()) + 7200
        fresh_token = _make_jwt(exp)
        encrypted_token = encrypt_api_key(fresh_token, pub_key)

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
                access_token=encrypted_token,
                access_token_expiry=str(exp),
                encryption_public_key=str(pub_key),
                encryption_private_key=str(priv_key),
            )
        })

        tm = TokenManager("default", config_path, private_key_path=priv_key, public_key_path=pub_key)

        with patch.object(tm, "_generate_token") as mock_gen:
            result = tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=encrypted_token,
            )

        assert result == fresh_token
        mock_gen.assert_not_called()

    def test_new_token_is_stored_encrypted(self, tmp_path: Path):
        """When a new token is generated, it's encrypted before persisting."""
        from icav2_cli_plugins.utils.api_key_encryption import (
            generate_key_pair, is_encrypted,
        )

        config_path = tmp_path / "config"
        priv_key = tmp_path / "id_rsa"
        pub_key = tmp_path / "id_rsa.pub"
        generate_key_pair(priv_key, pub_key)

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key="api-key",
                encryption_public_key=str(pub_key),
                encryption_private_key=str(priv_key),
            )
        })

        tm = TokenManager("default", config_path, private_key_path=priv_key, public_key_path=pub_key)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token):
            tm.get_valid_token(
                "api-key", "https://ica.illumina.com/ica/rest",
                cached_token=None,
            )

        # Verify the stored token is encrypted
        parser = ConfigParser()
        profiles = parser.parse_file(config_path)
        stored = profiles["default"].access_token
        assert is_encrypted(stored)

    def test_encrypted_api_key_is_decrypted_for_generation(self, tmp_path: Path):
        """When API key is encrypted, it's decrypted before calling _generate_token."""
        from icav2_cli_plugins.utils.api_key_encryption import (
            generate_key_pair, encrypt_api_key,
        )

        config_path = tmp_path / "config"
        priv_key = tmp_path / "id_rsa"
        pub_key = tmp_path / "id_rsa.pub"
        generate_key_pair(priv_key, pub_key)

        plain_api_key = "my-secret-api-key"
        encrypted_api_key = encrypt_api_key(plain_api_key, pub_key)

        _write_config(config_path, {
            "default": ProfileConfig(
                name="default",
                x_api_key=encrypted_api_key,
                encryption_public_key=str(pub_key),
                encryption_private_key=str(priv_key),
            )
        })

        tm = TokenManager("default", config_path, private_key_path=priv_key, public_key_path=pub_key)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token) as mock_gen:
            tm.get_valid_token(
                encrypted_api_key, "https://ica.illumina.com/ica/rest",
                cached_token=None,
            )

        # _generate_token should have received the decrypted key
        mock_gen.assert_called_once_with(plain_api_key, "https://ica.illumina.com/ica/rest")


class TestValidateEnvToken:
    """Tests for validate_env_token function."""

    def test_valid_jwt_passes(self):
        """A valid, non-expired JWT is returned as-is."""
        from icav2_cli_plugins.utils.token_manager import validate_env_token

        exp = int(time.time()) + 7200  # Expires in 2 hours
        token = _make_jwt(exp)
        result = validate_env_token(token)
        assert result == token

    def test_expired_jwt_exits(self, capsys):
        """An expired JWT causes sys.exit(1) with appropriate error message."""
        from icav2_cli_plugins.utils.token_manager import validate_env_token

        exp = int(time.time()) - 100  # Already expired
        token = _make_jwt(exp)

        with pytest.raises(SystemExit) as exc_info:
            validate_env_token(token)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ICAV2_ACCESS_TOKEN is expired" in captured.err
        assert "Unset the variable or provide a valid token" in captured.err

    def test_malformed_string_exits(self, capsys):
        """A non-JWT string causes sys.exit(1) with appropriate error message."""
        from icav2_cli_plugins.utils.token_manager import validate_env_token

        with pytest.raises(SystemExit) as exc_info:
            validate_env_token("not-a-valid-jwt-at-all")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ICAV2_ACCESS_TOKEN is malformed (not a valid JWT)" in captured.err
        assert "Unset the variable or provide a valid token" in captured.err

    def test_jwt_without_exp_exits(self, capsys):
        """A JWT missing the 'exp' claim causes sys.exit(1) with appropriate error message."""
        from icav2_cli_plugins.utils.token_manager import validate_env_token

        # Create a JWT without exp claim
        token = jwt.encode({"iss": "test", "sub": "user"}, "secret", algorithm="HS256")

        with pytest.raises(SystemExit) as exc_info:
            validate_env_token(token)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ICAV2_ACCESS_TOKEN is missing the 'exp' claim" in captured.err
        assert "Unset the variable or provide a valid token" in captured.err

    def test_no_fallback_on_expired(self):
        """Verify expired token raises SystemExit — no fallback behavior."""
        from icav2_cli_plugins.utils.token_manager import validate_env_token

        exp = int(time.time()) - 1  # Just expired
        token = _make_jwt(exp)

        with pytest.raises(SystemExit) as exc_info:
            validate_env_token(token)

        assert exc_info.value.code == 1

    def test_token_expiring_exactly_now_exits(self, capsys):
        """A token with exp equal to current time is considered expired."""
        from icav2_cli_plugins.utils.token_manager import validate_env_token

        exp = int(time.time())  # Expires right now
        token = _make_jwt(exp)

        with pytest.raises(SystemExit) as exc_info:
            validate_env_token(token)

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ICAV2_ACCESS_TOKEN is expired" in captured.err
