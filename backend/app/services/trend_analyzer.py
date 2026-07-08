import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from app.schemas.models import BusinessTrend, TrendDirectionEnum, DataTypeEnum

def calculate_growth_trend(
    sheet_name: str, 
    df: pd.DataFrame, 
    date_col: str, 
    metric_col: str,
    metric_type: DataTypeEnum
) -> Optional[BusinessTrend]:
    """Calculates linear slope direction, percentage growth, and period rate for time series data."""
    # Work on a copy sorted by date
    df_clean = df[[date_col, metric_col]].dropna()
    if len(df_clean) < 2:
        return None
        
    df_clean = df_clean.sort_values(by=date_col)
    
    # Aggregate values by Date to avoid duplicate date indexes distorting trends
    grouped = df_clean.groupby(date_col)[metric_col].sum().reset_index()
    if len(grouped) < 2:
        return None
        
    first_val = grouped[metric_col].iloc[0]
    last_val = grouped[metric_col].iloc[-1]
    
    # Calculate percentage change
    if first_val != 0 and not pd.isna(first_val):
        pct_change = float(((last_val - first_val) / abs(first_val)) * 100.0)
    else:
        pct_change = 0.0
        
    # Fit basic linear trend direction (slope)
    x = np.arange(len(grouped))
    y = grouped[metric_col].values
    try:
        slope, _ = np.polyfit(x, y, 1)
    except Exception:
        slope = 0.0
        
    if slope > 0.001:
        direction = TrendDirectionEnum.UPWARD
    elif slope < -0.001:
        direction = TrendDirectionEnum.DOWNWARD
    else:
        direction = TrendDirectionEnum.FLAT
        
    # Compute moving average
    moving_avg = float(grouped[metric_col].rolling(min(3, len(grouped)), min_periods=1).mean().iloc[-1])
    
    description = (
        f"Metric '{metric_col}' shows an {direction.value.lower()} trend "
        f"across parsed periods on sheet '{sheet_name}'. Net change: {round(pct_change, 2)}%. "
        f"Recent moving average value stands at {round(moving_avg, 2)}."
    )
    
    return BusinessTrend(
        metric=metric_col,
        direction=direction,
        percentage_change=round(pct_change, 2),
        time_col=date_col,
        growth_rate=round(float(slope), 4),
        description=description,
        worksheet=sheet_name
    )

def calculate_contributor_rankings(
    df: pd.DataFrame, 
    cat_col: str, 
    num_col: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Computes top and bottom contributors for categories sorted by their metric totals."""
    cleaned = df[[cat_col, num_col]].dropna()
    if cleaned.empty:
        return [], []
        
    grouped = cleaned.groupby(cat_col)[num_col].sum().reset_index()
    total_val = grouped[num_col].sum()
    
    if total_val == 0:
        return [], []
        
    # Sort descending
    grouped_sorted = grouped.sort_values(by=num_col, ascending=False)
    
    rankings = []
    for _, row in grouped_sorted.iterrows():
        val = float(row[num_col])
        share = float((val / total_val) * 100.0)
        rankings.append({
            "category": str(row[cat_col]),
            "value": round(val, 2),
            "share": round(share, 2)
        })
        
    top_contributors = rankings[:3]
    bottom_contributors = rankings[-3:] if len(rankings) > 3 else []
    
    return top_contributors, bottom_contributors
