"""
GPT-4 analysis for call summarization and action item extraction.

Analyzes call transcripts to generate summaries, extract action items,
and assign sentiment and urgency scores.
"""

import logging
import json
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI

from config import get_settings
from database import SentimentType

logger = logging.getLogger(__name__)


# Response models
class ActionItem(BaseModel):
    """Action item extracted from call."""
    description: str = Field(..., description="Clear description of the action item")
    assigned_to: Optional[str] = Field(None, description="Person responsible (if mentioned)")
    priority: int = Field(default=3, ge=1, le=5, description="Priority level 1-5")
    due_date: Optional[str] = Field(None, description="Due date if mentioned")


class CallAnalysis(BaseModel):
    """Complete call analysis result."""
    summary: str = Field(..., description="2-3 sentence summary of the call")
    key_topics: List[str] = Field(default_factory=list, description="Main topics discussed")
    action_items: List[ActionItem] = Field(default_factory=list, description="Extracted action items")
    sentiment: SentimentType = Field(..., description="Overall sentiment")
    urgency_score: int = Field(..., ge=1, le=5, description="Urgency level 1-5")
    customer_satisfaction: Optional[int] = Field(None, ge=1, le=5, description="Customer satisfaction 1-5")
    next_steps: Optional[str] = Field(None, description="Recommended next steps")


class AIAnalysisService:
    """Service for AI-powered call analysis."""

    def __init__(self):
        """Initialize AI analysis service."""
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)

    def _build_system_prompt(self) -> str:
        """Build system prompt for call analysis."""
        return """You are an expert call analyst for a business. Your job is to analyze call transcripts and extract key information.

For each call transcript, you must provide:

1. **Summary**: A concise 2-3 sentence summary capturing the main purpose and outcome of the call.

2. **Key Topics**: List of 3-5 main topics or themes discussed in the call.

3. **Action Items**: Specific tasks or commitments made during the call. Each action item should include:
   - Clear description of what needs to be done
   - Who is responsible (if mentioned)
   - Priority level (1=low, 5=critical)
   - Due date if mentioned

4. **Sentiment**: Overall emotional tone of the call:
   - positive: Friendly, satisfied, enthusiastic, collaborative
   - neutral: Professional, matter-of-fact, transactional
   - negative: Frustrated, angry, dissatisfied, confrontational

5. **Urgency Score** (1-5):
   - 1: Routine follow-up, no time pressure
   - 2: Standard inquiry, normal timeline
   - 3: Important but not urgent
   - 4: Time-sensitive, needs attention soon
   - 5: Critical, requires immediate action

6. **Customer Satisfaction** (1-5, if applicable):
   - How satisfied the customer seems with the interaction

7. **Next Steps**: Recommended actions or follow-up activities.

Focus on actionable insights and be objective in your analysis."""

    def _build_user_prompt(self, transcript: str, metadata: Optional[dict] = None) -> str:
        """
        Build user prompt with transcript and optional metadata.

        Args:
            transcript: Call transcript text
            metadata: Optional call metadata (caller, duration, etc.)

        Returns:
            Formatted prompt string
        """
        prompt_parts = []

        if metadata:
            prompt_parts.append("**Call Metadata:**")
            if metadata.get("caller_name"):
                prompt_parts.append(f"Caller: {metadata['caller_name']}")
            if metadata.get("called_name"):
                prompt_parts.append(f"Agent: {metadata['called_name']}")
            if metadata.get("duration_seconds"):
                duration_min = metadata["duration_seconds"] / 60
                prompt_parts.append(f"Duration: {duration_min:.1f} minutes")
            if metadata.get("direction"):
                prompt_parts.append(f"Direction: {metadata['direction']}")
            prompt_parts.append("")

        prompt_parts.append("**Call Transcript:**")
        prompt_parts.append(transcript)
        prompt_parts.append("")
        prompt_parts.append("Please analyze this call and provide structured output.")

        return "\n".join(prompt_parts)

    async def analyze_call(
        self,
        transcript: str,
        metadata: Optional[dict] = None
    ) -> CallAnalysis:
        """
        Analyze call transcript using GPT-4.

        Args:
            transcript: Full call transcript
            metadata: Optional call metadata for context

        Returns:
            CallAnalysis object with all extracted information

        Raises:
            Exception: If analysis fails
        """
        logger.info(f"Analyzing call transcript ({len(transcript)} chars)")

        try:
            # Build prompts
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(transcript, metadata)

            # Define the function schema for structured output
            function_schema = {
                "name": "analyze_call",
                "description": "Analyze a call transcript and extract structured information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string",
                            "description": "2-3 sentence summary of the call"
                        },
                        "key_topics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Main topics discussed (3-5 items)"
                        },
                        "action_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "assigned_to": {"type": "string"},
                                    "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                                    "due_date": {"type": "string"}
                                },
                                "required": ["description", "priority"]
                            },
                            "description": "Action items from the call"
                        },
                        "sentiment": {
                            "type": "string",
                            "enum": ["positive", "neutral", "negative"],
                            "description": "Overall sentiment of the call"
                        },
                        "urgency_score": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Urgency level (1=low, 5=critical)"
                        },
                        "customer_satisfaction": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 5,
                            "description": "Customer satisfaction score"
                        },
                        "next_steps": {
                            "type": "string",
                            "description": "Recommended next steps"
                        }
                    },
                    "required": ["summary", "key_topics", "sentiment", "urgency_score"]
                }
            }

            # Call GPT-4 with function calling
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                functions=[function_schema],
                function_call={"name": "analyze_call"},
                temperature=0.3,  # Lower temperature for more consistent analysis
            )

            # Extract function call result
            function_call = response.choices[0].message.function_call
            if not function_call:
                raise ValueError("No function call in response")

            # Parse JSON response
            analysis_data = json.loads(function_call.arguments)

            # Validate and parse with Pydantic
            analysis = CallAnalysis(**analysis_data)

            logger.info(
                f"Analysis complete: sentiment={analysis.sentiment}, "
                f"urgency={analysis.urgency_score}, "
                f"action_items={len(analysis.action_items)}"
            )

            return analysis

        except Exception as e:
            logger.error(f"Call analysis failed: {e}", exc_info=True)
            raise

    async def generate_summary_only(
        self,
        transcript: str,
        max_sentences: int = 3
    ) -> str:
        """
        Generate a quick summary without full analysis.

        Useful for preview or when full analysis isn't needed.

        Args:
            transcript: Call transcript
            max_sentences: Maximum sentences in summary

        Returns:
            Summary text
        """
        logger.info(f"Generating summary for {len(transcript)} chars")

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a call analyst. Summarize the following call transcript in {max_sentences} sentences or less."
                    },
                    {
                        "role": "user",
                        "content": transcript
                    }
                ],
                temperature=0.3,
                max_tokens=200,
            )

            summary = response.choices[0].message.content.strip()
            logger.info(f"Summary generated: {len(summary)} chars")

            return summary

        except Exception as e:
            logger.error(f"Summary generation failed: {e}", exc_info=True)
            raise

    async def extract_action_items_only(self, transcript: str) -> List[ActionItem]:
        """
        Extract only action items from transcript.

        Args:
            transcript: Call transcript

        Returns:
            List of ActionItem objects
        """
        logger.info(f"Extracting action items from {len(transcript)} chars")

        try:
            system_prompt = """Extract all action items and commitments from this call transcript.
            Focus on specific tasks that need to be done, who should do them, and any deadlines mentioned."""

            function_schema = {
                "name": "extract_action_items",
                "description": "Extract action items from a call",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action_items": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "description": {"type": "string"},
                                    "assigned_to": {"type": "string"},
                                    "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                                    "due_date": {"type": "string"}
                                },
                                "required": ["description", "priority"]
                            }
                        }
                    },
                    "required": ["action_items"]
                }
            }

            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": transcript}
                ],
                functions=[function_schema],
                function_call={"name": "extract_action_items"},
                temperature=0.3,
            )

            function_call = response.choices[0].message.function_call
            if not function_call:
                return []

            data = json.loads(function_call.arguments)
            action_items = [ActionItem(**item) for item in data.get("action_items", [])]

            logger.info(f"Extracted {len(action_items)} action items")
            return action_items

        except Exception as e:
            logger.error(f"Action item extraction failed: {e}", exc_info=True)
            raise


# Global service instance
_analysis_service: Optional[AIAnalysisService] = None


def get_analysis_service() -> AIAnalysisService:
    """Get global AI analysis service instance."""
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = AIAnalysisService()
    return _analysis_service


if __name__ == "__main__":
    # Test analysis
    import asyncio
    from config import configure_logging

    configure_logging()

    async def test():
        service = get_analysis_service()

        # Sample transcript
        transcript = """
        Agent: Thank you for calling TechSupport, this is Sarah. How can I help you today?
        Customer: Hi Sarah, I'm having trouble with my account login. I keep getting an error.
        Agent: I'm sorry to hear that. Let me look into this for you. Can I have your account email?
        Customer: Sure, it's john.doe@example.com
        Agent: Thank you. I can see the issue - your account was temporarily locked due to multiple failed login attempts. I'll unlock it now.
        Customer: Oh, I see. I forgot I changed my password last week.
        Agent: No problem! I've unlocked your account. You should be able to log in now. I'd also recommend enabling two-factor authentication for extra security.
        Customer: That's a great idea. Can you help me set that up?
        Agent: Absolutely! I'll send you an email with instructions. It should arrive within 5 minutes.
        Customer: Perfect, thank you so much for your help!
        Agent: You're welcome! Is there anything else I can help you with today?
        Customer: No, that's all. Thanks again!
        Agent: Have a great day!
        """

        result = await service.analyze_call(
            transcript,
            metadata={
                "caller_name": "John Doe",
                "called_name": "Sarah",
                "duration_seconds": 180,
                "direction": "inbound"
            }
        )

        print("\n=== Call Analysis ===")
        print(f"Summary: {result.summary}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Urgency: {result.urgency_score}/5")
        print(f"Topics: {', '.join(result.key_topics)}")
        print(f"\nAction Items ({len(result.action_items)}):")
        for item in result.action_items:
            print(f"  - {item.description} (Priority: {item.priority})")

    asyncio.run(test())
