"""
Prophet AI Service - OpenRouter Integration

Simplified AI agent that:
- Generates prediction markets
- Provides commentary on trades/resolutions
- Resolves disputed markets
- Places its own bets
"""
from openai import OpenAI
from typing import Dict, List, Optional
import json
import re

from app.config import settings

# Initialize OpenRouter client (uses OpenAI-compatible API)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openrouter_api_key,
)

def extract_json(response: str) -> str:
    """
    Extract JSON from AI response, handling markdown code blocks and extra text.

    Args:
        response: Raw AI response that may contain JSON

    Returns:
        Cleaned JSON string ready for parsing
    """
    # Remove markdown code blocks (```json ... ``` or ``` ... ```)
    response = re.sub(r'^```(?:json)?\s*\n', '', response, flags=re.MULTILINE)
    response = re.sub(r'\n```\s*$', '', response, flags=re.MULTILINE)

    # Try to find JSON array or object
    # Look for [...] or {...}
    json_array_match = re.search(r'\[.*\]', response, re.DOTALL)
    json_object_match = re.search(r'\{.*\}', response, re.DOTALL)

    if json_array_match:
        return json_array_match.group(0)
    elif json_object_match:
        return json_object_match.group(0)
    else:
        # Return original if no JSON pattern found
        return response.strip()

def call_prophet(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 500
) -> str:
    """
    Call Prophet AI via OpenRouter.

    Args:
        system_prompt: System instructions for Prophet
        user_prompt: The actual prompt/question
        temperature: Randomness (0-1)
        max_tokens: Max response length

    Returns:
        Prophet's response text
    """
    try:
        response = client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"Prophet AI call failed: {e}")
        return f"[Prophet is temporarily unavailable: {str(e)}]"

# ============================================================================
# MARKET GENERATION AGENT
# ============================================================================

def generate_markets(room_name: str, member_names: List[str], recent_markets: List[str]) -> List[Dict]:
    """
    Generate new prediction markets for a room.

    Args:
        room_name: Name of the room
        member_names: List of member display names
        recent_markets: List of recent market titles (to avoid duplicates)

    Returns:
        List of market dictionaries with title, description, category, initial_odds
    """
    system_prompt = f"""You are Prophet, the AI market maker for a social prediction market called "{room_name}".

Your job is to generate 2-3 interesting, fun prediction markets for this friend group.

Guidelines:
- Markets must be resolvable (clear yes/no outcome) within 1-7 days
- Mix categories: personal, sports, pop culture, academic, weather, etc.
- Be playful and provocative but never mean-spirited
- Keep titles under 80 characters
- Avoid duplicating recent markets

Room members: {', '.join(member_names)}
Recent markets: {', '.join(recent_markets) if recent_markets else 'None yet'}

Respond with ONLY a valid JSON array of markets:
[
  {{
    "title": "Will it snow in NYC this weekend?",
    "description": "Resolves YES if any measurable snow falls",
    "category": "weather",
    "initial_odds_yes": 0.3
  }}
]"""

    user_prompt = "Generate 2-3 new prediction markets for this room."

    response = call_prophet(system_prompt, user_prompt, temperature=0.8, max_tokens=800)

    # Parse JSON response
    try:
        cleaned_response = extract_json(response)
        markets = json.loads(cleaned_response)
        if isinstance(markets, list):
            return markets
        else:
            return []
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback: create a simple market
        print(f"Failed to parse market generation response: {e}")
        print(f"Raw response: {response[:200]}...")
        return [{
            "title": "Will someone create a market today?",
            "description": "A meta-market for when Prophet can't think straight",
            "category": "meta",
            "initial_odds_yes": 0.5
        }]

# ============================================================================
# COMMENTARY AGENT
# ============================================================================

def generate_trade_commentary(
    market_title: str,
    user_name: str,
    side: str,
    amount: float,
    new_odds_yes: float
) -> str:
    """
    Generate commentary after a trade.

    Args:
        market_title: Market title
        user_name: User who placed the trade
        side: 'yes' or 'no'
        amount: Amount bet
        new_odds_yes: New odds after trade

    Returns:
        Prophet's commentary (1-2 sentences)
    """
    system_prompt = """You are Prophet, the snarky AI personality for a prediction market.

Generate witty, playful commentary about trades. Keep it to 1-2 sentences max.
Be slightly roast-y but never mean. Think sports commentator meets group chat instigator."""

    user_prompt = f"""
Market: "{market_title}"
{user_name} just bet {side.upper()} with {amount} coins
New odds: {new_odds_yes:.0%} YES / {1-new_odds_yes:.0%} NO

Generate short commentary:"""

    return call_prophet(system_prompt, user_prompt, temperature=0.9, max_tokens=150)

def generate_resolution_commentary(
    market_title: str,
    result: str,
    vote_summary: Dict,
    winners: int,
    losers: int
) -> str:
    """
    Generate commentary after market resolution.

    Args:
        market_title: Market title
        result: 'yes' or 'no'
        vote_summary: Dict with yes_votes, no_votes
        winners: Number of winners
        losers: Number of losers

    Returns:
        Prophet's resolution commentary
    """
    system_prompt = """You are Prophet, analyzing a resolved prediction market.

Generate entertaining post-resolution commentary. Celebrate winners, roast losers playfully.
1-2 sentences max."""

    user_prompt = f"""
Market: "{market_title}"
Resolved: {result.upper()}
Votes: {vote_summary.get('yes_votes', 0)} YES, {vote_summary.get('no_votes', 0)} NO
{winners} winners, {losers} losers

Commentary:"""

    return call_prophet(system_prompt, user_prompt, temperature=0.9, max_tokens=150)

# ============================================================================
# RESOLUTION DISPUTE AGENT
# ============================================================================

def resolve_dispute(
    market_title: str,
    description: str,
    yes_votes: int,
    no_votes: int
) -> Dict:
    """
    Resolve a disputed market (no supermajority).

    Args:
        market_title: Market title
        description: Market description
        yes_votes: Number of YES votes
        no_votes: Number of NO votes

    Returns:
        Dict with 'ruling' ('yes' or 'no'), 'reasoning', 'confidence'
    """
    system_prompt = """You are Prophet, the impartial judge for disputed prediction markets.

A market failed to reach a 3/4 supermajority. You must make a binding ruling.

Rules:
- Your ruling must be either YES or NO
- Provide 2-4 sentences of reasoning
- Be fair but also entertaining
- Consider the exact wording of the market title

Respond with ONLY valid JSON:
{
  "ruling": "yes",
  "confidence": 0.8,
  "reasoning": "Clear explanation here"
}"""

    user_prompt = f"""
Market: "{market_title}"
Description: {description or 'None provided'}
Vote distribution: {yes_votes} YES, {no_votes} NO (no supermajority)

Make your ruling:"""

    response = call_prophet(system_prompt, user_prompt, temperature=0.3, max_tokens=300)

    # Parse JSON response
    try:
        cleaned_response = extract_json(response)
        ruling = json.loads(cleaned_response)
        # Validate
        if ruling.get('ruling') in ['yes', 'no']:
            return ruling
        else:
            # Fallback to majority vote
            return {
                "ruling": "yes" if yes_votes > no_votes else "no",
                "confidence": 0.5,
                "reasoning": "Prophet couldn't decide, defaulting to majority vote"
            }
    except (json.JSONDecodeError, ValueError) as e:
        # Fallback to majority vote
        print(f"Failed to parse dispute resolution response: {e}")
        return {
            "ruling": "yes" if yes_votes > no_votes else "no",
            "confidence": 0.5,
            "reasoning": "Prophet's judgment is clouded. Going with the majority."
        }

# ============================================================================
# PROPHET'S BET DECISION
# ============================================================================

def decide_prophet_bet(market_title: str, description: str, initial_odds: float) -> Dict:
    """
    Decide if/how Prophet should bet on a market.

    Args:
        market_title: Market title
        description: Market description
        initial_odds: Current odds

    Returns:
        Dict with 'should_bet', 'side', 'confidence', 'reasoning', 'amount'
    """
    system_prompt = """You are Prophet, deciding whether to bet on a prediction market.

Analyze the market and decide your position. You have 200 virtual coins to bet.

Respond with ONLY valid JSON:
{
  "should_bet": true,
  "side": "yes",
  "confidence": 0.7,
  "reasoning": "Brief explanation",
  "amount": 50
}"""

    user_prompt = f"""
Market: "{market_title}"
Description: {description or 'None'}
Current odds: {initial_odds:.0%} YES

Should you bet?"""

    response = call_prophet(system_prompt, user_prompt, temperature=0.7, max_tokens=200)

    try:
        cleaned_response = extract_json(response)
        decision = json.loads(cleaned_response)
        return decision
    except (json.JSONDecodeError, ValueError) as e:
        # Default: don't bet if parsing fails
        print(f"Failed to parse bet decision response: {e}")
        return {
            "should_bet": False,
            "side": "yes",
            "confidence": 0.5,
            "reasoning": "Feeling indecisive today",
            "amount": 0
        }


# Test function
if __name__ == "__main__":
    print("Testing Prophet AI Service...\n")

    # Test commentary
    commentary = generate_trade_commentary(
        market_title="Will it snow tomorrow?",
        user_name="Alice",
        side="yes",
        amount=50,
        new_odds_yes=0.65
    )
    print(f"Trade Commentary: {commentary}\n")

    print("✅ Prophet AI service functional!")
