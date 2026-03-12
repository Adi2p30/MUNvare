"""
Agent Orchestrator - Coordinates multiple agents to complete complex tasks
Supports parallel execution, sequential pipelines, and streaming responses
Includes memory tracking for enhanced LLM context
"""
from typing import Dict, Any, List, Generator, Union
import concurrent.futures
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .research_agent import ResearchAgent
from .analysis_agent import AnalysisAgent
from .formatting_agent import FormattingAgent
from .poi_specialist import POISpecialistAgent
from .verification_agent import VerificationAgent
from .coalition_builder_agent import CoalitionBuilderAgent
from .debate_coach_agent import DebateCoachAgent
from .resolution_crafter_agent import ResolutionCrafterAgent
from .crisis_manager_agent import CrisisManagerAgent
from .importance_filter_agent import ImportanceFilterAgent
from .live_notes_agent import LiveNotesAgent
from managers.memory_manager import MemoryManager


class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents to complete complex MUN research tasks.
    Manages workflow, agent coordination, and output synthesis.
    """

    def __init__(self, vectordb=None):
        """
        Initialize the orchestrator with all specialized agents.

        Args:
            vectordb: Optional vector database for context retrieval
        """
        self.vectordb = vectordb

        # Core agents
        self.research_agent = ResearchAgent()
        self.analysis_agent = AnalysisAgent()
        self.formatting_agent = FormattingAgent()

        # Specialized agents
        self.poi_specialist = POISpecialistAgent()
        self.verification_agent = VerificationAgent()
        self.coalition_builder = CoalitionBuilderAgent()
        self.debate_coach = DebateCoachAgent()
        self.resolution_crafter = ResolutionCrafterAgent()
        self.crisis_manager = CrisisManagerAgent()

        # Live processing agents (Gemma-based for speed)
        self.importance_filter = ImportanceFilterAgent()
        self.live_notes_agent = LiveNotesAgent()

        # Memory manager for tracking and context
        self.memory = MemoryManager()

        self.workflow_history = []
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

    def execute_research_workflow(self, research_type: str, country: str, topic: str,
                                  target_country: str = "", analyze: bool = True) -> Dict[str, Any]:
        """
        Execute a complete research workflow with multiple agents.

        Args:
            research_type: Type of research (foreign_policy, poi, country_profile, etc.)
            country: Country name
            topic: Research topic
            target_country: Optional target country (for POI)
            analyze: Whether to include strategic analysis

        Returns:
            Dictionary with formatted research output
        """
        print(f"🚀 Starting {research_type} workflow for {country} on {topic}")

        # Step 1: Get context from vector database if available
        context = None
        if self.vectordb:
            try:
                query = f"{country} {topic} {research_type}"
                context = self.vectordb.get_context_for_query(query, max_context_length=2500)
                print("✓ Retrieved context from knowledge base")
            except Exception as e:
                print(f"⚠ Could not retrieve context: {e}")

        # Add memory context to enhance LLM understanding
        memory_context = self.memory.get_compact_memory_for_llm(max_tokens=300)
        research_history = self.memory.get_research_history_for_topic(country, topic)

        if memory_context or research_history:
            additional_context = f"\n\n# System Memory\n{memory_context}\n\n{research_history}"
            if context:
                context = context + additional_context
            else:
                context = additional_context
            print("✓ Added memory context to LLM")

        # Step 2: Research Agent conducts research
        print(f"🔍 Research Agent: Conducting {research_type} research...")
        research_task = {
            'type': research_type,
            'country': country,
            'topic': topic,
            'target_country': target_country
        }

        research_result = self.research_agent.execute(research_task, context)
        print("✓ Research completed")

        # Track research in memory
        self.memory.track_research_completed(
            research_type,
            country,
            topic,
            research_result.get('raw_research', '')[:300]
        )
        self.memory.track_agent_execution(self.research_agent.name, f"{research_type} research", True)
        self.memory.update_session_context({
            'current_country': country,
            'current_topic': topic,
            'last_research_type': research_type
        })

        # Step 3: Analysis Agent provides strategic insights (if requested)
        analysis_result = None
        if analyze:
            print(f"📊 Analysis Agent: Generating strategic insights...")
            analysis_task = {
                'research_output': research_result['raw_research'],
                'analysis_type': 'strategic',
                'country': country,
                'topic': topic
            }
            analysis_result = self.analysis_agent.execute(analysis_task)
            print("✓ Analysis completed")

        # Step 4: Formatting Agent creates professional output
        print(f"✨ Formatting Agent: Creating professional output...")
        formatting_task = {
            'research': research_result['raw_research'],
            'analysis': analysis_result['analysis'] if analysis_result else '',
            'format_type': research_type,
            'country': country,
            'topic': topic
        }

        formatted_result = self.formatting_agent.execute(formatting_task)
        print("✓ Output formatted")

        # Step 5: Compile final result
        final_output = {
            'success': True,
            'output': formatted_result['formatted_output'],
            'metadata': {
                'research_type': research_type,
                'country': country,
                'topic': topic,
                'agents_used': [
                    self.research_agent.name,
                    self.analysis_agent.name if analyze else None,
                    self.formatting_agent.name
                ],
                'workflow': 'research_analysis_format' if analyze else 'research_format'
            }
        }

        # Log workflow
        self.workflow_history.append({
            'type': research_type,
            'country': country,
            'topic': topic,
            'success': True
        })

        print("✅ Workflow completed successfully!")
        return final_output

    def generate_poi_questions(self, country: str, topic: str, target_country: str = "") -> Dict[str, Any]:
        """Generate POI questions using agentic workflow."""
        return self.execute_research_workflow(
            research_type='poi',
            country=country,
            topic=topic,
            target_country=target_country,
            analyze=True
        )

    def research_foreign_policy(self, country: str, topic: str) -> Dict[str, Any]:
        """Research foreign policy using agentic workflow."""
        return self.execute_research_workflow(
            research_type='foreign_policy',
            country=country,
            topic=topic,
            analyze=True
        )

    def generate_country_profile(self, country: str, topic: str = "") -> Dict[str, Any]:
        """Generate country profile using agentic workflow."""
        return self.execute_research_workflow(
            research_type='country_profile',
            country=country,
            topic=topic,
            analyze=True
        )

    def find_allies(self, country: str, topic: str) -> Dict[str, Any]:
        """Find potential allies using agentic workflow."""
        return self.execute_research_workflow(
            research_type='allies',
            country=country,
            topic=topic,
            analyze=True
        )

    def analyze_opposition(self, country: str, topic: str) -> Dict[str, Any]:
        """Analyze opposition using agentic workflow."""
        return self.execute_research_workflow(
            research_type='opposition',
            country=country,
            topic=topic,
            analyze=True
        )

    def suggest_modcaucus_topics(self, agenda: str, committee: str) -> Dict[str, Any]:
        """Generate moderated caucus topic suggestions."""
        print(f"🚀 Starting modcaucus workflow for {agenda}")

        # Get context
        context = None
        if self.vectordb:
            try:
                context = self.vectordb.get_context_for_query(agenda, max_context_length=2000)
                print("✓ Retrieved context")
            except Exception as e:
                print(f"⚠ Could not retrieve context: {e}")

        # Research Agent generates topics
        print(f"🔍 Research Agent: Generating modcaucus topics...")
        research_result = self.research_agent.research_modcaucus_topics(agenda, committee, context)
        print("✓ Topics generated")

        # Format output
        print(f"✨ Formatting Agent: Creating professional output...")
        formatting_task = {
            'research': research_result['raw_research'],
            'analysis': '',
            'format_type': 'modcaucus',
            'country': '',
            'topic': agenda
        }

        formatted_result = self.formatting_agent.execute(formatting_task)
        print("✓ Output formatted")

        print("✅ Workflow completed!")
        return {
            'success': True,
            'output': formatted_result['formatted_output'],
            'metadata': {
                'research_type': 'modcaucus',
                'agenda': agenda,
                'committee': committee
            }
        }

    def prepare_debate(self, my_country: str, opponent_country: str, topic: str) -> Dict[str, Any]:
        """Prepare for debate using multi-agent workflow."""
        print(f"🚀 Starting debate prep workflow: {my_country} vs {opponent_country} on {topic}")

        # Get context
        context = None
        if self.vectordb:
            try:
                query = f"{my_country} {opponent_country} {topic} debate"
                context = self.vectordb.get_context_for_query(query, max_context_length=3000)
                print("✓ Retrieved context")
            except Exception as e:
                print(f"⚠ Could not retrieve context: {e}")

        # Research both positions
        print(f"🔍 Research Agent: Analyzing both positions...")
        research_task = {
            'type': 'general',
            'country': my_country,
            'topic': f"Debate preparation: {my_country} vs {opponent_country} on {topic}"
        }

        research_result = self.research_agent.execute(research_task, context)
        print("✓ Research completed")

        # Strategic analysis for debate
        print(f"📊 Analysis Agent: Developing debate strategy...")
        analysis_task = {
            'research_output': research_result['raw_research'],
            'analysis_type': 'debate_prep',
            'country': my_country,
            'topic': topic
        }

        analysis_result = self.analysis_agent.execute(analysis_task)
        print("✓ Strategy developed")

        # Format for easy use
        print(f"✨ Formatting Agent: Creating debate prep guide...")
        formatting_task = {
            'research': research_result['raw_research'],
            'analysis': analysis_result['analysis'],
            'format_type': 'general',
            'country': my_country,
            'topic': f"Debate vs {opponent_country}"
        }

        formatted_result = self.formatting_agent.execute(formatting_task)
        print("✓ Guide formatted")

        print("✅ Debate prep complete!")
        return {
            'success': True,
            'output': formatted_result['formatted_output'],
            'metadata': {
                'research_type': 'debate_prep',
                'my_country': my_country,
                'opponent': opponent_country,
                'topic': topic
            }
        }

    def generate_crisis_response(self, country: str, crisis_description: str) -> Dict[str, Any]:
        """Generate crisis response using multi-agent workflow."""
        print(f"🚀 Starting crisis response workflow for {country}")

        # Get context
        context = None
        if self.vectordb:
            try:
                context = self.vectordb.get_context_for_query(f"{country} crisis management", max_context_length=2000)
                print("✓ Retrieved context")
            except Exception as e:
                print(f"⚠ Could not retrieve context: {e}")

        # Research crisis context
        print(f"🔍 Research Agent: Analyzing crisis...")
        research_task = {
            'type': 'general',
            'country': country,
            'topic': f"Crisis: {crisis_description}"
        }

        research_result = self.research_agent.execute(research_task, context)
        print("✓ Analysis completed")

        # Strategic response planning
        print(f"📊 Analysis Agent: Developing response strategy...")
        analysis_task = {
            'research_output': research_result['raw_research'],
            'analysis_type': 'crisis_response',
            'country': country,
            'topic': crisis_description
        }

        analysis_result = self.analysis_agent.execute(analysis_task)
        print("✓ Strategy developed")

        # Format response plan
        print(f"✨ Formatting Agent: Creating action plan...")
        formatting_task = {
            'research': research_result['raw_research'],
            'analysis': analysis_result['analysis'],
            'format_type': 'general',
            'country': country,
            'topic': "Crisis Response Plan"
        }

        formatted_result = self.formatting_agent.execute(formatting_task)
        print("✓ Plan formatted")

        print("✅ Crisis response ready!")
        return {
            'success': True,
            'output': formatted_result['formatted_output'],
            'metadata': {
                'research_type': 'crisis_response',
                'country': country
            }
        }

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get statistics about workflows executed."""
        return {
            'total_workflows': len(self.workflow_history),
            'recent_workflows': self.workflow_history[-5:],
            'agents': {
                'research': self.research_agent.name,
                'analysis': self.analysis_agent.name,
                'formatting': self.formatting_agent.name,
                'poi_specialist': self.poi_specialist.name,
                'verification': self.verification_agent.name,
                'coalition_builder': self.coalition_builder.name,
                'debate_coach': self.debate_coach.name,
                'resolution_crafter': self.resolution_crafter.name,
                'crisis_manager': self.crisis_manager.name
            }
        }

    # ==================== INTRICATE PIPELINE METHODS ====================

    def execute_parallel_pipeline(self, country: str, topic: str, tasks: List[str]) -> Dict[str, Any]:
        """
        Execute multiple agent tasks in parallel for maximum efficiency.

        Args:
            country: Country name
            topic: Topic
            tasks: List of task types to execute in parallel

        Returns:
            Dictionary with all results
        """
        print(f"🚀 Starting parallel pipeline with {len(tasks)} agents for {country} on {topic}")

        # Get shared context once
        context = None
        if self.vectordb:
            try:
                query = f"{country} {topic}"
                context = self.vectordb.get_context_for_query(query, max_context_length=3000)
                print(f"✓ Retrieved shared context")
            except Exception as e:
                print(f"⚠ Could not retrieve context: {e}")

        # Execute tasks in parallel using ThreadPoolExecutor
        futures = {}
        results = {}

        for task_type in tasks:
            if task_type == 'research':
                future = self.executor.submit(
                    self.research_agent.execute,
                    {'type': 'foreign_policy', 'country': country, 'topic': topic},
                    context
                )
                futures['research'] = future

            elif task_type == 'allies':
                future = self.executor.submit(
                    self.coalition_builder.execute,
                    {'country': country, 'topic': topic, 'research_context': context},
                    context
                )
                futures['allies'] = future

            elif task_type == 'opposition':
                future = self.executor.submit(
                    self.research_agent.execute,
                    {'type': 'opposition', 'country': country, 'topic': topic},
                    context
                )
                futures['opposition'] = future

            elif task_type == 'poi':
                future = self.executor.submit(
                    self.poi_specialist.execute,
                    {'country': country, 'topic': topic},
                    context
                )
                futures['poi'] = future

        # Collect results as they complete
        print(f"⏳ Waiting for {len(futures)} parallel tasks...")
        for task_name, future in futures.items():
            try:
                results[task_name] = future.result(timeout=120)
                print(f"✓ {task_name} completed")
            except Exception as e:
                print(f"✗ {task_name} failed: {e}")
                results[task_name] = {'success': False, 'error': str(e)}

        print(f"✅ Parallel pipeline completed! {len(results)} results ready")

        return {
            'success': True,
            'results': results,
            'metadata': {
                'execution_mode': 'parallel',
                'tasks_completed': len(results),
                'country': country,
                'topic': topic
            }
        }

    def execute_comprehensive_research_pipeline(self, country: str, topic: str,
                                                committee: str = "", stream: bool = False) -> Union[Generator, Dict[str, Any]]:
        """
        Execute a comprehensive research pipeline with multiple stages.

        Pipeline stages:
        1. Parallel Research (Foreign Policy, Allies, Opposition)
        2. Verification (Quality check)
        3. Strategic Analysis
        4. Debate Preparation
        5. Coalition Strategy
        6. Resolution Drafting
        7. Final Formatting

        Args:
            country: Country name
            topic: Topic
            committee: Committee name
            stream: Whether to stream progress updates

        Yields:
            Progress updates if streaming, final result otherwise
        """
        if stream:
            yield {'stage': 'init', 'message': f'🚀 Starting comprehensive research for {country} on {topic}'}

        # Stage 1: Parallel Research (3 agents at once)
        if stream:
            yield {'stage': 'research', 'message': '📚 Stage 1: Conducting parallel research...'}

        parallel_results = self.execute_parallel_pipeline(country, topic, ['research', 'allies', 'opposition'])
        research_output = parallel_results['results'].get('research', {}).get('raw_research', '')
        allies_output = parallel_results['results'].get('allies', {}).get('coalition_strategy', '')
        opposition_output = parallel_results['results'].get('opposition', {}).get('raw_research', '')

        if stream:
            yield {'stage': 'research', 'message': '✓ Research complete', 'data': {
                'research_length': len(research_output),
                'allies_found': 'Yes' if allies_output else 'No',
                'opposition_analyzed': 'Yes' if opposition_output else 'No'
            }}

        # Stage 2: Verification
        if stream:
            yield {'stage': 'verification', 'message': '🔍 Stage 2: Verifying research quality...'}

        verification_result = self.verification_agent.execute({
            'research_output': research_output,
            'topic': topic,
            'country': country
        })

        if stream:
            yield {'stage': 'verification', 'message': '✓ Verification complete'}

        # Stage 3: Strategic Analysis
        if stream:
            yield {'stage': 'analysis', 'message': '📊 Stage 3: Generating strategic analysis...'}

        analysis_result = self.analysis_agent.execute({
            'research_output': f"{research_output}\n\nAllies Strategy:\n{allies_output}\n\nOpposition Analysis:\n{opposition_output}",
            'analysis_type': 'strategic',
            'country': country,
            'topic': topic
        })

        if stream:
            yield {'stage': 'analysis', 'message': '✓ Strategic analysis complete'}

        # Stage 4: Debate Preparation
        if stream:
            yield {'stage': 'debate_prep', 'message': '🎯 Stage 4: Preparing debate strategy...'}

        debate_prep = self.debate_coach.execute({
            'country': country,
            'topic': topic,
            'research': research_output,
            'goals': 'Win debate and persuade committee'
        })

        if stream:
            yield {'stage': 'debate_prep', 'message': '✓ Debate preparation complete'}

        # Stage 5: Resolution Strategy
        if stream:
            yield {'stage': 'resolution', 'message': '📝 Stage 5: Drafting resolution strategy...'}

        resolution_draft = self.resolution_crafter.execute({
            'country': country,
            'topic': topic,
            'committee': committee or 'General Assembly',
            'objectives': f"Advance {country}'s position on {topic}",
            'research': research_output
        })

        if stream:
            yield {'stage': 'resolution', 'message': '✓ Resolution draft complete'}

        # Stage 6: Final Formatting
        if stream:
            yield {'stage': 'formatting', 'message': '✨ Stage 6: Creating professional output...'}

        # Combine all outputs
        combined_output = f"""# Comprehensive MUN Research Package: {country} on {topic}

{research_output}

---

## Coalition Strategy
{allies_output}

---

## Opposition Analysis
{opposition_output}

---

## Strategic Analysis
{analysis_result['analysis']}

---

## Debate Preparation
{debate_prep['debate_preparation']}

---

## Resolution Strategy
{resolution_draft['resolution']}

---

## Verification Report
{verification_result['verification_report']}
"""

        formatted_result = self.formatting_agent.execute({
            'research': combined_output,
            'analysis': '',
            'format_type': 'general',
            'country': country,
            'topic': topic
        })

        if stream:
            yield {'stage': 'formatting', 'message': '✓ Formatting complete'}
            yield {'stage': 'complete', 'message': '✅ Comprehensive research pipeline complete!',
                   'data': formatted_result}
        else:
            return {
                'success': True,
                'output': formatted_result['formatted_output'],
                'components': {
                    'research': research_output,
                    'allies': allies_output,
                    'opposition': opposition_output,
                    'analysis': analysis_result['analysis'],
                    'debate_prep': debate_prep['debate_preparation'],
                    'resolution': resolution_draft['resolution'],
                    'verification': verification_result['verification_report']
                },
                'metadata': {
                    'pipeline': 'comprehensive_research',
                    'stages_completed': 6,
                    'agents_used': 7
                }
            }

    def execute_crisis_pipeline(self, country: str, crisis_description: str,
                                stream: bool = False) -> Union[Generator, Dict[str, Any]]:
        """
        Execute rapid crisis response pipeline.

        Pipeline:
        1. Crisis Analysis (Crisis Manager)
        2. Parallel Strategy Development (Coalition Builder + Debate Coach)
        3. Immediate Actions Plan
        4. Final Formatting

        Args:
            country: Country responding to crisis
            crisis_description: Description of the crisis
            stream: Whether to stream updates

        Yields/Returns:
            Progress updates or final crisis response plan
        """
        if stream:
            yield {'stage': 'init', 'message': f'🚨 CRISIS RESPONSE for {country}', 'urgency': 'HIGH'}

        # Stage 1: Crisis Analysis
        if stream:
            yield {'stage': 'analysis', 'message': '⚡ Analyzing crisis situation...'}

        crisis_response = self.crisis_manager.execute({
            'country': country,
            'crisis_description': crisis_description,
            'time_sensitivity': 'High',
            'immediate_impacts': 'Analyzing...'
        })

        if stream:
            yield {'stage': 'analysis', 'message': '✓ Crisis analysis complete'}

        # Stage 2: Parallel Strategy Development
        if stream:
            yield {'stage': 'strategy', 'message': '🤝 Developing diplomatic strategy (parallel)...'}

        # Execute coalition and debate prep in parallel
        coalition_future = self.executor.submit(
            self.coalition_builder.execute,
            {
                'country': country,
                'topic': f"Crisis Response: {crisis_description[:50]}...",
                'goals': 'Build support for crisis response'
            }
        )

        debate_future = self.executor.submit(
            self.debate_coach.execute,
            {
                'country': country,
                'topic': f"Crisis: {crisis_description[:50]}...",
                'goals': 'Defend response and maintain credibility'
            }
        )

        coalition_strategy = coalition_future.result(timeout=120)
        debate_prep = debate_future.result(timeout=120)

        if stream:
            yield {'stage': 'strategy', 'message': '✓ Strategy development complete'}

        # Stage 3: Format and Deliver
        if stream:
            yield {'stage': 'finalize', 'message': '📋 Finalizing crisis response plan...'}

        combined_response = f"""{crisis_response['crisis_response']}

---

## COALITION MOBILIZATION STRATEGY
{coalition_strategy['coalition_strategy']}

---

## COMMUNICATION & DEBATE STRATEGY
{debate_prep['debate_preparation']}
"""

        formatted_result = self.formatting_agent.execute({
            'research': combined_response,
            'analysis': '',
            'format_type': 'general',
            'country': country,
            'topic': 'Crisis Response Plan'
        })

        if stream:
            yield {'stage': 'complete', 'message': '✅ Crisis response plan ready!',
                   'data': formatted_result}
        else:
            return {
                'success': True,
                'output': formatted_result['formatted_output'],
                'metadata': {
                    'pipeline': 'crisis_response',
                    'urgency': 'high',
                    'agents_used': 4
                }
            }

    def execute_debate_mastery_pipeline(self, country: str, topic: str,
                                       opponent_country: str = "", stream: bool = False) -> Union[Generator, Dict[str, Any]]:
        """
        Execute comprehensive debate preparation pipeline.

        Pipeline:
        1. Research (Parallel: Own position + Opponent analysis)
        2. POI Strategy Development
        3. Debate Coaching
        4. Verification & Quality Check
        5. Final Package

        Args:
            country: Delegate's country
            topic: Debate topic
            opponent_country: Primary opponent
            stream: Whether to stream

        Yields/Returns:
            Progress or final debate prep package
        """
        if stream:
            yield {'stage': 'init', 'message': f'🎭 Preparing {country} for elite debate performance'}

        # Stage 1: Parallel Research
        if stream:
            yield {'stage': 'research', 'message': '📖 Researching positions (parallel)...'}

        own_research_future = self.executor.submit(
            self.research_agent.execute,
            {'type': 'foreign_policy', 'country': country, 'topic': topic}
        )

        opponent_research_future = self.executor.submit(
            self.research_agent.execute,
            {'type': 'foreign_policy', 'country': opponent_country or 'opponents', 'topic': topic}
        ) if opponent_country else None

        own_research = own_research_future.result(timeout=120)
        opponent_research = opponent_research_future.result(timeout=120) if opponent_research_future else None

        if stream:
            yield {'stage': 'research', 'message': '✓ Research complete'}

        # Stage 2: POI Strategy
        if stream:
            yield {'stage': 'poi', 'message': '❓ Crafting strategic POI questions...'}

        poi_strategy = self.poi_specialist.execute({
            'country': country,
            'topic': topic,
            'target_country': opponent_country
        })

        # Also get defensive prep
        poi_defense = self.poi_specialist.analyze_defensive_prep(country, topic)

        if stream:
            yield {'stage': 'poi', 'message': '✓ POI strategy complete'}

        # Stage 3: Comprehensive Debate Coaching
        if stream:
            yield {'stage': 'coaching', 'message': '🎯 Developing debate battle plan...'}

        debate_plan = self.debate_coach.execute({
            'country': country,
            'topic': topic,
            'opponent_country': opponent_country,
            'research': own_research['raw_research'],
            'goals': 'Dominate debate and persuade committee'
        })

        if stream:
            yield {'stage': 'coaching', 'message': '✓ Debate plan complete'}

        # Stage 4: Verification
        if stream:
            yield {'stage': 'verification', 'message': '🔍 Quality check...'}

        verification = self.verification_agent.execute({
            'research_output': own_research['raw_research'],
            'topic': topic,
            'country': country
        })

        if stream:
            yield {'stage': 'verification', 'message': '✓ Verified'}

        # Stage 5: Format Everything
        if stream:
            yield {'stage': 'formatting', 'message': '✨ Creating debate mastery package...'}

        full_package = f"""# 🎭 DEBATE MASTERY PACKAGE: {country} on {topic}

## YOUR POSITION & RESEARCH
{own_research['raw_research']}

---

## OPPONENT ANALYSIS
{opponent_research['raw_research'] if opponent_research else 'General opposition analysis included in debate plan'}

---

## POI WARFARE
### Offensive POIs
{poi_strategy['poi_questions']}

### Defensive Preparation
{poi_defense['defensive_prep']}

---

## DEBATE BATTLE PLAN
{debate_plan['debate_preparation']}

---

## RESEARCH VERIFICATION
{verification['verification_report']}
"""

        formatted_result = self.formatting_agent.execute({
            'research': full_package,
            'analysis': '',
            'format_type': 'general',
            'country': country,
            'topic': f"Debate Preparation vs {opponent_country or 'Committee'}"
        })

        if stream:
            yield {'stage': 'complete', 'message': '🏆 Debate mastery package ready!',
                   'data': formatted_result}
        else:
            return {
                'success': True,
                'output': formatted_result['formatted_output'],
                'components': {
                    'own_research': own_research['raw_research'],
                    'opponent_research': opponent_research['raw_research'] if opponent_research else None,
                    'poi_offensive': poi_strategy['poi_questions'],
                    'poi_defensive': poi_defense['defensive_prep'],
                    'debate_plan': debate_plan['debate_preparation'],
                    'verification': verification['verification_report']
                },
                'metadata': {
                    'pipeline': 'debate_mastery',
                    'agents_used': 5,
                    'parallel_stages': 1
                }
            }

    def execute_live_notes_pipeline(self, transcript_chunk: str, speaker: str = "Unknown",
                                     timestamp: str = None, context: str = None, stream: bool = False) -> Union[Generator, Dict[str, Any]]:
        """
        Execute a fast live notes pipeline for real-time processing.

        Pipeline stages (optimized for <500ms total):
        1. Importance Filtering (Gemma, ~100ms) - Parallel with Note Generation
        2. Live Note Generation (Gemma, ~200ms) - Only if important

        Args:
            transcript_chunk: Raw transcript text
            speaker: Speaker name/delegate
            timestamp: ISO timestamp
            context: Optional session context
            stream: Whether to stream progress updates

        Yields/Returns:
            Progress updates if streaming, final result otherwise
        """
        from datetime import datetime

        if timestamp is None:
            timestamp = datetime.now().isoformat()

        if stream:
            yield {'stage': 'init', 'message': f'🎙️ Processing transcript from {speaker}'}

        # Stage 1: Filter for importance (fast pre-check)
        if stream:
            yield {'stage': 'filtering', 'message': '🔍 Analyzing importance...'}

        # Quick keyword pre-filter to skip obviously unimportant content
        if not self.importance_filter.quick_filter(transcript_chunk):
            if stream:
                yield {'stage': 'skip', 'message': '⏭️ Skipped: Not important', 'data': {'skipped': True}}
            else:
                return {
                    'success': True,
                    'skipped': True,
                    'importance': 0,
                    'note': None
                }
            return

        # Full importance analysis with Gemma
        filter_task = {
            'transcript_chunk': transcript_chunk,
            'speaker': speaker,
            'timestamp': timestamp
        }

        # Run filtering
        try:
            filter_result = self.importance_filter.execute(filter_task, context=context)
        except Exception as e:
            print(f"⚠ Importance filter error: {e}")
            filter_result = {'is_important': False, 'importance': 0}

        if stream:
            yield {'stage': 'filtering', 'message': f'✓ Importance: {filter_result.get("importance", 0)}/10',
                   'data': filter_result}

        # Check if important enough (threshold: 7/10)
        if not filter_result.get('is_important', False):
            if stream:
                yield {'stage': 'skip', 'message': '⏭️ Below importance threshold', 'data': {'skipped': True}}
            else:
                return {
                    'success': True,
                    'skipped': True,
                    'importance': filter_result.get('importance', 0),
                    'note': None
                }
            return

        # Stage 2: Generate structured note
        if stream:
            yield {'stage': 'note_generation', 'message': '📝 Generating structured note...'}

        notes_task = {
            'transcript_chunk': transcript_chunk,
            'speaker': speaker,
            'timestamp': timestamp,
            'category': filter_result.get('category', 'general'),
            'summary': filter_result.get('summary', '')
        }

        try:
            note_result = self.live_notes_agent.execute(notes_task, context=context)
        except Exception as e:
            print(f"⚠ Live notes agent error: {e}")
            note_result = {
                'title': f'Note from {speaker}',
                'content': transcript_chunk[:200],
                'tags': [filter_result.get('category', 'general')],
                'category': filter_result.get('category', 'general'),
                'timestamp': timestamp,
                'speaker': speaker
            }

        if stream:
            yield {'stage': 'complete', 'message': '✅ Note generated!',
                   'data': {
                       'importance': filter_result.get('importance'),
                       'note': note_result
                   }}
        else:
            return {
                'success': True,
                'skipped': False,
                'importance': filter_result.get('importance'),
                'category': filter_result.get('category'),
                'note': note_result
            }

    def __del__(self):
        """Cleanup executor when orchestrator is destroyed."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
