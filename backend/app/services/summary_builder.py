import pandas as pd
from typing import Dict, List, Any
from app.schemas.models import (
    BusinessSummary, 
    WorkbookMetadata, 
    WorksheetMetadata, 
    ColumnSchema, 
    WorkbookHealth, 
    DetectedKPI, 
    BusinessTrend, 
    BusinessFact, 
    DatasetStatistics,
    DataTypeEnum
)

def build_summary(
    df_collection: Dict[str, pd.DataFrame],
    file_bytes: bytes,
    health: WorkbookHealth,
    column_types: Dict[str, Dict[str, DataTypeEnum]],
    kpis: List[DetectedKPI],
    trends: List[BusinessTrend],
    facts: List[BusinessFact]
) -> BusinessSummary:
    """Consolidates clean DataFrames, health checks, KPIs, trends, and column stats into a BusinessSummary object."""
    
    # 1. Build Worksheet and Workbook Metadata
    sheet_meta_list: List[WorksheetMetadata] = []
    for sheet_name, df in df_collection.items():
        col_schemas: List[ColumnSchema] = []
        for col_name in df.columns:
            dtype = column_types[sheet_name].get(col_name, DataTypeEnum.UNKNOWN)
            # Sample 3 string values for validation preview
            samples = df[col_name].dropna().head(3).astype(str).tolist()
            col_schemas.append(ColumnSchema(
                name=col_name,
                datatype=dtype,
                sample_values=samples
            ))
            
        sheet_meta_list.append(WorksheetMetadata(
            name=sheet_name,
            columns=col_schemas,
            row_count=len(df),
            col_count=len(df.columns),
            is_empty=df.empty
        ))
        
    metadata = WorkbookMetadata(
        sheets=sheet_meta_list,
        file_size_bytes=len(file_bytes),
        active_sheets_count=len(sheet_meta_list)
    )

    # 2. Build descriptive statistics per sheet column
    stats_dict: Dict[str, Dict[str, DatasetStatistics]] = {}
    for sheet_name, df in df_collection.items():
        stats_dict[sheet_name] = {}
        for col in df.columns:
            col_data = df[col].dropna()
            dtype = column_types[sheet_name].get(col, DataTypeEnum.UNKNOWN)
            
            # Check if this column type is numeric/currency/percentage
            is_numeric = dtype in [DataTypeEnum.NUMERIC, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE]
            
            if is_numeric and not col_data.empty:
                desc = col_data.describe()
                stats_dict[sheet_name][col] = DatasetStatistics(
                    mean=round(float(desc.get("mean", 0.0)), 2),
                    min=round(float(desc.get("min", 0.0)), 2),
                    max=round(float(desc.get("max", 0.0)), 2),
                    count=int(desc.get("count", 0)),
                    std=round(float(desc.get("std", 0.0)), 2) if not pd.isna(desc.get("std")) else 0.0
                )
            else:
                stats_dict[sheet_name][col] = DatasetStatistics(
                    count=len(col_data)
                )

    return BusinessSummary(
        metadata=metadata,
        health=health,
        kpis=kpis,
        trends=trends,
        facts=facts,
        statistics=stats_dict
    )
