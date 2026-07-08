import pandas as pd
from typing import Dict, List, Any
from app.schemas.models import BusinessSummary, DataTypeEnum
from app.services.data_intelligence import ingest_workbook
from app.services.quality_analyzer import analyze_workbook_quality
from app.services.schema_detector import detect_column_type
from app.services.kpi_detector import detect_kpis
from app.services.trend_analyzer import calculate_growth_trend, calculate_contributor_rankings
from app.services.fact_generator import generate_facts
from app.services.summary_builder import build_summary

class BusinessIntelligenceService:
    """Orchestrates the conversion of a raw uploaded Excel workbook into structured, clean business summaries."""
    
    @staticmethod
    def analyze_workbook(file_bytes: bytes) -> BusinessSummary:
        """Executes the ingestion, cleaning, diagnostics, calculation, and fact extraction steps."""
        # 1. Clean Dataframes
        df_collection = ingest_workbook(file_bytes)
        
        # 2. Quality Diagnostics
        health = analyze_workbook_quality(file_bytes, df_collection)
        
        # 3. Detect column types
        column_types: Dict[str, Dict[str, DataTypeEnum]] = {}
        for sheet_name, df in df_collection.items():
            column_types[sheet_name] = {}
            for col in df.columns:
                column_types[sheet_name][col] = detect_column_type(col, df[col])
                
        # 4. KPI Discovery
        kpis = []
        for sheet_name, df in df_collection.items():
            sheet_types = column_types[sheet_name]
            kpis.extend(detect_kpis(sheet_name, df, sheet_types))
            
        # 5. Trend & Contributor Calculations
        trends = []
        rankings = {}
        for sheet_name, df in df_collection.items():
            sheet_types = column_types[sheet_name]
            
            # Identify columns
            date_cols = [c for c, t in sheet_types.items() if t == DataTypeEnum.DATE]
            num_cols = [c for c, t in sheet_types.items() if t in [DataTypeEnum.NUMERIC, DataTypeEnum.CURRENCY, DataTypeEnum.PERCENTAGE]]
            cat_cols = [c for c, t in sheet_types.items() if t == DataTypeEnum.CATEGORICAL]
            
            # Time trends
            if date_cols and num_cols:
                # Group by first date column to keep it simple and clean
                d_col = date_cols[0]
                for n_col in num_cols:
                    trend = calculate_growth_trend(sheet_name, df, d_col, n_col, sheet_types[n_col])
                    if trend:
                        trends.append(trend)
                        
            # Category share rankings
            if cat_cols and num_cols:
                # Limit categories to avoid long loops (analyze up to 2 categorical columns)
                for c_col in cat_cols[:2]:
                    for n_col in num_cols:
                        top, bottom = calculate_contributor_rankings(df, c_col, n_col)
                        if top:
                            rankings[f"{sheet_name}|{c_col}|{n_col}"] = {
                                "top": top,
                                "bottom": bottom
                            }
                            
        # 6. Fact Summarization
        facts = generate_facts(kpis, trends, rankings)
        
        # 7. Package Summary Payload
        summary = build_summary(
            df_collection=df_collection,
            file_bytes=file_bytes,
            health=health,
            column_types=column_types,
            kpis=kpis,
            trends=trends,
            facts=facts
        )
        
        return summary
