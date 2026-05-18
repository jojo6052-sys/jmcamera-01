from types import SimpleNamespace

from app.services.scoring import compute_recommendation


def test_compute_recommendation_returns_rank_and_score():
    candidate = SimpleNamespace(
        current_price_jpy=8000,
        buyout_price_jpy=12000,
        seller_rating=96,
        image_urls=['a.jpg', 'b.jpg', 'c.jpg'],
        description='動作品 返品不可ではありません',
        title='Nikon F3 HP',
    )

    result = compute_recommendation(candidate)
    assert 0 <= result['total_score'] <= 100
    assert result['rank'] in {'S', 'A', 'B', 'C', 'NG'}
    assert result['expected_sale_price_jpy'] >= 12000
