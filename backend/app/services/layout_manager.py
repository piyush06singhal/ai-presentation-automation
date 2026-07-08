from pptx.util import Inches
from typing import Dict, Any, Tuple
from app.services.theme_manager import CorporateTheme

class LayoutManager:
    """Computes coordinate coordinates and spacing grids on a widescreen (16:9) canvas."""

    @staticmethod
    def get_slide_header_box() -> Tuple[Inches, Inches, Inches, Inches]:
        """Returns bounds for the standardized slide title block."""
        left = CorporateTheme.MARGIN_LEFT
        top = CorporateTheme.MARGIN_TOP
        width = CorporateTheme.SLIDE_WIDTH - (CorporateTheme.MARGIN_LEFT + CorporateTheme.MARGIN_RIGHT)
        height = Inches(0.8)
        return left, top, width, height

    @staticmethod
    def get_slide_footer_box() -> Tuple[Inches, Inches, Inches, Inches]:
        """Returns bounds for footer slide page numbering and branding notes."""
        left = CorporateTheme.MARGIN_LEFT
        top = CorporateTheme.SLIDE_HEIGHT - CorporateTheme.MARGIN_BOTTOM - Inches(0.4)
        width = CorporateTheme.SLIDE_WIDTH - (CorporateTheme.MARGIN_LEFT + CorporateTheme.MARGIN_RIGHT)
        height = Inches(0.4)
        return left, top, width, height

    @staticmethod
    def get_full_content_box() -> Tuple[Inches, Inches, Inches, Inches]:
        """Returns bounds for a slide that consumes the entire main canvas space."""
        left = CorporateTheme.MARGIN_LEFT
        top = Inches(1.4)
        width = CorporateTheme.SLIDE_WIDTH - (CorporateTheme.MARGIN_LEFT + CorporateTheme.MARGIN_RIGHT)
        height = Inches(5.0)
        return left, top, width, height

    @staticmethod
    def get_split_layout_boxes() -> Tuple[Tuple[Inches, Inches, Inches, Inches], Tuple[Inches, Inches, Inches, Inches]]:
        """Returns left visual block (e.g. chart/table) and right insights text block bounds."""
        top = Inches(1.4)
        height = Inches(5.0)
        
        # Left visual column consumes ~55% width
        left_col_left = CorporateTheme.MARGIN_LEFT
        left_col_width = Inches(6.5)
        
        # Right insight column consumes ~40% width
        right_col_left = left_col_left + left_col_width + CorporateTheme.GUTTER
        right_col_width = CorporateTheme.SLIDE_WIDTH - right_col_left - CorporateTheme.MARGIN_RIGHT
        
        left_box = (left_col_left, top, left_col_width, height)
        right_box = (right_col_left, top, right_col_width, height)
        
        return left_box, right_box

    @staticmethod
    def get_grid_cells(
        rows: int,
        cols: int,
        parent_box: Tuple[Inches, Inches, Inches, Inches] = None
    ) -> list:
        """Returns a list of coordinate boxes (left, top, width, height) mapped in a grid layout."""
        if not parent_box:
            parent_box = LayoutManager.get_full_content_box()
            
        p_left, p_top, p_width, p_height = parent_box
        
        # Grid gutter spacing
        gutter = CorporateTheme.GUTTER
        
        total_gutter_w = gutter * (cols - 1)
        total_gutter_h = gutter * (rows - 1)
        
        cell_width = (p_width - total_gutter_w) / cols
        cell_height = (p_height - total_gutter_h) / rows
        
        cells = []
        for r in range(rows):
            for c in range(cols):
                left = p_left + c * (cell_width + gutter)
                top = p_top + r * (cell_height + gutter)
                cells.append((left, top, cell_width, cell_height))
                
        return cells
