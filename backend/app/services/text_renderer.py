from pptx.util import Pt, Inches
from pptx.enum.text import PP_ALIGN
from typing import List, Tuple, Optional
from app.services.theme_manager import CorporateTheme
from app.services.layout_manager import LayoutManager

class TextRenderer:
    """Manages adding title blocks, bullet list points, footers, and font scale calculations."""

    @staticmethod
    def add_slide_header(slide, title_text: str, subtitle_text: Optional[str] = None):
        """Adds a standardized slide header block with correct styling."""
        left, top, width, height = LayoutManager.get_slide_header_box()
        
        tx_box = slide.shapes.add_textbox(left, top, width, height)
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        # Add Title paragraph
        p = tf.paragraphs[0]
        p.text = str(title_text).strip()
        p.font.name = CorporateTheme.FONT_TITLE
        p.font.size = Pt(CorporateTheme.SIZE_TITLE_SLIDE)
        p.font.bold = True
        p.font.color.rgb = CorporateTheme.PRIMARY
        
        # Optional Subtitle
        if subtitle_text:
            p2 = tf.add_paragraph()
            p2.text = str(subtitle_text).strip()
            p2.font.name = CorporateTheme.FONT_BODY
            p2.font.size = Pt(CorporateTheme.SIZE_BODY - 2)
            p2.font.color.rgb = CorporateTheme.SECONDARY
            p2.space_before = Pt(4)

    @staticmethod
    def add_slide_footer(slide, slide_num: int, total_slides: int):
        """Adds standardized footer branding and pagination elements."""
        left, top, width, height = LayoutManager.get_slide_footer_box()
        
        tx_box = slide.shapes.add_textbox(left, top, width, height)
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        p.text = f"DeckMate Automation  |  Slide {slide_num} of {total_slides}"
        p.font.name = CorporateTheme.FONT_BODY
        p.font.size = Pt(CorporateTheme.SIZE_CAPTION)
        p.font.color.rgb = CorporateTheme.SECONDARY

    @staticmethod
    def add_bullet_list(
        slide,
        items: List[str],
        bounding_box: Tuple[Inches, Inches, Inches, Inches],
        list_title: Optional[str] = None
    ):
        """Renders insight bullet items, automatically scaling font size to avoid layout overflows."""
        left, top, width, height = bounding_box
        
        tx_box = slide.shapes.add_textbox(left, top, width, height)
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        # Dynamic Font Size Auto-Fit
        total_chars = sum(len(x) for x in items) + (len(list_title) if list_title else 0)
        if total_chars > 500:
            font_size = CorporateTheme.SIZE_BODY - 3
        elif total_chars > 300:
            font_size = CorporateTheme.SIZE_BODY - 1.5
        else:
            font_size = CorporateTheme.SIZE_BODY
            
        p_idx = 0
        if list_title:
            p = tf.paragraphs[0]
            p.text = str(list_title).strip()
            p.font.name = CorporateTheme.FONT_BODY
            p.font.size = Pt(font_size + 1.5)
            p.font.bold = True
            p.font.color.rgb = CorporateTheme.PRIMARY
            p.space_after = Pt(8)
            p_idx += 1
            
        for item in items:
            p = tf.add_paragraph() if p_idx > 0 else tf.paragraphs[0]
            p.text = str(item).strip()
            p.font.name = CorporateTheme.FONT_BODY
            p.font.size = Pt(font_size)
            p.font.color.rgb = CorporateTheme.SECONDARY
            p.level = 0
            p.space_after = Pt(6)
            # Add simple bullet formatting indicator
            p.text = "•  " + p.text
            p_idx += 1
