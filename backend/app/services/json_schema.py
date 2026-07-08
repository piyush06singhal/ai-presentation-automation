import json
from app.schemas.models import StoryboardRequest

def get_presentation_plan_schema() -> str:
    """Generates and returns the structural JSON schema for a StoryboardRequest presentation plan."""
    return json.dumps(StoryboardRequest.model_json_schema(), indent=2)
