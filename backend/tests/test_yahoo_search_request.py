import pytest
from pydantic import ValidationError

from app.schemas.candidates import YahooSearchRequest


def test_yahoo_search_request_accepts_valid_price_range() -> None:
    payload = YahooSearchRequest(keyword="Nikon", limit=10, min_price=1000, max_price=5000)

    assert payload.keyword == "Nikon"
    assert payload.limit == 10


def test_yahoo_search_request_rejects_invalid_price_range() -> None:
    with pytest.raises(ValidationError, match="min_price must be less than or equal to max_price"):
        YahooSearchRequest(keyword="Nikon", min_price=5000, max_price=1000)


def test_yahoo_search_request_rejects_out_of_range_limit() -> None:
    with pytest.raises(ValidationError):
        YahooSearchRequest(keyword="Nikon", limit=51)
