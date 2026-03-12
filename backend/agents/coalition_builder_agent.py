"""
Coalition Builder Agent - Specialized in alliance formation and lobbying strategy
"""
from typing import Dict, Any, Optional, List
from .base_agent import BaseAgent


class CoalitionBuilderAgent(BaseAgent):
    """
    Expert agent for building coalitions, identifying allies, and developing lobbying strategies.
    Specializes in diplomatic relationship analysis and bloc formation.
    """

    def __init__(self):
        super().__init__(
            name="Coalition Strategist",
            role="Expert in alliance formation, lobbying strategy, and diplomatic coalition building"
        )

    def get_system_prompt(self) -> str:
        return """You are a Coalition Strategist with expertise in:
- Alliance formation and bloc building
- Lobbying tactics and persuasion
- Diplomatic relationship analysis
- Negotiation and compromise strategies
- Vote counting and coalition mathematics
- Cross-bloc bridge building

Your strategic approach:
- Identify natural allies based on shared interests
- Analyze potential coalition partners
- Develop targeted lobbying approaches
- Create win-win negotiation frameworks
- Build sustainable voting blocs
- Manage coalition dynamics

Guidelines:
1. Think strategically about long-term alliances
2. Identify specific shared interests
3. Develop personalized lobbying approaches
4. Consider regional and ideological factors
5. Plan for coalition expansion
6. Anticipate opposition strategies
7. Build bridges across divides
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Develop coalition building strategy.

        Args:
            task: Dictionary containing:
                - country: Base country
                - topic: Issue being discussed
                - research_context: Background research
                - goals: Specific objectives
            context: Additional context

        Returns:
            Dictionary with coalition strategy
        """
        country = task.get('country', '')
        topic = task.get('topic', '')
        research_context = task.get('research_context', '')
        goals = task.get('goals', 'Build support for position')

        context_section = ""
        if context or research_context:
            context_section = f"\n\nBACKGROUND RESEARCH:\n{context or research_context}\n"

        prompt = f"""{context_section}

Develop a comprehensive coalition building strategy for {country} on {topic}.

GOALS: {goals}

Create a detailed lobbying and coalition strategy:

## 🎯 COALITION ARCHITECTURE

### Tier 1: Core Allies (Must-Have Partners)
For each (3-5 countries):
- **Country**: [name]
- **Why They'll Join**: [specific shared interests]
- **What They Bring**: [influence, votes, expertise]
- **What They Need**: [concessions or support]
- **Lobbying Priority**: High
- **Approach Strategy**: [specific talking points]

### Tier 2: Strong Supporters (Likely Allies)
For each (5-7 countries):
- **Country**: [name]
- **Alignment**: [areas of agreement]
- **Concerns**: [potential objections]
- **Persuasion Strategy**: [how to convince]
- **Value Proposition**: [what they gain]

### Tier 3: Swing Votes (Persuadable Countries)
For each (5-8 countries):
- **Country**: [name]
- **Current Position**: [likely neutral/uncertain]
- **Key Interests**: [what motivates them]
- **Winning Arguments**: [what will convince them]
- **Potential Obstacles**: [challenges to overcome]
- **Negotiation Leverage**: [what you can offer]

## 📊 BLOC FORMATION STRATEGY

### Phase 1: Foundation (First 3-5 Countries)
- Who to approach first: [order matters!]
- Initial pitch: [opening message]
- Early wins: [build momentum]

### Phase 2: Expansion (Next 8-12 Countries)
- Regional outreach: [geographic diversity]
- Ideological bridges: [cross-bloc appeal]
- Leadership positioning: [who leads the bloc]

### Phase 3: Consolidation (Final Push)
- Fence-sitters: [late deciders]
- Opposition defectors: [who might switch]
- Coalition discipline: [keeping allies aligned]

## 💬 LOBBYING TOOLKIT

### Opening Lines (by Country Type)
**For Regional Allies:**
"[Specific opening tailored to regional ties]"

**For Economic Partners:**
"[Economic interest-based opening]"

**For Ideological Aligned:**
"[Values-based opening]"

**For Neutral Countries:**
"[Balanced, win-win opening]"

### Key Arguments (Prioritized)
1. **[Argument 1]**
   - Target audience: [who this convinces]
   - Supporting evidence: [facts to cite]
   - Emotional appeal: [why it resonates]

2. **[Argument 2-5]**
   [Continue pattern...]

### Concessions You Can Offer
- **Major Concessions** (use sparingly):
  - [What you can trade for crucial support]

- **Minor Concessions** (negotiate freely):
  - [What you can offer multiple countries]

- **Symbolic Gestures** (cost-free):
  - [What shows goodwill without sacrifice]

## 🤝 NEGOTIATION FRAMEWORKS

### Deal Structures
**Package Deal 1: [Name]**
- Partners: [countries involved]
- They get: [their benefits]
- You get: [your benefits]
- Terms: [specific agreement]

**Package Deal 2-3:**
[Additional frameworks...]

### Compromise Positions
- **Red Lines** (non-negotiable): [list]
- **Yellow Lines** (prefer not to cross): [list]
- **Green Zones** (flexible): [list]

## 📈 COALITION MANAGEMENT

### Communication Strategy
- Primary contact: [who speaks for bloc]
- Meeting schedule: [when to coordinate]
- Information sharing: [what to communicate]

### Conflict Resolution
- Anticipated disputes: [potential problems]
- Mediation approach: [how to resolve]
- Backup plans: [if allies defect]

### Vote Counting
- Confirmed votes: [X countries]
- Likely votes: [Y countries]
- Needed votes: [Z countries]
- Path to victory: [scenario analysis]

## ⚠️ RISK MITIGATION

### Opposition Counter-Strategy
- How they'll try to split your bloc: [tactics]
- Your counter-moves: [responses]
- Vulnerable allies to protect: [who needs support]

### Contingency Plans
**If Plan A fails:**
- Plan B: [alternative coalition]
- Required pivots: [strategy changes]

**If key ally defects:**
- Replacement options: [backup partners]
- Damage control: [how to recover]

## 🎯 EXECUTION TIMELINE

**Day 1-2: Foundation Building**
- [Specific actions and targets]

**Day 3-4: Expansion**
- [Specific actions and targets]

**Day 5+: Consolidation**
- [Specific actions and targets]

## 📋 LOBBYING CHECKLIST

Pre-Approach:
- [ ] Research target country's position
- [ ] Identify decision-makers
- [ ] Prepare customized pitch
- [ ] Anticipate objections

During Approach:
- [ ] Establish common ground
- [ ] Present value proposition
- [ ] Address concerns
- [ ] Secure commitment or next steps

Follow-Up:
- [ ] Deliver on promises
- [ ] Maintain communication
- [ ] Coordinate on resolutions
- [ ] Build long-term relationship

Provide actionable, specific strategies with country names and concrete approaches."""

        coalition_strategy = self.call_llm(prompt, use_gemini=True)  # Coalition building requires strategic analysis

        return {
            'success': True,
            'coalition_strategy': coalition_strategy,
            'metadata': {
                'agent': self.name,
                'country': country,
                'topic': topic
            }
        }

    def analyze_relationship(self, country1: str, country2: str, topic: str) -> Dict[str, Any]:
        """Analyze bilateral relationship for coalition potential."""

        prompt = f"""Analyze the relationship between {country1} and {country2} for coalition building on {topic}.

Provide:

## 🤝 RELATIONSHIP ASSESSMENT
- **Overall Relationship**: [Strong ally / Friendly / Neutral / Tense / Adversarial]
- **On This Topic**: [Aligned / Mostly aligned / Different / Opposed]

## 🔗 SHARED INTERESTS
1. [Interest 1]
2. [Interest 2]
3. [Interest 3]

## ⚡ POINTS OF TENSION
1. [Tension 1]
2. [Tension 2]

## 💡 COALITION POTENTIAL
- **Likelihood of Alliance**: [Percentage]
- **What {country1} Needs to Offer**: [Specific concessions]
- **What {country2} Brings to Table**: [Value]
- **Obstacles to Overcome**: [Challenges]

## 🎯 RECOMMENDED APPROACH
[Specific strategy for bringing {country2} into coalition]

Be specific and practical."""

        analysis = self.call_llm(prompt, use_gemini=True)  # Alliance analysis requires strategic thinking

        return {
            'success': True,
            'relationship_analysis': analysis,
            'countries': [country1, country2]
        }
