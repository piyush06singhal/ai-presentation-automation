from pptx.dml.color import RGBColor
from pptx.util import Inches

class CorporateTheme:
    """Defines presentation typography, margins, color palette, and layout dimensions."""

    # Page Dimensions
    SLIDE_WIDTH = Inches(13.33)
    SLIDE_HEIGHT = Inches(7.5)

    # Core Color Palette
    PRIMARY = RGBColor(15, 23, 42)        # Slate 900
    SECONDARY = RGBColor(71, 85, 105)    # Slate 600
    ACCENT = RGBColor(14, 165, 233)       # Sky 500
    BACKGROUND_DARK = RGBColor(9, 13, 22) # Near Black
    BACKGROUND_LIGHT = RGBColor(248, 250, 252) # Slate 50
    WHITE = RGBColor(255, 255, 255)
    LIGHT_GRAY = RGBColor(226, 232, 240)  # Slate 200

    # System Status Colors
    SUCCESS = RGBColor(16, 185, 129)      # Emerald 500
    WARNING = RGBColor(245, 158, 11)      # Amber 500
    ERROR = RGBColor(239, 68, 68)         # Rose 500

    # Typography
    FONT_TITLE = "Trebuchet MS"
    FONT_BODY = "Calibri"

    # Font Sizes
    SIZE_TITLE_MAIN = 40
    SIZE_TITLE_SLIDE = 24
    SIZE_BODY = 14
    SIZE_CAPTION = 11
    SIZE_KPI_VAL = 36
    SIZE_KPI_LABEL = 12

    # Spacing and Margins
    MARGIN_LEFT = Inches(0.8)
    MARGIN_RIGHT = Inches(0.8)
    MARGIN_TOP = Inches(0.6)
    MARGIN_BOTTOM = Inches(0.6)
    GUTTER = Inches(0.4)

    # Chart Colors
    CHART_COLORS = [
        RGBColor(14, 165, 233),  # Sky 500
        RGBColor(16, 185, 129),  # Emerald 500
        RGBColor(245, 158, 11),  # Amber 500
        RGBColor(139, 92, 246),  # Violet 500
        RGBColor(236, 72, 153),  # Pink 500
    ]
