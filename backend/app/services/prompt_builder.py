import json
from typing import Dict, Any, List
from app.schemas.models import BusinessSummary

def build_system_prompt() -> str:
    """Generates the base system rules and computational constraints for the LLM."""
    return (
        "You are an expert Executive Presentation Storyboard Planner. "
        "Your task is to plan a structured, highly persuasive slide deck using ONLY provided database facts. "
        "Strictly adhere to the following computation and logic rules:\n\n"
        "COMPUTATION BANS:\n"
        "1. DO NOT calculate, aggregate, or adjust any numeric values. Use the metrics EXACTLY as they appear in the Fact Sheet.\n"
        "2. If a metric or column is not explicitly computed and presented in the Fact Sheet, you cannot refer to it.\n"
        "3. DO NOT fabricate any business metrics or make claims about margins, costs, or growth not explicitly listed in the facts.\n\n"
        "NARRATIVE AND PLANNING CONTROLS:\n"
        "1. Each slide must use a specific layout template ID (e.g., Title, Agenda, Executive Summary, KPI Dashboard, Trend Analysis, Category Comparison, Recommendations, Appendix).\n"
        "2. Make slide titles and business insights context-specific and adapted to the target audience's interests.\n"
        "3. Every slide must reference a single source worksheet from the workbook metadata.\n"
        "4. Recommendations must be directly backed by the provided facts. If a fact indicates a metric decline, do not suggest growth.\n"
        "5. Keep slide insights extremely concise and punchy (no long paragraphs). Every insight bullet item MUST start with a bold prefix label, e.g. '**Task Volatility**: High standard deviation in days required' or '**Department Share**: Marketing comprises 34% of active projects.' This is critical to ensure slides look visual rather than like a document.\n\n"
        "OUTPUT FORMATTING:\n"
        "You must return ONLY a valid JSON object matching the requested schema. No additional text, markdown containers, or explanations."
    )

def build_user_prompt(
    summary: BusinessSummary,
    audience_name: str,
    audience_profile: Dict[str, Any],
    objective: str,
    slide_count: int
) -> str:
    """Assembles the dynamic context parameters, workbook statistics, audience instructions, and target layout schema."""
    # Format facts list
    facts_text = "\n".join([f"- [{f.fact_id}] {f.statement} (Worksheet: {f.source_worksheet})" for f in summary.facts])
    if not facts_text:
        facts_text = "- No business facts detected."
        
    # Format KPIs list
    kpis_text = "\n".join([
        f"- KPI: {k.name} | Value: {k.unit or ''}{k.value} | Worksheet: {k.worksheet} | Column: {k.column}"
        for k in summary.kpis
    ])
    if not kpis_text:
        kpis_text = "- No primary KPIs detected."

    # Format trends list
    trends_text = "\n".join([
        f"- Metric: {t.metric} | Direction: {t.direction.value} | Net Change: {t.percentage_change}% | Worksheet: {t.worksheet}"
        for t in summary.trends
    ])
    if not trends_text:
        trends_text = "- No growth trends detected."

    # Format health issues
    health_text = "\n".join([
        f"- [{i.severity.value}] {i.warning} Recommendation: {i.recommendation}"
        for i in summary.health.issues if i.severity.value in ["MEDIUM", "HIGH"]
    ])
    if not health_text:
        health_text = "- Workbook Health is clean."

    # Format worksheets schemas
    sheets_schema = []
    for s in summary.metadata.sheets:
        cols_info = [f"{c.name} ({c.datatype.value})" for c in s.columns]
        sheets_schema.append(f"Worksheet: '{s.name}' ({s.row_count} rows, {s.col_count} columns)\n  Columns: {', '.join(cols_info)}")
    schema_text = "\n".join(sheets_schema)

    # Format output JSON template shape
    json_shape = {
        "slides": [
            {
                "slide_id": "slide_01",
                "template_id": "Title",
                "title": "Title of the slide",
                "objective": "Objective of this slide",
                "worksheet": "Source worksheet name",
                "chart_type": "Line | Bar | Pie | Horizontal Bar | None (null if not using a chart)",
                "x_axis": "column_name (null if no chart)",
                "y_axis": ["column_name_1", "column_name_2 (null if no chart)"],
                "insights": ["**Key Metric**: 2-3 concise insight bullets formatted exactly with a bold prefix label."],
                "required_kpis": ["KPI_Name_1", "KPI_Name_2"],
                "recommendations": ["**Action Step**: Action-oriented recommendations formatted with a bold prefix label (optional)"],
                "speaker_notes": "Detailed speech notes for the presenter",
                "why_created": "Logical justification for creating this slide",
                "priority": 1,
                "confidence": 0.95
            }
        ]
    }

    return (
        f"--- CONTEXT DATA ---\n"
        f"PRESENTATION OBJECTIVE:\n{objective}\n\n"
        f"TARGET AUDIENCE:\n{audience_name}\n"
        f"- Writing Tone Guideline: {audience_profile['tone_instruction']}\n"
        f"- Metric Area of Concern: {', '.join(audience_profile['focus_metrics'])}\n"
        f"- Recommendation Scope: {audience_profile['recommendation_focus']}\n"
        f"- Target Detail Level: {audience_profile['detail_level']}\n\n"
        f"SLIDE DECK TARGET COUNT:\nGenerate exactly {slide_count} slides representing a complete narrative flow.\n\n"
        f"DATASET WORKBOOK SCHEMA:\n{schema_text}\n\n"
        f"DETERMINISTIC FACT SHEET (Source facts to write copy from):\n{facts_text}\n\n"
        f"PRIMARY COMPUTED KPIs:\n{kpis_text}\n\n"
        f"CALCULATED TRENDS:\n{trends_text}\n\n"
        f"WORKBOOK HEALTH ALERTS:\n{health_text}\n\n"
        f"--- EXPECTED JSON OUTPUT SCHEMA ---\n"
        f"You must return a valid JSON object matching the following structure:\n"
        f"{json.dumps(json_shape, indent=2)}\n\n"
        f"Confirm that all column names, worksheet names, and values referenced in the slides match the context details exactly. Do not invent any names."
    )
