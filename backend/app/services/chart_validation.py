from typing import Optional, List, Tuple, Dict
from app.schemas.models import DataTypeEnum

def validate_and_override_chart(
    sheet_name: str,
    column_types: Dict[str, DataTypeEnum],
    chart_type: Optional[str],
    x_axis: Optional[str],
    y_axis: Optional[List[str]],
    row_count: int,
    cardinality: int = 0
) -> Tuple[Optional[str], Optional[str], Optional[List[str]]]:
    """Applies strict data rules to validate and override recommended chart specifications."""
    
    if not chart_type or chart_type.lower() == "none":
        return None, None, None

    # Normalise chart type string
    c_type_normalized = chart_type.strip().lower()
    
    # Validation: columns must be selected
    if not x_axis or not y_axis:
        return None, None, None

    # Validation: X column must exist in types schema
    x_type = column_types.get(x_axis)
    if not x_type:
        return None, None, None

    # Validation: Y columns must all exist in types schema
    valid_y_axis = [y for y in y_axis if y in column_types]
    if not valid_y_axis:
        return None, None, None

    # Rule 1: High Density Data Check
    # If the categories or dates exceed 15 unique items, it will cause layout issues in PPT. Force a Summary Table.
    if row_count > 15 or cardinality > 15:
        # Override to table
        return None, x_axis, valid_y_axis

    # Rule 2: Date Axis Trend Check
    # Date series must always render as a Line Chart.
    if x_type == DataTypeEnum.DATE:
        if c_type_normalized != "line":
            return "Line", x_axis, valid_y_axis
        return "Line", x_axis, valid_y_axis

    # Rule 3: Categorical Axis Check
    # Names/Categories should never map to a Line Chart.
    if x_type == DataTypeEnum.CATEGORICAL:
        if c_type_normalized == "line":
            # Override line to vertical bar
            return "Bar", x_axis, valid_y_axis
            
        # Composition rule (Pie charts are only clean if items are small <= 5)
        if c_type_normalized == "pie" and (row_count > 5 or cardinality > 5):
            # Override crowded pie charts to vertical bar
            return "Bar", x_axis, valid_y_axis
            
        # Standard comparisons mapping values
        if c_type_normalized == "horizontal bar":
            return "Horizontal Bar", x_axis, valid_y_axis
        if c_type_normalized == "pie":
            return "Pie", x_axis, valid_y_axis
        return "Bar", x_axis, valid_y_axis

    # Rule 4: Fallback checks if datatypes are unknown or numeric
    # If both axes are numeric, default to Bar or scatter (mapped to Bar)
    return "Bar", x_axis, valid_y_axis
