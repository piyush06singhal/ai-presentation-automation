import re
from typing import Optional, Any
import pandas as pd

def clean_column_name(name: Any) -> str:
    """Clean column name to ensure it's a string, stripped of extra spaces/newlines."""
    if name is None:
        return ""
    name_str = str(name).strip()
    name_str = re.sub(r'\s+', ' ', name_str)
    return name_str

def parse_currency(val: Any) -> Optional[float]:
    """Parse string currency representation (e.g. '$1,200.50') to float."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    # Strip currency signs, spaces, and commas
    cleaned = re.sub(r'[^\d\.\-]', '', val_str)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None

def parse_percentage(val: Any) -> Optional[float]:
    """Parse percentage string (e.g. '12.5%') or numeric representations to float (e.g. 0.125)."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
        
    val_str = str(val).strip()
    is_percent_sign = '%' in val_str
    cleaned = re.sub(r'[^\d\.\-]', '', val_str)
    try:
        num = float(cleaned) if cleaned else None
        if num is not None and is_percent_sign:
            return num / 100.0
        return num
    except ValueError:
        return None

def parse_date(val: Any) -> Optional[pd.Timestamp]:
    """Safely parse various cell representations to a Pandas Timestamp."""
    if val is None or pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val
    try:
        parsed = pd.to_datetime(val, errors='raise')
        return parsed
    except Exception:
        return None
