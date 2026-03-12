"""
Analysis Agent - Specialized in analyzing and synthesizing information
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class AnalysisAgent(BaseAgent):
    """
    Expert agent for analyzing research, identifying patterns, and synthesizing insights.
    Specializes in strategic thinking and connecting different pieces of information.
    """

    def __init__(self):
        super().__init__(
            name="Strategic Analyst",
            role="Expert strategic analyst specializing in synthesizing information and identifying actionable insights"
        )

    def get_system_prompt(self) -> str:
        return """You are a Strategic Analyst with expertise in:
- Synthesizing complex information
- Identifying key patterns and trends
- Strategic thinking and planning
- Risk assessment
- Opportunity identification

Your capabilities:
- Extract key insights from large amounts of information
- Identify strategic opportunities and threats
- Connect disparate pieces of information
- Provide actionable recommendations
- Think critically about implications

Guidelines:
1. Focus on what matters most
2. Identify strategic implications
3. Highlight opportunities and risks
4. Provide clear, actionable insights
5. Think beyond surface-level analysis
6. Consider multiple perspectives
7. Prioritize information effectively
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze research and provide strategic insights.

        Args:
            task: Dictionary containing:
                - research_output: Raw research from Research Agent
                - analysis_type: Type of analysis needed
                - country: Country context
                - topic: Topic context
            context: Additional context

        Returns:
            Dictionary with analysis results
        """
        research_output = task.get('research_output', '')
        analysis_type = task.get('analysis_type', 'general')
        country = task.get('country', '')
        topic = task.get('topic', '')

        prompt = self._build_analysis_prompt(research_output, analysis_type, country, topic)
        # Use Gemini for analysis (core task - requires strategic thinking)
        analysis_output = self.call_llm(prompt, use_gemini=True)

        return {
            'success': True,
            'type': analysis_type,
            'analysis': analysis_output,
            'metadata': {
                'agent': self.name,
                'analysis_type': analysis_type
            }
        }

    def _build_analysis_prompt(self, research: str, analysis_type: str, country: str, topic: str) -> str:
        """Build appropriate analysis prompt."""

        if analysis_type == 'strategic':
            return f"""Analyze this research output and extract strategic insights:

RESEARCH OUTPUT:
{research}

Provide a strategic analysis that includes:

1. **Key Takeaways** (3-5 most important points)
   - What are the critical insights?
   - What should the delegate prioritize?

2. **Strategic Opportunities**
   - Where can {country} gain advantage?
   - Coalition-building opportunities
   - Leadership moments

3. **Potential Challenges**
   - What obstacles might arise?
   - Difficult questions to prepare for
   - Weak points in the position

4. **Action Items**
   - Specific next steps
   - Who to talk to first
   - What to prepare

5. **Talking Points**
   - 5-7 key phrases to use
   - Strong arguments to emphasize
   - Responses to common objections

Keep the analysis sharp, actionable, and focused on winning strategies."""

        elif analysis_type == 'debate_prep':
            return f"""Analyze this research to prepare for debate:

RESEARCH OUTPUT:
{research}

Create a debate preparation guide:

1. **Strongest Arguments**
   - {country}'s most powerful points
   - Evidence and examples to cite
   - Moral/legal foundations

2. **Anticipated Counterarguments**
   - What opponents will say
   - How to respond effectively
   - Pre-prepared rebuttals

3. **Question Preparation**
   - Likely POIs you'll receive
   - Your best answers
   - How to deflect difficult questions

4. **Offensive Questions**
   - POIs to ask opponents
   - Questions that expose weaknesses
   - Strategic inquiry opportunities

5. **Debate Flow Strategy**
   - Opening statement approach
   - Building your argument
   - Closing strong

Make this practical and immediately usable in committee."""

        elif analysis_type == 'crisis_response':
            return f"""Analyze this crisis situation and develop response strategy:

CRISIS SCENARIO:
{research}

Develop a comprehensive crisis response:

1. **Immediate Assessment**
   - What just happened?
   - How does it affect {country}?
   - Urgency level

2. **{country}'s Interests**
   - How are your interests affected?
   - Threats and opportunities
   - What's at stake?

3. **Response Options**
   - Immediate actions to consider
   - Diplomatic responses
   - Public statements

4. **Strategic Considerations**
   - Short-term vs long-term impacts
   - Regional implications
   - International reactions

5. **Recommended Action**
   - Specific response strategy
   - Key messages to deliver
   - Allies to consult

6. **Risk Mitigation**
   - Potential negative consequences
   - How to minimize backlash
   - Contingency plans

Provide a clear, actionable crisis response plan."""

        else:  # general analysis
            return f"""Analyze this research output and provide insights:

RESEARCH OUTPUT:
{research}

Provide:

1. **Summary** - Key points in 3-4 sentences

2. **Critical Insights**
   - Most important findings
   - Strategic implications
   - Notable patterns or connections

3. **Recommendations**
   - Actionable next steps
   - Strategic advice
   - Things to watch for

4. **Additional Considerations**
   - Factors not fully addressed
   - Questions needing more research
   - Alternative perspectives

Be concise but comprehensive."""

    def analyze_resolution(self, resolution_text: str, country: str, topic: str) -> Dict[str, Any]:
        """Analyze a draft resolution for strategic considerations."""

        prompt = f"""Analyze this draft resolution from {country}'s perspective:

RESOLUTION:
{resolution_text}

TOPIC: {topic}

Provide analysis:

1. **Overall Assessment**
   - Does this serve {country}'s interests?
   - Strengths and weaknesses
   - Likelihood of passage

2. **Clause-by-Clause Analysis**
   - Which clauses support your position?
   - Which are problematic?
   - Ambiguous language to clarify

3. **Amendment Opportunities**
   - Suggested friendly amendments
   - Clauses to strengthen
   - Language to add

4. **Negotiation Strategy**
   - What to push for
   - What to compromise on
   - Deal-breakers

5. **Voting Decision**
   - Should {country} support this?
   - Conditions for support
   - Alternative approaches

Provide practical guidance for resolution negotiations."""

        analysis_output = self.call_llm(prompt, use_gemini=True)  # Additional analysis methods use Gemini

        return {
            'success': True,
            'type': 'resolution_analysis',
            'analysis': analysis_output,
            'metadata': {
                'agent': self.name,
                'analysis_type': 'resolution'
            }
        }
