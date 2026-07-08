from typing import List
from app.schemas.models import BusinessSummary, SlidePlan
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
            # If worksheet doesn't exist, we skip or raise exception to prevent broken slides
            raise ValidationException(
                f"Validation failed: Worksheet '{slide.worksheet}' referenced in slide '{slide.title}' "
                f"does not exist in workbook. Available: {list(available_sheets.keys())}"
            )

        sheet_meta = available_sheets[slide.worksheet]
        sheet_columns = {c.name: c.datatype for c in sheet_meta.columns}

        # 3. Chart Columns Validation
        if slide.chart_type and slide.chart_type.lower() != "none":
            # X Axis validation
            if not slide.x_axis or slide.x_axis not in sheet_columns:
                raise ValidationException(
                    f"Validation failed: Chart x_axis '{slide.x_axis}' in slide '{slide.title}' "
                    f"does not exist in worksheet '{slide.worksheet}'."
                )

            # Y Axis validation
            if not slide.y_axis:
                raise ValidationException(
                    f"Validation failed: Chart y_axis is missing for slide '{slide.title}'."
                )
                
            invalid_y = [y for y in slide.y_axis if y not in sheet_columns]
            if invalid_y:
                raise ValidationException(
                    f"Validation failed: Y-Axis columns {invalid_y} referenced in slide '{slide.title}' "
                    f"do not exist in worksheet '{slide.worksheet}'."
                )

            # 4. Chart Engine Overrides
            # Calculate column cardinality if it's categorical
            cardinality = 0
            # Note: We can check unique values from metadata, or approximate. We default to row_count.
            new_chart, new_x, new_y = validate_and_override_chart(
                sheet_name=slide.worksheet,
                column_types=sheet_columns,
                chart_type=slide.chart_type,
                x_axis=slide.x_axis,
                y_axis=slide.y_axis,
                row_count=sheet_meta.row_count,
                cardinality=sheet_meta.row_count # Fallback mapping
            )
            slide.chart_type = new_chart
            slide.x_axis = new_x
            slide.y_axis = new_y

        # 5. Recommendations Validation
        if slide.recommendations:
            slide.recommendations = validate_recommendations(slide.recommendations, summary.trends)

        valid_slides.append(slide)

    return valid_slides
