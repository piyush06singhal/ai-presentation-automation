import pandas as pd
from typing import List, Tuple, Optional, Any
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.util import Inches, Pt
from app.services.theme_manager import CorporateTheme

class ChartBuilder:
    """Translates raw Pandas Dataframe values into native, editable Microsoft PowerPoint charts."""

    @staticmethod
    def draw_chart(
        slide,
        bounding_box: Tuple[Inches, Inches, Inches, Inches],
        chart_type: str,
        df: pd.DataFrame,
        x_col: str,
        y_cols: List[str]
    ) -> Any:
        """Constructs and renders a native slide chart using data points from the target columns."""
        left, top, width, height = bounding_box
        
        # 1. Determine Chart Type Enum
        c_type_lower = chart_type.strip().lower()
        if c_type_lower == "line":
            chart_enum = XL_CHART_TYPE.LINE
        elif c_type_lower == "bar" or c_type_lower == "vertical bar":
            chart_enum = XL_CHART_TYPE.COLUMN_CLUSTERED
        elif c_type_lower == "pie":
            chart_enum = XL_CHART_TYPE.PIE
        elif c_type_lower == "horizontal bar":
            chart_enum = XL_CHART_TYPE.BAR_CLUSTERED
        elif c_type_lower == "stacked column":
            chart_enum = XL_CHART_TYPE.COLUMN_STACKED
        elif c_type_lower == "area":
            chart_enum = XL_CHART_TYPE.AREA
        else:
            chart_enum = XL_CHART_TYPE.COLUMN_CLUSTERED  # Fallback

        # 2. Extract and format series categories
        # Sort by dates if X is a date axis to preserve time progression
        if pd.api.types.is_datetime64_any_dtype(df[x_col]):
            df_sorted = df.sort_values(by=x_col)
            if len(df_sorted) > 15:
                df_sorted = df_sorted.head(15)
            # Format dates to short text (e.g. YYYY-MM-DD)
            categories = df_sorted[x_col].dt.strftime('%Y-%m-%d').tolist()
            df_source = df_sorted
        else:
            if len(df) > 15:
                df_source = df.head(15)
            else:
                df_source = df
            categories = df_source[x_col].astype(str).tolist()

        # 3. Compile Chart Data
        chart_data = CategoryChartData()
        chart_data.categories = categories
        
        for y_col in y_cols:
            # Safe fill empty/nan metrics
            series_values = pd.to_numeric(df_source[y_col], errors='coerce').fillna(0.0).tolist()
            chart_data.add_series(y_col, tuple(series_values))

        # 4. Inject Shape
        chart_shape = slide.shapes.add_chart(
            chart_enum, left, top, width, height, chart_data
        )
        chart = chart_shape.chart
        
        # 5. Apply Visual Styles
        chart.has_legend = len(y_cols) > 1 or chart_enum == XL_CHART_TYPE.PIE
        if chart.has_legend:
            chart.legend.position = XL_LEGEND_POSITION.RIGHT
            chart.legend.font.name = CorporateTheme.FONT_BODY
            chart.legend.font.size = Pt(CorporateTheme.SIZE_CAPTION)

        # Style data labels & colors
        try:
            # We can attempt to set standard theme colors for the series
            for i, series in enumerate(chart.series):
                color_idx = i % len(CorporateTheme.CHART_COLORS)
                series.format.fill.solid()
                series.format.fill.fore_color.rgb = CorporateTheme.CHART_COLORS[color_idx]
        except Exception:
            # Fallback if specific XML format properties aren't supported on this shape variant
            pass

        return chart_shape
