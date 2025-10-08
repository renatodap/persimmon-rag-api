"""
AI service for summarization using Anthropic Claude.
Generates intelligent summaries with key actions and topics.
"""
from typing import Dict, List

import structlog
from anthropic import Anthropic

from app.config import settings
from app.core.errors import AIServiceError

logger = structlog.get_logger()


class AIService:
    """Anthropic Claude client for AI operations."""

    def __init__(self) -> None:
        """Initialize Anthropic client."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-3-5-sonnet-20241022"

    async def generate_summary(
        self, content: str, content_type: str = "text"
    ) -> Dict[str, any]:
        """
        Generate AI summary with key actions and topics.

        Args:
            content: Content to summarize
            content_type: Type of content (text, url, pdf, image)

        Returns:
            dict: {summary, keyActions, topics, wordCount}

        Raises:
            AIServiceError: If AI service fails
        """
        try:
            system_prompt = """You are an expert at summarizing content. Generate:
1. A concise summary (2-3 sentences)
2. Key actions or takeaways (3-5 bullet points)
3. Main topics/tags (3-5 keywords)

Respond in JSON format:
{
    "summary": "...",
    "keyActions": ["action1", "action2", ...],
    "topics": ["topic1", "topic2", ...]
}"""

            user_prompt = f"""Content Type: {content_type}

Content:
{content[:5000]}

Generate a summary, key actions, and topics."""

            logger.info("ai_summary_request", content_length=len(content), model=self.model)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract JSON response
            result_text = response.content[0].text
            import json

            result = json.loads(result_text)

            # Log cost tracking
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)

            logger.info(
                "ai_summary_success",
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
            )

            # Calculate word count
            word_count = len(content.split())

            return {
                "summary": result.get("summary", ""),
                "keyActions": result.get("keyActions", []),
                "topics": result.get("topics", []),
                "wordCount": word_count,
            }

        except json.JSONDecodeError as e:
            logger.error("ai_summary_json_error", error=str(e))
            raise AIServiceError("Failed to parse AI response")
        except Exception as e:
            logger.error("ai_summary_error", error=str(e))
            raise AIServiceError(f"AI summarization failed: {str(e)}")

    async def generate_title(self, content: str, content_type: str = "text") -> str:
        """
        Generate a title for content.

        Args:
            content: Content to generate title for
            content_type: Type of content

        Returns:
            Generated title

        Raises:
            AIServiceError: If AI service fails
        """
        try:
            prompt = f"""Generate a short, descriptive title (max 10 words) for this {content_type}:

{content[:1000]}

Title:"""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )

            title = response.content[0].text.strip().strip('"')

            logger.info("ai_title_generated", title=title)

            return title

        except Exception as e:
            logger.error("ai_title_error", error=str(e))
            return f"Untitled {content_type.capitalize()}"


# Global AI service instance
ai_service = AIService()
