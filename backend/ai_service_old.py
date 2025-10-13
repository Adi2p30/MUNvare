import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
import json

load_dotenv()

# Try to import AI providers
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIService:
    """AI service for chat, speech generation, and note analysis"""

    def __init__(self, vectordb):
        self.vectordb = vectordb

        # Initialize AI clients
        self.anthropic_client = None
        self.openai_client = None

        if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
            self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def get_available_provider(self):
        """Get the first available AI provider"""
        if self.anthropic_client:
            return 'anthropic'
        elif self.openai_client:
            return 'openai'
        return None

    def chat_with_context(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """Chat with RAG context from MUN book"""

        # Get relevant context from vector database
        context = self.vectordb.get_context_for_query(user_message, max_context_length=3000)

        system_prompt = f"""You are an expert MUN (Model United Nations) advisor and assistant.
You help delegates with research, speech writing, strategy, and understanding MUN procedures.

You have access to a comprehensive MUN guidebook. Use this context to answer questions accurately:

CONTEXT FROM MUN BOOK:
{context}

When answering:
- Be specific and practical
- Reference MUN procedures and best practices
- Provide examples when relevant
- If writing speeches, follow MUN speech format
- Consider the delegate's country perspective when relevant
- Be encouraging and supportive

If the user asks for speech generation, follow the MUN speech structure from the book."""

        provider = self.get_available_provider()

        if provider == 'anthropic':
            return self._chat_anthropic(system_prompt, user_message, conversation_history)
        elif provider == 'openai':
            return self._chat_openai(system_prompt, user_message, conversation_history)
        else:
            return "AI service not configured. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env file."

    def _chat_anthropic(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> str:
        """Chat using Anthropic Claude"""
        messages = []

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def _chat_openai(self, system_prompt: str, user_message: str, history: List[Dict] = None) -> str:
        """Chat using OpenAI"""
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_speech(self, country: str, topic: str, committee: str = "",
                        stance: str = "", speech_type: str = "GSL") -> str:
        """Generate MUN speech based on parameters"""

        prompt = f"""Generate a {speech_type} speech for MUN.

Country: {country}
Committee: {committee if committee else 'General'}
Topic: {topic}
Stance: {stance if stance else 'To be determined based on country policy'}

Requirements:
1. Follow proper MUN speech format
2. Stay in character for the country
3. Use diplomatic language
4. Include 3-4 key points
5. Reference facts and statistics where relevant
6. Keep it between 60-90 seconds when spoken
7. Consider the country's foreign policy and past positions

Generate a professional, impactful MUN speech."""

        return self.chat_with_context(prompt)

    def analyze_notes(self, notes: str) -> Dict:
        """Analyze notes and generate insights"""

        prompt = f"""Analyze these MUN research notes and provide:

1. Key Points Summary (3-5 bullet points)
2. Suggested Arguments (specific points the delegate can make)
3. Potential Counter-Arguments (what others might say)
4. Research Gaps (what information is missing)
5. Strategy Recommendations

NOTES:
{notes}

Provide a structured analysis."""

        provider = self.get_available_provider()

        if provider == 'anthropic':
            analysis = self._chat_anthropic(
                "You are an expert MUN advisor analyzing delegate research notes.",
                prompt,
                None
            )
        elif provider == 'openai':
            analysis = self._chat_openai(
                "You are an expert MUN advisor analyzing delegate research notes.",
                prompt,
                None
            )
        else:
            return {"error": "AI service not configured"}

        return {
            "analysis": analysis,
            "word_count": len(notes.split()),
            "estimated_reading_time": f"{len(notes.split()) // 200} min"
        }

    def generate_poi_questions(self, country: str, topic: str, target_country: str = "") -> List[str]:
        """Generate Point of Information questions"""

        target_text = f" about {target_country}" if target_country else ""

        prompt = f"""Generate 5 strong Point of Information (POI) questions for a MUN delegate.

My Country: {country}
Topic: {topic}
Target{target_text}

Requirements:
- Questions should be challenging but respectful
- Based on facts and real situations
- Should expose weaknesses in positions or require detailed answers
- Follow MUN POI etiquette
- Each question should be concise (1-2 sentences)

Generate 5 POI questions."""

        response = self.chat_with_context(prompt)

        # Try to extract questions (simple parsing)
        questions = []
        for line in response.split('\n'):
            line = line.strip()
            if line and ('?' in line or line[0].isdigit()):
                # Clean up numbering
                clean_line = line.lstrip('0123456789.-) ')
                if clean_line:
                    questions.append(clean_line)

        return questions[:5] if questions else [response]

    def research_foreign_policy(self, country: str, topic: str) -> str:
        """Research foreign policy for a country on a topic"""

        prompt = f"""Research and explain {country}'s foreign policy position on: {topic}

Include:
1. Current Official Position
2. Historical Stance
3. Key Actions Taken
4. International Alliances Relevant to This Issue
5. Domestic Factors Influencing Policy
6. Likely Position in MUN Debate

Provide factual, well-researched information suitable for MUN preparation."""

        return self.chat_with_context(prompt)

    def suggest_moderated_caucus_topics(self, main_agenda: str, committee: str = "") -> List[str]:
        """Suggest moderated caucus topics for an agenda"""

        prompt = f"""For a MUN committee discussing: {main_agenda}
Committee: {committee if committee else 'General'}

Suggest 8 specific moderated caucus topics that:
1. Are subtopics of the main agenda
2. Encourage debate and discussion
3. Are actionable and solution-oriented
4. Fit within the committee's mandate
5. Are timely and relevant

List only the topics, one per line."""

        response = self.chat_with_context(prompt)

        # Parse topics
        topics = []
        for line in response.split('\n'):
            line = line.strip()
            if line and len(line) > 10:
                # Clean up numbering and bullet points
                clean_line = line.lstrip('0123456789.-•* ')
                if clean_line and len(clean_line) > 10:
                    topics.append(clean_line)

        return topics[:8] if topics else [response]


if __name__ == "__main__":
    # Test the AI service
    from vectordb import initialize_vector_db

    print("Initializing vector database...")
    vectordb = initialize_vector_db()

    print("\nInitializing AI service...")
    ai_service = AIService(vectordb)

    print(f"\nAvailable provider: {ai_service.get_available_provider()}")

    # Test chat
    print("\n=== Testing Chat ===")
    response = ai_service.chat_with_context("What are the key rules of procedure in MUN?")
    print(response[:300] + "...")

    # Test speech generation
    print("\n=== Testing Speech Generation ===")
    speech = ai_service.generate_speech(
        country="India",
        topic="Climate Change and Sustainable Development",
        committee="UNEP"
    )
    print(speech[:300] + "...")
