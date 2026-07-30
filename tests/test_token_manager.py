#!/usr/bin/env python3
"""
Unit tests for TokenManager.

Tests caching, freshness checking, and token generation logic.
"""

import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import jwt
import pytest

from icav2_cli_plugins.utils.token_manager import TokenManager


def _make_jwt(exp: int, extra_claims: dict | None = None) -> str:
    """Helper: create a JWT with given exp claim."""
    payload = {"exp": exp, "iss": "test"}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, "secret", algorithm="HS256")


class TestTokenManagerInit:
    def test_cache_path_computed(self, tmp_path: Path):
        tm = TokenManager("my-profile", tmp_path)
        assert tm._cache_path == tmp_path / "my-profile" / "session.yaml"

    def test_stores_profile_name(self, tmp_path: Path):
        tm = TokenManager("prod", tmp_path)
        assert tm.profile_name == "prod"


class TestReadCache:
    def test_returns_none_when_no_file(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        assert tm._read_cache() is None

    def test_reads_valid_cache(self, tmp_path: Path):
        cache_dir = tmp_path / "test"
        cache_dir.mkdir(parents=True)
        session_file = cache_dir / "session.yaml"
        session_file.write_text("access_token: my-token-value\ntoken_epoch: 12345\n")

        tm = TokenManager("test", tmp_path)
        assert tm._read_cache() == "my-token-value"

    def test_returns_none_for_malformed_yaml(self, tmp_path: Path):
        cache_dir = tmp_path / "test"
        cache_dir.mkdir(parents=True)
        session_file = cache_dir / "session.yaml"
        session_file.write_text(":::invalid yaml[[[")

        tm = TokenManager("test", tmp_path)
        assert tm._read_cache() is None

    def test_returns_none_when_key_missing(self, tmp_path: Path):
        cache_dir = tmp_path / "test"
        cache_dir.mkdir(parents=True)
        session_file = cache_dir / "session.yaml"
        session_file.write_text("token_epoch: 12345\n")

        tm = TokenManager("test", tmp_path)
        assert tm._read_cache() is None

    def test_returns_none_when_value_not_string(self, tmp_path: Path):
        cache_dir = tmp_path / "test"
        cache_dir.mkdir(parents=True)
        session_file = cache_dir / "session.yaml"
        session_file.write_text("access_token: 12345\ntoken_epoch: 12345\n")

        tm = TokenManager("test", tmp_path)
        # Integer value, not a string
        assert tm._read_cache() is None


class TestWriteCache:
    def test_creates_directories_and_file(self, tmp_path: Path):
        tm = TokenManager("new-profile", tmp_path)
        tm._write_cache("my-token")

        assert tm._cache_path.exists()
        assert (tmp_path / "new-profile").is_dir()

    def test_writes_correct_yaml_content(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        before = int(time.time())
        tm._write_cache("token-abc")
        after = int(time.time())

        from ruamel.yaml import YAML
        yaml = YAML()
        with open(tm._cache_path) as fh:
            data = yaml.load(fh)

        assert data["access_token"] == "token-abc"
        assert before <= data["token_epoch"] <= after

    def test_sets_permissions_0600(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        tm._write_cache("secure-token")

        import stat
        mode = tm._cache_path.stat().st_mode & 0o777
        assert mode == 0o600


class TestIsTokenFresh:
    def test_fresh_token(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        # Token expires in 2 hours (7200 seconds) — well above threshold
        exp = int(time.time()) + 7200
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is True

    def test_stale_token_at_threshold(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        # Token expires exactly at threshold (3600 seconds)
        exp = int(time.time()) + 3600
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is False

    def test_stale_token_below_threshold(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        # Token expires in 1800 seconds — below threshold
        exp = int(time.time()) + 1800
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is False

    def test_expired_token(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        # Already expired
        exp = int(time.time()) - 100
        token = _make_jwt(exp)
        assert tm._is_token_fresh(token) is False

    def test_invalid_jwt(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        assert tm._is_token_fresh("not-a-jwt") is False

    def test_jwt_without_exp_claim(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)
        # JWT without exp claim
        token = jwt.encode({"iss": "test"}, "secret", algorithm="HS256")
        assert tm._is_token_fresh(token) is False


class TestGenerateToken:
    def test_successful_generation(self, tmp_path: Path):
        tm = TokenManager("prod", tmp_path)

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
        tm = TokenManager("prod", tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"access_token": "fallback-token"}

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            result = tm._generate_token("key", "https://ica.illumina.com/ica/rest")

        assert result == "fallback-token"

    def test_raises_on_http_error(self, tmp_path: Path):
        tm = TokenManager("prod", tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 403

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to generate token.*prod"):
                tm._generate_token("bad-key", "https://ica.illumina.com/ica/rest")

    def test_raises_when_no_token_in_response(self, tmp_path: Path):
        tm = TokenManager("prod", tmp_path)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"something_else": "value"}

        with patch("icav2_cli_plugins.utils.token_manager.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="response did not contain a token"):
                tm._generate_token("key", "https://ica.illumina.com/ica/rest")


class TestGetValidToken:
    def test_returns_cached_fresh_token(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)

        # Write a fresh token to cache
        exp = int(time.time()) + 7200
        fresh_token = _make_jwt(exp)
        tm._write_cache(fresh_token)

        # Should return cached token without calling _generate_token
        with patch.object(tm, "_generate_token") as mock_gen:
            result = tm.get_valid_token("api-key", "https://ica.illumina.com/ica/rest")

        assert result == fresh_token
        mock_gen.assert_not_called()

    def test_generates_new_when_cache_stale(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)

        # Write a stale token to cache
        exp = int(time.time()) + 1000  # Below threshold
        stale_token = _make_jwt(exp)
        tm._write_cache(stale_token)

        # Should generate a new token
        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token) as mock_gen:
            result = tm.get_valid_token("api-key", "https://ica.illumina.com/ica/rest")

        assert result == new_token
        mock_gen.assert_called_once_with("api-key", "https://ica.illumina.com/ica/rest")

    def test_generates_new_when_no_cache(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token) as mock_gen:
            result = tm.get_valid_token("api-key", "https://ica.illumina.com/ica/rest")

        assert result == new_token
        mock_gen.assert_called_once()

    def test_generates_new_when_cache_malformed(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)

        # Write malformed content
        tm._cache_path.parent.mkdir(parents=True, exist_ok=True)
        tm._cache_path.write_text("not valid yaml::: [[")

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token) as mock_gen:
            result = tm.get_valid_token("api-key", "https://ica.illumina.com/ica/rest")

        assert result == new_token
        mock_gen.assert_called_once()

    def test_writes_cache_after_generation(self, tmp_path: Path):
        tm = TokenManager("test", tmp_path)

        new_exp = int(time.time()) + 7200
        new_token = _make_jwt(new_exp)

        with patch.object(tm, "_generate_token", return_value=new_token):
            tm.get_valid_token("api-key", "https://ica.illumina.com/ica/rest")

        # Verify the cache was written
        assert tm._cache_path.exists()
        cached = tm._read_cache()
        assert cached == new_token


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
