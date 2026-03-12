"""
Importance Filter Agent - Fast filtering of transcript chunks for relevance
Uses Gemma (Ollama) for sub-second latency
"""
from typing import Dict, Any, Optional
import json
from .base_agent import BaseAgent


class ImportanceFilterAgent(BaseAgent):
    """
    Filters transcript chunks to identify important content worthy of note-taking.
    Optimized for speed using local Gemma model.
    """

    def __init__(self):
        super().__init__(
            name="Importance Filter Agent",
            role="Fast filtering and importance scoring of live transcripts"
        )

    def get_system_prompt(self) -> str:
        """System prompt optimized for fast, accurate filtering."""
        return """You are a rapid-fire importance filter for MUN (Model United Nations) sessions.

Your job: Analyze transcript chunks in <500ms and score importance (0-10).

IMPORTANT CATEGORIES (score 7-10):
- "key_decision": Voting outcomes, procedural motions, resolutions
- "country_position": Country statements on policy, alliances, opposition
- "alliance_signal": Coalition building, bloc formation, agreement hints
- "strategic_move": POI attacks, amendments, crisis responses

NOT IMPORTANT (score 0-6):
- "procedural": Basic formalities, roll call, time announcements
- "noise": Chitchat, unclear audio, repetition

OUTPUT FORMAT (JSON only):
{
  "importance": <int 0-10>,
  "category": "<category>",
  "summary": "<one sentence summary>",
  "is_important": <bool, true if >=7>
}

Be FAST and DECISIVE. You have 100ms to decide."""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Filter a transcript chunk for importance.

        Args:
            task: Dictionary with 'transcript_chunk', 'speaker', 'timestamp'
            context: Optional session context (delegate info, topic, etc.)

        Returns:
            {
                'importance': int (0-10),
                'category': str,
                'summary': str,
                'is_important': bool,
                'agent': str
            }
        """
        transcript_chunk = task.get('transcript_chunk', '')
        speaker = task.get('speaker', 'Unknown')
        timestamp = task.get('timestamp', '')

        # Build prompt
        prompt = f"""TRANSCRIPT CHUNK:
Speaker: {speaker}
Time: {timestamp}
Text: "{transcript_chunk}"
"""

        if context:
            prompt = f"SESSION CONTEXT: {context}\n\n{prompt}"

        prompt += "\n\nANALYZE NOW (JSON only):"

        # Call Gemma for fast filtering (use_gemini=False)
        try:
            response = self.call_llm(prompt, use_gemini=False)

            # Parse JSON response
            # Try to extract JSON from response
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()

            result = json.loads(response)

            # Ensure all fields are present
            importance = result.get('importance', 0)
            result['is_important'] = importance >= 7
            result['agent'] = self.name

            return result

        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            print(f"⚠ ImportanceFilterAgent: JSON parse error: {e}")
            return {
                'importance': 0,
                'category': 'noise',
                'summary': 'Unable to parse',
                'is_important': False,
                'agent': self.name
            }
        except Exception as e:
            print(f"⚠ ImportanceFilterAgent error: {e}")
            return {
                'importance': 0,
                'category': 'noise',
                'summary': 'Error during filtering',
                'is_important': False,
                'agent': self.name
            }

    def quick_filter(self, transcript_chunk: str) -> bool:
        """
        Ultra-fast boolean filter without detailed analysis.

        Args:
            transcript_chunk: Raw transcript text

        Returns:
            True if potentially important, False otherwise
        """
        # Quick keyword-based pre-filter
        important_keywords = [
            'vote', 'motion', 'resolution', 'amendment',
            'alliance', 'coalition', 'support', 'oppose',
            'position', 'policy', 'stance', 'crisis',
            'POI', 'point of information', 'question'
        ]

        chunk_lower = transcript_chunk.lower()
        return any(keyword in chunk_lower for keyword in important_keywords)
