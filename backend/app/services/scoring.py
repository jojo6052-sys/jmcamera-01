from __future__ import annotations

from typing import Any


def compute_recommendation(candidate: Any) -> dict:
    current_price = float(candidate.current_price_jpy or 0)
    buyout_price = float(candidate.buyout_price_jpy or 0)
    seller_rating = float(candidate.seller_rating or 70)
    image_count = len(candidate.image_urls or [])
    description = (candidate.description or "").lower()

    expected_sale_price_jpy = max(current_price * 1.8, buyout_price * 1.4, 12000)
    expected_sale_price_usd = expected_sale_price_jpy / 155.0
    expected_profit = expected_sale_price_jpy - current_price
    expected_margin = (expected_profit / expected_sale_price_jpy * 100) if expected_sale_price_jpy else 0

    similarity_score = min(25, max(8, 15 + (len(candidate.title or "") % 10)))
    profit_score = min(20, max(0, expected_margin / 2.5))
    rotation_score = 10
    seller_score = min(15, max(0, (seller_rating - 70) / 2))

    risk_words = ["返品不可", "ノークレーム", "不動", "部品取り", "カビ", "曇り大", "水没", "落下"]
    risk_hits = sum(1 for w in risk_words if w in description)
    description_risk = min(10, risk_hits * 2.5)

    bargain_score = min(10, max(0, (expected_sale_price_jpy - current_price) / 3000))
    image_score = 5 if image_count >= 3 else (3 if image_count == 2 else 1)
    image_risk = max(0, 5 - image_score)

    total = similarity_score + profit_score + rotation_score + seller_score + (10 - description_risk) + bargain_score + image_score
    total = max(0, min(100, round(total, 2)))

    if seller_rating < 40:
        rank = "NG"
        caution = "Seller rating is too low."
    elif total >= 85:
        rank = "S"
        caution = ""
    elif total >= 70:
        rank = "A"
        caution = ""
    elif total >= 55:
        rank = "B"
        caution = "Check item details before bidding."
    elif total >= 40:
        rank = "C"
        caution = "Higher risk profile."
    else:
        rank = "NG"
        caution = "Low expected return and/or high risk."

    return {
        "similarity_score": round(similarity_score, 2),
        "expected_sale_price_usd": round(expected_sale_price_usd, 2),
        "expected_sale_price_jpy": round(expected_sale_price_jpy, 2),
        "expected_profit_jpy": round(expected_profit, 2),
        "expected_profit_margin": round(expected_margin, 2),
        "recommended_max_bid_jpy": round(current_price * 1.1, 2),
        "seller_risk_score": round(max(0, 15 - seller_score), 2),
        "description_risk_score": round(description_risk, 2),
        "image_risk_score": round(image_risk, 2),
        "total_score": total,
        "rank": rank,
        "reason": f"Profit margin {expected_margin:.1f}% with seller rating {seller_rating:.1f}.",
        "caution": caution,
    }
