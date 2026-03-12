"""
API tests for Configuration endpoints
Tests delegate and committee configuration
"""
import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


class TestConfigEndpoints:
    """Test Configuration API endpoints"""

    @patch('app.config_manager')
    def test_get_config(self, mock_config_manager, client):
        """Test GET /api/config"""
        mock_config_manager.get_config.return_value = {
            'my_delegate': {'country': 'USA'},
            'other_delegates': [],
            'committee_info': {}
        }

        response = client.get('/api/config')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'my_delegate' in data

    @patch('app.config_manager')
    def test_set_delegate_info(self, mock_config_manager, client):
        """Test POST /api/config/delegate"""
        mock_config_manager.set_delegate_info.return_value = None
        mock_config_manager.get_config.return_value = {
            'my_delegate': {
                'country': 'USA',
                'committee': 'UNSC'
            }
        }

        response = client.post('/api/config/delegate', json={
            'country': 'USA',
            'committee': 'UNSC',
            'position': 'Permanent Member'
        })

        assert response.status_code == 200

    @patch('app.config_manager')
    def test_add_other_delegate(self, mock_config_manager, client):
        """Test POST /api/config/delegates"""
        mock_config_manager.add_other_delegate.return_value = {
            'id': 'delegate-id',
            'country': 'China'
        }

        response = client.post('/api/config/delegates', json={
            'country': 'China',
            'position': 'Permanent Member'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['country'] == 'China'

    @patch('app.config_manager')
    def test_delete_other_delegate(self, mock_config_manager, client):
        """Test DELETE /api/config/delegates/<delegate_id>"""
        response = client.delete('/api/config/delegates/delegate-id')

        assert response.status_code == 200
        mock_config_manager.remove_other_delegate.assert_called_with('delegate-id')

    @patch('app.config_manager')
    def test_set_committee_info(self, mock_config_manager, client):
        """Test POST /api/config/committee"""
        mock_config_manager.set_committee_info.return_value = None
        mock_config_manager.get_config.return_value = {
            'committee_info': {
                'name': 'UNSC',
                'topic': 'International Peace'
            }
        }

        response = client.post('/api/config/committee', json={
            'name': 'UNSC',
            'topic': 'International Peace',
            'rules': 'Standard ROPs'
        })

        assert response.status_code == 200
