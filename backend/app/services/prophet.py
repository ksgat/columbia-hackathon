"""
Prophet AI service - Claude Opus 4.6 via OpenRouter
Provides AI predictions and market analysis
"""
import httpx
from typing import Dict, Optional, List
from app.config import settings
import json


class ProphetService:
    """
    Prophet AI - Uses Claude Opus 4.6 for market predictions.
    """

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "anthropic/claude-opus-4-6"  # Use Opus 4.6

    async def analyze_market(
        self,
        question: str,
        description: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Get Prophet's prediction for a market.

        Args:
            question: The market question
            description: Optional detailed description
            context: Optional additional context (room info, related markets, etc.)

        Returns:
            Dictionary with:
            - probability: Float 0-1
            - reasoning: String explanation
            - confidence: Float 0-1
            - key_factors: List of important factors
        """
        # Build prompt
        prompt = self._build_analysis_prompt(question, description, context)

        # Call Claude
        response = await self._call_claude(prompt)

        # Parse response
        return self._parse_analysis_response(response)

    async def suggest_markets(
        self,
        room_name: str,
        room_description: Optional[str] = None,
        existing_markets: Optional[List[str]] = None,
        count: int = 5
    ) -> List[Dict]:
        """
        Suggest interesting market questions for a room.

        Args:
            room_name: Name of the room
            room_description: Description of the room's theme
            existing_markets: List of existing market questions
            count: Number of suggestions to generate

        Returns:
            List of market suggestions with question, description, type
        """
        prompt = self._build_suggestion_prompt(
            room_name, room_description, existing_markets, count
        )

        response = await self._call_claude(prompt)
        return self._parse_suggestions_response(response)

    async def detect_manipulation(
        self,
        market_question: str,
        trades: List[Dict],
        unusual_activity: Optional[Dict] = None
    ) -> Dict:
        """
        Analyze trading patterns for potential manipulation.

        Args:
            market_question: The market question
            trades: Recent trades
            unusual_activity: Any flagged unusual patterns

        Returns:
            Dictionary with:
            - is_suspicious: Boolean
            - confidence: Float 0-1
            - flags: List of concerns
            - recommendation: String
        """
        prompt = self._build_manipulation_prompt(market_question, trades, unusual_activity)
        response = await self._call_claude(prompt)
        return self._parse_manipulation_response(response)

    async def _call_claude(self, prompt: str, system: Optional[str] = None) -> str:
        """
        Make API call to Claude via OpenRouter.

        Args:
            prompt: The user prompt
            system: Optional system prompt

        Returns:
            Claude's response text
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://prophecy.ai",  # Optional but recommended
            "X-Title": "Prophecy AI",  # Optional but recommended
            "Content-Type": "application/json",
        }

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": self.model,
            "messages": messages,
        }

        if system:
            payload["messages"].insert(0, {"role": "system", "content": system})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        return data["choices"][0]["message"]["content"]

    def _build_analysis_prompt(
        self,
        question: str,
        description: Optional[str],
        context: Optional[Dict]
    ) -> str:
        """Build prompt for market analysis."""
        prompt = f"""Analyze this prediction market and provide your assessment.

Market Question: {question}"""

        if description:
            prompt += f"\n\nDescription: {description}"

        if context:
            prompt += f"\n\nContext: {json.dumps(context, indent=2)}"

        prompt += """

Please provide:
1. Your probability estimate (0.0 to 1.0) that this will resolve YES
2. Your confidence in this estimate (0.0 to 1.0)
3. Key factors influencing your prediction
4. Clear reasoning for your assessment

Respond in JSON format:
{
  "probability": 0.X,
  "confidence": 0.X,
  "key_factors": ["factor 1", "factor 2", ...],
  "reasoning": "Your detailed explanation..."
}"""

        return prompt

    def _build_suggestion_prompt(
        self,
        room_name: str,
        room_description: Optional[str],
        existing_markets: Optional[List[str]],
        count: int
    ) -> str:
        """Build prompt for market suggestions."""
        prompt = f"""Suggest {count} interesting prediction market questions for this room.

Room: {room_name}"""

        if room_description:
            prompt += f"\nDescription: {room_description}"

        if existing_markets:
            prompt += f"\n\nExisting markets:\n" + "\n".join(f"- {m}" for m in existing_markets)

        prompt += f"""

Create {count} engaging, specific, and resolvable prediction market questions.
Each should:
- Be clear and unambiguous
- Have a definite resolution criteria
- Be interesting to the room's audience
- Be different from existing markets

Respond in JSON format:
[
  {{
    "question": "Clear, specific question?",
    "description": "Brief explanation and resolution criteria",
    "type": "binary" or "multiple_choice"
  }},
  ...
]"""

        return prompt

    def _build_manipulation_prompt(
        self,
        market_question: str,
        trades: List[Dict],
        unusual_activity: Optional[Dict]
    ) -> str:
        """Build prompt for manipulation detection."""
        prompt = f"""Analyze trading activity for potential market manipulation.

Market: {market_question}

Recent trades:
{json.dumps(trades, indent=2)}"""

        if unusual_activity:
            prompt += f"\n\nFlagged activity:\n{json.dumps(unusual_activity, indent=2)}"

        prompt += """

Look for:
- Wash trading patterns
- Coordinated manipulation
- Pump and dump schemes
- Unusual volume patterns
- Price manipulation

Respond in JSON format:
{
  "is_suspicious": true/false,
  "confidence": 0.X,
  "flags": ["concern 1", "concern 2", ...],
  "recommendation": "What action to take, if any"
}"""

        return prompt

    def _parse_analysis_response(self, response: str) -> Dict:
        """Parse Claude's analysis response."""
        try:
            # Try to parse as JSON
            data = json.loads(response)
            return {
                "probability": float(data.get("probability", 0.5)),
                "confidence": float(data.get("confidence", 0.5)),
                "key_factors": data.get("key_factors", []),
                "reasoning": data.get("reasoning", response),
            }
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback if not valid JSON
            return {
                "probability": 0.5,
                "confidence": 0.3,
                "key_factors": [],
                "reasoning": response,
            }

    def _parse_suggestions_response(self, response: str) -> List[Dict]:
        """Parse Claude's market suggestions."""
        try:
            data = json.loads(response)
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Fallback
        return []

    def _parse_manipulation_response(self, response: str) -> Dict:
        """Parse Claude's manipulation analysis."""
        try:
            data = json.loads(response)
            return {
                "is_suspicious": bool(data.get("is_suspicious", False)),
                "confidence": float(data.get("confidence", 0.5)),
                "flags": data.get("flags", []),
                "recommendation": data.get("recommendation", "Monitor activity"),
            }
        except (json.JSONDecodeError, KeyError, ValueError):
            return {
                "is_suspicious": False,
                "confidence": 0.0,
                "flags": [],
                "recommendation": "Unable to analyze",
            }


# Singleton instance
_prophet_service: Optional[ProphetService] = None


def get_prophet() -> ProphetService:
    """Get the Prophet service singleton."""
    global _prophet_service
    if _prophet_service is None:
        _prophet_service = ProphetService()
    return _prophet_service
