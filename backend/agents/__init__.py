"""
MUNvare Agentic AI System

A sophisticated multi-agent system for professional MUN research and analysis.

Agents:
- BaseAgent: Foundation class for all agents
- ResearchAgent: Specialized in conducting thorough research
- AnalysisAgent: Expert in strategic analysis and synthesis
- FormattingAgent: Creates professional, well-formatted outputs
- POISpecialistAgent: Expert in crafting strategic Points of Information
- VerificationAgent: Fact-checking and quality assurance specialist
- CoalitionBuilderAgent: Alliance formation and lobbying expert
- DebateCoachAgent: Debate preparation and rhetorical strategy
- ResolutionCrafterAgent: UN resolution drafting and clause construction
- CrisisManagerAgent: Crisis response and rapid decision-making
- AgentOrchestrator: Coordinates agents to complete complex workflows

Usage:
    from agents import AgentOrchestrator

    orchestrator = AgentOrchestrator(vectordb=your_vectordb)
    result = orchestrator.research_foreign_policy("India", "Climate Change")
    print(result['output'])  # Professional formatted output
"""

from .base_agent import BaseAgent
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
from .orchestrator import AgentOrchestrator

__all__ = [
    'BaseAgent',
    'ResearchAgent',
    'AnalysisAgent',
    'FormattingAgent',
    'POISpecialistAgent',
    'VerificationAgent',
    'CoalitionBuilderAgent',
    'DebateCoachAgent',
    'ResolutionCrafterAgent',
    'CrisisManagerAgent',
    'ImportanceFilterAgent',
    'LiveNotesAgent',
    'AgentOrchestrator'
]

__version__ = '2.0.0'
