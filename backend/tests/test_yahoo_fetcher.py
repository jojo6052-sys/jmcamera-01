from app.services.yahoo_fetcher import _parse_candidates, fetch_yahoo_candidates


def test_parse_candidates_extracts_basic_fields():
    html = """
    <ul>
      <li class='Product'>
        <a class='Product__titleLink' href='https://auctions.yahoo.co.jp/jp/auction/test12345'>link</a>
        <h3 class='Product__title'>Nikon F3 HP Body</h3>
        <span class='Product__priceValue'>12,500円</span>
        <img class='Product__imageData' src='https://img.example.com/a.jpg' />
      </li>
    </ul>
    """
    rows = _parse_candidates(html, keyword='nikon f3', limit=10)
    assert len(rows) == 1
    assert rows[0].auction_id == 'test12345'
    assert rows[0].current_price_jpy == 12500.0
    assert rows[0].image_urls == ['https://img.example.com/a.jpg']


def test_fetch_yahoo_candidates_falls_back_on_error(monkeypatch):
    monkeypatch.setattr('app.services.yahoo_fetcher.settings.yahoo_fetch_mode', 'live')
    monkeypatch.setattr('app.services.yahoo_fetcher.time.sleep', lambda _seconds: None)

    def boom(_keyword: str, **_kwargs):
        raise RuntimeError('network error')

    monkeypatch.setattr('app.services.yahoo_fetcher._search_html', boom)
    rows = fetch_yahoo_candidates('canon ae-1', limit=3)
    assert len(rows) == 3
    assert all('サンプル候補' in row.title for row in rows)


def test_fetch_yahoo_candidates_uses_fallback_mode_without_network(monkeypatch):
    monkeypatch.setattr('app.services.yahoo_fetcher.settings.yahoo_fetch_mode', 'fallback')

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError('live Yahoo fetch should not run in fallback mode')

    monkeypatch.setattr('app.services.yahoo_fetcher._search_html', fail_if_called)
    rows = fetch_yahoo_candidates('nikon f3', limit=2)
    assert len(rows) == 2
    assert all(row.description == 'MVP fallback candidate.' for row in rows)


def test_fetch_yahoo_candidates_uses_live_mode_when_enabled(monkeypatch):
    html = """
    <ul>
      <li class='Product'>
        <a class='Product__titleLink' href='https://auctions.yahoo.co.jp/jp/auction/live12345'>link</a>
        <h3 class='Product__title'>Canon AE-1 Body</h3>
        <span class='Product__priceValue'>8,500円</span>
      </li>
    </ul>
    """
    monkeypatch.setattr('app.services.yahoo_fetcher.settings.yahoo_fetch_mode', 'live')
    monkeypatch.setattr('app.services.yahoo_fetcher.time.sleep', lambda _seconds: None)
    monkeypatch.setattr('app.services.yahoo_fetcher._search_html', lambda *_args, **_kwargs: html)
    rows = fetch_yahoo_candidates('canon ae-1', limit=3)
    assert len(rows) == 1
    assert rows[0].auction_id == 'live12345'
    assert rows[0].description == 'Fetched from Yahoo Auctions search results.'
