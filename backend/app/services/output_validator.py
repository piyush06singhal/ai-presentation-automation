from typing import List, Dict, Tuple, Optional
from app.schemas.models import BusinessSummary, SlidePlan, DataTypeEnum
from app.services.exceptions import ValidationException
from app.services.chart_validation import validate_and_override_chart
from app.services.recommendation_validator import validate_recommendations

SUPPORTED_TEMPLATES = [
    "Title",
    "Agenda",
    "Executive Summary",
    "KPI Dashboard",
    "Trend Analysis",
    "Category Comparison",
    "Recommendations",
    "Appendix"
]

def _resolve_columns_for_plan(
    worksheet_meta,
    column_types: Dict[str, DataTypeEnum],
    plan_x: Optional[str] = None,
    plan_y: Optional[List[str]] = None
) -> Tuple[str, List[str]]:
    """Resolves valid X and Y columns, falling back to sheet schema if plan columns are missing or invalid."""
    # 1. Resolve X Column
    x_col = None
    if plan_x and plan_x in column_types:
        x_col = plan_x
    else:
        # First categorical column
        cat_cols = [c.name for c in worksheet_meta.columns if c.datatype in [DataTypeEnum.CATEGORICAL, DataTypeEnum.IDENTIFIER]]
        if cat_cols:
            x_col = cat_cols[0]
            
    if not x_col:
        cols = list(column_types.keys())
        x_col = cols[0] if cols else ""

    # 2. Resolve Y Columns
    y_cols = []
    if plan_y:
        y_cols = [y for y in plan_y if y in column_types]
        
    if not y_cols:
        # All numeric columns
        num_cols = [c.name for c in worksheet_meta.columns if c.datatype in [DataTypeEnum.NUMERIC, DataTypeEnum.PERCENTAGE, DataTypeEnum.CURRENCY]]
        y_cols = num_cols[:3]

    if not y_cols:
        y_cols = [col for col in column_types.keys() if col != x_col][:2]

    # Prevent duplicate x_col in y_cols
    y_cols = [y for y in y_cols if y != x_col]
    
    return x_col, y_cols

def validate_presentation_plan(slides: List[SlidePlan], summary: BusinessSummary) -> List[SlidePlan]:
    """Validates the structure, worksheet references, and metrics mapping of all proposed slides."""
    if not slides:
        raise ValidationException("The generated presentation plan contains no slides.")

    valid_slides: List[SlidePlan] = []
    available_sheets = {s.name: s for s in summary.metadata.sheets}

    for slide in slides:
        # 1. Template Validation
        if slide.template_id not in SUPPORTED_TEMPLATES:
            # Fallback to general Executive Summary layout
            slide.template_id = "Executive Summary"

        # 2. Worksheet Validation
        if slide.worksheet not in available_sheets:
            raise ValidationException(
                f"Validation failed: Worksheet '{slide.worksheet}' referenced in slide '{slide.title}' "
                f"does not exist in workbook. Available: {list(available_sheets.keys())}"
            )

        sheet_meta = available_sheets[slide.worksheet]
        sheet_columns = {c.name: c.datatype for c in sheet_meta.columns}

        # 3. Chart Columns Validation & Resolution
        if slide.chart_type and slide.chart_type.lower() != "none":
            # Dynamically resolve columns to ensure they are valid and exist in the dataframe
            resolved_x, resolved_y = _resolve_columns_for_plan(
                sheet_meta,
                sheet_columns,
                slide.x_axis,
                slide.y_axis
            )
            slide.x_axis = resolved_x
            slide.y_axis = resolved_y

            # 4. Chart Engine Overrides
            new_chart, new_x, new_y = validate_and_override_chart(
                sheet_name=slide.worksheet,
                column_types=sheet_columns,
                chart_type=slide.chart_type,
                x_axis=slide.x_axis,
                y_axis=slide.y_axis,
                row_count=sheet_meta.row_count,
                cardinality=sheet_meta.row_count
            )
            slide.chart_type = new_chart
            slide.x_axis = new_x
            slide.y_axis = new_y

        # 5. Recommendations Validation
        if slide.recommendations:
            slide.recommendations = validate_recommendations(slide.recommendations, summary.trends)

        valid_slides.append(slide)

    return valid_slides
