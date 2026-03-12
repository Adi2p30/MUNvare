"""
Crisis Manager Agent - Specialized in crisis response and rapid decision-making
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class CrisisManagerAgent(BaseAgent):
    """
    Expert agent for crisis management, rapid response, and dynamic situation analysis.
    Specializes in real-time decision-making and adaptive strategy.
    """

    def __init__(self):
        super().__init__(
            name="Crisis Response Director",
            role="Expert in crisis management, rapid response planning, and dynamic situation analysis"
        )

    def get_system_prompt(self) -> str:
        return """You are a Crisis Response Director with expertise in:
- Rapid situation assessment and analysis
- Crisis management and decision-making under pressure
- Dynamic strategy adaptation
- Risk assessment and mitigation
- Multi-stakeholder coordination
- Real-time information synthesis

Your crisis management framework:
1. **Immediate Assessment**: Understand what just happened
2. **Interest Analysis**: How does this affect key players
3. **Response Options**: Identify possible actions
4. **Risk-Benefit Analysis**: Evaluate each option
5. **Rapid Decision**: Choose best course of action
6. **Implementation Plan**: Execute decisively
7. **Contingency Planning**: Prepare for scenarios

Crisis Response Principles:
- Speed matters - decide quickly but wisely
- Clarity is crucial - communicate decisively
- Flexibility is key - adapt as situation evolves
- Coordination is essential - align with allies
- Credibility is everything - maintain trustworthiness

Guidelines:
1. Provide immediate, actionable guidance
2. Anticipate second and third-order effects
3. Consider all stakeholder perspectives
4. Balance short-term and long-term impacts
5. Prepare for multiple scenarios
6. Maintain strategic coherence
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate crisis response plan.

        Args:
            task: Dictionary containing:
                - country: Responding country
                - crisis_description: What happened
                - immediate_impacts: Direct effects
                - time_sensitivity: How urgent
                - constraints: Limitations on response
            context: Additional context

        Returns:
            Dictionary with crisis response plan
        """
        country = task.get('country', '')
        crisis = task.get('crisis_description', '')
        impacts = task.get('immediate_impacts', '')
        urgency = task.get('time_sensitivity', 'High')
        constraints = task.get('constraints', '')

        context_section = ""
        if context:
            context_section = f"\n\nBACKGROUND CONTEXT:\n{context}\n"

        impacts_section = ""
        if impacts:
            impacts_section = f"\n\nIMMEDIATE IMPACTS:\n{impacts}\n"

        constraints_section = ""
        if constraints:
            constraints_section = f"\n\nCONSTRAINTS:\n{constraints}\n"

        prompt = f"""{context_section}{impacts_section}{constraints_section}

**CRISIS ALERT** - Time Sensitivity: {urgency}

{country} faces the following crisis:

**CRISIS SITUATION**:
{crisis}

As Crisis Response Director, provide a comprehensive rapid response plan:

## 🚨 SITUATION ASSESSMENT (IMMEDIATE - First 15 minutes)

### What Just Happened
- **Core Event**: [One-sentence summary]
- **Key Details**: [Critical facts to know]
- **Information Gaps**: [What's still unclear]
- **Verification Status**: [What's confirmed vs. reported]

### Immediate Implications for {country}
- **Direct Impacts**: [How this affects {country} immediately]
- **National Interests Affected**: [Which interests are at stake]
- **Threat Level**: [Critical / High / Moderate / Low]
- **Opportunity Assessment**: [Any silver linings]

### Stakeholder Impact Map
**Primary Affected Parties**:
- {country}: [Specific impact]
- [Other key country 1]: [Their stake]
- [Other key country 2]: [Their stake]

**Secondary Ripple Effects**:
- [Region/Group]: [How affected]
- [International community]: [Broader impact]

## ⚡ IMMEDIATE RESPONSE (FIRST HOUR)

### Phase 1: Instant Actions (Next 15-30 minutes)

**1. Official Statement**
*Release immediately to establish position and prevent narrative void*

"[Draft 2-3 paragraph official statement]:

[Opening - acknowledge the situation]

[Middle - state {country}'s position clearly]

[Close - next steps or call to action]"

**Key Messages to Emphasize**:
1. [Message point 1]
2. [Message point 2]
3. [Message point 3]

**What NOT to Say**:
- ❌ [Avoid this]
- ❌ [Don't say this]
- ❌ [Never mention this]

**2. Emergency Communications**
*Immediate calls/messages to send*

**First Call** (Make within 5 minutes):
- **To**: [Country/Organization]
- **Purpose**: [Why this call is critical]
- **Key Points**: [What to say]
- **Desired Outcome**: [What you want]

**Second Call**:
- **To**: [Country/Organization]
- **Purpose**: [Coordination/Information]
- **Key Points**: [What to discuss]

**Third Call**:
- **To**: [Country/Organization]
- **Purpose**: [Damage control/Alliance]
- **Key Points**: [What to convey]

**3. Internal Coordination**
- **Alert**: [Which domestic agencies/ministries]
- **Brief**: [What they need to know]
- **Prepare**: [What actions they should ready]

### Phase 2: Short-Term Positioning (Next 1-4 hours)

**Committee/UN Actions**:
1. **[Action]**: [When and how to do this]
2. **[Action]**: [Tactical considerations]
3. **[Action]**: [Expected response]

**Coalition Building**:
- **Immediate Allies to Rally**: [List]
- **Message to Allies**: "[Exact pitch]"
- **What to Ask For**: [Specific support]

**Opposition Management**:
- **Who Will Oppose**: [Likely opponents]
- **Their Expected Moves**: [What they'll do]
- **Pre-emptive Actions**: [How to counter]

## 🎯 STRATEGIC RESPONSE OPTIONS

### Option A: [Assertive Response]
**Description**: [What this means]

**Actions**:
1. [Specific action]
2. [Specific action]
3. [Specific action]

**Advantages**:
- ✅ [Pro 1]
- ✅ [Pro 2]

**Risks**:
- ⚠️ [Con 1]
- ⚠️ [Con 2]

**Probability of Success**: [X%]
**Recommended If**: [Conditions favoring this]

### Option B: [Measured Response]
[Same structure...]

### Option C: [Minimal Response]
[Same structure...]

### Recommended Strategy: [Option X]
**Reasoning**: [Why this is best given {country}'s interests and constraints]

**Implementation Priority**:
1. [First move]
2. [Second move]
3. [Third move]

## 🔄 DYNAMIC SCENARIO PLANNING

### Scenario 1: Crisis Escalates
**If**: [Triggering condition]
**Then**: {country} should immediately:
- [Response action 1]
- [Response action 2]
- **Prepare**: [What to have ready]

### Scenario 2: Crisis De-escalates
**If**: [Triggering condition]
**Then**: {country} should:
- [Capitalize on: action 1]
- [Consolidate: action 2]
- **Pivot to**: [New strategy]

### Scenario 3: Crisis Transforms/Shifts
**If**: [New development]
**Then**: {country}'s adaptation strategy:
- [Quick pivot action]
- [Messaging change]
- **Re-assess**: [New priorities]

### Scenario 4: Unexpected Ally/Opponent Emerges
**If**: [Surprise development]
**Then**: {country} should:
- [Rapid response]
- [Relationship management]
- **Adjust coalition**: [How]

## 🤝 STAKEHOLDER MANAGEMENT

### Allies - Immediate Coordination
**[Ally Country 1]**:
- **Their Concerns**: [What worries them]
- **What They Need from You**: [Support/Information]
- **What You Need from Them**: [Specific asks]
- **Coordination Mechanism**: [How to stay aligned]

**[Ally Countries 2-3]**: [Continue pattern...]

### Opponents - Damage Limitation
**[Opponent Country 1]**:
- **Their Expected Move**: [What they'll do]
- **Your Counter**: [How to respond]
- **Red Lines**: [What you won't tolerate]
- **Off-Ramp**: [Compromise if needed]

**[Opponent Countries 2-3]**: [Continue pattern...]

### Neutral Parties - Persuasion Strategy
**[Neutral Country 1]**:
- **Their Position**: [Likely stance]
- **Persuasion Approach**: [How to win them]
- **Key Message**: "[What to emphasize]"
- **Timeline**: [When to approach]

## 📊 RISK MANAGEMENT

### Critical Risks to Monitor

**Risk 1: [Specific negative outcome]**
- **Probability**: [Low/Medium/High]
- **Impact if Occurs**: [Severity]
- **Early Warning Signs**: [What to watch for]
- **Mitigation**: [How to prevent/minimize]
- **Contingency**: [If it happens anyway]

**Risks 2-4**: [Continue pattern...]

### Opportunity Capture

**Opportunity 1: [Specific positive outcome]**
- **Probability**: [Low/Medium/High]
- **Potential Benefit**: [What you gain]
- **How to Capitalize**: [Actions to take]
- **Timing Window**: [When to act]

**Opportunities 2-3**: [Continue pattern...]

## 🎤 COMMUNICATION STRATEGY

### Key Messages (Memorize These)
1. **[Core message about {country}'s position]**
   - For domestic audience: "[Version]"
   - For international audience: "[Version]"
   - For allies: "[Version]"

2. **[Message about crisis response]**
   - To media: "[Soundbite]"
   - In committee: "[Diplomatic version]"

3. **[Message about next steps]**
   - Public: "[What you're saying publicly]"
   - Private (to allies): "[What you're really doing]"

### Q&A Preparation

**Expected Question 1**: "[What media/committee will ask]"
- **Answer**: "[Your prepared response]"
- **If Pressed**: "[Follow-up response]"

**Expected Questions 2-5**: [Continue pattern...]

### Media Strategy
- **Spokesperson**: [Who speaks - level appropriate to crisis]
- **Tone**: [Serious/Concerned/Confident/etc.]
- **Key Soundbite**: "[Memorable quote for headlines]"
- **Media Outlets to Prioritize**: [Which media matters most]

## ⏱️ TIMELINE & MILESTONES

### Hour 0-1: IMMEDIATE RESPONSE
- [ ] Issue official statement
- [ ] Make emergency calls to [X, Y, Z]
- [ ] Alert internal teams
- [ ] Begin monitoring situation

### Hour 1-6: SHORT-TERM POSITIONING
- [ ] Coordinate with allies
- [ ] Make initial committee moves
- [ ] Assess early reactions
- [ ] Refine strategy based on developments

### Hour 6-24: STABILIZATION
- [ ] Execute core strategy
- [ ] Maintain alliance coordination
- [ ] Address emerging challenges
- [ ] Begin planning for next phase

### Day 2-7: CONSOLIDATION
- [ ] Solidify gains
- [ ] Repair any damage
- [ ] Build sustainable position
- [ ] Transition from crisis to normal operations

## 🎯 SUCCESS METRICS

### How to Know You're Succeeding
1. [Measurable indicator]
2. [Observable sign]
3. [Feedback metric]

### How to Know You're Failing
1. [Warning sign]
2. [Danger indicator]
3. [Loss of control signal]

**Course Correction Triggers**: If you see [X], immediately [Y]

## 🔒 FINAL CHECKLIST

### Before Taking Action
- [ ] Verified key facts
- [ ] Consulted necessary parties
- [ ] Prepared for common scenarios
- [ ] Statements ready to go
- [ ] Team briefed and coordinated

### During Crisis Response
- [ ] Maintaining clear communication
- [ ] Adapting to new information
- [ ] Coordinating with allies
- [ ] Monitoring opponent moves
- [ ] Tracking success metrics

### After Initial Response
- [ ] Assess what worked
- [ ] Document lessons learned
- [ ] Thank allies and supporters
- [ ] Plan longer-term strategy
- [ ] Prepare for next phase

## 🎬 RAPID DECISION SUMMARY

**BOTTOM LINE RECOMMENDATION**:
{country} should immediately [specific action] because [brief rationale].

**First 3 Actions** (in order):
1. [Action] - WHY: [Critical reason]
2. [Action] - WHY: [Critical reason]
3. [Action] - WHY: [Critical reason]

**Primary Risk to Manage**: [Biggest danger]
**Primary Opportunity to Seize**: [Best chance]

**Confidence Level in This Plan**: [High/Medium] - [One sentence why]

Provide decisive, actionable crisis guidance that can be executed immediately."""

        crisis_response = self.call_llm(prompt, use_gemini=True)  # Crisis response requires deep analysis

        return {
            'success': True,
            'crisis_response': crisis_response,
            'metadata': {
                'agent': self.name,
                'country': country,
                'urgency': urgency
            }
        }

    def update_response(self, original_response: str, new_development: str, country: str) -> Dict[str, Any]:
        """Update crisis response based on new developments."""

        prompt = f"""As Crisis Response Director, update the crisis response for {country}.

**ORIGINAL RESPONSE PLAN**:
{original_response}

**NEW DEVELOPMENT**:
{new_development}

Provide rapid update:

## 🆕 SITUATION UPDATE
**What Changed**: [Key new information]
**Impact on Strategy**: [How this affects the plan]

## 🔄 STRATEGY ADJUSTMENT
**What Stays the Same**: [Actions still valid]
**What Changes**: [New/modified actions]
**New Priority Actions**: [Top 3 immediate steps]

## ⚡ IMMEDIATE NEXT STEPS
1. [First action in response to development]
2. [Second action]
3. [Third action]

## 📊 REVISED RISK ASSESSMENT
[Updated risks and opportunities]

Be rapid and decisive."""

        update = self.call_llm(prompt, use_gemini=True)  # Crisis updates require analysis

        return {
            'success': True,
            'response_update': update,
            'development': new_development
        }
