import pytest
from unittest.mock import MagicMock, patch
from app.schemas.models import (
    BusinessSummary, 
    WorkbookMetadata, 
    WorksheetMetadata, 
    ColumnSchema, 
    WorkbookHealth,
    DataTypeEnum, 
    DetectedKPI, 
    BusinessTrend, 
    BusinessFact, 
    TrendDirectionEnum,
    SlidePlan,
    SeverityEnum
)
from app.services.exceptions import JSONParsingException, ValidationException, GroqAPIException
from app.services.audience_adapter import get_audience_instructions
from app.services.prompt_builder import build_user_prompt
from app.services.chart_validation import validate_and_override_chart
from app.services.recommendation_validator import validate_recommendations
from app.services.output_validator import validate_presentation_plan
from app.services.storyboard_generator import parse_and_validate_storyboard
from app.services.presentation_planner import PresentationPlannerService

@pytest.fixture
def mock_summary():
    """Generates a dummy BusinessSummary dataset for context queries."""
    sheets = [
        WorksheetMetadata(
            name="Q3_Sales",
            columns=[
                ColumnSchema(name="Date", datatype=DataTypeEnum.DATE),
                ColumnSchema(name="Product", datatype=DataTypeEnum.CATEGORICAL),
                ColumnSchema(name="Revenue", datatype=DataTypeEnum.CURRENCY)
            ],
            row_count=10,
            col_count=3,
            is_empty=False
        )
    ]
    metadata = WorkbookMetadata(sheets=sheets, file_size_bytes=1000, active_sheets_count=1)
    health = WorkbookHealth(issues=[], overall_score=100.0)
    kpis = [
        DetectedKPI(
            name="Revenue",
            value=12000.0,
            column="Revenue",
            worksheet="Q3_Sales",
            confidence=1.0,
            unit="$",
            description="Sales total revenue."
        )
    ]
    trends = [
        BusinessTrend(
            metric="Revenue",
            direction=TrendDirectionEnum.DOWNWARD,
            percentage_change=-15.5,
            time_col="Date",
            growth_rate=-1.2,
            description="Revenue dropped by 15.5%.",
            worksheet="Q3_Sales"
        )
    ]
    facts = [
        BusinessFact(
            fact_id="FACT_001",
            statement="Revenue fell by 15.5%.",
            source_worksheet="Q3_Sales",
            metrics=["Revenue"],
            importance=3
        )
    ]
    
    return BusinessSummary(
        metadata=metadata,
        health=health,
        kpis=kpis,
        trends=trends,
        facts=facts,
        statistics={"Q3_Sales": {}}
    )

def test_audience_tone_matching():
    finance_profile = get_audience_instructions("Finance")
    assert finance_profile["detail_level"] == "HIGH"
    assert "precision" in finance_profile["tone_instruction"].lower() or "analytical" in finance_profile["tone_instruction"].lower()
    
    # Check fallback for unknown profiles
    fallback_profile = get_audience_instructions("UnknownRole")
    assert fallback_profile["detail_level"] == "LOW"  # CEO fallback

def test_prompt_builder_structure(mock_summary):
    profile = get_audience_instructions("CEO")
    prompt = build_user_prompt(
        summary=mock_summary,
        audience_name="CEO",
        audience_profile=profile,
        objective="Review margins",
        slide_count=5
    )
    
    # Assert crucial elements are merged in prompt string
    assert "CEO" in prompt
    assert "FACT_001" in prompt
    assert "Revenue fell by 15.5%" in prompt
    assert "Q3_Sales" in prompt

def test_chart_engine_overrides():
    col_types = {"Date": DataTypeEnum.DATE, "Revenue": DataTypeEnum.CURRENCY, "Region": DataTypeEnum.CATEGORICAL}
    
    # Trend line overrides: Date X-axis must yield a Line Chart
    chart, x, y = validate_and_override_chart("Sheet1", col_types, "Pie", "Date", ["Revenue"], 8)
    assert chart == "Line"
    
    # Large datasets should fall back to Table layout (None)
    chart, x, y = validate_and_override_chart("Sheet1", col_types, "Bar", "Region", ["Revenue"], 20)
    assert chart is None
    
    # Categorical Line recommendation should override to Bar
    chart, x, y = validate_and_override_chart("Sheet1", col_types, "Line", "Region", ["Revenue"], 8)
    assert chart == "Bar"

def test_recommendations_contradiction_filter():
    trends = [
        BusinessTrend(
            metric="Revenue",
            direction=TrendDirectionEnum.DOWNWARD,
            percentage_change=-10.0,
            time_col="Date",
            growth_rate=-0.5,
            description="Decline",
            worksheet="Sheet1"
        )
    ]
    
    recs = [
        "Continue scaling high revenue growth strategies.", # CONTRADICTORY (downward trend vs growth advice)
        "Investigate pricing factors to recover revenue declines.", # VALID
        "Optimize marketing campaign spending." # VALID
    ]
    
    clean_recs = validate_recommendations(recs, trends)
    assert len(clean_recs) == 2
    assert "growth" not in clean_recs[0].lower()

def test_storyboard_generator_parsing():
    valid_json = """
    {
      "slides": [
        {
          "slide_id": "slide_01",
          "template_id": "Title",
          "title": "Welcome",
          "objective": "Intro",
          "worksheet": "Q3_Sales",
          "insights": ["Start session"],
          "speaker_notes": "Welcome team",
          "why_created": "Necessity",
          "priority": 1,
          "confidence": 1.0
        }
      ]
    }
    """
    slides = parse_and_validate_storyboard(valid_json)
    assert len(slides) == 1
    assert slides[0].title == "Welcome"

    # Test markdown wrapper stripping
    wrapped_json = "```json\n" + valid_json + "\n```"
    slides_wrapped = parse_and_validate_storyboard(wrapped_json)
    assert len(slides_wrapped) == 1
    assert slides_wrapped[0].title == "Welcome"

    # Test malformed payload trigger
    invalid_json = "{'slides': []"
    with pytest.raises(JSONParsingException):
        parse_and_validate_storyboard(invalid_json)

def test_output_validation_errors(mock_summary):
    # Slide references a non-existent sheet
    slide = SlidePlan(
        slide_id="slide_1",
        template_id="Title",
        title="Revenue Analysis",
        objective="Review sales",
        worksheet="Invalid_Worksheet_Name",
        insights=["Insights"],
        speaker_notes="Notes",
        why_created="Reason",
        priority=1,
        confidence=1.0
    )
    
    with pytest.raises(ValidationException):
        validate_presentation_plan([slide], mock_summary)

@patch("app.services.groq_client.GroqClientWrapper.query_llm")
def test_presentation_planner_orchestrator(mock_query, mock_summary):
    # Mock LLM JSON output response
    mock_query.return_value = """
    {
      "slides": [
        {
          "slide_id": "slide_1",
          "template_id": "Title",
          "title": "Quarterly Report",
          "objective": "Review performance metrics",
          "worksheet": "Q3_Sales",
          "insights": ["Revenue fell by 15.5%"],
          "speaker_notes": "First slide",
          "why_created": "Context",
          "priority": 1,
          "confidence": 1.0
        }
      ]
    }
    """
    planner = PresentationPlannerService()
    plan = planner.generate_presentation_plan(
        summary=mock_summary,
        audience="CEO",
        objective="Review sales performance",
        slide_count=1
    )
    
    assert plan.audience == "CEO"
    assert len(plan.slides) == 1
    assert plan.slides[0].title == "Quarterly Report"
