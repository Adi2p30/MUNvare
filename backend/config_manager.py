"""
Configuration and setup manager for MUN session
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

class ConfigManager:
    """Manages MUN session configuration"""

    def __init__(self, config_dir="./data/config"):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        self.config_file = os.path.join(config_dir, "mun_config.json")
        self.config = self.load_config()

    def load_config(self) -> Dict:
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return self.get_default_config()

    def get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            'my_delegate': {
                'country': '',
                'committee': '',
                'agenda': '',
                'portfolio': ''
            },
            'other_delegates': [],
            'committee_info': {
                'committee': '',
                'agenda': '',
                'study_guide': '',
                'position_paper_due': ''
            },
            'presets': {
                'selected': None,
                'custom': []
            },
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

    def save_config(self, config: Dict):
        """Save configuration to file"""
        config['updated_at'] = datetime.now().isoformat()
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        self.config = config

    def update_my_delegate(self, country: str, committee: str, agenda: str, portfolio: str = ""):
        """Update my delegate information"""
        self.config['my_delegate'] = {
            'country': country,
            'committee': committee,
            'agenda': agenda,
            'portfolio': portfolio
        }
        self.save_config(self.config)

    def add_other_delegate(self, country: str, notes: str = ""):
        """Add another delegate"""
        delegate = {
            'id': f"delegate_{len(self.config['other_delegates'])}",
            'country': country,
            'notes': notes,
            'added_at': datetime.now().isoformat()
        }
        self.config['other_delegates'].append(delegate)
        self.save_config(self.config)
        return delegate

    def remove_delegate(self, delegate_id: str):
        """Remove a delegate"""
        self.config['other_delegates'] = [
            d for d in self.config['other_delegates']
            if d['id'] != delegate_id
        ]
        self.save_config(self.config)

    def update_committee_info(self, committee: str, agenda: str, study_guide: str = "", position_paper_due: str = ""):
        """Update committee information"""
        self.config['committee_info'] = {
            'committee': committee,
            'agenda': agenda,
            'study_guide': study_guide,
            'position_paper_due': position_paper_due
        }
        self.save_config(self.config)

    def get_context_for_llm(self) -> str:
        """Get configuration context for LLM"""
        my_del = self.config['my_delegate']
        comm_info = self.config['committee_info']
        other_dels = self.config['other_delegates']

        context = f"""
MUN SESSION CONTEXT:

My Delegate:
- Country: {my_del['country']}
- Committee: {my_del['committee']}
- Agenda: {my_del['agenda']}
- Portfolio: {my_del['portfolio']}

Committee Information:
- Committee: {comm_info['committee']}
- Agenda: {comm_info['agenda']}
- Study Guide: {comm_info['study_guide']}

Other Delegates in Committee:
"""
        for delegate in other_dels:
            context += f"- {delegate['country']}"
            if delegate['notes']:
                context += f" (Notes: {delegate['notes']})"
            context += "\n"

        return context.strip()
