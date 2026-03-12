"""
Unit tests for Agent Orchestrator
Tests multi-agent coordination and workflow management
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestAgentOrchestrator:
    """Test Agent Orchestrator functionality"""

    @patch('agents.orchestrator.ResearchAgent')
    @patch('agents.orchestrator.AnalysisAgent')
    @patch('agents.orchestrator.FormattingAgent')
    def test_orchestrator_initialization(self, mock_formatting, mock_analysis, mock_research):
        """Test orchestrator initializes all agents"""
        from agents.orchestrator import AgentOrchestrator

        mock_vectordb = Mock()
        orchestrator = AgentOrchestrator(vectordb=mock_vectordb)

        assert orchestrator.vectordb == mock_vectordb
        assert orchestrator.research_agent is not None
        assert orchestrator.analysis_agent is not None
        assert orchestrator.formatting_agent is not None

    @patch('agents.orchestrator.ResearchAgent')
    @patch('agents.orchestrator.AnalysisAgent')
    @patch('agents.orchestrator.FormattingAgent')
    @patch('agents.orchestrator.MemoryManager')
    def test_research_workflow_execution(self, mock_memory, mock_formatting, mock_analysis, mock_research):
        """Test executing a complete research workflow"""
        from agents.orchestrator import AgentOrchestrator

        # Setup mocks
        mock_vectordb = Mock()
        mock_vectordb.get_context_for_query = Mock(return_value="Vector DB context")

        mock_research_instance = Mock()
        mock_research_instance.execute = Mock(return_value={
            'success': True,
            'output': 'Research findings'
        })
        mock_research.return_value = mock_research_instance

        mock_analysis_instance = Mock()
        mock_analysis_instance.execute = Mock(return_value={
            'success': True,
            'output': 'Analysis results'
        })
        mock_analysis.return_value = mock_analysis_instance

        mock_formatting_instance = Mock()
        mock_formatting_instance.execute = Mock(return_value={
            'success': True,
            'output': 'Formatted output'
        })
        mock_formatting.return_value = mock_formatting_instance

        mock_memory_instance = Mock()
        mock_memory_instance.get_compact_memory_for_llm = Mock(return_value="Memory context")
        mock_memory_instance.get_research_history_for_topic = Mock(return_value="Research history")
        mock_memory.return_value = mock_memory_instance

        orchestrator = AgentOrchestrator(vectordb=mock_vectordb)

        result = orchestrator.execute_research_workflow(
            research_type="foreign_policy",
            country="USA",
            topic="Climate Change",
            analyze=True
        )

        assert result is not None
        assert mock_research_instance.execute.called
        assert mock_analysis_instance.execute.called
        assert mock_formatting_instance.execute.called

    @patch('agents.orchestrator.POISpecialistAgent')
    def test_poi_generation_workflow(self, mock_poi):
        """Test POI generation workflow"""
        from agents.orchestrator import AgentOrchestrator

        mock_poi_instance = Mock()
        mock_poi_instance.execute = Mock(return_value={
            'success': True,
            'output': 'Generated POI questions'
        })
        mock_poi.return_value = mock_poi_instance

        orchestrator = AgentOrchestrator()

        result = orchestrator.execute_poi_workflow(
            country="USA",
            target_country="China",
            topic="Trade Policy"
        )

        assert result is not None
        mock_poi_instance.execute.assert_called_once()

    @patch('agents.orchestrator.CoalitionBuilderAgent')
    def test_coalition_building_workflow(self, mock_coalition):
        """Test coalition building workflow"""
        from agents.orchestrator import AgentOrchestrator

        mock_coalition_instance = Mock()
        mock_coalition_instance.execute = Mock(return_value={
            'success': True,
            'output': 'Coalition strategy'
        })
        mock_coalition.return_value = mock_coalition_instance

        orchestrator = AgentOrchestrator()

        result = orchestrator.execute_coalition_workflow(
            country="USA",
            topic="Climate Change",
            position="Support renewable energy"
        )

        assert result is not None
        mock_coalition_instance.execute.assert_called_once()

    @patch('agents.orchestrator.CrisisManagerAgent')
    def test_crisis_response_workflow(self, mock_crisis):
        """Test crisis response workflow"""
        from agents.orchestrator import AgentOrchestrator

        mock_crisis_instance = Mock()
        mock_crisis_instance.execute = Mock(return_value={
            'success': True,
            'output': 'Crisis response plan'
        })
        mock_crisis.return_value = mock_crisis_instance

        orchestrator = AgentOrchestrator()

        result = orchestrator.execute_crisis_workflow(
            country="USA",
            crisis_scenario="Sudden conflict in region",
            time_pressure="high"
        )

        assert result is not None
        mock_crisis_instance.execute.assert_called_once()

    def test_memory_integration_in_workflows(self, mock_vectordb):
        """Test that workflows integrate with memory manager"""
        from agents.orchestrator import AgentOrchestrator

        with patch('agents.orchestrator.MemoryManager') as mock_memory_class:
            mock_memory_instance = Mock()
            mock_memory_instance.get_compact_memory_for_llm = Mock(return_value="Memory")
            mock_memory_instance.get_research_history_for_topic = Mock(return_value="History")
            mock_memory_instance.track_agent_execution = Mock()
            mock_memory_class.return_value = mock_memory_instance

            orchestrator = AgentOrchestrator(vectordb=mock_vectordb)

            # Verify memory manager was initialized
            assert orchestrator.memory is not None
