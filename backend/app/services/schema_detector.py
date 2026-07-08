import pandas as pd
import re
from typing import List
from app.schemas.models import DataTypeEnum

def detect_column_type(col_name: str, series: pd.Series) -> DataTypeEnum:
    """Infers the semantic data type of a pandas Series."""
    # Drop null values for analysis
    cleaned_series = series.dropna()
    if cleaned_series.empty:
        return DataTypeEnum.UNKNOWN

    col_name_lower = col_name.lower()
    
    # 1. Date Detection
    # Check if pandas has parsed it as datetime or if values resemble dates
    if pd.api.types.is_datetime64_any_dtype(series):
        return DataTypeEnum.DATE
        
    # Check string values for date formats
    first_non_null_vals = cleaned_series.head(5).astype(str).tolist()
    date_patterns = [
        r'^\d{4}-\d{2}-\d{2}',            # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{4}',            # MM/DD/YYYY or DD/MM/YYYY
        r'^\d{2}-\d{2}-\d{4}',            # DD-MM-YYYY
        r'^\d{4}/\d{2}/\d{2}'             # YYYY/MM/DD
    ]
    is_date_pattern = False
    for val in first_non_null_vals:
        if any(re.match(p, val.strip()) for p in date_patterns):
            is_date_pattern = True
            break
    if is_date_pattern or "date" in col_name_lower or "period" in col_name_lower or "month" in col_name_lower:
        # Try to parse to confirm
        try:
            pd.to_datetime(cleaned_series.head(5), errors='raise')
            return DataTypeEnum.DATE
        except Exception:
            pass

    # 2. Boolean Detection
    unique_vals = cleaned_series.unique()
    if len(unique_vals) <= 3: # allow True, False, and potential NaN
        set_vals = {str(x).strip().lower() for x in unique_vals}
        boolean_sets = [
            {"true", "false"},
            {"yes", "no"},
            {"y", "n"},
            {"1", "0"},
            {1, 0},
            {1.0, 0.0}
        ]
        if any(set_vals.issubset({str(v) for v in b_set}) for b_set in boolean_sets):
            return DataTypeEnum.BOOLEAN

    # 3. Currency Detection
    currency_keywords = ["price", "cost", "revenue", "sales", "amount", "profit", "spend", "margin_val"]
    currency_symbols = ["$", "€", "£", "¥", "rs", "rupiah"]
    has_currency_symbol_in_data = any(any(sym in str(x) for sym in currency_symbols) for x in cleaned_series.head(5))
    has_currency_name = any(kw in col_name_lower for kw in currency_keywords) or any(sym in col_name_lower for sym in currency_symbols)
    
    if has_currency_symbol_in_data or (has_currency_name and pd.api.types.is_numeric_dtype(cleaned_series)):
        return DataTypeEnum.CURRENCY
    if has_currency_name and not pd.api.types.is_numeric_dtype(cleaned_series):
        # Check if it cleans up to numeric values
        sample_str = str(cleaned_series.iloc[0])
        cleaned_sample = re.sub(r'[^\d\.\-]', '', sample_str)
        if cleaned_sample:
            try:
                float(cleaned_sample)
                return DataTypeEnum.CURRENCY
            except ValueError:
                pass

    # 4. Percentage Detection
    has_percent_symbol_in_data = any('%' in str(x) for x in cleaned_series.head(5))
    has_percent_name = "%" in col_name_lower or "percent" in col_name_lower or "rate" in col_name_lower or "growth" in col_name_lower
    
    if has_percent_symbol_in_data or (has_percent_name and pd.api.types.is_numeric_dtype(cleaned_series)):
        return DataTypeEnum.PERCENTAGE

    # 5. Identifier Detection
    id_keywords = ["id", "code", "key", "number", "no.", "serial", "sku", "invoice"]
    is_id_name = any(kw in col_name_lower for kw in id_keywords)
    if is_id_name:
        return DataTypeEnum.IDENTIFIER
        
    # Pattern checks for standard alphanumeric codes (e.g. INV-10023, US-901)
    if not pd.api.types.is_numeric_dtype(cleaned_series):
        sample_vals = cleaned_series.head(5).astype(str).tolist()
        id_pattern = r'^[A-Z0-9]{1,8}[-\s][A-Z0-9]{1,10}$'
        alphanumeric_with_digits = r'^[A-Z]+[0-9]+[A-Z0-9]*$'
        
        is_id = True
        for val in sample_vals:
            v_clean = val.strip().upper()
            if not (re.match(id_pattern, v_clean) or re.match(alphanumeric_with_digits, v_clean)):
                is_id = False
                break
        if is_id:
            return DataTypeEnum.IDENTIFIER

    # 6. Numeric Detection
    if pd.api.types.is_numeric_dtype(cleaned_series):
        # Check if it behaves as categories (e.g. Year 2021, 2022)
        if len(unique_vals) < len(cleaned_series) * 0.05 and len(unique_vals) < 15:
            # Low cardinality numeric could be category or years
            if all(float(x).is_integer() and 1900 <= x <= 2100 for x in unique_vals):
                return DataTypeEnum.CATEGORICAL
        return DataTypeEnum.NUMERIC

    # 7. Categorical Detection
    if not pd.api.types.is_numeric_dtype(cleaned_series):
        # Strings with standard cardinality
        return DataTypeEnum.CATEGORICAL

    return DataTypeEnum.UNKNOWN
