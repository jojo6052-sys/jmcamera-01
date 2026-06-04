from app.services.yahoo_fetcher import YahooCandidatePayload, _filter_candidates


def make_row(title: str, price: float):
    return YahooCandidatePayload(
        auction_id='a1',
        title=title,
        normalized_title=title.lower(),
        url='https://example.com',
        current_price_jpy=price,
        buyout_price_jpy=None,
        bid_count=0,
        end_time=None,
        seller_id=None,
        seller_rating=None,
        description=None,
        image_urls=[],
        search_keyword='nikon',
    )


def test_filter_candidates_by_price_and_exclude_word():
    rows = [
        make_row('Nikon F3 Body', 12000),
        make_row('Nikon ジャンク Body', 9000),
        make_row('Nikon FM2 Body', 30000),
    ]

    filtered = _filter_candidates(rows, min_price=10000, max_price=25000, exclude_words=['ジャンク'])
    assert len(filtered) == 1
    assert filtered[0].title == 'Nikon F3 Body'
