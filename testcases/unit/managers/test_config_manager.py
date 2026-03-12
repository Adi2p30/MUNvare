"""
Unit tests for Config Manager
Tests delegate and committee configuration
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))


class TestConfigManager:
    """Test Config Manager functionality"""

    def test_set_delegate_info(self, temp_data_dir):
        """Test setting delegate information"""
        from managers.config_manager import ConfigManager

        manager = ConfigManager(data_dir=str(temp_data_dir / 'config'))

        delegate_info = {
            'country': 'United States',
            'committee': 'UNSC',
            'position': 'Permanent Member',
            'goals': 'Maintain peace'
        }

        manager.set_delegate_info(delegate_info)

        config = manager.get_config()
        assert config['my_delegate'] == delegate_info

    def test_add_other_delegate(self, temp_data_dir):
        """Test adding other delegates"""
        from managers.config_manager import ConfigManager

        manager = ConfigManager(data_dir=str(temp_data_dir / 'config'))

        delegate = {
            'country': 'China',
            'position': 'Permanent Member',
            'notes': 'Strong on sovereignty'
        }

        manager.add_other_delegate(delegate)

        config = manager.get_config()
        assert len(config['other_delegates']) == 1
        assert config['other_delegates'][0]['country'] == 'China'

    def test_remove_other_delegate(self, temp_data_dir):
        """Test removing other delegates"""
        from managers.config_manager import ConfigManager

        manager = ConfigManager(data_dir=str(temp_data_dir / 'config'))

        delegate = {'country': 'China'}
        added = manager.add_other_delegate(delegate)
        delegate_id = added['id']

        manager.remove_other_delegate(delegate_id)

        config = manager.get_config()
        assert len(config['other_delegates']) == 0

    def test_set_committee_info(self, temp_data_dir):
        """Test setting committee information"""
        from managers.config_manager import ConfigManager

        manager = ConfigManager(data_dir=str(temp_data_dir / 'config'))

        committee_info = {
            'name': 'UNSC',
            'topic': 'Situation in Middle East',
            'rules': 'Standard ROPs'
        }

        manager.set_committee_info(committee_info)

        config = manager.get_config()
        assert config['committee_info'] == committee_info

    def test_get_config(self, temp_data_dir):
        """Test getting complete configuration"""
        from managers.config_manager import ConfigManager

        manager = ConfigManager(data_dir=str(temp_data_dir / 'config'))

        config = manager.get_config()

        assert 'my_delegate' in config
        assert 'other_delegates' in config
        assert 'committee_info' in config

    def test_config_persistence(self, temp_data_dir):
        """Test that configuration persists to disk"""
        from managers.config_manager import ConfigManager

        manager = ConfigManager(data_dir=str(temp_data_dir / 'config'))
        manager.set_delegate_info({'country': 'USA'})

        # Create new manager to test persistence
        manager2 = ConfigManager(data_dir=str(temp_data_dir / 'config'))
        config = manager2.get_config()

        assert config['my_delegate']['country'] == 'USA'
