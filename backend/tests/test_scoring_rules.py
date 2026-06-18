from types import SimpleNamespace

from app.services.scoring import compute_recommendation


class Rule(SimpleNamespace):
    enabled = True


def candidate(**overrides):
    data = {
        'current_price_jpy': 8000,
        'buyout_price_jpy': 12000,
        'seller_rating': 96,
        'image_urls': ['a.jpg', 'b.jpg', 'c.jpg'],
        'description': '動作品 防湿庫保管',
        'title': 'Nikon F3 HP',
        'normalized_title': 'nikon f3 hp',
        'search_keyword': 'Nikon F3',
        'seller_id': 'safe-seller',
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_manual_scoring_rule_adjusts_score_and_bid():
    base = compute_recommendation(candidate())
    adjusted = compute_recommendation(
        candidate(),
        scoring_rules=[
            Rule(
                name='Expert Nikon F3 preference',
                match_type='keyword',
                pattern='Nikon F3',
                score_adjustment=8,
                max_bid_adjustment_pct=5,
                risk_level='positive',
                reason='実績上、整備済みなら回転が早い',
            )
        ],
    )

    assert adjusted['total_score'] > base['total_score']
    assert adjusted['recommended_max_bid_jpy'] > base['recommended_max_bid_jpy']
    assert 'manual knowledge' in adjusted['reason']


def test_critical_manual_rule_forces_ng():
    result = compute_recommendation(
        candidate(seller_id='risky-seller'),
        scoring_rules=[
            Rule(
                name='Blacklisted seller',
                match_type='seller_id',
                pattern='risky-seller',
                score_adjustment=-50,
                max_bid_adjustment_pct=-50,
                risk_level='critical',
                reason='過去に説明相違が多い',
            )
        ],
    )

    assert result['rank'] == 'NG'
    assert result['caution'] == 'Manual critical scoring rule matched.'


def test_description_and_image_risks_are_explained():
    result = compute_recommendation(
        candidate(
            description='ジャンク 不動 カビあり ノークレーム',
            image_urls=['placeholder.jpg'],
        )
    )

    assert result['description_risk_score'] >= 10
    assert result['image_risk_score'] > 0
    assert 'description risks' in result['reason']
    assert 'image findings' in result['reason']
