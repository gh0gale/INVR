"""Profile version hash must fit the column it is written to.

Regression: the `P9-04` fix swapped MD5 for SHA-256 without truncating, but the
live `user_profiles.profile_version_hash` column is varchar(32), sized when the
value was an MD5 digest. Every profile save failed with Postgres 22001,
"value too long for type character varying(32)", which surfaced to the user as a
database error when entering their capital amount.

The hash exists only to detect that a profile changed, so 128 bits is ample.
"""
import pytest

from app.schemas.profile import HASH_LENGTH, UserProfileRequest, UserProfileResponse


def make_profile(**overrides) -> UserProfileRequest:
    base = dict(
        experience="intermediate",
        goal="wealth_growth",
        timeframe="swing",
        risk="moderate",
        portfolio={"Equities": 0.6, "Cash": 0.4},
        capital=100000.0,
    )
    base.update(overrides)
    return UserProfileRequest(**base)


def hash_for(**overrides) -> str:
    return UserProfileResponse.create_with_hash(make_profile(**overrides), []).profile_version_hash


def test_hash_fits_the_database_column():
    """The actual regression. varchar(32) rejects anything longer."""
    assert len(hash_for()) <= HASH_LENGTH


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"capital": 0.0},
        {"capital": 9_999_999_999.99},
        {"portfolio": {"A": 0.1, "B": 0.2, "C": 0.3, "D": 0.4}},
        {"goal": "capital_preservation", "risk": "conservative"},
        {"experience": "advanced", "timeframe": "long_term"},
    ],
)
def test_hash_length_is_stable_across_profile_shapes(overrides):
    """A bigger portfolio must not produce a longer hash."""
    assert len(hash_for(**overrides)) == HASH_LENGTH


def test_hash_is_deterministic():
    assert hash_for() == hash_for()


def test_hash_changes_when_the_profile_changes():
    """Truncation must not defeat the point of the hash."""
    baseline = hash_for()
    assert hash_for(capital=200000.0) != baseline
    assert hash_for(risk="aggressive") != baseline
    assert hash_for(portfolio={"Equities": 0.7, "Cash": 0.3}) != baseline


def test_hash_is_hex():
    assert all(c in "0123456789abcdef" for c in hash_for())


class TestEmptyPortfolio:
    """Audit finding E2E-01, found by the end-to-end run on 2026-08-23.

    A user holding only cash could not create a profile: the weights validator
    rejected `{}` with "must sum up to 1.0 (Current sum: 0)". That is the
    product's own target user - a beginner with capital and no holdings - and
    the rule forced them to invent an allocation, which then flowed into
    `semantic_profile` and the tutor's portfolio mode as if it were real.
    """

    def test_empty_portfolio_is_accepted(self):
        from app.schemas.profile import UserProfileRequest

        p = UserProfileRequest(
            experience="beginner", goal="wealth_growth", timeframe="swing",
            risk="moderate", capital=250000.0, portfolio={},
        )
        assert p.portfolio == {}

    def test_complete_allocation_is_still_accepted(self):
        from app.schemas.profile import UserProfileRequest

        p = UserProfileRequest(
            experience="intermediate", goal="wealth_growth", timeframe="swing",
            risk="moderate", capital=250000.0, portfolio={"IT": 0.6, "Banking": 0.4},
        )
        assert sum(p.portfolio.values()) == pytest.approx(1.0)

    def test_partial_allocation_is_still_rejected(self):
        """An empty portfolio means "nothing". A 60% one means a mistake."""
        from pydantic import ValidationError

        from app.schemas.profile import UserProfileRequest

        with pytest.raises(ValidationError):
            UserProfileRequest(
                experience="intermediate", goal="wealth_growth", timeframe="swing",
                risk="moderate", capital=250000.0, portfolio={"IT": 0.6},
            )

    def test_an_empty_portfolio_still_hashes_to_32_chars(self):
        from app.schemas.profile import UserProfileRequest, UserProfileResponse

        req = UserProfileRequest(
            experience="beginner", goal="wealth_growth", timeframe="swing",
            risk="moderate", capital=250000.0, portfolio={},
        )
        assert len(UserProfileResponse.create_with_hash(req, []).profile_version_hash) == 32
