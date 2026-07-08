import logging
from typing import List
from app.schemas.models import BusinessSummary, StoryboardRequest, SlidePlan
from app.services.exceptions import DeckMateException, GroqAPIException, JSONParsingException, ValidationException
from app.services.audience_adapter import get_audience_instructions
from app.services.prompt_builder import build_system_prompt, build_user_prompt
from app.services.groq_client import GroqClientWrapper
from app.services.storyboard_generator import parse_and_validate_storyboard
from app.services.output_validator import validate_presentation_plan

logger = logging.getLogger(__name__)

class PresentationPlannerService:
    """Orchestrates LLM presentation design, audience adaptation copywriting, and slide validation steps."""

    def __init__(self):
        self.groq_client = GroqClientWrapper()

    def generate_presentation_plan(
        self,
        summary: BusinessSummary,
        audience: str,
        objective: str,
        slide_count: int = 5
    ) -> StoryboardRequest:
        """Plans the narrative flow of slides, generating a validated and adapted storyboard plan."""
        logger.info(f"Initiating presentation planning (Audience: {audience}, Target Slides: {slide_count})")
        
        # 1. Resolve target audience profiles
        audience_profile = get_audience_instructions(audience)
        
        # 2. Build system and user prompts
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(
            summary=summary,
            audience_name=audience,
            audience_profile=audience_profile,
            objective=objective,
            slide_count=slide_count
        )
        
        # 3. Call Groq LLM
        try:
            raw_response = self.groq_client.query_llm(system_prompt, user_prompt)
        except GroqAPIException as e:
            logger.error(f"Groq API connection failure in planner: {str(e)}")
            raise
            
        # 4. Parse JSON Response
        try:
            slides = parse_and_validate_storyboard(raw_response)
        except JSONParsingException as e:
            logger.error(f"JSON validation failure in planner: {str(e)}")
            raise

        # 5. Output Validation Pipeline
        try:
            validated_slides = validate_presentation_plan(slides, summary)
        except ValidationException as e:
            logger.error(f"Output verification failed for generated slides: {str(e)}")
            raise

        # 6. Return Structured Storyboard Request
        return StoryboardRequest(
            audience=audience,
            objective=objective,
            slides=validated_slides
        )
