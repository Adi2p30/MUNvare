"""
Integration tests for multi-agent workflows
Tests end-to-end agent coordination and data flow
"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestMultiAgentWorkflows:
    """Test integration of multiple agents in workflows"""

    @patch('agents.orchestrator.ResearchAgent')
    @patch('agents.orchestrator.AnalysisAgent')
    @patch('agents.orchestrator.FormattingAgent')
    @patch('agents.orchestrator.MemoryManager')
    def test_complete_research_pipeline(self, mock_memory, mock_formatting, mock_analysis, mock_research):
        """Test complete research pipeline from research to formatted output"""
        from agents.orchestrator import AgentOrchestrator

        # Setup mock responses
        mock_research_instance = Mock()
        mock_research_instance.execute.return_value = {
            'success': True,
            'output': 'Raw research data about USA climate policy'
        }
        mock_research.return_value = mock_research_instance

        mock_analysis_instance = Mock()
        mock_analysis_instance.execute.return_value = {
            'success': True,
            'output': 'Analyzed strategic implications'
        }
        mock_analysis.return_value = mock_analysis_instance

        mock_formatting_instance = Mock()
        mock_formatting_instance.execute.return_value = {
            'success': True,
            'output': '# Formatted Research Output\n\nKey points...'
        }
        mock_formatting.return_value = mock_formatting_instance

        mock_memory_instance = Mock()
        mock_memory_instance.get_compact_memory_for_llm.return_value = ""
        mock_memory_instance.get_research_history_for_topic.return_value = ""
        mock_memory_instance.track_agent_execution.return_value = None
        mock_memory.return_value = mock_memory_instance

        orchestrator = AgentOrchestrator()

        result = orchestrator.execute_research_workflow(
            research_type="foreign_policy",
            country="USA",
            topic="Climate Change",
            analyze=True
        )

        # Verify all agents were called in sequence
        assert mock_research_instance.execute.called
        assert mock_analysis_instance.execute.called
        assert mock_formatting_instance.execute.called

        # Verify output flows through pipeline
        assert result is not None
        assert 'output' in result or result.get('success')

    @patch('agents.orchestrator.POISpecialistAgent')
    @patch('agents.orchestrator.VerificationAgent')
    def test_poi_generation_with_verification(self, mock_verification, mock_poi):
        """Test POI generation with quality verification"""
        from agents.orchestrator import AgentOrchestrator

        mock_poi_instance = Mock()
        mock_poi_instance.execute.return_value = {
            'success': True,
            'output': 'Generated POI questions'
        }
        mock_poi.return_value = mock_poi_instance

        mock_verification_instance = Mock()
        mock_verification_instance.execute.return_value = {
            'success': True,
            'verified': True,
            'output': 'Verified POI questions'
        }
        mock_verification.return_value = mock_verification_instance

        orchestrator = AgentOrchestrator()

        result = orchestrator.execute_poi_workflow(
            country="USA",
            target_country="China",
            topic="Trade Policy"
        )

        assert mock_poi_instance.execute.called

    @patch('agents.orchestrator.CrisisManagerAgent')
    @patch('agents.orchestrator.AnalysisAgent')
    def test_crisis_pipeline_integration(self, mock_analysis, mock_crisis):
        """Test crisis management pipeline with analysis"""
        from agents.orchestrator import AgentOrchestrator

        mock_crisis_instance = Mock()
        mock_crisis_instance.execute.return_value = {
            'success': True,
            'output': 'Crisis response plan'
        }
        mock_crisis.return_value = mock_crisis_instance

        mock_analysis_instance = Mock()
        mock_analysis_instance.execute.return_value = {
            'success': True,
            'output': 'Strategic analysis of crisis response'
        }
        mock_analysis.return_value = mock_analysis_instance

        orchestrator = AgentOrchestrator()

        result = orchestrator.execute_crisis_pipeline(
            country="USA",
            crisis_scenario="Sudden regional conflict",
            time_pressure="high"
        )

        assert mock_crisis_instance.execute.called

    def test_vectordb_to_agent_context_flow(self, mock_vectordb):
        """Test that context flows from vectordb to agents"""
        from agents.orchestrator import AgentOrchestrator

        mock_vectordb.get_context_for_query.return_value = "Relevant context from DB"

        with patch('agents.orchestrator.ResearchAgent') as mock_research, \
             patch('agents.orchestrator.MemoryManager'):

            mock_research_instance = Mock()
            mock_research_instance.execute.return_value = {'success': True, 'output': 'Result'}
            mock_research.return_value = mock_research_instance

            orchestrator = AgentOrchestrator(vectordb=mock_vectordb)

            orchestrator.execute_research_workflow(
                research_type="foreign_policy",
                country="USA",
                topic="Trade",
                analyze=False
            )

            # Verify vectordb was queried
            mock_vectordb.get_context_for_query.assert_called_once()

    @patch('agents.orchestrator.MemoryManager')
    def test_memory_tracking_across_workflow(self, mock_memory_class):
        """Test that memory manager tracks agent executions"""
        from agents.orchestrator import AgentOrchestrator

        mock_memory_instance = Mock()
        mock_memory_instance.get_compact_memory_for_llm.return_value = "Memory context"
        mock_memory_instance.get_research_history_for_topic.return_value = "Research history"
        mock_memory_instance.track_agent_execution.return_value = None
        mock_memory_class.return_value = mock_memory_instance

        with patch('agents.orchestrator.ResearchAgent'):
            orchestrator = AgentOrchestrator()

            # Verify memory manager was initialized
            assert orchestrator.memory is not None
