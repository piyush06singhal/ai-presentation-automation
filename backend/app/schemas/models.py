from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from enum import Enum

class DataTypeEnum(str, Enum):
    NUMERIC = "NUMERIC"
    CURRENCY = "CURRENCY"
    PERCENTAGE = "PERCENTAGE"
    DATE = "DATE"
    CATEGORICAL = "CATEGORICAL"
    BOOLEAN = "BOOLEAN"
    IDENTIFIER = "IDENTIFIER"
    UNKNOWN = "UNKNOWN"

class SeverityEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TrendDirectionEnum(str, Enum):
    UPWARD = "UPWARD"
    DOWNWARD = "DOWNWARD"
    FLAT = "FLAT"
    UNKNOWN = "UNKNOWN"

class HealthIssue(BaseModel):
    severity: SeverityEnum
    warning: str
    recommendation: str
    worksheet: str
    column: Optional[str] = None

class WorkbookHealth(BaseModel):
    issues: List[HealthIssue] = Field(default_factory=list)
    overall_score: float = Field(..., ge=0.0, le=100.0)

class ColumnSchema(BaseModel):
    name: str
    datatype: DataTypeEnum
    sample_values: List[str] = Field(default_factory=list)

class WorksheetMetadata(BaseModel):
    name: str
    columns: List[ColumnSchema] = Field(default_factory=list)
    row_count: int
    col_count: int
    is_empty: bool

class WorkbookMetadata(BaseModel):
    sheets: List[WorksheetMetadata] = Field(default_factory=list)
    file_size_bytes: int
    active_sheets_count: int

class DetectedKPI(BaseModel):
    name: str
    value: float
    column: str
    worksheet: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    unit: Optional[str] = None
    description: str

class BusinessTrend(BaseModel):
    metric: str
    direction: TrendDirectionEnum
    percentage_change: float
    time_col: str
    growth_rate: float
    description: str
    worksheet: str

class BusinessFact(BaseModel):
    fact_id: str
    statement: str
    source_worksheet: str
    metrics: List[str] = Field(default_factory=list)
    importance: int = Field(..., ge=1, le=3)

class DatasetStatistics(BaseModel):
    mean: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    count: int
    std: Optional[float] = None

class BusinessSummary(BaseModel):
    metadata: WorkbookMetadata
    health: WorkbookHealth
    kpis: List[DetectedKPI] = Field(default_factory=list)
    trends: List[BusinessTrend] = Field(default_factory=list)
    facts: List[BusinessFact] = Field(default_factory=list)
    statistics: Dict[str, Dict[str, DatasetStatistics]] = Field(default_factory=dict)

class SlidePlan(BaseModel):
    slide_id: str
    template_id: str = Field(..., description="Slide layout template ID")
    title: str
    objective: str
    worksheet: str
    chart_type: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[List[str]] = None
    insights: List[str] = Field(..., max_length=4)
    required_kpis: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    speaker_notes: str
    why_created: str
    priority: int = Field(1, ge=1, le=3)
    confidence: float = Field(1.0, ge=0.0, le=1.0)

class StoryboardRequest(BaseModel):
    audience: str
    objective: str
    slides: List[SlidePlan]

class StoryboardLLMResponse(BaseModel):
    slides: List[SlidePlan]
