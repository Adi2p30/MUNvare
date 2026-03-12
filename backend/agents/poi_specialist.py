"""
POI Specialist Agent - Expert in crafting strategic Points of Information
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class POISpecialistAgent(BaseAgent):
    """
    Highly specialized agent focused exclusively on generating strategic POI questions.
    Expert in parliamentary procedure, debate tactics, and strategic questioning.
    """

    def __init__(self):
        super().__init__(
            name="POI Strategist",
            role="Elite specialist in Points of Information strategy and parliamentary debate tactics"
        )

    def get_system_prompt(self) -> str:
        return """You are a POI Strategist - the absolute best at crafting Points of Information.

Your expertise includes:
- Parliamentary debate tactics and timing
- Strategic questioning techniques
- Exposing logical fallacies and contradictions
- Building coalition opportunities through questions
- Defensive preparation against POIs
- Using POIs to advance your position

Your POI philosophy:
1. **Strategic Intent**: Every question serves a purpose
2. **Precision**: Questions must be sharp and focused
3. **Tactical Timing**: Know when to strike
4. **Follow-up Ready**: Always have the next question
5. **Diplomatic Yet Powerful**: Professional but devastating

POI Question Categories:
- **Contradiction Exposers**: Highlight inconsistencies
- **Evidence Demanders**: Force them to provide specifics
- **Consequence Highlighters**: Show implications they missed
- **Coalition Builders**: Create openings for cooperation
- **Position Advancers**: Frame questions that help your stance

You create POIs that:
✓ Are impossible to dodge
✓ Expose weaknesses elegantly
✓ Build your credibility
✓ Create strategic opportunities
✓ Sound diplomatic yet powerful
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """Generate strategic POI questions."""
        country = task.get('country', '')
        topic = task.get('topic', '')
        target_country = task.get('target_country', '')

        context_section = ""
        if context:
            context_section = f"\n\nRELEVANT BACKGROUND:\n{context}\n"

        target_text = f" targeting {target_country}" if target_country else " for general use"

        prompt = f"""{context_section}

Generate 10 elite-level POI questions for {country} on {topic}{target_text}.

For each question, provide:

1. **The Question** (concise, under 25 words)
2. **Strategic Purpose** (why ask this)
3. **Expected Response** (how they'll likely answer)
4. **Your Counter** (how to follow up)
5. **Timing** (when in debate to use this)

Categories to cover:

### A. OFFENSIVE QUESTIONS (Attack Weaknesses)
Create 3 questions that:
- Expose contradictions in their position
- Demand specific evidence they can't provide
- Highlight negative consequences they're ignoring

### B. CLARIFICATION REQUESTS (Look Smart)
Create 3 questions that:
- Ask for details to show they're unprepared
- Request explanation of vague statements
- Probe implementation feasibility

### C. BRIDGE-BUILDING QUESTIONS (Coalition)
Create 2 questions that:
- Identify potential common ground
- Create openings for cooperation
- Show flexibility while maintaining position

### D. POSITION-ADVANCING QUESTIONS (Your Goals)
Create 2 questions that:
- Lead them to support your perspective
- Frame the debate in your favor
- Create quotable moments for you

Format each question set clearly with headers and strategic notes.
"""

        poi_questions = self.call_llm(prompt, use_gemini=True)  # POI generation requires strategic thinking

        return {
            'success': True,
            'poi_questions': poi_questions,
            'metadata': {
                'agent': self.name,
                'country': country,
                'topic': topic,
                'target': target_country
            }
        }

    def analyze_defensive_prep(self, country: str, topic: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Prepare defensive strategies against POIs you might receive."""

        context_section = ""
        if context:
            context_section = f"\n\nCONTEXT:\n{context}\n"

        prompt = f"""{context_section}

As the POI Strategist, prepare {country} for POIs they will RECEIVE on {topic}.

Provide:

## 🛡️ ANTICIPATED POIS

### High Probability POIs (You WILL get these)
For each:
1. **The POI**: "[Exact question]"
2. **Why They'll Ask**: [Their strategic intent]
3. **Your Response**: [Strong, brief answer]
4. **Turn It Around**: [How to use this to your advantage]

Generate 5 high-probability POIs.

### Difficult POIs (Tricky Questions)
For each:
1. **The POI**: "[Challenging question]"
2. **Why It's Dangerous**: [What makes this hard]
3. **Best Response**: [How to handle it]
4. **Deflection Tactic**: [If you need to avoid]

Generate 3 difficult POIs.

## 💡 DEFENSIVE STRATEGIES

### General Tactics
- How to buy time when needed
- Phrases to deflect gracefully
- When to decline a POI
- How to turn defense into offense

### Preparation Checklist
- Facts to memorize
- Statistics to have ready
- Quotes to reference
- Examples to cite

Make this immediately actionable for committee."""

        defensive_prep = self.call_llm(prompt, use_gemini=True)  # Defensive prep requires strategic thinking

        return {
            'success': True,
            'defensive_prep': defensive_prep,
            'metadata': {
                'agent': self.name,
                'prep_type': 'defensive',
                'country': country
            }
        }
