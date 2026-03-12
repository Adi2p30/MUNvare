"""
Resolution Crafter Agent - Specialized in drafting UN resolutions and clauses
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class ResolutionCrafterAgent(BaseAgent):
    """
    Expert agent for drafting UN resolutions, operative clauses, and amendments.
    Specializes in UN resolution format, diplomatic language, and clause strategy.
    """

    def __init__(self):
        super().__init__(
            name="Resolution Architect",
            role="Expert in UN resolution drafting, clause construction, and diplomatic treaty language"
        )

    def get_system_prompt(self) -> str:
        return """You are a Resolution Architect with mastery in:
- UN resolution format and structure
- Preambulatory and operative clause construction
- Diplomatic and legal language
- Implementation mechanisms
- Amendment strategy
- Consensus building through text

Your expertise includes:
- Proper UN resolution syntax and formatting
- Strategic clause ordering and dependencies
- Balancing specificity with flexibility
- Creating actionable implementation plans
- Drafting amendments that preserve intent
- Building compromise language

Guidelines:
1. Follow strict UN resolution format
2. Use proper preambulatory/operative verbs
3. Create implementable, specific clauses
4. Include verification mechanisms
5. Address funding and resources
6. Consider all stakeholders
7. Build in flexibility for negotiation
8. Use precise diplomatic language
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Draft resolution based on specifications.

        Args:
            task: Dictionary containing:
                - country: Sponsor country
                - topic: Resolution topic
                - committee: Committee name
                - objectives: What resolution should achieve
                - research: Background research
            context: Additional context

        Returns:
            Dictionary with resolution draft
        """
        country = task.get('country', '')
        topic = task.get('topic', '')
        committee = task.get('committee', 'General Assembly')
        objectives = task.get('objectives', '')
        research = task.get('research', '')

        context_section = ""
        if context or research:
            context_section = f"\n\nBACKGROUND RESEARCH:\n{context or research}\n"

        prompt = f"""{context_section}

As a Resolution Architect, draft a comprehensive UN resolution.

**Sponsor**: {country}
**Committee**: {committee}
**Topic**: {topic}
**Objectives**: {objectives}

Create a complete, professionally formatted resolution:

---

## RESOLUTION DRAFT

**Committee**: {committee}
**Topic**: {topic}
**Main Sponsors**: {country}, [suggest 2-3 ideal co-sponsors]
**Co-Sponsors**: [5-8 additional countries that would logically support]

---

### PREAMBULATORY CLAUSES

*[Draft 6-8 preambulatory clauses that establish context and justification]*

**Noting** [observation about current situation],

**Recognizing** [acknowledgment of relevant facts or principles],

**Recalling** [reference to previous resolutions, treaties, or UN documents],

**Acknowledging** [recognition of efforts or challenges],

**Concerned** [expression of worry about negative aspects],

**Emphasizing** [highlighting important principles or needs],

**Convinced** [statement of belief about solutions],

*[Continue with additional preambulatory clauses...]*

---

### OPERATIVE CLAUSES

#### Section 1: Core Actions

**1. Calls upon** all member states to [primary action or commitment];

**2. Urges** [specific actors] to [concrete action with measurable outcomes]:
   **a)** [Sub-clause providing details]
   **b)** [Sub-clause with specific metrics]
   **c)** [Sub-clause with timeline];

**3. Establishes** [new body, mechanism, or framework] with the mandate to:
   **a)** [Specific responsibility]
   **b)** [Specific responsibility]
   **c)** [Specific responsibility];

#### Section 2: Implementation Mechanisms

**4. Requests** the Secretary-General to [specific administrative action]:
   **a)** [Detail on implementation]
   **b)** [Resource allocation]
   **c)** [Reporting timeline];

**5. Decides** to allocate [specific resources or create funding mechanism]:
   **a)** [Funding source]
   **b)** [Amount or percentage]
   **c)** [Distribution mechanism];

**6. Encourages** member states to [voluntary additional actions]:
   **a)** [Specific action]
   **b)** [Specific action]
   **c)** [Specific action];

#### Section 3: Monitoring & Verification

**7. Calls for** the establishment of monitoring mechanisms including:
   **a)** [Reporting requirements for member states]
   **b)** [Independent verification process]
   **c)** [Timeline for reports];

**8. Requests** [specific UN body] to submit annual reports on:
   **a)** [Progress metric 1]
   **b)** [Progress metric 2]
   **c)** [Compliance status];

#### Section 4: Cooperation & Support

**9. Emphasizes** the importance of international cooperation through:
   **a)** [Specific cooperation mechanism]
   **b)** [Technical assistance provision]
   **c)** [Knowledge sharing platform];

**10. Invites** relevant international organizations to:
   **a)** [Specific role]
   **b)** [Specific contribution]
   **c)** [Coordination mechanism];

#### Section 5: Future Action

**11. Decides** to remain actively seized of the matter;

**12. Requests** a comprehensive review of this resolution's implementation after [timeframe].

---

## RESOLUTION STRATEGY GUIDE

### Clause Analysis

#### Must-Have Clauses (Red Lines)
- **Clause [X]**: [Why this is non-negotiable]
- **Clause [Y]**: [Why this is essential]

#### Negotiable Clauses (Trading Chips)
- **Clause [X]**: [What you'd accept in exchange]
- **Clause [Y]**: [Potential compromises]

#### Strategic Clauses (Positioning)
- **Clause [X]**: [How this advances agenda]
- **Clause [Y]**: [How this builds bridges]

### Amendment Preparedness

#### Friendly Amendments to Consider
1. **Potential Amendment**: [Description]
   - **Impact**: [How it changes resolution]
   - **Decision**: Accept / Negotiate / Reject
   - **Reasoning**: [Why]

2. **[Continue for 3-4 likely friendly amendments]**

#### Hostile Amendments to Expect
1. **Expected Amendment**: [Description]
   - **Sponsor**: [Likely source]
   - **Purpose**: [What they're trying to achieve]
   - **Counter-strategy**: [How to respond]
   - **Compromise**: [If you must give ground]

2. **[Continue for 3-4 likely hostile amendments]**

### Co-Sponsorship Strategy

#### Ideal Co-Sponsors (Priority Order)
1. **[Country]**
   - Why: [Strategic value]
   - What they bring: [Credibility, votes, expertise]
   - How to recruit: [Approach]
   - What they'll want: [Likely requests]

2-5. **[Continue for 4-5 ideal co-sponsors]**

#### Geographic Distribution Target
- Africa: [X countries]
- Asia: [X countries]
- Europe: [X countries]
- Americas: [X countries]
- Middle East: [X countries]

**Why this matters**: [Explanation of geographic diversity importance]

#### P5 Considerations
- **USA**: [Likely position - strategy]
- **China**: [Likely position - strategy]
- **Russia**: [Likely position - strategy]
- **UK**: [Likely position - strategy]
- **France**: [Likely position - strategy]

### Passage Strategy

#### Pre-Introduction
- **Timing**: [When to introduce - specific session/day]
- **Co-sponsors recruited**: [Minimum number needed]
- **Opposition briefing**: [Who to talk to first]
- **Bloc alignment**: [Which blocs support]

#### During Debate
- **Speaking order**: [Who speaks when]
- **POI strategy**: [How to handle questions]
- **Amendment handling**: [Process for considering changes]
- **Coalition discipline**: [Keeping supporters aligned]

#### Vote Projection
- **Strong support**: [Estimated countries]
- **Likely support**: [Estimated countries]
- **Possible swing votes**: [Estimated countries]
- **Expected opposition**: [Estimated countries]
- **Pass probability**: [Percentage with reasoning]

### Implementation Realism Check

#### Funding Assessment
- **Estimated cost**: [$X million/billion]
- **Funding source**: [Specific mechanism]
- **Member state contributions**: [How distributed]
- **Budget realism**: [Is this feasible?]

#### Timeline Feasibility
- **Short-term actions** (0-6 months): [List]
- **Medium-term actions** (6-24 months): [List]
- **Long-term actions** (2+ years): [List]
- **Realistic assessment**: [Can this actually be done?]

#### Enforcement Mechanism
- **Compliance incentives**: [What encourages following]
- **Non-compliance response**: [What happens if ignored]
- **Monitoring capacity**: [Who checks progress]
- **Realistic enforcement**: [How effective will this be]

## DIPLOMATIC LANGUAGE GUIDE

### Strength Levels of Operative Verbs
**Strongest** (Use for core requirements):
- Decides, Declares, Requests, Demands

**Moderate** (Use for important but flexible):
- Calls upon, Urges, Recommends, Affirms

**Softest** (Use for voluntary or sensitive):
- Encourages, Invites, Suggests, Notes

### Sub-Clause Structure Best Practices
- Each sub-clause should be specific and actionable
- Use parallel structure (all start similarly)
- Order from most to least important
- Include metrics where possible
- Specify responsible parties

### Compromise Language Techniques
- "While recognizing..." [acknowledge concerns]
- "Taking into account..." [show flexibility]
- "With due regard for..." [respect sensitivities]
- "As appropriate..." [allow discretion]

## RESOLUTION QUALITY CHECKLIST

### Format & Structure
- [ ] Proper preambulatory clause format
- [ ] Correct operative clause numbering
- [ ] Proper use of sub-clauses
- [ ] Appropriate verbs for strength level
- [ ] Consistent punctuation (commas, semicolons)

### Content & Substance
- [ ] Clear objectives
- [ ] Specific, measurable actions
- [ ] Implementation timeline
- [ ] Funding mechanism
- [ ] Monitoring/verification
- [ ] All stakeholders addressed

### Political Viability
- [ ] Likely to pass (majority support)
- [ ] Co-sponsor diversity
- [ ] P5 won't veto (if UNSC)
- [ ] Opposition concerns addressed
- [ ] Coalition stable

### Implementation Realism
- [ ] Actually implementable
- [ ] Funding is realistic
- [ ] Timeline is feasible
- [ ] Enforcement is possible
- [ ] Results are measurable

Draft a professional, strategic, implementable resolution with comprehensive supporting analysis."""

        resolution_draft = self.call_llm(prompt, use_gemini=True)  # Resolution drafting requires careful policy work

        return {
            'success': True,
            'resolution': resolution_draft,
            'metadata': {
                'agent': self.name,
                'country': country,
                'topic': topic,
                'committee': committee
            }
        }

    def draft_amendment(self, original_clause: str, objective: str, country: str) -> Dict[str, Any]:
        """Draft an amendment to a specific clause."""

        prompt = f"""As a Resolution Architect, draft an amendment for {country}.

**Original Clause**:
{original_clause}

**Amendment Objective**: {objective}

Provide:

## PROPOSED AMENDMENT

**Original Text**:
{original_clause}

**Amended Text**:
[Your revised clause maintaining proper format]

## AMENDMENT RATIONALE

**Why This Change**:
- [Substantive reason 1]
- [Substantive reason 2]

**How It Improves the Clause**:
- [Improvement 1]
- [Improvement 2]

## STRATEGIC CONSIDERATIONS

**Who Will Support**: [Likely supporters]
**Who May Oppose**: [Likely opponents]
**Compromise Potential**: [If/how to negotiate]

## PRESENTATION LANGUAGE

**How to Introduce**: "[Diplomatic phrasing for proposing amendment]"
**Key selling points**: [2-3 arguments for acceptance]

Be specific and maintain UN resolution format."""

        amendment = self.call_llm(prompt, use_gemini=True)  # Amendment drafting requires careful policy work

        return {
            'success': True,
            'amendment': amendment
        }

    def analyze_resolution(self, resolution_text: str, country: str, objectives: str) -> Dict[str, Any]:
        """Analyze an existing resolution from country's perspective."""

        prompt = f"""As a Resolution Architect, analyze this resolution from {country}'s perspective.

**{country}'s Objectives**: {objectives}

**RESOLUTION TEXT**:
{resolution_text}

Provide comprehensive analysis:

## ✅ STRENGTHS (From {country}'s perspective)
- [What serves your interests]

## ⚠️ CONCERNS
- [What's problematic]

## 🔧 RECOMMENDED AMENDMENTS

### Priority 1 - Critical Changes
**Clause**: [Which clause]
**Issue**: [What's wrong]
**Proposed Amendment**: [Exact text change]
**Justification**: [Why this helps]

### Priority 2-3 - Important Changes
[Continue pattern...]

### Priority 4-5 - Nice-to-Have Changes
[Continue pattern...]

## 📊 VOTE RECOMMENDATION
- **Position**: Support / Support with amendments / Abstain / Oppose
- **Reasoning**: [Why]
- **Conditions**: [What would change your vote]

## 💡 NEGOTIATION STRATEGY
[How to approach co-sponsors about changes]

Be specific and strategic."""

        analysis = self.call_llm(prompt, use_gemini=True)  # Clause analysis requires strategic thinking

        return {
            'success': True,
            'resolution_analysis': analysis
        }
