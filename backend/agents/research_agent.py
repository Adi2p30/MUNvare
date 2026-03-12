"""
Research Agent - Specialized in conducting research and gathering information
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """
    Expert agent for conducting thorough research on MUN topics.
    Specializes in foreign policy, country positions, and geopolitical analysis.
    """

    def __init__(self):
        super().__init__(
            name="Research Specialist",
            role="Expert MUN researcher specializing in international relations, foreign policy, and geopolitical analysis"
        )

    def get_system_prompt(self) -> str:
        return """You are an expert MUN Research Specialist with deep knowledge of:
- International relations and diplomacy
- Foreign policy analysis
- Geopolitical dynamics
- UN procedures and history
- Country-specific positions on global issues

Your expertise:
- Analyzing complex geopolitical situations
- Understanding historical context
- Identifying key stakeholders and their interests
- Providing accurate, sourced information
- Explaining policy positions clearly

Guidelines for your research:
1. Be thorough and accurate
2. Provide specific details and examples
3. Consider historical context
4. Identify key players and their motivations
5. Highlight important dates, events, and documents
6. Use diplomatic and professional language
7. Structure information logically
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Conduct research based on the task parameters.

        Args:
            task: Dictionary containing:
                - type: Type of research (foreign_policy, poi, country_profile, etc.)
                - country: Country name
                - topic: Topic of research
                - target_country: (Optional) Target country for POI
                - additional_context: (Optional) Extra context
            context: Vector database context or previous research

        Returns:
            Dictionary with research findings
        """
        research_type = task.get('type', 'general')
        country = task.get('country', '')
        topic = task.get('topic', '')
        target_country = task.get('target_country', '')

        # Build context-aware prompt
        prompt = self._build_research_prompt(research_type, country, topic, target_country, context)

        # Conduct research using Gemini (core task - requires depth and accuracy)
        research_output = self.call_llm(prompt, use_gemini=True)

        return {
            'success': True,
            'type': research_type,
            'country': country,
            'topic': topic,
            'raw_research': research_output,
            'metadata': {
                'agent': self.name,
                'research_type': research_type
            }
        }

    def _build_research_prompt(self, research_type: str, country: str, topic: str,
                               target_country: str, context: Optional[str]) -> str:
        """Build appropriate research prompt based on type."""

        context_section = ""
        if context:
            context_section = f"\n\nRELEVANT BACKGROUND INFORMATION:\n{context}\n"

        if research_type == 'foreign_policy':
            return f"""{context_section}

Conduct a comprehensive foreign policy analysis for {country} on the topic of {topic}.

Your analysis should include:

1. **Current Policy Stance**
   - What is {country}'s official position on {topic}?
   - Key policy statements and actions
   - Recent developments and changes

2. **Historical Context**
   - How has {country}'s position evolved?
   - Important historical events that shaped this stance
   - Past actions and commitments

3. **Domestic Factors**
   - Internal political considerations
   - Economic interests
   - Public opinion and pressure groups
   - Key government officials and their views

4. **International Relations**
   - Relationships with other major players
   - Alliance considerations
   - Regional dynamics
   - UN voting patterns on related issues

5. **Strategic Interests**
   - Why does {country} hold this position?
   - Economic, security, and political motivations
   - Long-term goals and objectives

6. **Key Documents & Statements**
   - Important speeches, resolutions, or treaties
   - Official government publications
   - UN statements

Provide detailed, accurate information that would help a MUN delegate represent {country} effectively."""

        elif research_type == 'poi':
            target_text = f" directed at {target_country}" if target_country else ""
            return f"""{context_section}

Generate strategic Points of Information (POIs) for a {country} delegate on the topic of {topic}{target_text}.

These POIs should:

1. **Challenge Assumptions**
   - Question underlying premises
   - Highlight contradictions
   - Test logical consistency

2. **Probe for Details**
   - Ask for specific examples
   - Request clarification on vague statements
   - Seek concrete policy proposals

3. **Expose Weaknesses**
   - Identify policy gaps
   - Highlight inconsistencies
   - Point out unintended consequences

4. **Advance Your Position**
   - Frame questions that support {country}'s stance
   - Create openings for your arguments
   - Build coalition opportunities

5. **Show Expertise**
   - Reference specific events, documents, or data
   - Demonstrate deep knowledge
   - Use diplomatic language

Generate 8-10 sharp, strategic POI questions that a {country} delegate could use effectively in committee."""

        elif research_type == 'country_profile':
            return f"""{context_section}

Create a comprehensive country profile for {country} focusing on {topic if topic else 'general MUN preparation'}.

Include:

1. **Basic Information**
   - Official name and government structure
   - Head of state and key ministers
   - Political system and stability
   - Economic overview (GDP, major industries, trade)

2. **Foreign Policy Overview**
   - General foreign policy principles
   - Regional leadership role
   - Key alliances and partnerships
   - Historical foreign policy patterns

3. **Position on {topic or 'Major Global Issues'}**
   - Detailed stance and rationale
   - Past actions and votes
   - Key speeches and statements

4. **Regional Context**
   - Regional dynamics and conflicts
   - Neighboring countries and relations
   - Regional organizations membership

5. **International Standing**
   - UN membership and contributions
   - Security Council history
   - Treaty commitments
   - International reputation

6. **Delegate Strategy Tips**
   - Speaking style to adopt
   - Natural allies and opponents
   - Key phrases and talking points
   - Things to emphasize or avoid

Provide information that enables complete, authentic representation of {country}."""

        elif research_type == 'allies':
            return f"""{context_section}

Identify potential allies for {country} on the topic of {topic}.

Provide:

1. **Primary Allies** (3-5 countries)
   - Countries with nearly identical positions
   - Reasons for alignment
   - Strength of relationship
   - Past cooperation examples

2. **Secondary Allies** (5-7 countries)
   - Countries with similar but not identical stances
   - Areas of agreement and disagreement
   - Potential for coalition building
   - Common interests

3. **Strategic Partners** (3-5 countries)
   - Countries that might be convinced to join your bloc
   - Their concerns and priorities
   - Arguments that might persuade them
   - What you can offer in return

4. **Lobbying Strategy**
   - Who to approach first
   - Key talking points for each group
   - Potential coalition structure
   - Leadership opportunities

5. **Bloc Formation Tips**
   - Suggested bloc name and focus
   - Draft resolution framework
   - Working paper strategy
   - Negotiation tactics

Provide actionable intelligence for effective lobbying and coalition building."""

        elif research_type == 'opposition':
            return f"""{context_section}

Analyze potential opposition to {country}'s position on {topic}.

Provide:

1. **Primary Opponents** (3-5 countries)
   - Countries with directly opposing positions
   - Reasons for opposition
   - Their key arguments
   - Past conflicts or disagreements

2. **Their Arguments**
   - Main talking points they'll use
   - Evidence they'll cite
   - Moral/legal arguments
   - Economic/security concerns

3. **Counter-Arguments**
   - How to refute their claims
   - Evidence supporting your position
   - Weaknesses in their arguments
   - Effective responses to POIs

4. **Debate Preparation**
   - Anticipated questions
   - Strong rebuttals
   - Facts and figures to cite
   - Diplomatic responses

5. **Neutralization Strategy**
   - How to minimize their impact
   - Potential compromises
   - Ways to divide their bloc
   - Building bridges where possible

Equip the delegate to effectively counter opposition and defend {country}'s position."""

        else:  # general research
            return f"""{context_section}

Conduct comprehensive research on: {topic} for {country}.

Provide thorough, well-structured information that would help a MUN delegate understand and effectively represent {country}'s position on this topic.

Include relevant historical context, current policy, key stakeholders, and strategic considerations."""

    def research_modcaucus_topics(self, agenda: str, committee: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Generate strategic moderated caucus topic suggestions."""

        context_section = ""
        if context:
            context_section = f"\n\nCOMMITTEE CONTEXT:\n{context}\n"

        prompt = f"""{context_section}

Generate strategic Moderated Caucus topic suggestions for a {committee} committee discussing: {agenda}

Suggest 8-10 specific, actionable moderated caucus topics that:

1. **Advance Debate**
   - Break down the broader agenda into focused subtopics
   - Move discussion from general to specific
   - Create opportunities for meaningful dialogue

2. **Build Consensus**
   - Topics that can unite different blocs
   - Areas where compromise is possible
   - Solutions-oriented discussions

3. **Show Leadership**
   - Demonstrate strategic thinking
   - Address controversial issues
   - Propose innovative approaches

4. **Generate Action**
   - Topics that lead to concrete clauses
   - Practical implementation discussions
   - Resource allocation debates

For each topic, provide:
- The specific topic title (concise, clear)
- Why this topic is strategic
- Expected outcomes
- Which blocs would support it

Format as a numbered list with brief explanations."""

        research_output = self.call_llm(prompt, use_gemini=True)  # Additional research methods use Gemini

        return {
            'success': True,
            'type': 'modcaucus',
            'agenda': agenda,
            'committee': committee,
            'raw_research': research_output,
            'metadata': {
                'agent': self.name,
                'research_type': 'modcaucus'
            }
        }
