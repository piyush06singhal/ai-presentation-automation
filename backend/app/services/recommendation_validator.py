from typing import List
from app.schemas.models import BusinessTrend, TrendDirectionEnum

def validate_recommendations(
    recommendations: List[str],
    trends: List[BusinessTrend]
) -> List[str]:
    """Filters recommendations, removing items that contradict calculated trend facts."""
    if not recommendations:
        return []

    valid_recs = []
    
    for rec in recommendations:
        rec_lower = rec.lower()
        is_valid = True
        
        for trend in trends:
            metric_lower = trend.metric.lower()
            
            # Check if this recommendation discusses the specific metric
            if metric_lower in rec_lower:
                if trend.direction == TrendDirectionEnum.DOWNWARD:
                    # Contradiction: Calculated decline, but LLM recommends growth/expansion
                    growth_words = ["increase", "growth", "grow", "expansion", "upward", "accelerate"]
                    if any(w in rec_lower for w in growth_words):
                        is_valid = False
                        break
                        
                elif trend.direction == TrendDirectionEnum.UPWARD:
                    # Contradiction: Calculated growth, but LLM recommends fixing declines/drops
                    decline_words = ["decline", "decrease", "drop", "downward", "reduction", "fall", "loss"]
                    if any(w in rec_lower for w in decline_words):
                        is_valid = False
                        break
                        
        if is_valid:
            valid_recs.append(rec)
            
    return valid_recs
