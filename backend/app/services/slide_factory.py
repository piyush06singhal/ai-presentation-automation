import pandas as pd
from typing import Dict, List
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from app.schemas.models import SlidePlan, BusinessSummary
from app.services.theme_manager import CorporateTheme
from app.services.layout_manager import LayoutManager
from app.services.text_renderer import TextRenderer
from app.services.content_renderer import ContentRenderer
from app.services.shape_builder import ShapeBuilder
from app.services.chart_builder import ChartBuilder
from app.services.table_builder import TableBuilder

class SlideFactory:
    """Dispatches layout construction tasks to build formatted presentation slides."""

    @staticmethod
    def build_slide(
        slide,
        plan: SlidePlan,
        summary: BusinessSummary,
        df_collection: Dict[str, pd.DataFrame]
    ):
        """Orchestrates header, visual layouts, insights, and speaker notes mapping."""
        template_id = plan.template_id
        
        # 1. Draw Slide Titles & Headers (unless it is the main Title slide)
        if template_id != "Title":
            ContentRenderer.render_header(slide, plan)
            
        # 2. Compile visual template layouts
        if template_id == "Title":
            SlideFactory._build_title_slide(slide, plan)
        elif template_id == "Agenda":
            SlideFactory._build_agenda_slide(slide, plan, summary)
        elif template_id == "KPI Dashboard":
            SlideFactory._build_kpi_dashboard_slide(slide, plan, summary)
        elif template_id == "Trend Analysis" or template_id == "Category Comparison":
            SlideFactory._build_chart_slide(slide, plan, summary, df_collection)
        elif template_id == "Summary Table":
            SlideFactory._build_table_slide(slide, plan, summary, df_collection)
        elif template_id == "Recommendations":
            SlideFactory._build_recommendation_slide(slide, plan)
        elif template_id == "Appendix":
            SlideFactory._build_appendix_slide(slide, plan, summary)
        else:
            # Fallback layout: standard executive summary layout (Text Flow)
            content_box = LayoutManager.get_full_content_box()
            ContentRenderer.render_insights(slide, plan.insights, content_box)

        # 3. Add Speaker notes
        ContentRenderer.apply_speaker_notes(slide, plan.speaker_notes)

    @staticmethod
    def _build_title_slide(slide, plan: SlidePlan):
        """Draws a clean, centered title page layout."""
        # 1. Main Title
        left = Inches(1.0)
        top = Inches(2.2)
        width = CorporateTheme.SLIDE_WIDTH - Inches(2.0)
        height = Inches(1.8)
        
        tx_box = slide.shapes.add_textbox(left, top, width, height)
        tf = tx_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        p.text = plan.title.upper()
        p.font.name = CorporateTheme.FONT_TITLE
        p.font.size = Pt(CorporateTheme.SIZE_TITLE_MAIN)
        p.font.bold = True
        p.font.color.rgb = CorporateTheme.PRIMARY
        
        # 2. Objective Subtitle
        p2 = tf.add_paragraph()
        p2.text = plan.objective
        p2.alignment = PP_ALIGN.CENTER
        p2.font.name = CorporateTheme.FONT_BODY
        p2.font.size = Pt(CorporateTheme.SIZE_BODY + 4)
        p2.font.color.rgb = CorporateTheme.ACCENT
        p2.space_before = Pt(12)

        # 3. Date / Presenter metadata block at bottom
        meta_left = Inches(2.0)
        meta_top = Inches(5.0)
        meta_width = CorporateTheme.SLIDE_WIDTH - Inches(4.0)
        meta_height = Inches(0.8)
        
        meta_box = slide.shapes.add_textbox(meta_left, meta_top, meta_width, meta_height)
        mtf = meta_box.text_frame
        mtf.word_wrap = True
        
        p3 = mtf.paragraphs[0]
        p3.alignment = PP_ALIGN.CENTER
        p3.text = "Prepared by DeckMate Presentation Automation Platform"
        p3.font.name = CorporateTheme.FONT_BODY
        p3.font.size = Pt(CorporateTheme.SIZE_CAPTION)
        p3.font.color.rgb = CorporateTheme.SECONDARY

    @staticmethod
    def _build_agenda_slide(slide, plan: SlidePlan, summary: BusinessSummary):
        """Renders the agenda slide listing analyzed worksheets as contents."""
        content_box = LayoutManager.get_full_content_box()
        
        agenda_items = []
        for i, s in enumerate(summary.metadata.sheets):
            agenda_items.append(f"Section {i+1}: {s.name} ({s.row_count} Rows Analyzed)")
            
        # Draw Agenda columns list
        ContentRenderer.render_insights(slide, agenda_items, content_box)

    @staticmethod
    def _build_kpi_dashboard_slide(slide, plan: SlidePlan, summary: BusinessSummary):
        """Renders 4 KPI cards arranged in a 2x2 grid, with insight bullets underneath."""
        # Split content zone: Top 60% for cards, bottom 40% for insights
        parent_left, parent_top, parent_width, parent_height = LayoutManager.get_full_content_box()
        
        grid_height = Inches(3.0)
        grid_box = (parent_left, parent_top, parent_width, grid_height)
        
        # Get up to 4 KPIs
        display_kpis = summary.kpis[:4]
        if not display_kpis:
            # Fallback to text summary
            ContentRenderer.render_insights(slide, plan.insights, (parent_left, parent_top, parent_width, parent_height))
            return
            
        cols = min(4, len(display_kpis))
        cells = LayoutManager.get_grid_cells(rows=1, cols=cols, parent_box=grid_box)
        
        for idx, cell in enumerate(cells):
            kpi = display_kpis[idx]
            val_str = f"{kpi.unit or ''}{kpi.value:,}" if kpi.unit != "%" else f"{kpi.value}%"
            # Draw Card
            ShapeBuilder.draw_kpi_card(
                slide=slide,
                left=cell[0],
                top=cell[1],
                width=cell[2],
                height=cell[3],
                metric_value=val_str,
                metric_label=kpi.name
            )
            
        # Insights bullet box placed in the remaining bottom space
        insight_box = (
            parent_left,
            parent_top + grid_height + Inches(0.3),
            parent_width,
            parent_height - grid_height - Inches(0.3)
        )
        ContentRenderer.render_insights(slide, plan.insights, insight_box)

    @staticmethod
    def _build_chart_slide(
        slide,
        plan: SlidePlan,
        summary: BusinessSummary,
        df_collection: Dict[str, pd.DataFrame]
    ):
        """Assembles split column layouts: Left column draws chart, right column draws bullet lists."""
        left_box, right_box = LayoutManager.get_split_layout_boxes()
        
        df = df_collection.get(plan.worksheet)
        chart_success = False
        
        # Attempt to render native chart
        if df is not None and plan.chart_type and plan.x_axis and plan.y_axis:
            try:
                ChartBuilder.draw_chart(
                    slide=slide,
                    bounding_box=left_box,
                    chart_type=plan.chart_type,
                    df=df,
                    x_col=plan.x_axis,
                    y_cols=plan.y_axis
                )
                chart_success = True
            except Exception:
                chart_success = False

        # Fallback to Summary Table if chart drawing fails or is set to None
        if not chart_success and df is not None and plan.x_axis and plan.y_axis:
            try:
                TableBuilder.draw_table(
                    slide=slide,
                    bounding_box=left_box,
                    df=df,
                    x_col=plan.x_axis,
                    y_cols=plan.y_axis
                )
            except Exception:
                # If table also fails, draw a callout warning
                ShapeBuilder.draw_callout_box(
                    slide=slide,
                    bounding_box=left_box,
                    text="Factual source data columns could not be loaded into visual shape grids.",
                    border_color=CorporateTheme.WARNING
                )

        # Draw bullet insights in the right column box
        ContentRenderer.render_insights(slide, plan.insights, right_box)

    @staticmethod
    def _build_table_slide(
        slide,
        plan: SlidePlan,
        summary: BusinessSummary,
        df_collection: Dict[str, pd.DataFrame]
    ):
        """Layout slide displaying a fullscreen data grid comparison list."""
        left_box, right_box = LayoutManager.get_split_layout_boxes()
        df = df_collection.get(plan.worksheet)
        
        if df is not None and plan.x_axis and plan.y_axis:
            try:
                TableBuilder.draw_table(
                    slide=slide,
                    bounding_box=left_box,
                    df=df,
                    x_col=plan.x_axis,
                    y_cols=plan.y_axis
                )
            except Exception:
                ShapeBuilder.draw_callout_box(
                    slide=slide,
                    bounding_box=left_box,
                    text="Failed to display data summary grid.",
                    border_color=CorporateTheme.ERROR
                )
                
        # Insights list
        ContentRenderer.render_insights(slide, plan.insights, right_box)

    @staticmethod
    def _build_recommendation_slide(slide, plan: SlidePlan):
        """Draws horizontal callout cards for each action item."""
        parent_left, parent_top, parent_width, parent_height = LayoutManager.get_full_content_box()
        
        recs = plan.recommendations if plan.recommendations else []
        if not recs:
            # Fallback to standard summary if recommendations list is empty
            ContentRenderer.render_insights(slide, plan.insights, (parent_left, parent_top, parent_width, parent_height))
            return
            
        rows = len(recs)
        cells = LayoutManager.get_grid_cells(rows=rows, cols=1, parent_box=(parent_left, parent_top, parent_width, parent_height))
        
        for idx, cell in enumerate(cells):
            ShapeBuilder.draw_callout_box(
                slide=slide,
                bounding_box=cell,
                text=recs[idx],
                border_color=CorporateTheme.SUCCESS
            )

    @staticmethod
    def _build_appendix_slide(slide, plan: SlidePlan, summary: BusinessSummary):
        """Displays data audit quality indicators and checks status logs."""
        left_box, right_box = LayoutManager.get_split_layout_boxes()
        
        # 1. Left side: Audit issues summary
        health_issues_str = []
        if not summary.health.issues:
            health_issues_str.append("Workbook checks passed. Health status is clean.")
        else:
            for issue in summary.health.issues[:6]:  # Limit to first 6 warnings to avoid overflow
                health_issues_str.append(f"[{issue.severity.value}] Worksheet '{issue.worksheet}': {issue.warning}")
                
        TextRenderer.add_bullet_list(
            slide=slide,
            items=health_issues_str,
            bounding_box=left_box,
            list_title="Workbook Data Quality Audit Log"
        )
        
        # 2. Right side: standard outline notes
        ContentRenderer.render_insights(slide, plan.insights, right_box)
