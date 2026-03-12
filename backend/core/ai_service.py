import json
import os
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# Import Gemini
try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Import Ollama
try:
    import ollama

    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Import Active Memory System
try:
    from .active_memory import get_active_memory
    from .memory_optimizer import start_background_optimizer

    ACTIVE_MEMORY_AVAILABLE = True
except ImportError:
    ACTIVE_MEMORY_AVAILABLE = False
    print("⚠ Active Memory system not available")


class AIService:
    """AI service using Ollama (gemma3:1b) for quick tasks and Gemini for complex tasks with Active Memory RAG"""

    def __init__(self, vectordb):
        self.vectordb = vectordb
        self.gemini_client = None
        self.ollama_client = None
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        # Initialize Active Memory System
        self.active_memory = None
        if ACTIVE_MEMORY_AVAILABLE:
            try:
                self.active_memory = get_active_memory()
                # Start background optimizer (runs every 5 minutes)
                start_background_optimizer(optimization_interval=300)
                print("✓ Active Memory RAG system initialized")
            except Exception as e:
                print(f"⚠ Could not initialize Active Memory: {e}")

        # Initialize Gemini for complex tasks
        if GEMINI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self.model = genai.GenerativeModel("gemini-2.5-flash-lite")
            self.gemini_client = self.model
            print("✓ Gemini AI initialized (gemini-2.5-flash-lite) for complex tasks")
        else:
            print("⚠ Gemini API key not found or google-generativeai not installed")

        # Initialize Ollama for quick tasks
        if OLLAMA_AVAILABLE:
            try:
                # Test connection
                ollama.list()
                self.ollama_client = ollama
                print(f"✓ Ollama initialized ({self.ollama_model}) for quick tasks")
            except Exception as e:
                print(f"⚠ Could not connect to Ollama at {self.ollama_host}: {e}")
                print("  Make sure Ollama is running: ollama serve")

    def get_available_provider(self):
        """Get the first available AI provider"""
        if self.ollama_client:
            return "ollama + gemini"
        if self.gemini_client:
            return "gemini"
        return None

    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama for quick/simple tasks"""
        if not self.ollama_client:
            # Fallback to Gemini if Ollama not available
            if self.gemini_client:
                response = self.model.generate_content(prompt)
                return response.text
            return (
                "AI service not configured. Please set GEMINI_API_KEY or start Ollama."
            )

        try:
            response = self.ollama_client.generate(
                model=self.ollama_model, prompt=prompt
            )
            return response["response"]
        except Exception as e:
            print(f"⚠ Ollama error: {e}, falling back to Gemini")
            # Fallback to Gemini
            if self.gemini_client:
                response = self.model.generate_content(prompt)
                return response.text
            return f"Error: {str(e)}"

    def _call_gemini(self, prompt: str) -> str:
        """Call Gemini for complex tasks"""
        if not self.gemini_client:
            return "Gemini not configured. Please set GEMINI_API_KEY in .env file."

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def chat_with_context(
        self, user_message: str, conversation_history: List[Dict] = None
    ) -> str:
        """Chat with RAG context from MUN book"""
        return self.chat_with_full_context(user_message, conversation_history, "", "")

    def chat_with_full_context(
        self,
        user_message: str,
        conversation_history: List[Dict] = None,
        config_context: str = "",
        notes_context: str = "",
    ) -> str:
        """Chat with full context: RAG + config + notes + ACTIVE MEMORY (uses Ollama for quick responses)"""

        if not self.ollama_client and not self.gemini_client:
            return (
                "AI service not configured. Please set GEMINI_API_KEY or start Ollama."
            )

        # STEP 1: Query Active Memory (ALWAYS FIRST!)
        active_memory_context = ""
        if self.active_memory:
            try:
                print("🧠 Querying active memory for relevant context...")
                active_memory_context = self.active_memory.get_context_for_llm(
                    user_message, max_tokens=1500
                )
                if active_memory_context:
                    print(
                        f"✓ Retrieved {len(active_memory_context)} chars from active memory"
                    )
            except Exception as e:
                print(f"⚠ Active memory query failed: {e}")

        # STEP 2: Get relevant context from MUN book vector database
        vectordb_context = self.vectordb.get_context_for_query(
            user_message, max_context_length=2000
        )

        # Build comprehensive system prompt with ALL context sources
        system_prompt = f"""You are an expert MUN (Model United Nations) advisor and assistant.
You help delegates with research, speech writing, strategy, and understanding MUN procedures.

You have access to multiple sources of information:

1. ACTIVE MEMORY (Past Conversations, Research, Notes):
{active_memory_context if active_memory_context else "No relevant memories found"}

2. MUN GUIDEBOOK KNOWLEDGE:
{vectordb_context}

3. DELEGATE'S CURRENT SESSION:
{config_context if config_context else "Not configured yet"}

4. DELEGATE'S RESEARCH NOTES:
{notes_context if notes_context else "No notes yet"}

When answering:
- PRIORITIZE information from Active Memory - it contains your past conversations and work
- Use ALL available context (memory, guidebook, session info, and notes)
- Be specific and practical
- Reference the delegate's country, committee, and agenda when relevant
- Provide examples from their notes and past work when applicable
- If you see relevant past conversations or research in Active Memory, reference them
- Follow MUN procedures and best practices
- Be encouraging and supportive

If the user asks for speech generation, incorporate their research notes and country position."""

        try:
            # Build conversation with context
            full_prompt = f"{system_prompt}\n\nUser: {user_message}\n\nAssistant:"

            # If there's history, include it
            if conversation_history and len(conversation_history) > 0:
                history_text = "\n".join(
                    [
                        f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                        for msg in conversation_history[-6:]  # Last 6 messages
                    ]
                )
                full_prompt = f"{system_prompt}\n\nConversation History:\n{history_text}\n\nUser: {user_message}\n\nAssistant:"

            # Use Ollama for chat (quick responses)
            response_text = self._call_ollama(full_prompt)

            # STEP 3: Cache this conversation in Active Memory
            if self.active_memory:
                try:
                    self.active_memory.cache_conversation(
                        user_message=user_message,
                        assistant_response=response_text,
                        metadata={
                            "has_config": bool(config_context),
                            "has_notes": bool(notes_context),
                        },
                    )
                except Exception as e:
                    print(f"⚠ Failed to cache conversation: {e}")

            return response_text

        except Exception as e:
            return f"Error: {str(e)}"

    def generate_speech(
        self,
        country: str,
        topic: str,
        committee: str = "",
        stance: str = "",
        speech_type: str = "GSL",
        notes_context: str = "",
    ) -> str:
        """Generate MUN speech based on parameters (uses Gemini for quality)"""

        if not self.gemini_client:
            return "AI service not configured. Please set GEMINI_API_KEY in .env file."

        prompt = f"""Generate a {speech_type} speech for MUN.

Country: {country}
Committee: {committee if committee else "General"}
Topic: {topic}
Stance: {stance if stance else "To be determined based on country policy"}

Requirements:
1. Follow proper MUN speech format
2. Stay in character for the country
3. Use diplomatic language
4. Include 3-4 key points
5. Reference facts and statistics where relevant
6. Keep it between 60-90 seconds when spoken
7. Consider the country's foreign policy and past positions
8. IMPORTANT: Use information from the delegate's research notes if available

Generate a professional, impactful MUN speech.

Research Notes Context:
{notes_context}"""

        # Use Gemini for speech generation (complex task requiring quality)
        speech = self._call_gemini(prompt)

        # Cache the generated speech in active memory
        if self.active_memory:
            try:
                self.active_memory.cache_speech(
                    {
                        "id": f"speech_{int(__import__('time').time() * 1000)}",
                        "country": country,
                        "topic": topic,
                        "speech_type": speech_type,
                        "content": speech,
                    }
                )
            except Exception as e:
                print(f"⚠ Failed to cache speech: {e}")

        return speech

    def analyze_notes(self, notes: str) -> Dict:
        """Analyze notes and generate insights (uses Ollama for quick analysis)"""

        if not self.ollama_client and not self.gemini_client:
            return {"error": "AI service not configured"}

        prompt = f"""Analyze these MUN research notes and provide:

1. Key Points Summary (3-5 bullet points)
2. Suggested Arguments (specific points the delegate can make)
3. Potential Counter-Arguments (what others might say)
4. Research Gaps (what information is missing)
5. Strategy Recommendations

NOTES:
{notes}

Provide a structured analysis."""

        # Use Ollama for quick note analysis
        analysis = self._call_ollama(prompt)

        return {
            "analysis": analysis,
            "word_count": len(notes.split()),
            "estimated_reading_time": f"{len(notes.split()) // 200} min",
        }

    def generate_poi_questions(
        self, country: str, topic: str, target_country: str = ""
    ) -> List[str]:
        """Generate Point of Information questions"""

        if not self.gemini_client:
            return ["AI service not configured"]

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

Generate 5 POI questions, numbered 1-5."""

        response = self.chat_with_context(prompt)

        # Try to extract questions (simple parsing)
        questions = []
        for line in response.split("\n"):
            line = line.strip()
            if line and ("?" in line or (line[0:2].replace(".", "").isdigit())):
                # Clean up numbering
                clean_line = line.lstrip("0123456789.-) ")
                if clean_line and len(clean_line) > 10:
                    questions.append(clean_line)

        return questions[:5] if questions else [response]

    def research_foreign_policy(self, country: str, topic: str) -> str:
        """Research foreign policy for a country on a topic"""

        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Create a comprehensive foreign policy brief for {country} on {topic}.

## CURRENT OFFICIAL POSITION

### Public Stance:
- Official government position (exact policy statement)
- Latest statements by leaders (quotes with dates)
- Voting record in UN/international forums
- Treaty commitments and obligations

### Real Position vs. Public Stance:
- What they say publicly vs. what they actually do
- Hidden motivations and priorities
- Contradictions to exploit in debate

## HISTORICAL CONTEXT & EVOLUTION

### Timeline of Policy Changes:
For last 10-20 years:
- [Year]: [Event/Policy Change]
  - What happened and why
  - Impact on current stance
  - Key figures involved

### Past Actions & Precedents:
- Previous votes on similar issues
- Historical treaties signed/rejected
- Past statements that can be quoted
- Actions taken (military, diplomatic, economic)

## STRATEGIC INTERESTS

### Economic Interests:
- Trade dependencies ($$ amounts, % of GDP)
- Key industries affected
- Resource concerns (oil, minerals, agriculture)
- Budget allocations
- Economic costs/benefits of different positions

### Political Interests:
- Domestic political pressures
- Public opinion (poll numbers if available)
- Powerful interest groups
- Electoral considerations
- Coalition/party politics

### Security Interests:
- Military/defense concerns
- Border security issues
- Alliances (NATO, regional pacts)
- Threat perceptions
- Strategic vulnerabilities

### Diplomatic Interests:
- Regional leadership ambitions
- International image concerns
- Relations with major powers
- Soft power considerations

## KEY RELATIONSHIPS

### Natural Allies on This Issue:
For each ally:
- Why they align with {country}
- Strength of relationship
- Shared interests
- Historical cooperation

### Adversaries/Competitors:
For each opponent:
- Nature of disagreement
- Historical conflicts
- Current tensions
- Red lines in relationship

### Swing Countries:
- Countries that could go either way
- What would make them support {country}
- What might push them away

## DOMESTIC FACTORS

### Government Structure:
- Who makes foreign policy decisions
- Institutional constraints
- Legislative approval needed?
- Bureaucratic influences

### Public Opinion:
- Polling data on this issue
- Media narratives
- Civil society positions
- Protest movements or support

### Economic Groups:
- Which industries benefit/lose
- Lobbying pressures
- Labor union positions
- Business interests

### Cultural/Religious Factors:
- Historical narratives
- National identity issues
- Religious influences
- Cultural sensitivities

## LIKELY MUN POSITION

### What They'll Argue:
8-10 specific arguments they'll make:
1. [Argument with exact phrasing]
   - Why it's persuasive
   - Evidence they'll cite
   - Emotional appeal

### Their Strategy Will Be:
- Goals they're trying to achieve
- Tactics they'll employ
- Countries they'll work with
- Resolutions they'll support/oppose

### How to Work With Them (if allies):
- What they need to hear
- What concessions they want
- How to frame your asks
- What NOT to say

### How to Counter Them (if opponents):
- Weaknesses in their position
- Contradictions to expose
- POI questions to ask
- Allies to peel away

## RESOLUTION PREFERENCES

### Clauses They'll Support:
- Types of actions they favor
- Language they prefer
- Red lines they won't cross

### Clauses They'll Oppose:
- What they'll try to remove
- Why they oppose it
- How strong their opposition is

### Amendments They'll Propose:
- Expected changes to resolutions
- Hidden agenda in amendments
- How to respond

## SPEECH-READY TALKING POINTS

10 key points with exact wording:
1. "[Quote-ready statement about their position]"
   - Context: [when to use]
   - Impact: [why it matters]
   - Source: [where this info comes from]

## VULNERABILITIES & PRESSURE POINTS

### Weaknesses to Exploit:
- Logical contradictions
- Unpopular positions
- Failed past policies
- Hypocrisy to expose

### How to Pressure Them:
- Issues they're sensitive about
- International reputation concerns
- Domestic political vulnerabilities
- Economic leverage points

Be EXTREMELY detailed with specific facts, quotes, statistics, dates, and actionable intelligence."""

        result = self.chat_with_context(prompt)

        # Cache this research in active memory
        if self.active_memory:
            try:
                self.active_memory.cache_research(
                    research_type="foreign_policy",
                    country=country,
                    topic=topic,
                    content=result,
                    metadata={
                        "timestamp": __import__("datetime").datetime.now().isoformat()
                    },
                )
            except Exception as e:
                print(f"⚠ Failed to cache research: {e}")

        return result

    def suggest_moderated_caucus_topics(
        self, main_agenda: str, committee: str = ""
    ) -> List[str]:
        """Suggest moderated caucus topics for an agenda (uses Ollama for quick suggestions)"""

        if not self.ollama_client and not self.gemini_client:
            return ["AI service not configured"]

        prompt = f"""For a MUN committee discussing: {main_agenda}
Committee: {committee if committee else "General"}

Suggest 8 specific moderated caucus topics that:
1. Are subtopics of the main agenda
2. Encourage debate and discussion
3. Are actionable and solution-oriented
4. Fit within the committee's mandate
5. Are timely and relevant

List only the topics, numbered 1-8, one per line."""

        # Use Ollama for quick topic suggestions
        response = self._call_ollama(prompt)

        # Parse topics
        topics = []
        for line in response.split("\n"):
            line = line.strip()
            if line and len(line) > 10:
                # Clean up numbering and bullet points
                clean_line = line.lstrip("0123456789.-•* ")
                if clean_line and len(clean_line) > 10:
                    topics.append(clean_line)

        return topics[:8] if topics else [response]

    def generate_speech_feedback(
        self, transcription: str, sentiment_data: Dict = None
    ) -> str:
        """Generate feedback for a recorded speech"""

        if not self.gemini_client:
            return "AI service not configured"

        sentiment_info = ""
        if sentiment_data:
            sentiment_info = f"\nSentiment Analysis: {sentiment_data.get('sentiment', 'N/A')} (Score: {sentiment_data.get('score', 'N/A')})"

        prompt = f"""Analyze this MUN speech transcription and provide constructive feedback:

TRANSCRIPTION:
{transcription}
{sentiment_info}

Provide feedback on:
1. Content Quality (arguments, facts, relevance)
2. Structure (opening, body, closing)
3. Diplomatic Language (tone, formality)
4. Clarity (is the message clear?)
5. Improvements (specific suggestions)

Be encouraging but constructive."""

        return self.chat_with_context(prompt)

    def suggest_allies(self, country: str, topic: str) -> str:
        """Suggest potential allies for lobbying"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""As an expert MUN strategist, analyze potential allies for {country} on the topic of {topic}.

Provide a DETAILED lobbying strategy:

## TOP 5 MOST LIKELY ALLIES

For each ally, provide:
- WHY they will support (specific reasons based on their interests)
- WHAT they want in return (concrete concessions or support)
- SHARED INTERESTS (common ground you can emphasize)
- APPROACH STRATEGY (specific talking points and timing)
- POTENTIAL OBSTACLES (what might make them hesitate)

## LOBBYING PRIORITIES

1. First Tier (Most Critical - approach first):
   - List countries with detailed explanation

2. Second Tier (Important but flexible):
   - List countries with approach strategy

3. Swing Votes (could go either way):
   - List countries and how to convince them

## NEGOTIATION TACTICS

- What to offer (specific clauses, amendments, support on other issues)
- What to emphasize (shared values, common threats, mutual benefits)
- What to avoid saying (sensitive topics that might offend)

## BLOC BUILDING STRATEGY

- How to create a working bloc
- Key countries to anchor your bloc
- How to expand your coalition

Be EXTREMELY specific with country names, exact interests, recent events, and actionable strategies."""

        return self.chat_with_context(prompt)

    def identify_opposition(self, country: str, topic: str) -> str:
        """Identify likely opposition countries"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""As an expert MUN analyst, identify and analyze the opposition to {country} on {topic}.

## TOP 5 LIKELY OPPONENTS

For each opponent, provide:
- WHY they oppose (specific national interests, historical reasons)
- THEIR MAIN ARGUMENTS (the exact points they'll make)
- THEIR STRENGTHS (what makes their position strong)
- THEIR WEAKNESSES (vulnerabilities you can exploit)
- VOTING BLOC they lead or belong to

## OPPOSITION ARGUMENTS & YOUR COUNTERS

List 8-10 specific arguments they will make, with:
- The argument word-for-word (as they'll say it)
- Why it's effective
- Your detailed counter-argument with facts
- POI questions to expose weaknesses
- How to reframe the debate to your advantage

## COMPROMISE STRATEGIES

1. Maximum compromise (what you can give up if needed):
2. Middle ground options (specific clause wordings):
3. Red lines (what you CANNOT compromise on):
4. How to present compromises without appearing weak:

## DIVIDE AND CONQUER TACTICS

- Which opposition countries might break rank
- What would make them switch sides
- How to isolate the hardliners
- Wedge issues to split their bloc

## DEFENSIVE STRATEGY

- Expected POI questions from opponents (with prepared answers)
- Vulnerable points in your position (how to defend them)
- How to avoid their traps
- When to pivot and when to stand firm

Be EXTREMELY detailed with specific arguments, facts, statistics, and real diplomatic language."""

        return self.chat_with_context(prompt)

    def get_key_facts(self, country: str, topic: str) -> str:
        """Get key facts and statistics"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Provide comprehensive, speech-ready facts about {country} and {topic}.

## CRITICAL STATISTICS (Use these in speeches!)

For each statistic, provide:
- The exact number/percentage
- What it means/why it matters
- How to use it in a speech (with example sentence)
- Source or timeframe (e.g., "According to 2023 data...")

Cover:
- Economic impact ($$ amounts, GDP %, trade figures)
- Population affected (specific numbers)
- Environmental/social metrics
- Comparative rankings (where country stands globally)
- Growth/decline trends (% change over time)

## RECENT EVENTS (Last 2-3 years)

For each event:
- Date and what happened
- Impact on {country}'s position
- How it changed the situation
- How to reference it in debate
- Which countries were involved

## KEY TREATIES & AGREEMENTS

List all relevant agreements with:
- Full name and year
- What {country} committed to
- Current compliance status
- How to use this in arguments
- Loopholes or exceptions

## LEADERSHIP STATEMENTS

Quote 5-10 actual statements by {country}'s leaders:
- Exact quote (or close paraphrase)
- Who said it and when
- Context and what it reveals
- How to use it in debate ("As [Leader] stated in [Year]...")

## ECONOMIC IMPACT DATA

Detailed breakdown:
- Budget allocations (specific amounts)
- Industry effects (which sectors affected)
- Trade statistics (import/export figures)
- Job numbers (employment impact)
- Cost-benefit analysis

## QUICK-REFERENCE TALKING POINTS

10 memorizable one-liners with statistics:
Example: "{{Country}} has invested $X billion in [topic], demonstrating our commitment"

Be SPECIFIC with numbers, dates, names, and exact figures. Everything should be usable in a speech."""

        return self.chat_with_context(prompt)

    def get_historical_context(self, country: str, topic: str) -> str:
        """Get historical context"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Provide historical context for {country}'s position on {topic}.

Cover:
1. Historical Background (last 20-30 years)
2. Major Policy Shifts and Why
3. Past UN Actions or Votes
4. Key Historical Events Shaping Current Position
5. Evolution of Stance Over Time

Be comprehensive but concise."""

        return self.chat_with_context(prompt)

    def generate_resolution_ideas(
        self, country: str, topic: str, committee: str
    ) -> str:
        """Generate resolution clause ideas"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Draft strategic resolution clauses for {country} in {committee} on {topic}.

## PREAMBULATORY CLAUSES (Context Setting)

Provide 5-7 clauses with:
- The exact wording (proper MUN format)
- Why this clause is important
- What precedent/treaty it references
- How it supports your operative clauses

## OPERATIVE CLAUSES (Actions)

Provide 10-12 clauses including:

### Must-Have Clauses (Your core agenda):
1. [Clause with exact wording]
   - Strategic value: [why this is critical]
   - Implementation: [how it would work]
   - Cost: [funding mechanism]
   - Timeline: [when it takes effect]
   - Verification: [how to measure success]

### Negotiable Clauses (Trading chips):
- Clauses you can compromise on
- What you'd want in return

### Poison Pills (To block opposition):
- Clauses that look good but actually benefit you
- How they constrain opponents

## IMPLEMENTATION MECHANISMS

For each major clause:
- Specific UN agency responsible
- Budget and funding sources
- Timeline with milestones
- Reporting requirements
- Enforcement mechanisms
- Penalty for non-compliance

## CO-SPONSORSHIP STRATEGY

### Ideal Co-Sponsors (Priority order):
1. [Country] - Why: [strategic reason]
2. [Country] - What they get: [benefit]
3. [Country] - How to convince them: [approach]

### Signatories to Target:
- Geographic diversity strategy
- Bloc representation
- P5 considerations

## AMENDMENT STRATEGY

### Friendly Amendments to Accept:
- Types of changes that strengthen your position
- Which countries' amendments to welcome

### Hostile Amendments to Reject:
- How to recognize poison amendments
- Diplomatic ways to vote them down
- Counter-amendments to propose

## PASSAGE STRATEGY

- Speaking order (when to introduce)
- Which allies speak in support (order matters)
- How to handle procedural motions
- Vote-counting predictions

Be SPECIFIC with exact clause wordings, country names, UN procedures, and tactical details."""

        return self.chat_with_context(prompt)

    def generate_country_profile(self, country: str, topic: str = "") -> str:
        """Generate comprehensive country profile"""
        if not self.gemini_client:
            return "AI service not configured"

        topic_text = f" especially regarding {topic}" if topic else ""

        prompt = f"""Create a detailed intelligence briefing on {country}{topic_text}.

## BASIC COUNTRY INFORMATION

### Demographics & Geography:
- Capital and major cities
- Population (with ethnic/religious breakdown %)
- Geographic features affecting policy
- Natural resources
- Strategic location importance

### Government & Leadership:
- Official government type
- Current leader(s) and tenure
- Leadership style (authoritarian, democratic, etc.)
- Key ministers/officials for foreign policy
- Political stability assessment
- Next election/transition dates

### Economic Profile:
- GDP (total and per capita)
- Major industries and exports
- Trade partners (top 5 with %%)
- Economic growth/decline trends
- Debt levels and fiscal health
- Currency and economic vulnerabilities

## FOREIGN POLICY CHARACTER

### Overall Diplomatic Approach:
- Alignment (Western, Non-Aligned, Regional bloc)
- Diplomatic style (aggressive, defensive, neutral)
- Historical foreign policy tradition
- How they view international institutions

### UN Behavior:
- Voting patterns (with/against major powers)
- Past resolutions sponsored
- Security Council record (if P5)
- UN agencies they support/oppose
- Financial contributions to UN

### Regional Role:
- Leadership ambitions in region
- Regional organizations membership
- Conflicts with neighbors
- Regional allies and rivals
- Cross-border issues

## KEY RELATIONSHIPS

### With Major Powers:
**United States:**
- Nature of relationship (ally, adversary, neutral)
- Key issues of cooperation/conflict
- Trade relationship
- Military ties or tensions

**China:**
- Economic dependencies
- Political alignment
- Belt and Road involvement
- Areas of competition

**Russia:**
- Historical ties
- Current relationship
- Energy dependencies
- Military cooperation

**European Union:**
- Trade relationships
- Political alignment
- Migration issues
- Diplomatic cooperation

### Regional Alliances:
- Military alliances (NATO, SCO, etc.)
- Economic blocs (EU, ASEAN, etc.)
- Political groupings
- Bilateral key partnerships

## STRATEGIC INTERESTS & PRIORITIES

### Top 3 National Priorities:
1. [Priority] - Why it matters, how it affects foreign policy
2. [Priority] - Budget allocation, political commitment
3. [Priority] - Trade-offs with other goals

### Economic Interests:
- Resource security needs (energy, food, minerals)
- Export markets to protect
- Investment priorities
- Technology transfer goals

### Security Concerns:
- Primary threats (specific countries/groups)
- Defense spending (% GDP, $$ amount)
- Military capabilities assessment
- Cyber and asymmetric warfare capabilities

### Soft Power Assets:
- Cultural influence
- Educational ties
- Media reach
- Development aid programs

## DOMESTIC POLITICS & FOREIGN POLICY

### Internal Pressures:
- Public opinion on international issues
- Nationalist movements
- Economic inequality affecting policy
- Ethnic/religious tensions

### Key Stakeholders:
- Military influence on policy
- Business/corporate interests
- Media and public intellectuals
- Civil society organizations

### Political Constraints:
- What the government CAN'T do (politically impossible)
- Coalition politics affecting foreign policy
- Legislative approval requirements

## HISTORICAL FACTORS

### Colonial/Imperial Legacy:
- Historical grievances
- Post-colonial relationships
- Reparations/restitution issues

### Major Historical Events Shaping Policy:
- Wars and conflicts
- Economic crises
- Revolutions or regime changes
- Traumatic national experiences

### Cultural and Religious Influences:
- Dominant religion(s) and political impact
- Cultural values affecting diplomacy
- Historical narratives taught in schools
- National myths and identity

## MUN BEHAVIOR PREDICTION{topic_text.upper() if topic else ""}

### Likely Positions:
- What they'll support and why
- What they'll oppose and why
- Their negotiation bottom lines
- What they'll trade for what

### Diplomatic Style in Committee:
- Aggressive or conciliatory
- Likely to make speeches or work behind scenes
- Historical MUN behavior patterns
- Resolution drafting approach

### Potential Allies:
- 5-7 countries they'll work with
- Shared interests for each
- How stable each alliance is

### Potential Opponents:
- 5-7 countries they'll clash with
- Points of contention
- How hostile each relationship is

## PRESSURE POINTS & VULNERABILITIES

### What They Fear:
- Economic sanctions impact
- Diplomatic isolation
- Military vulnerabilities
- Reputation damage

### What They Need:
- Resources they depend on
- International legitimacy
- Market access
- Technology/expertise

### Negotiation Leverage:
- What they can offer others
- What they're desperate to avoid
- Where they'll compromise
- Where they won't budge

## QUICK REFERENCE

### In One Sentence:
"[Country] is a [description] that prioritizes [X] and will likely [action] on [topic]"

### Key Stats to Memorize:
- Population: [number]
- GDP: [$amount]
- Military: [spending/ranking]
- UN Vote Alignment: [% with major powers]

### Top 3 Arguments They'll Make:
1. [Argument in their voice]
2. [Argument in their voice]
3. [Argument in their voice]

### How to Counter Them:
1. [Specific weakness to exploit]
2. [Key contradiction to expose]
3. [Ally to turn against them]

Be EXTREMELY specific with numbers, names, dates, and actionable intelligence for MUN use."""

        return self.chat_with_context(prompt)

    def generate_resolution_draft(
        self, country: str, topic: str, committee: str
    ) -> str:
        """Generate a complete resolution draft"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Draft a complete UN resolution on {topic} for {committee}.

Country perspective: {country if country else "Neutral"}

Include:
1. Heading (Committee, Topic, Sponsors)
2. 5-7 Preambulatory Clauses
3. 8-10 Operative Clauses
4. Implementation mechanisms
5. Funding/resource allocation
6. Monitoring and evaluation

Use proper MUN resolution format with proper clause structure."""

        return self.chat_with_context(prompt)

    def generate_crisis_response(self, country: str, crisis: str) -> str:
        """Generate response to a crisis"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Generate {country}'s response to this crisis: {crisis}

Provide:
1. Immediate Statement (what to say in committee)
2. Policy Position (what actions to support/oppose)
3. Diplomatic Strategy (who to work with)
4. Key Talking Points (3-5 main points)
5. Potential Actions to Propose
6. Red Lines (what not to accept)

Be specific and actionable for immediate use."""

        return self.chat_with_context(prompt)

    def prepare_debate(self, my_country: str, opponent_country: str, topic: str) -> str:
        """Prepare for debate against specific country"""
        if not self.gemini_client:
            return "AI service not configured"

        prompt = f"""Create a battle plan for {my_country} to debate against {opponent_country} on {topic}.

## OPPONENT ANALYSIS

### Their Position & Motivations:
- Exact stance they'll take
- Why they hold this position (economic, political, cultural reasons)
- What they're trying to achieve
- Their leverage and advantages

### Their Arguments (Predict exactly what they'll say):

For each argument (provide 6-8):
1. **Exact quote/paraphrase**: "[What they'll say]"
   - Why it's effective: [analysis]
   - Evidence they'll use: [specific facts/stats]
   - Emotional appeal: [how it plays to the room]

## YOUR COUNTER-STRATEGY

### Counter-Arguments (For each of their arguments):

1. **Direct rebuttal**: [Your counter with facts]
   - Statistics to cite: [specific numbers]
   - Examples to reference: [real cases]
   - How to frame it: "[Exact phrasing to use]"

2. **Reframe the debate**: [Change the focus to your strength]
   - New angle: [perspective shift]
   - Rhetorical device: [how to pivot]

### Offensive Arguments (Proactive points):

10 strong arguments to make BEFORE they speak:
1. [Argument with exact wording]
   - Supporting evidence: [facts/stats]
   - Rhetorical impact: [why it works]
   - Follow-up if challenged: [backup point]

## POI STRATEGY

### Questions to Ask Them (8-10 questions):

Each POI should:
- Expose a weakness or contradiction
- Force them into a difficult position
- Make them look inconsistent

Format:
1. **POI**: "[Exact question to ask]"
   - Best timing: [when to raise it]
   - Expected answer: [what they'll say]
   - Your follow-up: [how to press further]
   - If they dodge: [alternate angle]

### POI Defense (Questions they'll ask you):

Predict 8-10 POIs they'll raise:
1. **Expected POI**: "[What they'll ask]"
   - Why it's challenging: [the trap]
   - **Your answer**: "[Exact response - memorize this]"
   - If pressed further: "[Backup response]"
   - Don't say: [what to avoid]

## RHETORICAL TACTICS

### Verbal Techniques:
- When to be aggressive vs. diplomatic
- How to make them defensive
- When to show emotion vs. stay calm
- Facial expressions and body language

### Debate Floor Management:
- When to speak in speaker's list
- How to dominate moderated caucuses
- When to yield time vs. take full time
- How to build momentum

### Turning Points:
- Key moments to make your move
- How to read the room
- When to go for the kill
- When to appear reasonable

## ALLIANCE TACTICS

### Other Countries in Debate:
- Who to reference for credibility
- Who to align with publicly
- Who NOT to associate with
- How to split {opponent_country}'s supporters

### Working the Room:
- Who to look at when speaking
- How to appeal to swing votes
- How to isolate your opponent
- Building consensus against them

## OVERALL STRATEGY

### Phase 1 - Opening:
- First statement to make
- Tone to set
- Alliances to signal

### Phase 2 - Engagement:
- When to attack directly
- When to let others attack
- How to maintain initiative

### Phase 3 - Closing:
- How to position for voting
- Final arguments to emphasize
- Damage control if needed

### Contingency Plans:
- If they bring up [X]: [Response]
- If they're winning the room: [Pivot]
- If an ally betrays you: [Recovery]
- If facts are disputed: [Evidence strategy]

## MEMORABLE QUOTES

5-7 pre-written zingers you can use:
1. "[Powerful quote that will get remembered]"
   - Context: [when to use it]
   - Effect: [what it accomplishes]

Be EXTREMELY specific with exact wordings, timing, and tactical decisions. This should be a complete battle plan."""

        return self.chat_with_context(prompt)

    # ============= SPEECH RATING & ANALYSIS METHODS =============

    def analyze_speech_grammar(self, speech_text: str) -> Dict:
        """Analyze grammar and language quality of a speech"""
        if not self.gemini_client:
            return {"error": "AI service not configured"}

        prompt = f"""Analyze this MUN speech for SPOKEN language quality. Remember: this is meant to be SPOKEN OUT LOUD, not read. Punctuation, capitalization, and formatting don't matter - focus on how it SOUNDS.

SPEECH:
{speech_text}

PROVIDE EXACTLY 5 CONCISE POINTS (bullet points only, no paragraphs):

## GRAMMAR SCORE: [X/10]

## KEY ISSUES:
- [First major issue that affects spoken clarity]
- [Second major issue that affects spoken delivery]
- [Third issue with vocabulary or word choice]
- [Fourth issue with sentence flow when spoken]
- [Fifth issue or overall language quality point]

Be CONCISE. Each point should be one sentence maximum. Focus on SPOKEN delivery, not written grammar."""

        response = self.chat_with_context(prompt)
        return {"analysis": response}

    def analyze_speech_ethics(self, speech_text: str, country: str = "") -> Dict:
        """Evaluate speech for diplomatic ethics and appropriateness"""
        if not self.gemini_client:
            return {"error": "AI service not configured"}

        country_context = f" representing {country}" if country else ""

        prompt = f"""Evaluate this MUN speech{country_context} for ethics and diplomacy. Remember: MUN speeches should be AGGRESSIVE and IMPACTFUL, not boring. Passion and force are good - just check if lines are crossed.

SPEECH:
{speech_text}

PROVIDE EXACTLY 5 CONCISE POINTS (bullet points only):

## ETHICS SCORE: [X/10]

## KEY OBSERVATIONS:
- [Is the aggression appropriate or does it cross ethical lines?]
- [Any problematic accusations, personal attacks, or unfair characterizations?]
- [Cultural sensitivity issues or stereotyping to flag?]
- [Logical fallacies or manipulation tactics being used?]
- [Overall diplomatic appropriateness - is it powerful but respectful?]

Be CONCISE. Each point one sentence. Remember: aggressive and passionate is GOOD in MUN speeches."""

        response = self.chat_with_context(prompt)
        return {"analysis": response}

    def analyze_speech_impact(
        self, speech_text: str, topic: str = "", audience: str = ""
    ) -> Dict:
        """Analyze how to make speech more impactful and persuasive"""
        if not self.gemini_client:
            return {"error": "AI service not configured"}

        context = f" on {topic}" if topic else ""
        audience_info = f" for {audience} committee" if audience else ""

        prompt = f"""Analyze this MUN speech{context}{audience_info} for IMPACT. This needs to be AGGRESSIVE, POWERFUL, and MEMORABLE. Weak speeches lose debates. Rate how well this would DESTROY opponents.

SPEECH:
{speech_text}

PROVIDE EXACTLY 5 CONCISE POINTS (bullet points only):

## IMPACT SCORE: [X/10]

## KEY IMPACT FACTORS:
- [Does the opening grab attention and set aggressive tone, or is it weak?]
- [Are the arguments hitting hard with facts and emotion, or falling flat?]
- [Is there memorable rhetoric that delegates will quote, or is it forgettable?]
- [Does it make opponents uncomfortable and defensive, or do they not care?]
- [Will this speech change votes and win debates, or just fill time?]

Be CONCISE and BRUTAL. Each point one sentence. Focus on WINNING."""

        response = self.chat_with_context(prompt)
        return {"analysis": response}

    def generate_speech_summary_and_rewrite(
        self,
        speech_text: str,
        grammar_analysis: str,
        ethics_analysis: str,
        impact_analysis: str,
        country: str = "",
        topic: str = "",
    ) -> Dict:
        """Generate comprehensive summary from all analyses and rewrite the speech"""
        if not self.gemini_client:
            return {"error": "AI service not configured"}

        context_info = (
            f"Country: {country}, Topic: {topic}" if country and topic else ""
        )

        prompt = f"""Based on the three analyses below, create a SUMMARY and REWRITE of this MUN speech.

ORIGINAL SPEECH:
{speech_text}

GRAMMAR ANALYSIS:
{grammar_analysis}

ETHICS ANALYSIS:
{ethics_analysis}

IMPACT ANALYSIS:
{impact_analysis}

Context: {context_info}

Provide:

## OVERALL SUMMARY (EXACTLY 10 BULLET POINTS):
Synthesize all three analyses into 10 actionable points. Each point should be ONE sentence maximum. Focus on what matters for WINNING.

- [Point 1]
- [Point 2]
- [Point 3]
- [Point 4]
- [Point 5]
- [Point 6]
- [Point 7]
- [Point 8]
- [Point 9]
- [Point 10]

## IMPROVED SPEECH:
Rewrite the ENTIRE speech incorporating ALL feedback. Make it:
- AGGRESSIVE and POWERFUL (not boring)
- Grammatically sound when SPOKEN
- Ethically appropriate but still forceful
- MEMORABLE and quotable
- Designed to WIN debates

Include delivery markers like [PAUSE], [RAISE VOICE], [SLOW DOWN] where appropriate.

Provide the complete rewritten speech below, ready to deliver."""

        response = self.chat_with_context(prompt)
        return {"summary_and_rewrite": response}

    def rate_speech_comprehensive(
        self, speech_text: str, country: str = "", topic: str = "", committee: str = ""
    ) -> Dict:
        """Provide comprehensive speech rating across all dimensions"""
        if not self.gemini_client:
            return {"error": "AI service not configured"}

        context = f"""
Country: {country if country else "Not specified"}
Topic: {topic if topic else "Not specified"}
Committee: {committee if committee else "Not specified"}
"""

        prompt = f"""As a professional MUN judge and speech evaluator, provide a comprehensive rating of this speech.

CONTEXT:
{context}

SPEECH:
{speech_text}

Provide detailed evaluation:

## OVERALL SCORE: [X/100]

## CATEGORY SCORES:

### Content (30 points):
- Relevance to topic: [X/10]
- Argument strength: [X/10]
- Evidence quality: [X/10]
- Detailed feedback: [analysis]

### Delivery & Style (25 points):
- Diplomatic tone: [X/10]
- Clarity: [X/8]
- Engagement: [X/7]
- Detailed feedback: [analysis]

### Structure (20 points):
- Organization: [X/7]
- Flow: [X/7]
- Opening/Closing: [X/6]
- Detailed feedback: [analysis]

### Language (15 points):
- Grammar: [X/7]
- Vocabulary: [X/8]
- Detailed feedback: [analysis]

### Impact (10 points):
- Persuasiveness: [X/5]
- Memorability: [X/5]
- Detailed feedback: [analysis]

## STRENGTHS:
Top 5 things this speech does well

## AREAS FOR IMPROVEMENT:
Top 5 specific improvements needed

## COMPETITIVE ANALYSIS:
- How this would rank in a real MUN: [Top 10%, Top 25%, Average, Below Average]
- Compared to award-winning speeches: [analysis]
- What's missing for excellence: [specific gaps]

## LETTER GRADE: [A+/A/A-/B+/B/B-/C+/C/D/F]

## ONE SENTENCE SUMMARY:
[Concise overall assessment]

Be honest, constructive, and specific."""

        response = self.chat_with_context(prompt)
        return {"analysis": response}

    # ============= CHIT GENERATION METHODS =============

    def generate_poi_chit(
        self, to_country: str, question: str = "", topic: str = "", my_country: str = ""
    ) -> str:
        """Generate a chit to ask a POI question (uses Ollama for quick generation)"""
        if not self.ollama_client and not self.gemini_client:
            return "AI service not configured"

        from_info = f" from {my_country}" if my_country else ""

        prompt = f"""Generate a professional MUN chit{from_info} to {to_country} requesting to ask a Point of Information.

Context:
- Topic: {topic if topic else "General discussion"}
- Question to ask: {question if question else "To be determined"}

The chit should:
1. Be concise (2-3 sentences max)
2. Be polite and professional
3. Clearly state you want to ask a POI
4. Optionally preview the topic of the question (without giving away the full question)
5. Follow proper MUN chit etiquette

Provide 3 different versions:
1. **Formal**: Very diplomatic and proper
2. **Friendly**: Professional but warm
3. **Direct**: Concise and to-the-point

Format each as a ready-to-write chit."""

        # Use Ollama for quick chit generation
        return self._call_ollama(prompt)

    def generate_lobbying_chit(
        self, to_country: str, purpose: str = "", my_country: str = "", topic: str = ""
    ) -> str:
        """Generate a chit for lobbying or alliance building (uses Ollama for quick generation)"""
        if not self.ollama_client and not self.gemini_client:
            return "AI service not configured"

        from_info = f" from {my_country}" if my_country else ""
        topic_info = f" regarding {topic}" if topic else ""

        prompt = f"""Generate a professional MUN lobbying chit{from_info} to {to_country}{topic_info}.

Purpose: {purpose if purpose else "Discuss potential collaboration"}

The chit should:
1. Be diplomatic and inviting
2. Clearly state the purpose (meet to discuss, form alliance, negotiate clause, etc.)
3. Be respectful of their time
4. Suggest a meeting (modcaucus, unmodcaucus, or specific time)
5. Create interest without revealing full strategy

Provide 3 different versions:

1. **Alliance Building**: For potential allies, warm and cooperative
2. **Negotiation**: For countries you need to win over, strategic
3. **Bloc Formation**: For organizing multiple countries, leadership-focused

Format each as a ready-to-write chit with proper tone and structure."""

        # Use Ollama for quick chit generation
        return self._call_ollama(prompt)

    def generate_general_chit(
        self,
        to_country: str,
        message: str,
        my_country: str = "",
        tone: str = "professional",
    ) -> str:
        """Generate a general communication chit (uses Ollama for quick generation)"""
        if not self.ollama_client and not self.gemini_client:
            return "AI service not configured"

        from_info = f" from {my_country}" if my_country else ""

        prompt = f"""Generate a MUN chit{from_info} to {to_country}.

Message to convey: {message}
Desired tone: {tone}

The chit should:
1. Match the requested tone ({tone})
2. Be concise (2-4 sentences typically)
3. Clearly communicate the message
4. Follow MUN chit etiquette
5. Be appropriately formal or informal based on purpose

Provide the chit text ready to write."""

        # Use Ollama for quick chit generation
        return self._call_ollama(prompt)

    def generate_directive_chit(
        self,
        to_country: str,
        directive: str,
        my_country: str = "",
        urgency: str = "normal",
    ) -> str:
        """Generate a directive chit (uses Ollama for quick generation)"""
        if not self.ollama_client and not self.gemini_client:
            return "AI service not configured"

        from_info = f" from {my_country}" if my_country else ""

        prompt = f"""Generate a directive MUN chit{from_info} to {to_country}.

Directive/Request: {directive}
Urgency level: {urgency}

The chit should:
1. Clearly state the action requested
2. Convey appropriate urgency ({urgency})
3. Be diplomatic even when urgent
4. Provide necessary context
5. Request confirmation if needed

Provide 2 versions:
1. **Diplomatic**: Polite request format
2. **Urgent**: More direct, for time-sensitive matters

Format as ready-to-write chits."""

        # Use Ollama for quick chit generation
        return self._call_ollama(prompt)

    def generate_chit_response(
        self, original_chit: str, response_type: str = "positive", my_country: str = ""
    ) -> str:
        """Generate a response to a received chit (uses Ollama for quick generation)"""
        if not self.ollama_client and not self.gemini_client:
            return "AI service not configured"

        from_info = f" from {my_country}" if my_country else ""

        prompt = f"""Generate a response chit{from_info} to this received chit:

RECEIVED CHIT:
{original_chit}

Response type: {response_type} (positive/negative/neutral/counter-proposal)

The response should:
1. Acknowledge their message
2. Clearly state your response ({response_type})
3. Maintain diplomatic tone even if declining
4. Suggest next steps if appropriate
5. Keep it concise

Provide the response chit ready to send."""

        # Use Ollama for quick chit generation
        return self._call_ollama(prompt)

    # ============= SESSION SUMMARIZATION =============

    def generate_session_summary(
        self,
        session_data: Dict,
        notes: List[Dict],
        speeches: List[Dict],
        chat_history: List[Dict],
    ) -> Dict:
        """Generate comprehensive MUN session summary (uses Ollama for quick summaries)"""
        if not self.ollama_client and not self.gemini_client:
            return {"error": "AI service not configured"}

        # Prepare context
        session_info = f"""
Session Name: {session_data.get("name", "Unknown")}
Description: {session_data.get("description", "N/A")}
Dates: {session_data.get("dates", "N/A")}
Duration: {session_data.get("created_at", "")} to {session_data.get("ended_at", "N/A")}
"""

        notes_summary = "\n\n".join(
            [
                f"**{note.get('title', 'Untitled')}**\n{note.get('content', '')[:500]}..."
                for note in notes[:20]  # Limit to prevent token overflow
            ]
        )

        speeches_summary = "\n\n".join(
            [
                f"**Speech on {speech.get('topic', 'Unknown')}** ({speech.get('country', 'Unknown')})\n{speech.get('content', '')[:300]}..."
                for speech in speeches[:10]
            ]
        )

        chat_summary = "\n".join(
            [
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:200]}..."
                for msg in chat_history[-30:]  # Last 30 messages
            ]
        )

        prompt = f"""As an expert MUN advisor, generate a comprehensive summary of this completed MUN session.

## SESSION INFORMATION:
{session_info}

## NOTES CREATED ({len(notes)} total):
{notes_summary}

## SPEECHES GIVEN ({len(speeches)} total):
{speeches_summary}

## AI INTERACTIONS (Last 30):
{chat_summary}

Generate a comprehensive session summary with the following structure:

# MUN SESSION SUMMARY

## EXECUTIVE SUMMARY
[2-3 paragraph overview of the entire session]

## KEY ACHIEVEMENTS
- [Major accomplishments]
- [Successful strategies]
- [Important outcomes]

## RESEARCH CONDUCTED
### Topics Covered:
- [Main research areas]
- [Countries analyzed]
- [Issues explored]

### Key Findings:
- [Important facts discovered]
- [Strategic insights gained]
- [Useful data points]

## DIPLOMATIC ACTIVITIES
### Speeches:
- [Speech topics and effectiveness]
- [Key arguments made]
- [Reception and impact]

### Alliances & Negotiations:
- [Countries worked with]
- [Agreements reached]
- [Conflicts managed]

## SKILLS DEVELOPED
- [Public speaking improvements]
- [Research skills gained]
- [Diplomatic techniques learned]
- [Procedural knowledge acquired]

## LESSONS LEARNED
### What Worked Well:
- [Successful strategies]
- [Effective approaches]

### Areas for Improvement:
- [Challenges faced]
- [Mistakes made]
- [Skills to develop]

## KNOWLEDGE BASE FOR FUTURE SESSIONS
[Compressed, actionable knowledge that would be useful in future MUNs]

### Key Facts & Statistics:
- [Important data to remember]

### Effective Arguments:
- [Arguments that worked]

### Procedural Insights:
- [MUN procedures learned]

### Country Positions:
- [Understanding of different countries' stances]

## RECOMMENDATIONS FOR NEXT SESSION
- [Specific advice for improvement]
- [Topics to research further]
- [Skills to practice]

Be comprehensive but concise. Focus on actionable insights and transferable knowledge."""

        # Use Ollama for quick session summary
        response = self._call_ollama(prompt)

        # Also generate compressed memory for import
        memory_prompt = f"""Based on this MUN session, create a compressed knowledge base that can be imported into future sessions.

Session Context:
{session_info}

Include only the most valuable, reusable information:
1. Key facts and statistics discovered
2. Effective arguments and counter-arguments
3. Country positions and behaviors
4. Successful diplomatic strategies
5. Important procedural knowledge
6. Useful resources and references

Format as a structured knowledge base (bullet points, concise statements).
Limit to approximately 1000 words of the most critical information."""

        # Use Ollama for quick memory compression
        compressed_memory = self._call_ollama(memory_prompt)

        return {
            "summary": response,
            "compressed_memory": compressed_memory,
            "stats": {
                "notes_count": len(notes),
                "speeches_count": len(speeches),
                "chat_interactions": len(chat_history),
            },
        }

    def merge_session_memories(self, existing_memory: str, imported_memory: str) -> str:
        """Merge imported session memory with existing session (uses Ollama for quick merging)"""
        if not self.ollama_client and not self.gemini_client:
            return existing_memory

        prompt = f"""Intelligently merge these two MUN knowledge bases, removing duplicates and organizing information coherently.

## EXISTING KNOWLEDGE:
{existing_memory}

## IMPORTED KNOWLEDGE:
{imported_memory}

Create a unified, well-organized knowledge base that:
1. Removes duplicate information
2. Combines complementary insights
3. Maintains clear structure
4. Prioritizes most useful information
5. Stays concise and actionable

Output the merged knowledge base."""

        # Use Ollama for quick memory merging
        return self._call_ollama(prompt)


if __name__ == "__main__":
    # Test the AI service
    from core.vectordb import initialize_vector_db

    print("Initializing vector database...")
    vectordb = initialize_vector_db()

    print("\nInitializing AI service...")
    ai_service = AIService(vectordb)

    print(f"\nAvailable provider: {ai_service.get_available_provider()}")

    # Test chat
    print("\n=== Testing Chat ===")
    response = ai_service.chat_with_context(
        "What are the key rules of procedure in MUN?"
    )
    print(response[:300] + "...")

    # Test speech generation
    print("\n=== Testing Speech Generation ===")
    speech = ai_service.generate_speech(
        country="India",
        topic="Climate Change and Sustainable Development",
        committee="UNEP",
    )
    print(speech[:300] + "...")
