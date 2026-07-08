from typing import List, Dict

class TemplateLayoutConfig:
    """Configures metadata and constraint properties for individual slide templates."""
    def __init__(self, template_id: str, name: str, layout_type: str, allowed_charts: List[str]):
        self.template_id = template_id
        self.name = name
        self.layout_type = layout_type  # "FULL", "SPLIT", "GRID", "FLOW"
        self.allowed_charts = allowed_charts

TEMPLATE_REGISTRY: Dict[str, TemplateLayoutConfig] = {
    "Title": TemplateLayoutConfig(
        template_id="Title",
        name="Title Slide",
        layout_type="FULL",
        allowed_charts=[]
    ),
    "Agenda": TemplateLayoutConfig(
        template_id="Agenda",
        name="Agenda Slide",
        layout_type="FULL",
        allowed_charts=[]
    ),
    "Executive Summary": TemplateLayoutConfig(
        template_id="Executive Summary",
        name="Executive Summary Slide",
        layout_type="FLOW",
        allowed_charts=[]
    ),
    "KPI Dashboard": TemplateLayoutConfig(
        template_id="KPI Dashboard",
        name="KPI Dashboard Slide",
        layout_type="GRID",
        allowed_charts=[]
    ),
    "Trend Analysis": TemplateLayoutConfig(
        template_id="Trend Analysis",
        name="Trend Analysis Slide",
        layout_type="SPLIT",
        allowed_charts=["Line", "Area"]
    ),
    "Category Comparison": TemplateLayoutConfig(
        template_id="Category Comparison",
        name="Category Comparison Slide",
        layout_type="SPLIT",
        allowed_charts=["Bar", "Horizontal Bar", "Pie"]
    ),
    "Summary Table": TemplateLayoutConfig(
        template_id="Summary Table",
        name="Data Summary Table Slide",
        layout_type="SPLIT",
        allowed_charts=[]
    ),
    "Recommendations": TemplateLayoutConfig(
        template_id="Recommendations",
        name="Recommendations Slide",
        layout_type="FLOW",
        allowed_charts=[]
    ),
    "Appendix": TemplateLayoutConfig(
        template_id="Appendix",
        name="Appendix Slide",
        layout_type="FULL",
        allowed_charts=[]
    )
}

def get_template_config(template_id: str) -> TemplateLayoutConfig:
    """Retrieves config parameters for a slide layout or falls back to Executive Summary."""
    return TEMPLATE_REGISTRY.get(template_id, TEMPLATE_REGISTRY["Executive Summary"])
