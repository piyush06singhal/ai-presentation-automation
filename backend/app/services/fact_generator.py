from typing import List, Dict, Any
from app.schemas.models import BusinessFact, DetectedKPI, BusinessTrend

def generate_facts(
    kpis: List[DetectedKPI], 
    trends: List[BusinessTrend], 
    rankings: Dict[str, Dict[str, Any]]
) -> List[BusinessFact]:
    """Generates structured, clear, and action-ready business facts from raw mathematical records."""
    facts: List[BusinessFact] = []
    fact_counter = 1
    
    # 1. Fact generation from KPI lists
    for kpi in kpis:
        val_formatted = f"{kpi.unit}{kpi.value:,}" if kpi.unit and kpi.unit != "%" else f"{kpi.value:,} {kpi.unit or ''}".strip()
        statement = f"Total {kpi.name} calculated stands at {val_formatted} for worksheet '{kpi.worksheet}'."
        
        # High confidence KPIs represent core facts (importance 2 or 3)
        importance = 3 if kpi.confidence >= 0.9 else 2
        facts.append(BusinessFact(
            fact_id=f"FACT_{fact_counter:03d}",
            statement=statement,
            source_worksheet=kpi.worksheet,
            metrics=[kpi.name],
            importance=importance
        ))
        fact_counter += 1

    # 2. Fact generation from Trends
    for trend in trends:
        direction_str = "upward" if trend.percentage_change >= 0 else "downward"
        pct_formatted = abs(trend.percentage_change)
        statement = f"{trend.metric} showed a net {direction_str} shift of {pct_formatted}% over the period."
        
        facts.append(BusinessFact(
            fact_id=f"FACT_{fact_counter:03d}",
            statement=statement,
            source_worksheet=trend.worksheet,
            metrics=[trend.metric],
            importance=3  # Trends represent high-level highlights
        ))
        fact_counter += 1

    # 3. Fact generation from Rankings / Category Contributors
    # rankings key style: "sheet_name|cat_col|num_col" -> { "top": [...], "bottom": [...] }
    for rank_key, value_dicts in rankings.items():
        parts = rank_key.split("|")
        if len(parts) < 3:
            continue
        s_name, cat_col, num_col = parts[0], parts[1], parts[2]
        
        top_list = value_dicts.get("top", [])
        if top_list:
            lead = top_list[0]
            statement = f"'{lead['category']}' is the primary contributor in column '{num_col}', accounting for {lead['share']}% of the total."
            facts.append(BusinessFact(
                fact_id=f"FACT_{fact_counter:03d}",
                statement=statement,
                source_worksheet=s_name,
                metrics=[num_col],
                importance=3
            ))
            fact_counter += 1
            
        bottom_list = value_dicts.get("bottom", [])
        if bottom_list:
            lowest = bottom_list[-1]
            statement = f"'{lowest['category']}' represents the smallest share in '{num_col}', accounting for {lowest['share']}%."
            facts.append(BusinessFact(
                fact_id=f"FACT_{fact_counter:03d}",
                statement=statement,
                source_worksheet=s_name,
                metrics=[num_col],
                importance=1
            ))
            fact_counter += 1
            
    return facts
