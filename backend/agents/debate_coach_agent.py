"""
Debate Coach Agent - Specialized in debate preparation and rhetorical strategy
"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent


class DebateCoachAgent(BaseAgent):
    """
    Expert agent for debate preparation, rhetorical strategy, and persuasive communication.
    Acts as a debate coach and speech trainer.
    """

    def __init__(self):
        super().__init__(
            name="Debate Coach",
            role="Expert debate coach specializing in persuasive communication and rhetorical strategy"
        )

    def get_system_prompt(self) -> str:
        return """You are an elite Debate Coach with expertise in:
- Competitive debate tactics and strategy
- Rhetorical devices and persuasion techniques
- Argument construction and refutation
- Public speaking and delivery
- Psychological tactics in debate
- Cross-examination and questioning

Your coaching philosophy:
- Build confidence through preparation
- Develop layered argumentation
- Anticipate and preempt counterarguments
- Use rhetoric strategically
- Master timing and delivery
- Control debate framing and narrative

Techniques you teach:
1. **Argument Structure**: Claim-Evidence-Impact framework
2. **Rhetorical Devices**: Metaphor, repetition, triads, contrast
3. **Defensive Tactics**: Reframing, redirecting, absorbing
4. **Offensive Tactics**: Exposing, pressuring, cornering
5. **Emotional Intelligence**: Reading the room, adapting tone
6. **Strategic Silence**: When not to speak

Guidelines:
- Be practical and immediately applicable
- Provide specific examples and phrases
- Anticipate opponent moves
- Build comprehensive battle plans
- Focus on winning strategies
"""

    def execute(self, task: Dict[str, Any], context: Optional[str] = None) -> Dict[str, Any]:
        """
        Create comprehensive debate preparation plan.

        Args:
            task: Dictionary containing:
                - country: Delegate's country
                - topic: Debate topic
                - opponent_country: Primary opponent (optional)
                - research: Background research
                - goals: Debate objectives
            context: Additional context

        Returns:
            Dictionary with debate preparation plan
        """
        country = task.get('country', '')
        topic = task.get('topic', '')
        opponent = task.get('opponent_country', 'various opponents')
        research = task.get('research', '')
        goals = task.get('goals', 'Defend position and persuade committee')

        context_section = ""
        if context or research:
            context_section = f"\n\nRESEARCH CONTEXT:\n{context or research}\n"

        prompt = f"""{context_section}

As an elite Debate Coach, prepare {country} for debate on {topic} against {opponent}.

DEBATE OBJECTIVES: {goals}

Create a comprehensive debate battle plan:

## 🎯 DEBATE STRATEGY OVERVIEW

### Your Position Summary
[One-sentence framing of {country}'s position that will resonate]

### Debate Objectives
1. **Primary Goal**: [Main thing to achieve]
2. **Secondary Goals**: [Additional objectives]
3. **Success Metrics**: [How to know you're winning]

### Overall Approach
[Aggressive / Defensive / Balanced / Strategic - with reasoning]

## 💪 OFFENSIVE STRATEGY

### Your Strongest Arguments (The "Big Guns")

**Argument 1: [Compelling Title]**
- **Claim**: [Your position in one sentence]
- **Evidence**: [Specific facts, statistics, examples]
- **Impact**: [Why this matters - emotional + logical]
- **Delivery**: "[Exact powerful phrasing to use]"
- **Visual/Metaphor**: [Memorable image or comparison]
- **When to Deploy**: [Optimal timing]

**Arguments 2-5**:
[Continue detailed pattern...]

### Rhetorical Techniques to Use

**Opening Statement Structure**:
1. **Hook** (first 10 seconds): "[Attention-grabbing opening]"
2. **Frame**: "[How to define the debate]"
3. **Preview**: "[Roadmap of your arguments]"
4. **Memorable Line**: "[Quotable statement]"

**Mid-Debate Tactics**:
- **Repetition for Emphasis**: "Key phrase" to repeat 3-4 times
- **Triads**: Three parallel points that resonate
- **Contrast**: "Not [X], but [Y]" formulations
- **Metaphors**: [2-3 powerful metaphors to use]

**Closing Strategy**:
1. **Circle back**: [Reference your opening]
2. **Summarize**: [Hit key points again]
3. **Call to action**: [What you want committee to do]
4. **Memorable final line**: "[Leave them with this]"

## 🛡️ DEFENSIVE STRATEGY

### Anticipated Attacks (And Your Responses)

**Attack 1: "[What they'll say]"**
- **Why it's effective**: [Analysis of the threat]
- **Immediate response**: "[Your quick rebuttal]"
- **Deeper refutation**: [Detailed counter with evidence]
- **Turn it around**: [How to make this help you]
- **If pressed further**: "[Backup response]"
- **Don't say**: [What to avoid]

**Attacks 2-6**:
[Continue pattern for major anticipated attacks...]

### Defensive Principles
1. **Never admit weakness directly** - reframe instead
2. **Absorb and redirect** - acknowledge then pivot
3. **Use jiu-jitsu** - turn their strength into weakness
4. **Buy time when needed**: "That's an important question that requires context..."

### Pre-Prepared Deflections
- When they cite questionable data: "[Response]"
- When they use emotional appeals: "[Response]"
- When they're winning the room: "[Recovery tactic]"
- When caught without answer: "[Graceful dodge]"

## ❓ POI WARFARE

### POIs to Ask Opponents (8-10 Questions)

**Killer Question 1**: "[Exact question]"
- **Purpose**: [What this exposes]
- **Best timing**: [When to ask - be specific]
- **Expected answer**: [What they'll likely say]
- **Your follow-up**: [How to press further]
- **If they dodge**: "[Alternative angle]"
- **Impact**: [How this helps you win]

**Questions 2-8**:
[Continue detailed pattern...]

### POIs You'll Receive (And Responses)

**Expected POI 1**: "[What they'll ask]"
- **Why it's dangerous**: [The trap]
- **Perfect response**: "[Memorize this exact answer]"
- **Backup if pressed**: "[Secondary response]"
- **Counter-question**: "[Turn tables on them]"

**Expected POIs 2-6**:
[Continue pattern...]

### POI Decision Matrix
- **Accept POIs when**: [Situations to take questions]
- **Decline POIs when**: [When to refuse]
- **How to decline gracefully**: "[Polite refusal language]"

## 🎭 PERFORMANCE ELEMENTS

### Vocal Delivery
- **Pace**: [Fast for excitement / Slow for gravitas / Varied for interest]
- **Volume**: [When to be loud, when to be quiet]
- **Tone**: [Serious / Passionate / Reasonable - and when to shift]
- **Pauses**: [Strategic silence for emphasis]

### Body Language
- **Posture**: [Confident stance]
- **Gestures**: [When and how to gesture]
- **Eye Contact**: [Who to look at when]
- **Facial Expressions**: [What to convey]

### Emotional Intelligence
- **Reading the room**: [Signs you're winning/losing]
- **Adapting mid-debate**: [When to shift strategy]
- **Building rapport**: [With whom and how]
- **Isolating opponents**: [How to make them defensive]

## 🎪 PSYCHOLOGICAL TACTICS

### Controlling the Narrative
1. **Frame First**: Define terms before they do
2. **Own the moral high ground**: [How to claim it]
3. **Make them defend**: Keep them reactive
4. **Build credibility early**: Cite sources, show expertise

### Pressure Tactics (Use Ethically)
- **Expose contradictions**: "[Technique]"
- **Force false choices**: "[Technique]"
- **Highlight consequences**: "[Technique]"
- **Build momentum**: "[Technique]"

### Managing Your Emotions
- **When frustrated**: [Coping technique]
- **When losing**: [Recovery mindset]
- **When winning**: [Stay humble, finish strong]
- **Under pressure**: [Breathing, grounding techniques]

## 📊 DEBATE FLOW MANAGEMENT

### Phase 1: Opening (First 25% of debate time)
**Objectives**:
- Establish your frame
- State clear position
- Show expertise
- Build credibility

**Actions**:
1. [Specific action]
2. [Specific action]
3. [Specific action]

### Phase 2: Engagement (Middle 50%)
**Objectives**:
- Respond to attacks
- Press opponents
- Build alliances
- Accumulate points

**Actions**:
1. [Specific action]
2. [Specific action]
3. [Specific action]

### Phase 3: Closing (Final 25%)
**Objectives**:
- Summarize wins
- Final emotional appeal
- Clear call to action
- Memorable conclusion

**Actions**:
1. [Specific action]
2. [Specific action]
3. [Specific action]

## 🎯 WINNING MOMENTS (Create These)

### Memorable Zingers (Pre-Written)
1. **[Powerful one-liner about your position]**
   - Context: [When to use]
   - Effect: [What it accomplishes]

2-4. **[Additional quotable lines]**
   [Continue...]

### Turning Points (Seize These)
- When opponent makes mistake: "[How to capitalize]"
- When momentum shifts: "[How to ride it]"
- When new information emerges: "[How to integrate]"
- When vote looks close: "[Final push]"

## 🎬 PRACTICE REGIMEN

### Before Debate
- [ ] Memorize 3-5 key statistics
- [ ] Practice opening statement 5+ times
- [ ] Rehearse responses to top 5 expected attacks
- [ ] Prepare 8-10 POI questions
- [ ] Visualize success scenarios

### During Debate
- [ ] Maintain composure
- [ ] Track argument flow
- [ ] Note opponent weaknesses
- [ ] Adjust strategy as needed
- [ ] Build to strong close

### After Each Speech
- [ ] What landed well?
- [ ] What fell flat?
- [ ] What surprised you?
- [ ] Adjust next intervention

## ⚠️ COMMON PITFALLS TO AVOID

1. **Being too defensive**: [How to avoid]
2. **Overcomplicating arguments**: [Keep it simple]
3. **Losing composure**: [Stay calm]
4. **Forgetting to listen**: [Active listening]
5. **Neglecting allies**: [Coalition maintenance]
6. **Peaking too early**: [Pacing strategy]

## 🏆 VICTORY CONDITIONS

### Signs You're Winning
- [Observable indicator 1]
- [Observable indicator 2]
- [Observable indicator 3]

### How to Close the Deal
[Final strategy to secure victory]

### Graceful Victory
[How to win without alienating future partners]

Provide specific, actionable debate coaching with exact phrases and tactical details."""

        debate_plan = self.call_llm(prompt, use_gemini=True)  # Debate coaching requires strategic planning

        return {
            'success': True,
            'debate_preparation': debate_plan,
            'metadata': {
                'agent': self.name,
                'country': country,
                'topic': topic
            }
        }

    def analyze_speech(self, speech_text: str, country: str) -> Dict[str, Any]:
        """Analyze a speech and provide coaching feedback."""

        prompt = f"""As a Debate Coach, analyze this speech from {country} and provide feedback:

SPEECH:
{speech_text}

Provide coaching feedback:

## 💪 STRENGTHS
- [What works well]

## ⚠️ AREAS FOR IMPROVEMENT
1. **[Issue]**
   - Current: [What they did]
   - Better approach: [How to improve]
   - Example: "[Exact better phrasing]"

## 🎯 RHETORICAL ANALYSIS
- Argument structure: [Assessment]
- Evidence usage: [Assessment]
- Persuasive techniques: [What's used well / missing]
- Emotional appeal: [Assessment]

## 📈 SPECIFIC IMPROVEMENTS
1. [Concrete suggestion]
2. [Concrete suggestion]
3. [Concrete suggestion]

## ⭐ OVERALL GRADE
- Content: [A-F]
- Delivery: [A-F]
- Persuasiveness: [A-F]
- Strategic Value: [A-F]

Be constructive and specific."""

        analysis = self.call_llm(prompt, use_gemini=True)  # Counter-argument analysis requires strategic thinking

        return {
            'success': True,
            'speech_analysis': analysis
        }
