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
    def boom(_keyword: str):
        raise RuntimeError('network error')

    monkeypatch.setattr('app.services.yahoo_fetcher._search_html', boom)
    rows = fetch_yahoo_candidates('canon ae-1', limit=3)
    assert len(rows) == 3
    assert all('サンプル候補' in row.title for row in rows)
