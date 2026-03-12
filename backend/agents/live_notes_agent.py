"""
Live Notes Agent - Generates structured notes from important transcript chunks
Uses Gemma (Ollama) for fast processing
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime
from .base_agent import BaseAgent


class LiveNotesAgent(BaseAgent):
    """
    Transforms important transcript chunks into structured, timestamped notes.
    Optimized for speed using local Gemma model.
    """

    def __init__(self):
        super().__init__(
            name="Live Notes Agent",
            role="Fast generation of structured notes from live transcripts"
        )

    def get_system_prompt(self) -> str:
        """System prompt optimized for fast note generation."""
        return """You are a lightning-fast note-taking agent for MUN sessions.

Your job: Transform transcript chunks into clear, actionable notes in <300ms.

NOTE STRUCTURE:
- Title: Short, descriptive (5-8 words max)
- Content: Key information, context, implications (2-3 sentences)
- Tags: Relevant keywords for filtering (3-5 tags)

CATEGORIES & TAG EXAMPLES:
- key_decision → ["voting", "motion", "passed/failed"]
- country_position → ["country_name", "policy", "stance"]
- alliance_signal → ["coalition", "bloc", "alliance"]
- strategic_move → ["POI", "amendment", "strategy"]

OUTPUT FORMAT (JSON only):
{
  "title": "<concise title>",
  "content": "<2-3 sentence summary with context>",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "<category from input>"
}

Be CONCISE and ACTION-ORIENTED. Focus on what matters."""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a structured note from an important transcript chunk.

        Args:
            task: Dictionary with 'transcript_chunk', 'speaker', 'timestamp', 'category', 'summary'
            context: Optional session context (delegate info, topic, etc.)

        Returns:
            {
                'title': str,
                'content': str,
                'tags': [str],
                'category': str,
                'timestamp': str (ISO format),
                'speaker': str,
                'agent': str
            }
        """
        transcript_chunk = task.get('transcript_chunk', '')
        speaker = task.get('speaker', 'Unknown')
        timestamp = task.get('timestamp', datetime.now().isoformat())
        category = task.get('category', 'general')
        importance_summary = task.get('summary', '')

        # Build prompt
        prompt = f"""GENERATE NOTE FROM TRANSCRIPT:

Category: {category}
Speaker: {speaker}
Importance Summary: {importance_summary}

Transcript:
"{transcript_chunk}"
"""

        if context:
            prompt = f"SESSION CONTEXT: {context}\n\n{prompt}"

        prompt += "\n\nGENERATE STRUCTURED NOTE (JSON only):"

        # Call Gemma for fast note generation (use_gemini=False)
        try:
            response = self.call_llm(prompt, use_gemini=False)

            # Parse JSON response
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()

            result = json.loads(response)

            # Add metadata
            result['timestamp'] = timestamp
            result['speaker'] = speaker
            result['agent'] = self.name

            # Ensure category matches input
            if 'category' not in result:
                result['category'] = category

            # Validate tags
            if 'tags' not in result or not isinstance(result['tags'], list):
                result['tags'] = [category]

            return result

        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            print(f"⚠ LiveNotesAgent: JSON parse error: {e}")
            return {
                'title': f"{category.replace('_', ' ').title()} - {speaker}",
                'content': importance_summary or transcript_chunk[:200],
                'tags': [category, speaker],
                'category': category,
                'timestamp': timestamp,
                'speaker': speaker,
                'agent': self.name
            }
        except Exception as e:
            print(f"⚠ LiveNotesAgent error: {e}")
            return {
                'title': f"Note from {speaker}",
                'content': transcript_chunk[:200],
                'tags': [category],
                'category': category,
                'timestamp': timestamp,
                'speaker': speaker,
                'agent': self.name
            }

    def generate_summary_note(self, notes: list) -> Dict[str, Any]:
        """
        Generate a summary note from multiple individual notes.

        Args:
            notes: List of note dictionaries

        Returns:
            Summary note dictionary
        """
        if not notes:
            return None

        # Build prompt with all notes
        notes_text = "\n\n".join([
            f"[{note.get('timestamp', '')}] {note.get('title', '')}: {note.get('content', '')}"
            for note in notes
        ])

        prompt = f"""SUMMARIZE THESE NOTES:

{notes_text}

Create a concise summary note that captures the key themes and decisions.

OUTPUT FORMAT (JSON only):
{{
  "title": "<summary title>",
  "content": "<3-4 sentence comprehensive summary>",
  "tags": ["summary", "tag2", "tag3"]
}}
"""

        try:
            response = self.call_llm(prompt, use_gemini=False)

            # Parse JSON response
            response = response.strip()
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()

            result = json.loads(response)
            result['timestamp'] = datetime.now().isoformat()
            result['category'] = 'summary'
            result['agent'] = self.name

            return result

        except Exception as e:
            print(f"⚠ LiveNotesAgent summary error: {e}")
            return {
                'title': 'Session Summary',
                'content': f"Summary of {len(notes)} notes from this session.",
                'tags': ['summary'],
                'category': 'summary',
                'timestamp': datetime.now().isoformat(),
                'agent': self.name
            }
