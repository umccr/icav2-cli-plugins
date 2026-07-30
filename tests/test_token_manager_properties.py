"""Property-based tests for the token manager."""

# Feature: profile-based-config, Property 6: Token cache freshness decision

import time
from pathlib import Path
from unittest.mock import patch

import jwt
import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from icav2_cli_plugins.utils.token_manager import TokenManager
from icav2_cli_plugins.utils.globals import TOKEN_REFRESH_THRESHOLD


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Strategy for generating exp offsets (seconds relative to "now")
# Covers a wide range: from well in the past to far in the future
exp_offset_strategy = st.integers(min_value=-86400, max_value=86400)

# Strategy for generating a fixed "now" time (realistic epoch timestamps)
fixed_now_strategy = st.integers(min_value=1_000_000_000, max_value=2_000_000_000)

# Strategy for generating malformed/invalid JWT strings
malformed_jwt_strategy = st.one_of(
    st.just(""),
    st.just("not-a-jwt"),
    st.just("abc.def.ghi"),
    st.text(min_size=0, max_size=100).filter(lambda s: "." not in s or len(s) < 5),
    st.just("eyJhbGciOiJIUzI1NiJ9.INVALID.SIGNATURE"),
)


def _make_jwt_with_exp(exp: int) -> str:
    """Create a valid JWT token with the given exp claim."""
    payload = {"exp": exp, "iss": "test", "sub": "user"}
    return jwt.encode(payload, "secret", algorithm="HS256")


# Use a fixed dummy path for TokenManager since _is_token_fresh doesn't use the filesystem
_DUMMY_CACHE_DIR = Path("/tmp/test-token-manager-pbt")


# ---------------------------------------------------------------------------
# Property 6: Token cache freshness decision
# ---------------------------------------------------------------------------


class TestTokenCacheFreshnessDecision:
    """Property 6: Token cache freshness decision.

    For any JWT access token, if the exp claim minus current epoch time is
    greater than 3600 seconds, the token SHALL be considered fresh (use from
    cache); otherwise it SHALL be considered stale (regenerate from API key).

    **Validates: Requirements 4.2, 4.3**
    """

    @settings(max_examples=200)
    @given(
        fixed_now=fixed_now_strategy,
        exp_offset=exp_offset_strategy,
    )
    def test_token_fresh_iff_exp_minus_now_greater_than_threshold(
        self, fixed_now: int, exp_offset: int
    ):
        """
        **Validates: Requirements 4.2, 4.3**

        Generate JWTs with various exp values and a fixed current time.
        Assert that the token is considered fresh iff (exp - now) > 3600.
        """
        exp = fixed_now + exp_offset
        token = _make_jwt_with_exp(exp)

        tm = TokenManager("test-profile", _DUMMY_CACHE_DIR)

        # Mock time.time() to return a fixed value for deterministic testing
        with patch("icav2_cli_plugins.utils.token_manager.time.time", return_value=float(fixed_now)):
            result = tm._is_token_fresh(token)

        # The token should be fresh iff (exp - now) > TOKEN_REFRESH_THRESHOLD
        expected_fresh = (exp - fixed_now) > TOKEN_REFRESH_THRESHOLD
        assert result == expected_fresh, (
            f"exp={exp}, now={fixed_now}, diff={exp - fixed_now}, "
            f"threshold={TOKEN_REFRESH_THRESHOLD}, "
            f"expected_fresh={expected_fresh}, got={result}"
        )

    @settings(max_examples=100)
    @given(fixed_now=fixed_now_strategy)
    def test_token_at_exact_threshold_is_stale(self, fixed_now: int):
        """
        **Validates: Requirements 4.2, 4.3**

        A token with (exp - now) == 3600 exactly is considered stale (not fresh),
        since the condition is strictly greater than.
        """
        exp = fixed_now + TOKEN_REFRESH_THRESHOLD  # exactly at threshold
        token = _make_jwt_with_exp(exp)

        tm = TokenManager("test-profile", _DUMMY_CACHE_DIR)

        with patch("icav2_cli_plugins.utils.token_manager.time.time", return_value=float(fixed_now)):
            result = tm._is_token_fresh(token)

        assert result is False, (
            f"Token at exact threshold should be stale: "
            f"exp={exp}, now={fixed_now}, diff={exp - fixed_now}"
        )

    @settings(max_examples=100)
    @given(fixed_now=fixed_now_strategy)
    def test_token_one_second_above_threshold_is_fresh(self, fixed_now: int):
        """
        **Validates: Requirements 4.2, 4.3**

        A token with (exp - now) == 3601 (one second above threshold) is considered fresh.
        """
        exp = fixed_now + TOKEN_REFRESH_THRESHOLD + 1
        token = _make_jwt_with_exp(exp)

        tm = TokenManager("test-profile", _DUMMY_CACHE_DIR)

        with patch("icav2_cli_plugins.utils.token_manager.time.time", return_value=float(fixed_now)):
            result = tm._is_token_fresh(token)

        assert result is True, (
            f"Token one second above threshold should be fresh: "
            f"exp={exp}, now={fixed_now}, diff={exp - fixed_now}"
        )

    @settings(max_examples=100)
    @given(malformed_token=malformed_jwt_strategy)
    def test_malformed_jwt_is_always_stale(self, malformed_token: str):
        """
        **Validates: Requirements 4.2, 4.3**

        Any malformed or invalid JWT string is treated as stale (returns False).
        """
        tm = TokenManager("test-profile", _DUMMY_CACHE_DIR)
        result = tm._is_token_fresh(malformed_token)

        assert result is False, (
            f"Malformed JWT should always be stale: token={malformed_token!r}"
        )

    @settings(max_examples=100)
    @given(fixed_now=fixed_now_strategy)
    def test_jwt_without_exp_claim_is_stale(self, fixed_now: int):
        """
        **Validates: Requirements 4.2, 4.3**

        A valid JWT that lacks the 'exp' claim is treated as stale.
        """
        # Create a JWT without an exp claim
        payload = {"iss": "test", "sub": "user", "iat": fixed_now}
        token = jwt.encode(payload, "secret", algorithm="HS256")

        tm = TokenManager("test-profile", _DUMMY_CACHE_DIR)

        with patch("icav2_cli_plugins.utils.token_manager.time.time", return_value=float(fixed_now)):
            result = tm._is_token_fresh(token)

        assert result is False, (
            "JWT without 'exp' claim should always be stale"
        )
