import io
import pytest
import pandas as pd
import openpyxl
from app.services.data_intelligence import ingest_workbook
from app.services.quality_analyzer import analyze_workbook_quality
from app.services.schema_detector import detect_column_type
from app.services.kpi_detector import detect_kpis
from app.services.trend_analyzer import calculate_growth_trend, calculate_contributor_rankings
from app.services.fact_generator import generate_facts
from app.services.business_intelligence import BusinessIntelligenceService
from app.schemas.models import DataTypeEnum, SeverityEnum, TrendDirectionEnum

def create_mock_excel(data_dict: dict, messy_header_offset: int = 0) -> bytes:
    """Helper to generate mock Excel workbook binary bytes with optional offsets."""
    output = io.BytesIO()
    
    # We use openpyxl to write to handle manual messy offsets
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)
    
    for sheet_name, rows in data_dict.items():
        ws = wb.create_sheet(title=sheet_name)
        
        # Write offset notes if messy
        for o in range(messy_header_offset):
            ws.append([f"Meta Note {o}", "", "Draft Report"])
            
        # Write actual rows
        for row in rows:
            ws.append(row)
            
    wb.save(output)
    return output.getvalue()

def test_data_intelligence_clean_headers():
    # Setup data with 2 rows of notes at top (messy headers)
    data = {
        "SalesData": [
            ["Region", "Year", "Net Revenue", "Growth Rate"],
            ["North", 2021, "$12,000", "12.5%"],
            ["South", 2022, "$18,500", "-4.2%"],
            ["West", 2023, None, "10%"]
        ]
    }
    file_bytes = create_mock_excel(data, messy_header_offset=2)
    
    # Run ingestion
    collection = ingest_workbook(file_bytes)
    assert "SalesData" in collection
    df = collection["SalesData"]
    
    # Assert columns cleaned and types processed
    assert list(df.columns) == ["Region", "Year", "Net Revenue", "Growth Rate"]
    assert df["Net Revenue"].iloc[0] == 12000.0
    assert df["Growth Rate"].iloc[0] == 0.125
    assert pd.isna(df["Net Revenue"].iloc[2])

def test_duplicate_header_resolution():
    data = {
        "Sheet1": [
            ["Sales", "Sales", "Date"],
            [100, 200, "2023-01-01"],
            [150, 250, "2023-02-01"]
        ]
    }
    file_bytes = create_mock_excel(data)
    collection = ingest_workbook(file_bytes)
    df = collection["Sheet1"]
    
    assert list(df.columns) == ["Sales", "Sales_1", "Date"]

def test_schema_detection():
    series_num = pd.Series([10.5, 20.1, 30.0])
    series_currency = pd.Series(["$100.00", "$200", "$150.50"])
    series_percent = pd.Series(["15%", "25.5%", "10%"])
    series_date = pd.Series(["2023-01-01", "2023-02-01", "2023-03-01"])
    series_cat = pd.Series(["Laptop", "Desktop", "Tablet"])
    series_bool = pd.Series(["Yes", "No", "Yes"])
    series_id = pd.Series(["INV-001", "INV-002", "INV-003"])
    
    assert detect_column_type("val", series_num) == DataTypeEnum.NUMERIC
    assert detect_column_type("cost", series_currency) == DataTypeEnum.CURRENCY
    assert detect_column_type("growth", series_percent) == DataTypeEnum.PERCENTAGE
    assert detect_column_type("date", series_date) == DataTypeEnum.DATE
    assert detect_column_type("product", series_cat) == DataTypeEnum.CATEGORICAL
    assert detect_column_type("active", series_bool) == DataTypeEnum.BOOLEAN
    assert detect_column_type("invoice_no", series_id) == DataTypeEnum.IDENTIFIER

def test_quality_analyzer_issues():
    # Empty worksheet + duplicates
    data = {
        "EmptySheet": [],
        "DataSheet": [
            ["Col1", "Col1", "NumericCol"],
            ["A", "B", 10],
            ["A", "B", 10], # Duplicate row
            [None, "C", 20]  # Missing Col1 cell
        ]
    }
    file_bytes = create_mock_excel(data)
    df_coll = ingest_workbook(file_bytes)
    
    health = analyze_workbook_quality(file_bytes, df_coll)
    
    # Assert checks
    issues_warnings = [i.warning for i in health.issues]
    assert any("empty" in w.lower() for w in issues_warnings)
    assert any("duplicate column headers" in w.lower() for w in issues_warnings)
    assert any("duplicate record" in w.lower() for w in issues_warnings)
    assert health.overall_score < 100.0

def test_kpi_detection():
    df = pd.DataFrame({
        "Revenue": [1000.0, 2000.0, 1500.0],
        "conversion_rate": [0.15, 0.20, 0.18],
        "UnrelatedCol": ["X", "Y", "Z"]
    })
    col_types = {
        "Revenue": DataTypeEnum.CURRENCY,
        "conversion_rate": DataTypeEnum.PERCENTAGE,
        "UnrelatedCol": DataTypeEnum.CATEGORICAL
    }
    
    kpis = detect_kpis("Sheet1", df, col_types)
    kpi_names = [k.name for k in kpis]
    
    assert "Revenue" in kpi_names
    assert "Conversion Rate" in kpi_names
    
    revenue_kpi = next(k for k in kpis if k.name == "Revenue")
    assert revenue_kpi.value == 4500.0  # Sum
    
    conversion_kpi = next(k for k in kpis if k.name == "Conversion Rate")
    assert conversion_kpi.value == 0.18  # Average

def test_trend_calculation():
    df = pd.DataFrame({
        "Period": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01"]),
        "Sales": [100.0, 150.0, 200.0]
    })
    
    trend = calculate_growth_trend("Sheet1", df, "Period", "Sales", DataTypeEnum.CURRENCY)
    assert trend is not None
    assert trend.direction == TrendDirectionEnum.UPWARD
    assert trend.percentage_change == 100.0  # from 100 to 200 is +100%

def test_contributor_rankings():
    df = pd.DataFrame({
        "Product": ["Laptop", "Desktop", "Laptop", "Tablet"],
        "Revenue": [1000.0, 500.0, 2000.0, 500.0]
    })
    
    top, bottom = calculate_contributor_rankings(df, "Product", "Revenue")
    assert top[0]["category"] == "Laptop"
    assert top[0]["value"] == 3000.0
    assert top[0]["share"] == 75.0  # 3000 / 4000 = 75%

def test_full_business_intelligence_orchestration():
    data = {
        "Monthly_Report": [
            ["Date", "Product", "Revenue", "Margin"],
            ["2023-01-01", "Laptop", 1000, 0.15],
            ["2023-02-01", "Desktop", 2000, 0.12],
            ["2023-03-01", "Laptop", 3000, 0.18],
            ["2023-03-01", "Tablet", 500, 0.10]
        ]
    }
    file_bytes = create_mock_excel(data)
    
    summary = BusinessIntelligenceService.analyze_workbook(file_bytes)
    
    assert len(summary.metadata.sheets) == 1
    assert len(summary.kpis) >= 2
    assert len(summary.trends) >= 2
    assert len(summary.facts) > 0
    assert "Monthly_Report" in summary.statistics
    assert "Revenue" in summary.statistics["Monthly_Report"]
    assert summary.statistics["Monthly_Report"]["Revenue"].mean == 1625.0
