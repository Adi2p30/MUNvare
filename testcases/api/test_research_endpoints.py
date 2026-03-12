"""
API tests for Research endpoints
Tests all research-related API routes including streaming endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestResearchEndpoints:
    """Test Research API endpoints"""

    @patch('app.agent_orchestrator')
    def test_comprehensive_research(self, mock_orchestrator, client):
        """Test POST /api/research/comprehensive"""
        mock_orchestrator.execute_comprehensive_research_pipeline.return_value = {
            'success': True,
            'output': 'Research results'
        }

        response = client.post('/api/research/comprehensive', json={
            'country': 'USA',
            'topic': 'Climate Change'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.agent_orchestrator')
    def test_foreign_policy_research(self, mock_orchestrator, client):
        """Test POST /api/research/foreign-policy"""
        mock_orchestrator.execute_research_workflow.return_value = {
            'success': True,
            'output': 'Foreign policy analysis'
        }

        response = client.post('/api/research/foreign-policy', json={
            'country': 'USA',
            'topic': 'Middle East'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.agent_orchestrator')
    def test_poi_research(self, mock_orchestrator, client):
        """Test POST /api/research/poi"""
        mock_orchestrator.execute_poi_workflow.return_value = {
            'success': True,
            'output': 'POI questions'
        }

        response = client.post('/api/research/poi', json={
            'country': 'USA',
            'target_country': 'China',
            'topic': 'Trade'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.agent_orchestrator')
    def test_crisis_response(self, mock_orchestrator, client):
        """Test POST /api/research/crisis-response"""
        mock_orchestrator.execute_crisis_pipeline.return_value = {
            'success': True,
            'output': 'Crisis response plan'
        }

        response = client.post('/api/research/crisis-response', json={
            'country': 'USA',
            'crisis_scenario': 'Regional conflict',
            'time_pressure': 'high'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.agent_orchestrator')
    def test_debate_prep(self, mock_orchestrator, client):
        """Test POST /api/research/debate-prep"""
        mock_orchestrator.execute_debate_mastery_pipeline.return_value = {
            'success': True,
            'output': 'Debate preparation'
        }

        response = client.post('/api/research/debate-prep', json={
            'country': 'USA',
            'topic': 'Nuclear Disarmament',
            'position': 'Support'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.agent_orchestrator')
    def test_allies_research(self, mock_orchestrator, client):
        """Test POST /api/research/allies"""
        mock_orchestrator.execute_coalition_workflow.return_value = {
            'success': True,
            'output': 'Potential allies'
        }

        response = client.post('/api/research/allies', json={
            'country': 'USA',
            'topic': 'Climate Change',
            'position': 'Support renewable energy'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.agent_orchestrator')
    def test_country_profile(self, mock_orchestrator, client):
        """Test POST /api/research/country-profile"""
        mock_orchestrator.execute_research_workflow.return_value = {
            'success': True,
            'output': 'Country profile'
        }

        response = client.post('/api/research/country-profile', json={
            'country': 'USA'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'output' in data

    @patch('app.notes_manager')
    def test_save_research_to_notes(self, mock_notes_manager, client):
        """Test POST /api/notes/save-research"""
        mock_notes_manager.create_note.return_value = {
            'id': 'note-123',
            'title': 'Research: Climate Change'
        }

        response = client.post('/api/notes/save-research', json={
            'title': 'Research: Climate Change',
            'content': 'Research findings...',
            'tags': ['research', 'climate']
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'note-123'
