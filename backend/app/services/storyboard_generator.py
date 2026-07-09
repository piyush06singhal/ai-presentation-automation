import json
from typing import List
from pydantic import ValidationError
from app.schemas.models import StoryboardLLMResponse, SlidePlan
from app.services.exceptions import JSONParsingException

def parse_and_validate_storyboard(raw_json_str: str) -> List[SlidePlan]:
    """Parses raw text JSON from the LLM, validating fields against Pydantic models."""
    cleaned_json = raw_json_str.strip()
    
    # Strip markdown code blocks if the LLM wrapped them in ```json ... ```
    if cleaned_json.startswith("```"):
        # find index of first newline
        first_newline = cleaned_json.find("\n")
        # find index of last backticks
        last_backticks = cleaned_json.rfind("```")
        if first_newline != -1 and last_backticks != -1:
            cleaned_json = cleaned_json[first_newline:last_backticks].strip()

    try:
        data = json.loads(cleaned_json)
    except json.JSONDecodeError as e:
        raise JSONParsingException(f"Failed to parse LLM response as JSON. Error: {str(e)}") from e

    # Pre-process slides data to coerce types and fill missing defaults safely
    if isinstance(data, dict) and "slides" in data and isinstance(data["slides"], list):
        for slide in data["slides"]:
            if isinstance(slide, dict):
                # 1. Sanitize priority
                if "priority" in slide:
                    try:
                        p = int(slide["priority"])
                        slide["priority"] = max(1, min(3, p))
                    except (ValueError, TypeError):
                        slide["priority"] = 2
                else:
                    slide["priority"] = 2

                # 2. Sanitize confidence
                if "confidence" in slide:
                    try:
                        c = float(slide["confidence"])
                        slide["confidence"] = max(0.0, min(1.0, c))
                    except (ValueError, TypeError):
                        slide["confidence"] = 1.0
                else:
                    slide["confidence"] = 1.0

                # 3. Coerce lists from None/missing to []
                for list_field in ["insights", "recommendations", "required_kpis", "y_axis"]:
                    if list_field not in slide or slide[list_field] is None:
                        slide[list_field] = []
                    elif not isinstance(slide[list_field], list):
                        slide[list_field] = [str(slide[list_field])]

                # 4. Coerce strings from None/missing to ""
                for str_field in ["title", "objective", "worksheet", "speaker_notes", "why_created"]:
                    if str_field not in slide or slide[str_field] is None:
                        slide[str_field] = ""
                    else:
                        slide[str_field] = str(slide[str_field])

    try:
        # Pydantic v2 validation
        storyboard = StoryboardLLMResponse.model_validate(data)
        return storyboard.slides
    except ValidationError as e:
        raise JSONParsingException(f"LLM JSON violates plan schemas. Validation error: {str(e)}") from e
