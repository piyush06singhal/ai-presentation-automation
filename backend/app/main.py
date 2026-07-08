import json
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas.models import BusinessSummary, StoryboardRequest
from app.services.data_intelligence import ingest_workbook
from app.services.business_intelligence import BusinessIntelligenceService
from app.services.presentation_planner import PresentationPlannerService
from app.services.ppt_compiler import PPTCompiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DeckMate Backend API", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PlanPayload(BaseModel):
    summary: BusinessSummary
    audience: str
    objective: str
    slide_count: int = 5

@app.get("/health")
def health_check():
    """Simple status check endpoint."""
    return {"status": "ok", "app": "DeckMate Services"}

@app.post("/api/analyze", response_model=BusinessSummary)
async def analyze_workbook_endpoint(file: UploadFile = File(...)):
    """Receives an Excel file, analyzes sheets, runs quality checks, and returns computed business facts."""
    if not file.filename.endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=400, detail="Only standard Excel workbooks (.xlsx, .xlsm) are supported.")
    
    try:
        file_bytes = await file.read()
        logger.info(f"Ingesting workbook: {file.filename} ({len(file_bytes)} bytes)")
        
        # 1. Ingest worksheets to dataframes
        df_collection = ingest_workbook(file_bytes)
        
        # 2. Extract facts, KPIs, trends, and health report
        summary = BusinessIntelligenceService.analyze_workbook(file_bytes, df_collection)
        return summary
    except Exception as e:
        logger.error(f"Error in analyze_workbook_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/plan", response_model=StoryboardRequest)
def plan_presentation_endpoint(payload: PlanPayload):
    """Orchestrates LLM presentation storyboarding using only calculated business facts."""
    try:
        planner = PresentationPlannerService()
        storyboard = planner.generate_presentation_plan(
            summary=payload.summary,
            audience=payload.audience,
            objective=payload.objective,
            slide_count=payload.slide_count
        )
        return storyboard
    except Exception as e:
        logger.error(f"Error in plan_presentation_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Presentation planning failed: {str(e)}")

@app.post("/api/generate")
async def generate_presentation_endpoint(
    file: UploadFile = File(...),
    storyboard: str = Form(...),
    summary: str = Form(...)
):
    """Compiles the validated slide plans and Excel metrics into an editable PowerPoint file."""
    try:
        file_bytes = await file.read()
        
        # Parse Form payload strings
        try:
            storyboard_data = json.loads(storyboard)
            storyboard_req = StoryboardRequest.model_validate(storyboard_data)
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Invalid storyboard JSON: {str(err)}")
            
        try:
            summary_data = json.loads(summary)
            summary_req = BusinessSummary.model_validate(summary_data)
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Invalid business summary JSON: {str(err)}")

        logger.info(f"Generating PPTX for storyboard with {len(storyboard_req.slides)} slides.")

        # Re-ingest dataframes for chart generation drawing logic
        df_collection = ingest_workbook(file_bytes)
        
        # Compile presentation bytes
        ppt_bytes = PPTCompiler.compile_presentation(
            plan=storyboard_req,
            summary=summary_req,
            df_collection=df_collection
        )

        return Response(
            content=ppt_bytes,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="deckmate_presentation.pptx"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        logger.error(f"Error in generate_presentation_endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"PowerPoint compilation failed: {str(e)}")
