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

    try:
        # Pydantic v2 validation
        storyboard = StoryboardLLMResponse.model_validate(data)
        return storyboard.slides
    except ValidationError as e:
        raise JSONParsingException(f"LLM JSON violates plan schemas. Validation error: {str(e)}") from e
